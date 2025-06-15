python -m lerobot.teleoperate \
    --robot.type=so100_follower \
    --robot.port=/dev/ttyACM1 \
    --robot.cameras="{laptop: {type: opencv, index_or_path: 2, width: 640, height: 480, fps: 30},phone: {type: opencv, index_or_path: 4, width: 640, height: 480, fps: 30}}" \
    --robot.id=right_follower_arm \
    --teleop.type=so100_leader \
    --teleop.port=/dev/ttyACM0 \
    --teleop.id=right_leader_arm
