DATASET_NAME=GLEXCO_DEMO_BOX_VENDA
ROBOT_TYPE=bimanual_follower

ROBOT_LEFT_PORT=/dev/ttyACM3
ROBOT_RIGHT_PORT=/dev/ttyACM1
TELEOP_LEFT_PORT=/dev/ttyACM2
TELEOP_RIGHT_PORT=/dev/ttyACM0


GENERAL_CAMERA_INDEX=2
WRIST_LEFT_CAMERA_INDEX=4
WRIST_RIGHT_CAMERA_INDEX=6


python -m lerobot.record_bimanual \
    --robot.type=${ROBOT_TYPE} \
    --robot.left_port=${ROBOT_LEFT_PORT} \
    --robot.right_port=${ROBOT_RIGHT_PORT} \
    --robot.id=my_awesome_follower_arm \
    --robot.cameras="{general: {type: opencv, index_or_path: ${GENERAL_CAMERA_INDEX}, width: 640, height: 480, fps: 30},wrist_left: {type: opencv, index_or_path: ${WRIST_LEFT_CAMERA_INDEX}, width: 640, height: 480, fps: 30},wrist_right: {type: opencv, index_or_path: ${WRIST_RIGHT_CAMERA_INDEX}, width: 640, height: 480, fps: 30}}" \
    --teleop.type=bimanual_leader \
    --teleop.left_port=${TELEOP_LEFT_PORT} \
    --teleop.right_port=${TELEOP_RIGHT_PORT} \
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