from blinker import Signal
from . import socketio

from typing import TypedDict, NotRequired
from app.customTypes import Number

import logging

logger = logging.getLogger("fgcs")

# Define signals
DroneError = Signal()
DroneConnectStatus = Signal()


@DroneError.connect
def droneErrorHandler(sender, msg: str) -> None:
    """
    Send drone error to the socket

    Args:
        msg: The error message to send to the client
    """
    logger.debug(f"dronErrorHandler called by: {sender} with msg: {msg}")
    socketio.emit("drone_error", {"message": msg})

    ## Optionally you can add return values
    ## That would be what the function would return to the caller
    # return {success: true}


class DroneConnectionStatusDataType(TypedDict):
    message: str
    progress: Number
    sub_message: NotRequired[str]


@DroneConnectStatus.connect
def droneConnectStatusHandler(sender, msg: DroneConnectionStatusDataType) -> None:
    """
    Send drone connect status updates to the socket

    Args:
        msg: The connect message to send to the client
    """
    logger.debug(f"droneConnectStatusHandler called by: {sender} with msg: {msg}")
    socketio.emit("drone_connect_status", msg)
