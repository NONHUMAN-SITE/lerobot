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

import logging
import time

from lerobot.common.errors import DeviceAlreadyConnectedError, DeviceNotConnectedError
from lerobot.common.motors import Motor, MotorCalibration, MotorNormMode
from lerobot.common.motors.feetech import (
    FeetechMotorsBus,
    OperatingMode,
)

from ..teleoperator import Teleoperator
from .config_bimanual_leader import BimanualLeaderConfig

logger = logging.getLogger(__name__)


class BimanualLeader(Teleoperator):
    """
    Bimanual teleoperator using two [SO-100 Leader Arms](https://github.com/TheRobotStudio/SO-ARM100)
    designed by TheRobotStudio. This provides 12 DOF total for teleoperation (6 DOF per arm).
    
    Left arm uses motor IDs 1-6, right arm uses motor IDs 7-12 to avoid conflicts.
    """

    config_class = BimanualLeaderConfig
    name = "bimanual_leader"

    def __init__(self, config: BimanualLeaderConfig):
        super().__init__(config)
        self.config = config
        
        # Create motor configurations for left arm (IDs 1-6)
        left_motors = {
            "shoulder_pan": Motor(1, "sts3215", MotorNormMode.RANGE_M100_100),
            "shoulder_lift": Motor(2, "sts3215", MotorNormMode.RANGE_M100_100),
            "elbow_flex": Motor(3, "sts3215", MotorNormMode.RANGE_M100_100),
            "wrist_flex": Motor(4, "sts3215", MotorNormMode.RANGE_M100_100),
            "wrist_roll": Motor(5, "sts3215", MotorNormMode.RANGE_M100_100),
            "gripper": Motor(6, "sts3215", MotorNormMode.RANGE_0_100),
        }
        
        # Create motor configurations for right arm (IDs 7-12)
        right_motors = {
            "shoulder_pan": Motor(7, "sts3215", MotorNormMode.RANGE_M100_100),
            "shoulder_lift": Motor(8, "sts3215", MotorNormMode.RANGE_M100_100),
            "elbow_flex": Motor(9, "sts3215", MotorNormMode.RANGE_M100_100),
            "wrist_flex": Motor(10, "sts3215", MotorNormMode.RANGE_M100_100),
            "wrist_roll": Motor(11, "sts3215", MotorNormMode.RANGE_M100_100),
            "gripper": Motor(12, "sts3215", MotorNormMode.RANGE_0_100),
        }

        # Separate calibrations for each arm
        left_calibration = {k.replace("left_", ""): v for k, v in self.calibration.items() if k.startswith("left_")}
        right_calibration = {k.replace("right_", ""): v for k, v in self.calibration.items() if k.startswith("right_")}
        
        # Create separate bus for each arm
        self.left_bus = FeetechMotorsBus(
            port=self.config.left_port,
            motors=left_motors,
            calibration=left_calibration,
        )
        
        self.right_bus = FeetechMotorsBus(
            port=self.config.right_port,
            motors=right_motors,
            calibration=right_calibration,
        )

    @property
    def action_features(self) -> dict[str, type]:
        """Action features for all motors (both arms with proper prefixes)"""
        action_ft = {}
        # Add left arm motors with prefix
        for motor in self.left_bus.motors:
            action_ft[f"left_{motor}.pos"] = float
        # Add right arm motors with prefix
        for motor in self.right_bus.motors:
            action_ft[f"right_{motor}.pos"] = float
        return action_ft

    @property
    def feedback_features(self) -> dict[str, type]:
        # TODO(rcadene, aliberts): Implement force feedback features
        return {}

    @property
    def is_connected(self) -> bool:
        """Check if both leader arms are connected"""
        return self.left_bus.is_connected and self.right_bus.is_connected

    def connect(self, calibrate: bool = True) -> None:
        """
        Connect both leader arms.
        We assume that at connection time, both arms are in rest positions,
        and torque can be safely disabled to run calibration.
        """
        if self.is_connected:
            raise DeviceAlreadyConnectedError(f"{self} already connected")

        logger.info("Connecting bimanual leader...")
        
        # Connect both arms
        logger.info("Connecting left leader arm...")
        self.left_bus.connect()
        logger.info("Connecting right leader arm...")
        self.right_bus.connect()
        
        # Calibrate if needed
        if not self.is_calibrated and calibrate:
            self.calibrate()

        # Configure both arms
        self.configure()
        logger.info(f"{self} connected successfully.")

    @property
    def is_calibrated(self) -> bool:
        """Check if both leader arms are calibrated"""
        return self.left_bus.is_calibrated and self.right_bus.is_calibrated

    def calibrate(self) -> None:
        """
        Calibrate both leader arms sequentially.
        This process involves setting homing offsets and recording range of motion for each arm.
        """
        logger.info(f"\nRunning calibration of {self}")
        
        # === CALIBRATE LEFT ARM ===
        logger.info("\n=== Calibrating LEFT leader arm (IDs 1-6) ===")
        self.left_bus.disable_torque()
        for motor in self.left_bus.motors:
            self.left_bus.write("Operating_Mode", motor, OperatingMode.POSITION.value)

        input("Move LEFT leader arm to the middle of its range of motion and press ENTER...")
        left_homing_offsets = self.left_bus.set_half_turn_homings()

        full_turn_motor = "wrist_roll"
        unknown_range_motors = [motor for motor in self.left_bus.motors if motor != full_turn_motor]
        print(
            f"Move all LEFT leader arm joints except '{full_turn_motor}' sequentially through their "
            "entire ranges of motion.\nRecording positions. Press ENTER to stop..."
        )
        left_range_mins, left_range_maxes = self.left_bus.record_ranges_of_motion(unknown_range_motors)
        left_range_mins[full_turn_motor] = 0
        left_range_maxes[full_turn_motor] = 4095

        # === CALIBRATE RIGHT ARM ===
        logger.info("\n=== Calibrating RIGHT leader arm (IDs 7-12) ===")
        self.right_bus.disable_torque()
        for motor in self.right_bus.motors:
            self.right_bus.write("Operating_Mode", motor, OperatingMode.POSITION.value)

        input("Move RIGHT leader arm to the middle of its range of motion and press ENTER...")
        right_homing_offsets = self.right_bus.set_half_turn_homings()

        unknown_range_motors = [motor for motor in self.right_bus.motors if motor != full_turn_motor]
        print(
            f"Move all RIGHT leader arm joints except '{full_turn_motor}' sequentially through their "
            "entire ranges of motion.\nRecording positions. Press ENTER to stop..."
        )
        right_range_mins, right_range_maxes = self.right_bus.record_ranges_of_motion(unknown_range_motors)
        right_range_mins[full_turn_motor] = 0
        right_range_maxes[full_turn_motor] = 4095

        # === SAVE COMBINED CALIBRATION ===
        self.calibration = {}
        
        # Add left arm calibration with prefix
        for motor, m in self.left_bus.motors.items():
            self.calibration[f"left_{motor}"] = MotorCalibration(
                id=m.id,  # IDs 1-6
                drive_mode=0,
                homing_offset=left_homing_offsets[motor],
                range_min=left_range_mins[motor],
                range_max=left_range_maxes[motor],
            )
            
        # Add right arm calibration with prefix
        for motor, m in self.right_bus.motors.items():
            self.calibration[f"right_{motor}"] = MotorCalibration(
                id=m.id,  # IDs 7-12
                drive_mode=0,
                homing_offset=right_homing_offsets[motor],
                range_min=right_range_mins[motor],
                range_max=right_range_maxes[motor],
            )

        # Write calibration to both buses
        left_calibration = {k.replace("left_", ""): v for k, v in self.calibration.items() if k.startswith("left_")}
        right_calibration = {k.replace("right_", ""): v for k, v in self.calibration.items() if k.startswith("right_")}
        
        self.left_bus.write_calibration(left_calibration)
        self.right_bus.write_calibration(right_calibration)
        
        self._save_calibration()
        logger.info(f"Calibration saved to {self.calibration_fpath}")

    def configure(self) -> None:
        """Configure both leader arms - disable torque for manual manipulation"""
        logger.info("Configuring left leader arm...")
        self.left_bus.disable_torque()
        self.left_bus.configure_motors()
        for motor in self.left_bus.motors:
            self.left_bus.write("Operating_Mode", motor, OperatingMode.POSITION.value)
            
        logger.info("Configuring right leader arm...")
        self.right_bus.disable_torque()
        self.right_bus.configure_motors()
        for motor in self.right_bus.motors:
            self.right_bus.write("Operating_Mode", motor, OperatingMode.POSITION.value)

    def setup_motors(self) -> None:
        """
        Interactive setup for motor IDs and baudrates.
        This should be run only once when setting up the hardware.
        """
        # Setup left arm motors (IDs 1-6)
        print("\n=== Setting up LEFT leader arm motors (will set IDs 1-6) ===")
        for motor in reversed(list(self.left_bus.motors.keys())):
            expected_id = self.left_bus.motors[motor].id
            input(f"Connect the controller board to the LEFT leader arm '{motor}' motor only and press enter.")
            self.left_bus.setup_motor(motor)
            print(f"LEFT leader arm '{motor}' motor ID set to {expected_id}")
            
        # Setup right arm motors (IDs 7-12)
        print("\n=== Setting up RIGHT leader arm motors (will set IDs 7-12) ===")
        for motor in reversed(list(self.right_bus.motors.keys())):
            expected_id = self.right_bus.motors[motor].id
            input(f"Connect the controller board to the RIGHT leader arm '{motor}' motor only and press enter.")
            self.right_bus.setup_motor(motor)
            print(f"RIGHT leader arm '{motor}' motor ID set to {expected_id}")
            
        print("\n✅ Leader motor setup complete!")
        print("Left leader arm motors: IDs 1-6")
        print("Right leader arm motors: IDs 7-12")

    def get_action(self) -> dict[str, float]:
        """
        Read current positions from both leader arms.
        Returns action dictionary with proper prefixes for teleoperation.
        """
        if not self.is_connected:
            raise DeviceNotConnectedError(f"{self} is not connected.")

        action = {}
        
        # Read left arm positions
        start = time.perf_counter()
        left_action = self.left_bus.sync_read("Present_Position")
        left_action = {f"left_{motor}.pos": val for motor, val in left_action.items()}
        action.update(left_action)
        dt_ms = (time.perf_counter() - start) * 1e3
        logger.debug(f"Read left leader arm action: {dt_ms:.1f}ms")
        
        # Read right arm positions
        start = time.perf_counter()
        right_action = self.right_bus.sync_read("Present_Position")
        right_action = {f"right_{motor}.pos": val for motor, val in right_action.items()}
        action.update(right_action)
        dt_ms = (time.perf_counter() - start) * 1e3
        logger.debug(f"Read right leader arm action: {dt_ms:.1f}ms")
        
        return action

    def send_feedback(self, feedback: dict[str, float]) -> None:
        """
        Send force feedback to both leader arms.
        
        Args:
            feedback: Dictionary with keys like "left_shoulder_pan.force", "right_gripper.force", etc.
        """
        # TODO(rcadene, aliberts): Implement force feedback for bimanual setup
        # This would involve separating feedback for left and right arms and sending to respective buses
        raise NotImplementedError("Force feedback not yet implemented for bimanual leader")

    def disconnect(self) -> None:
        """Disconnect both leader arms"""
        if not self.is_connected:
            raise DeviceNotConnectedError(f"{self} is not connected.")

        logger.info("Disconnecting bimanual leader...")
        
        # Disconnect both arms
        self.left_bus.disconnect()
        self.right_bus.disconnect()
        
        logger.info(f"{self} disconnected.")

'''
# Keep the original SO100Leader class for backward compatibility
class SO100Leader(Teleoperator):
    """
    [SO-100 Leader Arm](https://github.com/TheRobotStudio/SO-ARM100) designed by TheRobotStudio
    """

    config_class = SO100LeaderConfig
    name = "so100_leader"

    def __init__(self, config: SO100LeaderConfig):
        super().__init__(config)
        self.config = config
        self.bus = FeetechMotorsBus(
            port=self.config.port,
            motors={
                "shoulder_pan": Motor(1, "sts3215", MotorNormMode.RANGE_M100_100),
                "shoulder_lift": Motor(2, "sts3215", MotorNormMode.RANGE_M100_100),
                "elbow_flex": Motor(3, "sts3215", MotorNormMode.RANGE_M100_100),
                "wrist_flex": Motor(4, "sts3215", MotorNormMode.RANGE_M100_100),
                "wrist_roll": Motor(5, "sts3215", MotorNormMode.RANGE_M100_100),
                "gripper": Motor(6, "sts3215", MotorNormMode.RANGE_0_100),
            },
            calibration=self.calibration,
        )

    @property
    def action_features(self) -> dict[str, type]:
        return {f"{motor}.pos": float for motor in self.bus.motors}

    @property
    def feedback_features(self) -> dict[str, type]:
        return {}

    @property
    def is_connected(self) -> bool:
        return self.bus.is_connected

    def connect(self, calibrate: bool = True) -> None:
        if self.is_connected:
            raise DeviceAlreadyConnectedError(f"{self} already connected")

        self.bus.connect()
        if not self.is_calibrated and calibrate:
            self.calibrate()

        self.configure()
        logger.info(f"{self} connected.")

    @property
    def is_calibrated(self) -> bool:
        return self.bus.is_calibrated

    def calibrate(self) -> None:
        logger.info(f"\nRunning calibration of {self}")
        self.bus.disable_torque()
        for motor in self.bus.motors:
            self.bus.write("Operating_Mode", motor, OperatingMode.POSITION.value)

        input(f"Move {self} to the middle of its range of motion and press ENTER....")
        homing_offsets = self.bus.set_half_turn_homings()

        full_turn_motor = "wrist_roll"
        unknown_range_motors = [motor for motor in self.bus.motors if motor != full_turn_motor]
        print(
            f"Move all joints except '{full_turn_motor}' sequentially through their "
            "entire ranges of motion.\nRecording positions. Press ENTER to stop..."
        )
        range_mins, range_maxes = self.bus.record_ranges_of_motion(unknown_range_motors)
        range_mins[full_turn_motor] = 0
        range_maxes[full_turn_motor] = 4095

        self.calibration = {}
        for motor, m in self.bus.motors.items():
            self.calibration[motor] = MotorCalibration(
                id=m.id,
                drive_mode=0,
                homing_offset=homing_offsets[motor],
                range_min=range_mins[motor],
                range_max=range_maxes[motor],
            )

        self.bus.write_calibration(self.calibration)
        self._save_calibration()
        logger.info(f"Calibration saved to {self.calibration_fpath}")

    def configure(self) -> None:
        self.bus.disable_torque()
        self.bus.configure_motors()
        for motor in self.bus.motors:
            self.bus.write("Operating_Mode", motor, OperatingMode.POSITION.value)

    def setup_motors(self) -> None:
        for motor in reversed(self.bus.motors):
            input(f"Connect the controller board to the '{motor}' motor only and press enter.")
            self.bus.setup_motor(motor)
            print(f"'{motor}' motor id set to {self.bus.motors[motor].id}")

    def get_action(self) -> dict[str, float]:
        start = time.perf_counter()
        action = self.bus.sync_read("Present_Position")
        action = {f"{motor}.pos": val for motor, val in action.items()}
        dt_ms = (time.perf_counter() - start) * 1e3
        logger.debug(f"{self} read action: {dt_ms:.1f}ms")
        return action

    def send_feedback(self, feedback: dict[str, float]) -> None:
        # TODO(rcadene, aliberts): Implement force feedback
        raise NotImplementedError

    def disconnect(self) -> None:
        if not self.is_connected:
            DeviceNotConnectedError(f"{self} is not connected.")

        self.bus.disconnect()
        logger.info(f"{self} disconnected.")
'''
