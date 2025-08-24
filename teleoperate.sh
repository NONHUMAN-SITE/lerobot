ROBOT_TYPE=bimanual_follower
TELEOP_TYPE=bimanual_leader

ROBOT_LEFT_PORT=/dev/ttyACM0
ROBOT_RIGHT_PORT=/dev/ttyACM1
TELEOP_LEFT_PORT=/dev/ttyACM2
TELEOP_RIGHT_PORT=/dev/ttyACM0

python -m lerobot.teleoperate \
    --robot.type=${ROBOT_TYPE} \
    --robot.left_port=${ROBOT_LEFT_PORT} \
    --robot.right_port=${ROBOT_RIGHT_PORT} \
    --robot.id=my_awesome_follower_arm \
    --teleop.type=${TELEOP_TYPE} \
    --teleop.left_port=${TELEOP_LEFT_PORT} \
    --teleop.right_port=${TELEOP_RIGHT_PORT} \
    --teleop.id=my_awesome_leader_arm

#python -m lerobot.teleoperate \
#    --robot.type=so100_follower \
#    --robot.port=/dev/ttyACM0 \
#    --robot.id=left_follower_arm \
#    --teleop.type=so100_leader \
#    --teleop.port=/dev/ttyACM1  \
#    --teleop.id=left_leader_arm