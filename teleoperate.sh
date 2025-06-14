#python -m lerobot.teleoperate \
#    --robot.type=bimanual_follower \
#    --robot.left_port=/dev/ttyACM0 \
#    --robot.right_port=/dev/ttyACM1 \
#    --robot.id=my_awesome_follower_arm \
#    --teleop.type=bimanual_leader \
#    --teleop.left_port=/dev/ttyACM3 \
#    --teleop.right_port=/dev/ttyACM2 \
#    --teleop.id=my_awesome_leader_arm

python -m lerobot.teleoperate \
    --robot.type=so100_follower \
    --robot.port=/dev/ttyACM2 \
    --robot.id=right_follower_arm \
    --teleop.type=so100_leader \
    --teleop.port=/dev/ttyACM3 \
    --teleop.id=right_leader_arm