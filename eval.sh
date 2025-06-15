DATASET_NAME=LEROBOTHACKATON

CUDA_VISIBLE_DEVICES=0 python -m lerobot.record \
    --robot.type=bimanual_follower \
    --robot.left_port=/dev/ttyACM1 \
    --robot.right_port=/dev/ttyACM0 \
    --robot.id=my_awesome_follower_arm \
    --robot.cameras="{laptop: {type: opencv, index_or_path: 4, width: 640, height: 480, fps: 30},phone: {type: opencv, index_or_path: 2, width: 640, height: 480, fps: 30}}" \
    --display_data=false \
    --dataset.repo_id=NONHUMAN-RESEARCH/eval_$DATASET_NAME \
    --dataset.single_task="Pick and place objects" \
    --policy.path=/home/leonardo/NONHUMAN/robotic_frameworks/lerobot/outputs/models \