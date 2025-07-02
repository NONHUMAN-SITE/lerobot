DATASET_NAME=GLEXCO_DEMO_BOX_VENDA

python -m lerobot.record_bimanual \
    --robot.type=bimanual_follower \
    --robot.left_port=/dev/ttyACM3 \
    --robot.right_port=/dev/ttyACM1 \
    --robot.id=my_awesome_follower_arm \
    --robot.cameras="{laptop: {type: opencv, index_or_path: 2, width: 640, height: 480, fps: 30},phone: {type: opencv, index_or_path: 4, width: 640, height: 480, fps: 30}}" \
    --teleop.type=bimanual_leader \
    --teleop.left_port=/dev/ttyACM2 \
    --teleop.right_port=/dev/ttyACM0 \
    --teleop.id=my_awesome_leader_arm \
    --dataset.repo_id=NONHUMAN-RESEARCH/$DATASET_NAME \
    --dataset.num_episodes=0 \
    --dataset.continuous_recording=true \
    --dataset.single_task="Put the bandage in the box" \
    --resume=false

#python -m lerobot.record_bimanual \
#    --robot.type=so100_follower \
#    --robot.port=/dev/ttyACM1 \
#    --robot.cameras="{laptop: {type: opencv, index_or_path: 2, width: 640, height: 480, fps: 30}}" \
#    --robot.id=my_awesome_follower_arm \
#    --teleop.type=so100_leader \
#    --teleop.port=/dev/ttyACM0 \
#    --teleop.id=my_awesome_leader_arm \
#    --dataset.repo_id=NONHUMAN-RESEARCH/test-bimanual \
#    --dataset.num_episodes=0 \
#    --dataset.continuous_recording=true \
#    --dataset.single_task="Pick and place objects"