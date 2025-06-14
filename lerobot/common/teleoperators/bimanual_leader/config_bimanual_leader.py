#!/usr/bin/env python

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

from dataclasses import dataclass

from ..config import TeleoperatorConfig


@TeleoperatorConfig.register_subclass("bimanual_leader")
@dataclass
class BimanualLeaderConfig(TeleoperatorConfig):
    """
    Configuration for bimanual teleoperator using two SO-ARM100 leader arms.
    
    This setup provides 12 DOF total for teleoperation:
    - Left arm (IDs 1-6): left_shoulder_pan, left_shoulder_lift, left_elbow_flex, 
                          left_wrist_flex, left_wrist_roll, left_gripper
    - Right arm (IDs 7-12): right_shoulder_pan, right_shoulder_lift, right_elbow_flex,
                           right_wrist_flex, right_wrist_roll, right_gripper
    
    The arms are connected via separate serial ports to ensure proper communication.
    """
    
    # Serial ports for each leader arm
    left_port: str   # e.g., "/dev/ttyUSB0"
    right_port: str  # e.g., "/dev/ttyUSB1"

    def __post_init__(self):
        """Validate configuration after initialization"""
        if self.left_port == self.right_port:
            raise ValueError("Left and right leader arms must use different ports")


'''
# Keep the old config for backward compatibility
@TeleoperatorConfig.register_subclass("so100_leader")
@dataclass
class SO100LeaderConfig(TeleoperatorConfig):
    """
    Configuration for single SO-ARM100 leader arm (6 DOF).
    
    This is the original configuration for backward compatibility.
    For new bimanual setups, use BimanualLeaderConfig instead.
    """
    
    # Port to connect to the arm
    port: str
'''