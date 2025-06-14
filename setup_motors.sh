python -m lerobot.setup_motors \
    --robot.type=bimanual_follower \
    --robot.left_port=/dev/ttyACM0 \
    --robot.right_port=/dev/ttyACM1 \


#python -m lerobot.setup_motors \
#    --teleop.type=bimanual_leader \
#    --teleop.left_port=/dev/ttyACM0 \
#    --teleop.right_port=/dev/ttyACM1 \