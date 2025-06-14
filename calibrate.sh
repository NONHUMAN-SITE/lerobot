python -m lerobot.calibrate \
    --robot.type=bimanual_follower \
    --robot.left_port=/dev/ttyACM0 \
    --robot.right_port=/dev/ttyACM1 \
    --robot.id=my_awesome_follower_arm \
    --teleop.type=bimanual_leader \
    --teleop.left_port=/dev/ttyACM0 \
    --teleop.right_port=/dev/ttyACM1 \
    --teleop.id=my_awesome_leader_arm


#python -m lerobot.calibrate \
#    --robot.type=so101_follower \
#    --robot.port=/dev/tty.usbmodem58760431551 \
#    --robot.id=my_awesome_follower_arm