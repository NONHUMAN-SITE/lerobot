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
from functools import cached_property
from typing import Any

from lerobot.common.cameras.utils import make_cameras_from_configs
from lerobot.common.errors import DeviceAlreadyConnectedError, DeviceNotConnectedError
from lerobot.common.motors import Motor, MotorCalibration, MotorNormMode
from lerobot.common.motors.feetech import (
    FeetechMotorsBus,
    OperatingMode,
)

from ..robot import Robot
from ..utils import ensure_safe_goal_position
from .config_bimanual_follower import BimanualFollowerConfig, SO100FollowerConfig

logger = logging.getLogger(__name__)


class BimanualFollower(Robot):
    """
    Bimanual robot using two [SO-100 Follower Arms](https://github.com/TheRobotStudio/SO-ARM100)
    designed by TheRobotStudio. This provides 12 DOF total (6 DOF per arm).
    
    Left arm uses motor IDs 1-6, right arm uses motor IDs 7-12 to avoid conflicts.
    """

    config_class = BimanualFollowerConfig
    name = "bimanual_follower"

    def __init__(self, config: BimanualFollowerConfig):
        super().__init__(config)
        self.config = config
        norm_mode_body = MotorNormMode.DEGREES if config.use_degrees else MotorNormMode.RANGE_M100_100
        
        # Create motor configurations for left arm (IDs 1-6)
        left_motors = {
            "shoulder_pan": Motor(1, "sts3215", norm_mode_body),
            "shoulder_lift": Motor(2, "sts3215", norm_mode_body),
            "elbow_flex": Motor(3, "sts3215", norm_mode_body),
            "wrist_flex": Motor(4, "sts3215", norm_mode_body),
            "wrist_roll": Motor(5, "sts3215", norm_mode_body),
            "gripper": Motor(6, "sts3215", MotorNormMode.RANGE_0_100),
        }
        
        # Create motor configurations for right arm (IDs 7-12)
        right_motors = {
            "shoulder_pan": Motor(7, "sts3215", norm_mode_body),
            "shoulder_lift": Motor(8, "sts3215", norm_mode_body),
            "elbow_flex": Motor(9, "sts3215", norm_mode_body),
            "wrist_flex": Motor(10, "sts3215", norm_mode_body),
            "wrist_roll": Motor(11, "sts3215", norm_mode_body),
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
        
        self.cameras = make_cameras_from_configs(config.cameras)

    @property
    def _motors_ft(self) -> dict[str, type]:
        """Feature types for all motors (both arms with proper prefixes)"""
        motors_ft = {}
        # Add left arm motors with prefix
        for motor in self.left_bus.motors:
            motors_ft[f"left_{motor}.pos"] = float
        # Add right arm motors with prefix
        for motor in self.right_bus.motors:
            motors_ft[f"right_{motor}.pos"] = float
        return motors_ft

    @property
    def _cameras_ft(self) -> dict[str, tuple]:
        return {
            cam: (self.config.cameras[cam].height, self.config.cameras[cam].width, 3) for cam in self.cameras
        }

    @cached_property
    def observation_features(self) -> dict[str, type | tuple]:
        return {**self._motors_ft, **self._cameras_ft}

    @cached_property
    def action_features(self) -> dict[str, type]:
        return self._motors_ft

    @property
    def is_connected(self) -> bool:
        """Check if both arms and all cameras are connected"""
        return (self.left_bus.is_connected and 
                self.right_bus.is_connected and 
                all(cam.is_connected for cam in self.cameras.values()))

    def connect(self, calibrate: bool = True) -> None:
        """
        Connect both arms and cameras.
        We assume that at connection time, both arms are in rest positions,
        and torque can be safely disabled to run calibration.
        """
        if self.is_connected:
            raise DeviceAlreadyConnectedError(f"{self} already connected")

        logger.info("Connecting bimanual follower...")
        
        # Connect both arms
        logger.info("Connecting left arm...")
        self.left_bus.connect()
        logger.info("Connecting right arm...")
        self.right_bus.connect()
        
        # Calibrate if needed
        if not self.is_calibrated and calibrate:
            self.calibrate()

        # Connect cameras
        for cam_name, cam in self.cameras.items():
            logger.info(f"Connecting camera: {cam_name}")
            cam.connect()

        # Configure both arms
        self.configure()
        logger.info(f"{self} connected successfully.")

    @property
    def is_calibrated(self) -> bool:
        """Check if both arms are calibrated"""
        return self.left_bus.is_calibrated and self.right_bus.is_calibrated

    def calibrate(self) -> None:
        """
        Calibrate both arms sequentially.
        This process involves setting homing offsets and recording range of motion for each arm.
        """
        logger.info(f"\nRunning calibration of {self}")
        
        # === CALIBRATE LEFT ARM ===
        logger.info("\n=== Calibrating LEFT arm (IDs 1-6) ===")
        self.left_bus.disable_torque()
        for motor in self.left_bus.motors:
            self.left_bus.write("Operating_Mode", motor, OperatingMode.POSITION.value)

        input("Move LEFT arm to the middle of its range of motion and press ENTER...")
        left_homing_offsets = self.left_bus.set_half_turn_homings()

        full_turn_motor = "wrist_roll"
        unknown_range_motors = [motor for motor in self.left_bus.motors if motor != full_turn_motor]
        print(
            f"Move all LEFT arm joints except '{full_turn_motor}' sequentially through their "
            "entire ranges of motion.\nRecording positions. Press ENTER to stop..."
        )
        left_range_mins, left_range_maxes = self.left_bus.record_ranges_of_motion(unknown_range_motors)
        left_range_mins[full_turn_motor] = 0
        left_range_maxes[full_turn_motor] = 4095

        # === CALIBRATE RIGHT ARM ===
        logger.info("\n=== Calibrating RIGHT arm (IDs 7-12) ===")
        self.right_bus.disable_torque()
        for motor in self.right_bus.motors:
            self.right_bus.write("Operating_Mode", motor, OperatingMode.POSITION.value)

        input("Move RIGHT arm to the middle of its range of motion and press ENTER...")
        right_homing_offsets = self.right_bus.set_half_turn_homings()

        unknown_range_motors = [motor for motor in self.right_bus.motors if motor != full_turn_motor]
        print(
            f"Move all RIGHT arm joints except '{full_turn_motor}' sequentially through their "
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
        """Configure both arms with optimal PID settings"""
        logger.info("Configuring left arm...")
        with self.left_bus.torque_disabled():
            self.left_bus.configure_motors()
            for motor in self.left_bus.motors:
                self.left_bus.write("Operating_Mode", motor, OperatingMode.POSITION.value)
                # Set P_Coefficient to lower value to avoid shakiness (Default is 32)
                self.left_bus.write("P_Coefficient", motor, 16)
                # Set I_Coefficient and D_Coefficient to default value 0 and 32
                self.left_bus.write("I_Coefficient", motor, 0)
                self.left_bus.write("D_Coefficient", motor, 32)
                
        logger.info("Configuring right arm...")
        with self.right_bus.torque_disabled():
            self.right_bus.configure_motors()
            for motor in self.right_bus.motors:
                self.right_bus.write("Operating_Mode", motor, OperatingMode.POSITION.value)
                # Set P_Coefficient to lower value to avoid shakiness (Default is 32)
                self.right_bus.write("P_Coefficient", motor, 16)
                # Set I_Coefficient and D_Coefficient to default value 0 and 32
                self.right_bus.write("I_Coefficient", motor, 0)
                self.right_bus.write("D_Coefficient", motor, 32)

    def setup_motors(self) -> None:
        """
        Interactive setup for motor IDs and baudrates.
        This should be run only once when setting up the hardware.
        """
        # Setup left arm motors (IDs 1-6)
        print("\n=== Setting up LEFT arm motors (will set IDs 1-6) ===")
        for motor in reversed(list(self.left_bus.motors.keys())):
            expected_id = self.left_bus.motors[motor].id
            input(f"Connect the controller board to the LEFT arm '{motor}' motor only and press enter.")
            self.left_bus.setup_motor(motor)
            print(f"LEFT arm '{motor}' motor ID set to {expected_id}")
            
        # Setup right arm motors (IDs 7-12)
        print("\n=== Setting up RIGHT arm motors (will set IDs 7-12) ===")
        for motor in reversed(list(self.right_bus.motors.keys())):
            expected_id = self.right_bus.motors[motor].id
            input(f"Connect the controller board to the RIGHT arm '{motor}' motor only and press enter.")
            self.right_bus.setup_motor(motor)
            print(f"RIGHT arm '{motor}' motor ID set to {expected_id}")
            
        print("\n✅ Motor setup complete!")
        print("Left arm motors: IDs 1-6")
        print("Right arm motors: IDs 7-12")

    def get_observation(self) -> dict[str, Any]:
        """
        Read current state from both arms and all cameras.
        Returns observation dictionary with proper prefixes.
        """
        if not self.is_connected:
            raise DeviceNotConnectedError(f"{self} is not connected.")

        obs_dict = {}
        
        # Read left arm position
        start = time.perf_counter()
        left_obs = self.left_bus.sync_read("Present_Position")
        left_obs = {f"left_{motor}.pos": val for motor, val in left_obs.items()}
        obs_dict.update(left_obs)
        dt_ms = (time.perf_counter() - start) * 1e3
        logger.debug(f"Read left arm state: {dt_ms:.1f}ms")
        
        # Read right arm position
        start = time.perf_counter()
        right_obs = self.right_bus.sync_read("Present_Position")
        right_obs = {f"right_{motor}.pos": val for motor, val in right_obs.items()}
        obs_dict.update(right_obs)
        dt_ms = (time.perf_counter() - start) * 1e3
        logger.debug(f"Read right arm state: {dt_ms:.1f}ms")

        # Capture images from cameras
        for cam_key, cam in self.cameras.items():
            start = time.perf_counter()
            obs_dict[cam_key] = cam.async_read()
            dt_ms = (time.perf_counter() - start) * 1e3
            logger.debug(f"Read camera {cam_key}: {dt_ms:.1f}ms")

        return obs_dict

    def send_action(self, action: dict[str, Any]) -> dict[str, Any]:
        """
        Command both arms to move to target joint configurations.

        Args:
            action: Dictionary with keys like "left_shoulder_pan.pos", "right_gripper.pos", etc.

        Returns:
            The action actually sent to the motors (potentially clipped for safety).
        """
        if not self.is_connected:
            raise DeviceNotConnectedError(f"{self} is not connected.")

        # Separate actions for left and right arms
        left_actions = {}
        right_actions = {}
        
        for key, val in action.items():
            if key.endswith(".pos"):
                if key.startswith("left_"):
                    motor_name = key.replace("left_", "").removesuffix(".pos")
                    left_actions[motor_name] = val
                elif key.startswith("right_"):
                    motor_name = key.replace("right_", "").removesuffix(".pos")
                    right_actions[motor_name] = val

        # Apply safety limits if configured
        if self.config.max_relative_target is not None:
            # Left arm safety check
            if left_actions:
                left_present_pos = self.left_bus.sync_read("Present_Position")
                left_goal_present_pos = {key: (g_pos, left_present_pos[key]) for key, g_pos in left_actions.items()}
                left_actions = ensure_safe_goal_position(left_goal_present_pos, self.config.max_relative_target)
            
            # Right arm safety check
            if right_actions:
                right_present_pos = self.right_bus.sync_read("Present_Position")
                right_goal_present_pos = {key: (g_pos, right_present_pos[key]) for key, g_pos in right_actions.items()}
                right_actions = ensure_safe_goal_position(right_goal_present_pos, self.config.max_relative_target)

        # Send commands to arms
        sent_actions = {}
        
        if left_actions:
            self.left_bus.sync_write("Goal_Position", left_actions)
            sent_actions.update({f"left_{motor}.pos": val for motor, val in left_actions.items()})
            
        if right_actions:
            self.right_bus.sync_write("Goal_Position", right_actions)
            sent_actions.update({f"right_{motor}.pos": val for motor, val in right_actions.items()})
            
        return sent_actions

    def disconnect(self):
        """Disconnect both arms and all cameras"""
        if not self.is_connected:
            raise DeviceNotConnectedError(f"{self} is not connected.")

        logger.info("Disconnecting bimanual follower...")
        
        # Disconnect both arms
        self.left_bus.disconnect(self.config.disable_torque_on_disconnect)
        self.right_bus.disconnect(self.config.disable_torque_on_disconnect)
        
        # Disconnect cameras
        for cam in self.cameras.values():
            cam.disconnect()

        logger.info(f"{self} disconnected.")


# Keep the original SO100Follower class for backward compatibility
class SO100Follower(Robot):
    """
    [SO-100 Follower Arm](https://github.com/TheRobotStudio/SO-ARM100) designed by TheRobotStudio
    """

    config_class = SO100FollowerConfig
    name = "so100_follower"

    def __init__(self, config: SO100FollowerConfig):
        super().__init__(config)
        self.config = config
        norm_mode_body = MotorNormMode.DEGREES if config.use_degrees else MotorNormMode.RANGE_M100_100
        self.bus = FeetechMotorsBus(
            port=self.config.port,
            motors={
                "shoulder_pan": Motor(1, "sts3215", norm_mode_body),
                "shoulder_lift": Motor(2, "sts3215", norm_mode_body),
                "elbow_flex": Motor(3, "sts3215", norm_mode_body),
                "wrist_flex": Motor(4, "sts3215", norm_mode_body),
                "wrist_roll": Motor(5, "sts3215", norm_mode_body),
                "gripper": Motor(6, "sts3215", MotorNormMode.RANGE_0_100),
            },
            calibration=self.calibration,
        )
        self.cameras = make_cameras_from_configs(config.cameras)

    @property
    def _motors_ft(self) -> dict[str, type]:
        return {f"{motor}.pos": float for motor in self.bus.motors}

    @property
    def _cameras_ft(self) -> dict[str, tuple]:
        return {
            cam: (self.config.cameras[cam].height, self.config.cameras[cam].width, 3) for cam in self.cameras
        }

    @cached_property
    def observation_features(self) -> dict[str, type | tuple]:
        return {**self._motors_ft, **self._cameras_ft}

    @cached_property
    def action_features(self) -> dict[str, type]:
        return self._motors_ft

    @property
    def is_connected(self) -> bool:
        return self.bus.is_connected and all(cam.is_connected for cam in self.cameras.values())

    def connect(self, calibrate: bool = True) -> None:
        """
        We assume that at connection time, arm is in a rest position,
        and torque can be safely disabled to run calibration.
        """
        if self.is_connected:
            raise DeviceAlreadyConnectedError(f"{self} already connected")

        self.bus.connect()
        if not self.is_calibrated and calibrate:
            self.calibrate()

        for cam in self.cameras.values():
            cam.connect()

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
        print("Calibration saved to", self.calibration_fpath)

    def configure(self) -> None:
        with self.bus.torque_disabled():
            self.bus.configure_motors()
            for motor in self.bus.motors:
                self.bus.write("Operating_Mode", motor, OperatingMode.POSITION.value)
                # Set P_Coefficient to lower value to avoid shakiness (Default is 32)
                self.bus.write("P_Coefficient", motor, 16)
                # Set I_Coefficient and D_Coefficient to default value 0 and 32
                self.bus.write("I_Coefficient", motor, 0)
                self.bus.write("D_Coefficient", motor, 32)

    def setup_motors(self) -> None:
        for motor in reversed(self.bus.motors):
            input(f"Connect the controller board to the '{motor}' motor only and press enter.")
            self.bus.setup_motor(motor)
            print(f"'{motor}' motor id set to {self.bus.motors[motor].id}")

    def get_observation(self) -> dict[str, Any]:
        if not self.is_connected:
            raise DeviceNotConnectedError(f"{self} is not connected.")

        # Read arm position
        start = time.perf_counter()
        obs_dict = self.bus.sync_read("Present_Position")
        obs_dict = {f"{motor}.pos": val for motor, val in obs_dict.items()}
        dt_ms = (time.perf_counter() - start) * 1e3
        logger.debug(f"{self} read state: {dt_ms:.1f}ms")

        # Capture images from cameras
        for cam_key, cam in self.cameras.items():
            start = time.perf_counter()
            obs_dict[cam_key] = cam.async_read()
            dt_ms = (time.perf_counter() - start) * 1e3
            logger.debug(f"{self} read {cam_key}: {dt_ms:.1f}ms")

        return obs_dict

    def send_action(self, action: dict[str, Any]) -> dict[str, Any]:
        """Command arm to move to a target joint configuration.

        The relative action magnitude may be clipped depending on the configuration parameter
        `max_relative_target`. In this case, the action sent differs from original action.
        Thus, this function always returns the action actually sent.

        Raises:
            RobotDeviceNotConnectedError: if robot is not connected.

        Returns:
            the action sent to the motors, potentially clipped.
        """
        if not self.is_connected:
            raise DeviceNotConnectedError(f"{self} is not connected.")

        goal_pos = {key.removesuffix(".pos"): val for key, val in action.items() if key.endswith(".pos")}

        # Cap goal position when too far away from present position.
        # /!\ Slower fps expected due to reading from the follower.
        if self.config.max_relative_target is not None:
            present_pos = self.bus.sync_read("Present_Position")
            goal_present_pos = {key: (g_pos, present_pos[key]) for key, g_pos in goal_pos.items()}
            goal_pos = ensure_safe_goal_position(goal_present_pos, self.config.max_relative_target)

        # Send goal position to the arm
        self.bus.sync_write("Goal_Position", goal_pos)
        return {f"{motor}.pos": val for motor, val in goal_pos.items()}

    def disconnect(self):
        if not self.is_connected:
            raise DeviceNotConnectedError(f"{self} is not connected.")

        self.bus.disconnect(self.config.disable_torque_on_disconnect)
        for cam in self.cameras.values():
            cam.disconnect()

        logger.info(f"{self} disconnected.")
