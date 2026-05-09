from __future__ import annotations

import time
from threading import current_thread
from typing import TYPE_CHECKING

from app.signals import DroneError
from app.customTypes import Response
from app.utils import commandAccepted, sendingCommandLock
from pymavlink import mavutil

if TYPE_CHECKING:
    from app.drone import Drone


class ArmController:
    def __init__(self, drone: Drone) -> None:
        """
        The Arm controller controls all arm/disarming operations.

        Args:
            drone (Drone): The main drone object
        """
        self.controller_id = f"arm_{current_thread().ident}"
        self.drone = drone

    @sendingCommandLock
    def arm(self, force: bool = False) -> Response:
        """
        Arm the drone.

        Args:
            force (bool, optional): Option to force arm the drone. Defaults to False.

        Returns:
            Response: The response from the arm command
        """
        return_data = {
            "was_disarming": False,
            "was_force": force,
            "offer_force": False,
        }

        if self.drone.armed:
            return {"success": False, "message": "Already armed", "data": return_data}

        if not self.drone.reserve_message_type("COMMAND_ACK", self.controller_id):
            return {
                "success": False,
                "message": "Could not reserve COMMAND_ACK messages",
                "data": return_data,
            }

        try:
            self.drone.sendCommand(
                mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM,
                param1=1,  # 0=disarm, 1=arm
                param2=21196 if force else 0,  # force arm/disarm
            )
            self.drone.logger.info(f"Arming, force: {force}")

            response = self.drone.wait_for_message(
                "COMMAND_ACK",
                self.controller_id,
                condition_func=lambda msg: msg.command
                == mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM,
            )

            if commandAccepted(response, mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM):
                # Wait for the drone to be armed fully after the command has been accepted
                self.drone.logger.debug("Waiting for arm")
                while not self.drone.armed:
                    time.sleep(0.05)

                return {
                    "success": True,
                    "message": "Armed successfully",
                    "data": return_data,
                }
            else:
                self.drone.logger.debug("Arming failed")
                return_data["offer_force"] = True
                return {
                    "success": False,
                    "message": "Could not arm, command not accepted",
                    "data": return_data,
                }

        except Exception as e:
            self.drone.logger.error(e, exc_info=True)
            self.drone.error(str(e))

            ## Or you can have just have:                 (TODO: remove)
            DroneError.send(self, msg=str(e))

            return {
                "success": False,
                "message": "Could not arm, serial exception",
                "data": return_data,
            }
        finally:
            self.drone.release_message_type("COMMAND_ACK", self.controller_id)

    @sendingCommandLock
    def disarm(self, force: bool = False) -> Response:
        """
        Disarm the drone.

        Args:
            force (bool, optional): Option to force disarm the drone. Defaults to False.

        Returns:
            Response: The response from the disarm command
        """
        return_data = {
            "was_disarming": True,
            "was_force": force,
            "offer_force": False,
        }

        if not self.drone.armed:
            return {
                "success": False,
                "message": "Already disarmed",
                "data": return_data,
            }

        if not self.drone.reserve_message_type("COMMAND_ACK", self.controller_id):
            return {
                "success": False,
                "message": "Could not reserve COMMAND_ACK messages",
                "data": return_data,
            }

        try:
            self.drone.sendCommand(
                mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM,
                param1=0,  # 0=disarm, 1=arm
                param2=21196 if force else 0,  # force arm/disarm
            )

            self.drone.logger.info(f"Disarming, force: {force}")

            response = self.drone.wait_for_message(
                "COMMAND_ACK",
                self.controller_id,
                condition_func=lambda msg: msg.command
                == mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM,
            )

            if commandAccepted(response, mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM):
                # Wait for the drone to be disarmed fully after the command has been accepted
                self.drone.logger.debug("Waiting for disarm")
                while self.drone.armed:
                    time.sleep(0.05)

                return {
                    "success": True,
                    "message": "Disarmed successfully",
                    "data": return_data,
                }
            else:
                self.drone.logger.debug("Could not disarm, command not accepted")
                return_data["offer_force"] = True
                return {
                    "success": False,
                    "message": "Could not disarm, command not accepted",
                    "data": return_data,
                }

        except Exception as e:
            self.drone.logger.error(e, exc_info=True)
            if self.drone.droneErrorCb:
                self.drone.droneErrorCb(str(e))
            return {
                "success": False,
                "message": "Could not disarm, serial exception",
                "data": return_data,
            }
        finally:
            self.drone.release_message_type("COMMAND_ACK", self.controller_id)
