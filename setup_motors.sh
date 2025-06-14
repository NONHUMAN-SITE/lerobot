#python -m lerobot.setup_motors \
#    --robot.type=bimanual_follower \
#    --robot.left_port=/dev/ttyACM1 \
#    --robot.right_port=/dev/ttyACM0 \


#python -m lerobot.setup_motors \
#    --teleop.type=bimanual_leader \
#    --teleop.left_port=/dev/ttyACM0 \
#    --teleop.right_port=/dev/ttyACM1 \

python -m lerobot.setup_motors \
    --robot.type=so100_follower \
    --robot.port=/dev/ttyACM2 \
    --robot.id=jeje