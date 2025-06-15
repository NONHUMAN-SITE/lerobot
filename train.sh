DATASET_NAME=LEROBOTHACKATON

cd lerobot && python lerobot/scripts/train.py \
  --policy.path=lerobot/smolvla_base \
  --dataset.repo_id=NONHUMAN-RESEARCH/$DATASET_NAME \
  --batch_size=64 \
  --steps=20000 \
  --output_dir=outputs/train/smolvla_$DATASET_NAME \
  --job_name=smolvla_$DATASET_NAME \
  --policy.device=cuda \
  --wandb.enable=true