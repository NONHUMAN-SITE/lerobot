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

def create_inference_batch(batch_size: int, dof_per_arm: int, device: torch.device):
    """Crea un batch para inferencia (sin dimensión temporal en las observaciones)"""
    state_arm1 = torch.randn(batch_size, dof_per_arm, device=device)
    state_arm2 = torch.randn(batch_size, dof_per_arm, device=device)
    bimanual_state = torch.cat((state_arm1, state_arm2), dim=-1)
    return {
        "observation.state": bimanual_state,
        "observation.images.top": torch.rand(batch_size, 3, 480, 640, device=device),
        "task": ["perform a bimanual task"] * batch_size,
    }

# --- 3. Script de prueba ---
def test_bimanual_inference_dimensions():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"--- ANÁLISIS DE DIMENSIONES DE SALIDA SMOLVLA BIMANUAL EN {str(device).upper()} ---")

    target_config = SmolVLAConfigBimanual()
    dataset_stats = create_fake_dataset_stats(DOF_TARGET)
    pretrained_model_name = "lerobot/smolvla_base"
    
    print("\n=== CONFIGURACIÓN ===")
    print(f"DOF por brazo: {DOF_PER_ARM}")
    print(f"Número de brazos: {NUM_ARMS}")
    print(f"DOF total (objetivo): {DOF_TARGET}")
    print(f"chunk_size: {target_config.chunk_size}")
    print(f"n_action_steps: {target_config.n_action_steps}")
    print(f"max_action_dim: {target_config.max_action_dim}")
    
    print("\n1. Creando la arquitectura bimanual (12 DOF)...")
    policy = SmolVLAPolicy(config=target_config, dataset_stats=dataset_stats)
    
    print(f"\n2. Obteniendo los pesos preentrenados (6 DOF) de '{pretrained_model_name}'...")
    checkpoint_path = hf_hub_download(repo_id=pretrained_model_name, filename="model.safetensors")
    pretrained_state_dict = safetensors.torch.load_file(checkpoint_path)
    pretrained_state_dict = rename_checkpoint_keys(pretrained_state_dict, "model._orig_mod.//model.")
    
    print("\n3. Construyendo 'state_dict' con PESOS DUPLICADOS...")
    hybrid_state_dict = pretrained_state_dict.copy()
    
    # --- LÓGICA CLAVE: DUPLICACIÓN DE PESOS ---
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

    print("\n4. Cargando los pesos duplicados en el modelo...")
    policy.load_state_dict(hybrid_state_dict, strict=False)
    policy.to(device).eval()
    
    print("\n=== ANÁLISIS DE DIMENSIONES DE SALIDA ===")
    
    # Crear batch de inferencia
    batch_size = 2
    fake_batch = create_inference_batch(batch_size, DOF_PER_ARM, device)
    
    print(f"\nBatch de entrada:")
    print(f"  observation.state shape: {fake_batch['observation.state'].shape}")
    print(f"  observation.images.top shape: {fake_batch['observation.images.top'].shape}")
    print(f"  task: {fake_batch['task']}")
    
    # Test del método sample_actions del modelo interno
    print(f"\n=== DIMENSIONES INTERNAS ===")
    with torch.no_grad():
        # Preparar inputs como lo hace el policy
        images, img_masks = policy.prepare_images(fake_batch)
        state = policy.prepare_state(fake_batch)
        lang_tokens, lang_masks = policy.prepare_language(fake_batch)
        
        print(f"Estado paddeado shape: {state.shape}")
        print(f"Número de imágenes: {len(images)}")
        print(f"Shape de imagen procesada: {images[0].shape}")
        
        # Llamar directamente a sample_actions del modelo VLAFlowMatching
        raw_actions = policy.model.sample_actions(
            images, img_masks, lang_tokens, lang_masks, state
        )
        
        print(f"\n=== SALIDA DEL MODELO INTERNO (sample_actions) ===")
        print(f"Raw actions shape: {raw_actions.shape}")
        print(f"  - Batch size: {raw_actions.shape[0]}")
        print(f"  - Chunk size: {raw_actions.shape[1]}")
        print(f"  - Max action dim (con padding): {raw_actions.shape[2]}")
    
    # Test del método select_action de la policy
    print(f"\n=== SALIDA DE LA POLICY (select_action) ===")
    with torch.no_grad():
        single_action = policy.select_action(fake_batch)
        
        print(f"Single action shape: {single_action.shape}")
        print(f"  - Action dim (sin padding): {single_action.shape[0]}")
        print(f"Single action values (sample): {single_action[:6].cpu().numpy()}")  # Primeros 6 valores
    
    # Test con múltiples llamadas para ver el comportamiento de la cola
    print(f"\n=== COMPORTAMIENTO DE LA COLA DE ACCIONES ===")
    policy.reset()  # Resetear las colas
    actions_sequence = []
    
    for i in range(5):
        action = policy.select_action(fake_batch)
        actions_sequence.append(action.clone())
        print(f"Acción {i+1} shape: {action.shape}, primeros 3 valores: {action[:3].cpu().numpy()}")
    
    print(f"\n=== RESUMEN DE DIMENSIONES ===")
    print(f"Configuración:")
    print(f"  - chunk_size: {target_config.chunk_size}")
    print(f"  - n_action_steps: {target_config.n_action_steps}")
    print(f"  - max_action_dim: {target_config.max_action_dim}")
    print(f"  - action_feature.shape[0]: {target_config.action_feature.shape[0]}")
    
    print(f"\nSalidas del modelo:")
    print(f"  - sample_actions output: (batch_size={raw_actions.shape[0]}, chunk_size={raw_actions.shape[1]}, max_action_dim={raw_actions.shape[2]})")
    print(f"  - select_action output: (action_dim={single_action.shape[0]},)")
    print(f"  - Padding aplicado: {raw_actions.shape[2] - single_action.shape[0]} dimensiones")
    
    print(f"\n¡ANÁLISIS COMPLETADO EXITOSAMENTE!")

if __name__ == "__main__":
    test_bimanual_inference_dimensions()
