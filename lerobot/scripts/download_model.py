#!/usr/bin/env python

"""
Script simple para descargar un modelo de Hugging Face Hub.

Ejemplo de uso:
```bash
python lerobot/scripts/download_model.py \
    --repo_id=tu_usuario/nombre_del_modelo \
    --output_path=./mi_modelo_descargado
```
"""

from dataclasses import dataclass
from pathlib import Path

import draccus
from huggingface_hub import snapshot_download


@dataclass
class DownloadModelConfig:
    # ID del repositorio en Hugging Face (formato: usuario/nombre_modelo)
    repo_id: str
    # Path donde descargar el modelo
    output_path: Path
    # Rama específica del repositorio (opcional)
    branch: str | None = None


@draccus.wrap()
def main(cfg: DownloadModelConfig):
    """Descarga un modelo de Hugging Face Hub."""
    
    # Crear directorio de destino si no existe
    cfg.output_path.mkdir(parents=True, exist_ok=True)
    
    # Descargar modelo
    snapshot_download(
        repo_id=cfg.repo_id,
        repo_type="model",
        local_dir=cfg.output_path,
        revision=cfg.branch,
    )
    
    print(f"✅ Modelo descargado en: {cfg.output_path}")
    print(f"📦 Desde: https://huggingface.co/{cfg.repo_id}")


if __name__ == "__main__":
    main() 