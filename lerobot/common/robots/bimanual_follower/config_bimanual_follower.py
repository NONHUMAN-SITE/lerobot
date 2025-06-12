# Copyright 2024 The HuggingFace Inc. team. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from dataclasses import dataclass, field

from lerobot.common.cameras import CameraConfig

from ..config import RobotConfig


@RobotConfig.register_subclass("bimanual_follower")
@dataclass
class BimanualFollowerConfig(RobotConfig):
    """
    Configuration for bimanual robot using two SO-ARM100 follower arms.
    
    This setup provides 12 DOF total:
    - Left arm (IDs 1-6): left_shoulder_pan, left_shoulder_lift, left_elbow_flex, 
                          left_wrist_flex, left_wrist_roll, left_gripper
    - Right arm (IDs 7-12): right_shoulder_pan, right_shoulder_lift, right_elbow_flex,
                           right_wrist_flex, right_wrist_roll, right_gripper
    
    The arms are connected via separate serial ports to ensure proper communication.
    """
    
    # Serial ports for each arm
    left_port: str   # e.g., "/dev/ttyUSB0"
    right_port: str  # e.g., "/dev/ttyUSB1"

    # Safety and control settings
    disable_torque_on_disconnect: bool = True

    # Safety limit for maximum relative movement per step
    # This prevents dangerous large movements that could damage the robot
    # Set to None to disable, or a positive number to limit movement magnitude
    # Can be a single value for all motors or a list of 12 values (one per motor)
    max_relative_target: int | list[int] | None = None

    # Camera configurations
    cameras: dict[str, CameraConfig] = field(default_factory=dict)

    # Normalization mode for motor positions
    # - False: Use normalized range [-100, 100] or [0, 100] depending on motor
    # - True: Use degrees for angular joints (backward compatibility)
    use_degrees: bool = False

    def __post_init__(self):
        """Validate configuration after initialization"""
        if self.left_port == self.right_port:
            raise ValueError("Left and right arms must use different ports")
        
        if isinstance(self.max_relative_target, list) and len(self.max_relative_target) != 12:
            raise ValueError("max_relative_target list must have exactly 12 values (one per motor)")


# Keep the old config for backward compatibility
@RobotConfig.register_subclass("so100_follower")
@dataclass
class SO100FollowerConfig(RobotConfig):
    """
    Configuration for single SO-ARM100 follower arm (6 DOF).
    
    This is the original configuration for backward compatibility.
    For new bimanual setups, use BimanualFollowerConfig instead.
    """
    
    # Port to connect to the arm
    port: str

    disable_torque_on_disconnect: bool = True

    # `max_relative_target` limits the magnitude of the relative positional target vector for safety purposes.
    # Set this to a positive scalar to have the same value for all motors, or a list that is the same length as
    # the number of motors in your follower arms.
    max_relative_target: int | None = None

    # cameras
    cameras: dict[str, CameraConfig] = field(default_factory=dict)

    # Set to `True` for backward compatibility with previous policies/dataset
    use_degrees: bool = False
