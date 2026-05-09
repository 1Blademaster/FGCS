import time

import app.droneStatus as droneStatus
from app import logger, socketio
from app.drone import Drone


@socketio.on("reboot_autopilot")
def rebootAutopilot() -> None:
    """
    Attempt to reboot the autopilot, this will try to reconnect to the drone 3 times before stopping.

    Note: If SITL is running and you are connected via TCP 5763 then rebooting does not work as expected.
    Use TCP 5760 instead.
    """
    if not droneStatus.drone:
        return

    port = droneStatus.drone.port
    baud = droneStatus.drone.baud
    droneErrorCb = droneStatus.drone.droneErrorCb
    droneDisconnectCb = droneStatus.drone.droneDisconnectCb
    linkDebugStatsCb = droneStatus.drone.linkDebugStatsCb
    fetchingParameterCb = droneStatus.drone.fetchingParameterCb
    forwarding_address = droneStatus.drone.forwarding_address

    socketio.emit("disconnected_from_drone")

    reboot_success = droneStatus.drone.rebootAutopilot()

    if not reboot_success:
        logger.error("Failed to send reboot command to autopilot.")
        socketio.emit(
            "reboot_autopilot",
            {
                "success": False,
                "message": "Failed to send reboot command to autopilot.",
            },
        )
        return

    droneStatus.drone = None

    time.sleep(1.5)  # Wait for the port to be released and let the autopilot reboot

    socketio.emit("reboot_connecting")

    tries = 0
    while tries < 3:
        droneStatus.drone = Drone(
            port,
            baud=baud,
            forwarding_address=forwarding_address,
            droneErrorCb=droneErrorCb,
            droneDisconnectCb=droneDisconnectCb,
            linkDebugStatsCb=linkDebugStatsCb,
            fetchingParameterCb=fetchingParameterCb,
        )
        if droneStatus.drone.connectionError:
            tries += 1
            time.sleep(2)
        else:
            break
    else:
        droneStatus.drone = None
        logger.error("Could not reconnect to drone after 3 attempts.")
        socketio.emit(
            "reboot_autopilot",
            {
                "success": False,
                "message": "Could not reconnect to drone after 3 attempts.",
            },
        )
        return

    time.sleep(1)
    socketio.emit(
        "connected_to_drone", {"aircraft_type": droneStatus.drone.aircraft_type}
    )
    logger.info("Rebooted autopilot successfully.")
    socketio.emit(
        "reboot_autopilot",
        {"success": True, "message": "Rebooted autopilot successfully."},
    )
