DATASET_NAME=LEROBOTHACKATON

CUDA_VISIBLE_DEVICES=0 python lerobot/scripts/train.py \
  --policy.path=lerobot/smolvla_base \
  --dataset.repo_id=NONHUMAN-RESEARCH/$DATASET_NAME \
  --batch_size=64 \
  --steps=20000 \
  --output_dir=outputs/train/smolvla_output \
  --job_name=smolvla_$DATASET_NAME \
  --policy.device=cuda \
  --wandb.enable=true