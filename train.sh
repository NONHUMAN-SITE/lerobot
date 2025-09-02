DATASET_NAME=BRAZO_SALLUD

CUDA_VISIBLE_DEVICES=0 python lerobot/scripts/train.py \
  --policy.path=lerobot/smolvla_base \
  --dataset.repo_id=mbrq13/BRAZO_SALLUD \
  --batch_size=4 \
  --steps=100000 \
  --output_dir=outputs/train/smolvla_output_vlm_on \
  --job_name=smolvla_autobrik18_$DATASET_NAME \
  --policy.device=cuda \
  --wandb.enable=true \