#!/bin/bash

#echo "=== Calibrating Bimanual Follower Robot ==="
#python -m lerobot.calibrate \
#    --robot.type=bimanual_follower \
#    --robot.left_port=/dev/ttyACM0 \
#    --robot.right_port=/dev/ttyACM1 \
#    --robot.id=my_awesome_follower_arm
#
#echo ""
#echo "=== Calibrating Bimanual Leader Teleoperator ==="
#python -m lerobot.calibrate \
#    --teleop.type=bimanual_leader \
#    --teleop.left_port=/dev/ttyACM3 \
#    --teleop.right_port=/dev/ttyACM2 \
#    --teleop.id=my_awesome_leader_arm
#

python -m lerobot.calibrate \
    --robot.type=so100_follower \
    --robot.port=/dev/ttyACM0 \
    --robot.id=right_follower_arm


#python -m lerobot.calibrate \
#    --teleop.type=so100_leader \
#    --teleop.port=/dev/ttyACM0 \
#    --teleop.id=right_leader_arm


#python -m lerobot.calibrate \
#    --robot.type=so100_follower \
#    --robot.port=/dev/ttyACM1 \
#    --robot.id=right_follower_arm