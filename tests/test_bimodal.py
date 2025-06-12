import torch
import json
from dataclasses import dataclass
from huggingface_hub import hf_hub_download
import safetensors

# Asumiendo que estos archivos están en el mismo directorio o en el PYTHONPATH
from lerobot.common.policies.smolvla.configuration_smolvla import SmolVLAConfig
from lerobot.common.policies.smolvla.modeling_smolvla import SmolVLAPolicy, rename_checkpoint_keys
from lerobot.configs.types import FeatureType, PolicyFeature

# --- 1. Configuración ---
DOF_PER_ARM = 6
NUM_ARMS = 2
DOF_TARGET = DOF_PER_ARM * NUM_ARMS

@dataclass
class SmolVLAConfigBimanual(SmolVLAConfig):
    def __post_init__(self):
        super().__post_init__()
        self.input_features = {
            "observation.state": PolicyFeature(type=FeatureType.STATE, shape=(DOF_TARGET,)),
            "observation.images.top": PolicyFeature(type=FeatureType.VISUAL, shape=(3, 480, 640)),
        }
        self.output_features = {
            "action": PolicyFeature(type=FeatureType.ACTION, shape=(DOF_TARGET,)),
        }
        self.load_vlm_weights = True

# --- 2. Funciones de ayuda ---
def create_fake_dataset_stats(dof: int):
    return {
        "observation.state": {"mean": torch.zeros(dof), "std": torch.ones(dof)},
        "action": {"mean": torch.zeros(dof), "std": torch.ones(dof)},
    }

def create_fake_bimanual_batch(batch_size: int, chunk_size: int, dof_per_arm: int, device: torch.device):
    state_arm1 = torch.randn(batch_size, chunk_size, dof_per_arm, device=device)
    state_arm2 = torch.randn(batch_size, chunk_size, dof_per_arm, device=device)
    action_arm1 = torch.randn(batch_size, chunk_size, dof_per_arm, device=device)
    action_arm2 = torch.randn(batch_size, chunk_size, dof_per_arm, device=device)
    bimanual_state = torch.cat((state_arm1, state_arm2), dim=-1)
    bimanual_action = torch.cat((action_arm1, action_arm2), dim=-1)
    return {
        "observation.state": bimanual_state,
        "observation.images.top": torch.rand(batch_size, chunk_size, 3, 480, 640, device=device),
        "task": ["perform a bimanual task"] * batch_size,
        "action": bimanual_action,
    }

# --- 3. Script de prueba ---
def test_bimanual_weight_duplication():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"--- INICIO DE LA PRUEBA EN {str(device).upper()} ---")

    target_config = SmolVLAConfigBimanual()
    dataset_stats = create_fake_dataset_stats(DOF_TARGET)
    pretrained_model_name = "lerobot/smolvla_base"
    
    print("\n1. Creando la arquitectura bimanual (12 DOF)...")
    policy = SmolVLAPolicy(config=target_config, dataset_stats=dataset_stats)
    
    print(f"\n2. Obteniendo los pesos preentrenados (6 DOF) de '{pretrained_model_name}'...")
    checkpoint_path = hf_hub_download(repo_id=pretrained_model_name, filename="model.safetensors")
    pretrained_state_dict = safetensors.torch.load_file(checkpoint_path)
    pretrained_state_dict = rename_checkpoint_keys(pretrained_state_dict, "model._orig_mod.//model.")
    
    print("\n3. Construyendo 'state_dict' con PESOS DUPLICADOS...")
    hybrid_state_dict = pretrained_state_dict.copy()
    
    # --- LÓGICA CLAVE: DUPLICACIÓN DE PESOS ---
    # Creamos un nuevo tensor de pesos de destino que tendrá el conocimiento duplicado.
    
    # Para la capa de entrada `state_proj`
    checkpoint_state_weight = pretrained_state_dict['model.state_proj.weight']
    single_arm_state_weights = checkpoint_state_weight[:, :DOF_PER_ARM] # Pesos para 6 DOF
    # El nuevo tensor tendrá la forma correcta para 12 DOF
    duplicated_state_weight = torch.zeros_like(policy.model.state_proj.weight.data)
    duplicated_state_weight[:, :DOF_PER_ARM] = single_arm_state_weights     # Copia para el brazo 1
    duplicated_state_weight[:, DOF_PER_ARM:DOF_TARGET] = single_arm_state_weights # Copia para el brazo 2
    hybrid_state_dict['model.state_proj.weight'] = duplicated_state_weight
    
    # Para la capa de salida `action_out_proj` y su bias
    checkpoint_action_weight = pretrained_state_dict['model.action_out_proj.weight']
    checkpoint_action_bias = pretrained_state_dict['model.action_out_proj.bias']
    
    single_arm_action_weights = checkpoint_action_weight[:DOF_PER_ARM, :] # Pesos para 6 DOF
    single_arm_action_bias = checkpoint_action_bias[:DOF_PER_ARM]
    
    duplicated_action_weight = torch.zeros_like(policy.model.action_out_proj.weight.data)
    duplicated_action_bias = torch.zeros_like(policy.model.action_out_proj.bias.data)
    
    duplicated_action_weight[:DOF_PER_ARM, :] = single_arm_action_weights   # Copia para el brazo 1
    duplicated_action_weight[DOF_PER_ARM:DOF_TARGET, :] = single_arm_action_weights # Copia para el brazo 2
    
    duplicated_action_bias[:DOF_PER_ARM] = single_arm_action_bias           # Copia para el brazo 1
    duplicated_action_bias[DOF_PER_ARM:DOF_TARGET] = single_arm_action_bias       # Copia para el brazo 2
    
    hybrid_state_dict['model.action_out_proj.weight'] = duplicated_action_weight
    hybrid_state_dict['model.action_out_proj.bias'] = duplicated_action_bias
    # -----------------------------------------------
    
    # Eliminamos los búferes de normalización del state_dict
    keys_to_remove = [k for k in hybrid_state_dict if "normalize" in k]
    for key in keys_to_remove:
        del hybrid_state_dict[key]
    print("   => state_dict con pesos duplicados creado y búferes de normalización eliminados.")

    print("\n4. Cargando los pesos duplicados en el modelo...")
    policy.load_state_dict(hybrid_state_dict, strict=False)
    
    # --- VERIFICACIÓN FINAL ---
    print("\n--- VERIFICACIÓN DE LA DUPLICACIÓN DE PESOS ---")
    final_weights = policy.model.state_proj.weight.data
    
    # Aserción 1: Los pesos del brazo 1 deben coincidir con los del checkpoint.
    assert torch.allclose(final_weights[:, :DOF_PER_ARM], single_arm_state_weights), \
        "ERROR: Los pesos del primer brazo (0-5) no coinciden con los del checkpoint."
    print("   => Verificación 1/2: Pesos del primer brazo cargados correctamente.")
    print(final_weights[:, :DOF_PER_ARM])
    print(single_arm_state_weights)
    
    # Aserción 2: Los pesos del brazo 2 deben ser una COPIA de los del brazo 1.
    assert torch.allclose(final_weights[:, DOF_PER_ARM:DOF_TARGET], single_arm_state_weights), \
        "ERROR: Los pesos del segundo brazo (6-11) no son una copia de los del primero."
    print("   => Verificación 2/2: Pesos del segundo brazo duplicados correctamente.")
    print(final_weights[:, DOF_PER_ARM:DOF_TARGET])
    print(single_arm_state_weights)
    
    policy.to(device).eval()
    
    print("\n5. Ejecutando un forward pass de prueba...")
    fake_batch = create_fake_bimanual_batch(2, target_config.chunk_size, DOF_PER_ARM, device)
    with torch.no_grad():
        loss, _ = policy.forward(fake_batch)
    print(f"   => ¡ÉXITO! Forward pass completado. Loss: {loss.item():.4f}")

if __name__ == "__main__":
    test_bimanual_weight_duplication()