import torch
from lerobot.common.policies.factory import PreTrainedPolicy

def duplicate_weights(policy: PreTrainedPolicy):
    
    with torch.no_grad():
        # Copiar los pesos de las primeras 6 columnas del layer original
        first_6_weights = policy.model.action_out_proj.weight[:6, :]  # Shape: (6, 720)

        # Asignar estos pesos tanto a las primeras 6 como a las siguientes 6 posiciones
        policy.model.action_out_proj.weight[:6, :] = first_6_weights      # Primeras 6 columnas
        policy.model.action_out_proj.weight[6:12, :] = first_6_weights    # Siguientes 6 columnas (duplicadas)

        # También duplicar los bias si los hay
        if policy.model.action_out_proj.bias is not None:
            first_6_bias = policy.model.action_out_proj.bias[:6]
            policy.model.action_out_proj.bias[:6] = first_6_bias
            policy.model.action_out_proj.bias[6:12] = first_6_bias

    return policy