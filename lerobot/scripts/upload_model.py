#!/usr/bin/env python

# Copyright 2024 The HuggingFace Inc. team. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
Script simple para subir una carpeta de modelo a Hugging Face Hub.

Ejemplo de uso:
```bash
python lerobot/scripts/upload_model.py \
    --model_path=path/to/pretrained_model \
    --repo_id=tu_usuario/nombre_del_modelo
```
"""

from dataclasses import dataclass
from pathlib import Path

import draccus
from huggingface_hub import HfApi


@dataclass
class UploadModelConfig:
    # Path a la carpeta del modelo
    model_path: Path
    # ID del repositorio en Hugging Face (formato: usuario/nombre_modelo)
    repo_id: str
    # Si el repositorio debe ser privado
    private: bool = False


@draccus.wrap()
def main(cfg: UploadModelConfig):
    """Sube la carpeta del modelo a Hugging Face Hub."""
    
    if not cfg.model_path.exists():
        raise ValueError(f"La carpeta no existe: {cfg.model_path}")
    
    hub_api = HfApi()
    
    # Crear repositorio
    hub_api.create_repo(
        repo_id=cfg.repo_id,
        private=cfg.private,
        repo_type="model",
        exist_ok=True,
    )
    
    # Subir carpeta
    hub_api.upload_folder(
        repo_id=cfg.repo_id,
        folder_path=cfg.model_path,
        repo_type="model",
    )
    
    print(f"✅ Modelo subido a: https://huggingface.co/{cfg.repo_id}")


if __name__ == "__main__":
    main()
