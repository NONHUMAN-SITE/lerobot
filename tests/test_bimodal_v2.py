import torch
import json
from dataclasses import dataclass
from huggingface_hub import hf_hub_download
import safetensors

# Asumiendo que estos archivos están en el mismo directorio o en el PYTHONPATH
from lerobot.common.policies.smolvla_v2.configuration_smolvla import SmolVLAConfig
from lerobot.common.policies.smolvla_v2.modeling_smolvla import SmolVLAPolicy, rename_checkpoint_keys
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
    
    # print(f"\n2. Obteniendo los pesos preentrenados (6 DOF) de '{pretrained_model_name}'...")
    # checkpoint_path = hf_hub_download(repo_id=pretrained_model_name, filename="model.safetensors")
    # pretrained_state_dict = safetensors.torch.load_file(checkpoint_path)
    # pretrained_state_dict = rename_checkpoint_keys(pretrained_state_dict, "model._orig_mod.//model.")
    
    
    print("\n4. Cargando los pesos duplicados en el modelo...")
    policy.load_state_dict(pretrained_state_dict)
    
    # --- VERIFICACIÓN FINAL ---
    print("\n--- VERIFICACIÓN DE LA DUPLICACIÓN DE PESOS ---")
    final_weights = policy.model.state_proj.weight.data
    

if __name__ == "__main__":
    test_bimanual_weight_duplication()