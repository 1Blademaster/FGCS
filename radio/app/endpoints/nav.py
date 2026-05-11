from typing_extensions import TypedDict

import app.droneStatus as droneStatus
from app import logger, socketio
from app.utils import notConnectedError


class TakeoffDataType(TypedDict):
    alt: int


class RepositionDataType(TypedDict):
    lat: float
    lon: float
    alt: int


class LoiterRadiusDataType(TypedDict):
    radius: float


class WaypointRadiusDataType(TypedDict):
    value: float


@socketio.on("get_home_position")
def getHomePosition() -> None:
    """
    Gets the home position of the drone, only works when the dashboard or missions page is loaded.
    """
    if droneStatus.state not in ["dashboard", "missions"]:
        socketio.emit(
            "params_error",
            {
                "message": "You must be on the dashboard or missions screen to get the home position."
            },
        )
        logger.debug(f"Current state: {droneStatus.state}")
        return

    if not droneStatus.drone:
        return notConnectedError(action="get home position")

    result = droneStatus.drone.navController.getHomePosition()

    socketio.emit("home_position_result", result)


@socketio.on("takeoff")
def takeoff(data: TakeoffDataType) -> None:
    """
    Commands the drone to takeoff, only works when the dashboard page is loaded.
    """
    if droneStatus.state != "dashboard":
        socketio.emit(
            "params_error",
            {"message": "You must be on the dashboard screen to takeoff."},
        )
        logger.debug(f"Current state: {droneStatus.state}")
        return

    if not droneStatus.drone:
        return notConnectedError(action="takeoff")

    alt = data.get("alt", None)
    if alt is None or alt < 0:
        socketio.emit(
            "params_error",
            {"message": f"Takeoff altitude must be a positive number, got {alt}."},
        )
        return

    result = droneStatus.drone.navController.takeoff(alt)

    socketio.emit("nav_result", result)


@socketio.on("land")
def land() -> None:
    """
    Commands the drone to land, only works when the dashboard page is loaded.
    """
    if droneStatus.state != "dashboard":
        socketio.emit(
            "params_error",
            {"message": "You must be on the dashboard screen to land."},
        )
        logger.debug(f"Current state: {droneStatus.state}")
        return

    if not droneStatus.drone:
        return notConnectedError(action="land")

    result = droneStatus.drone.navController.land()

    socketio.emit("nav_result", result)


@socketio.on("reposition")
def reposition(data: RepositionDataType) -> None:
    """
    Commands the drone to reposition, only works when the dashboard page is loaded.
    """
    if droneStatus.state != "dashboard":
        socketio.emit(
            "params_error",
            {"message": "You must be on the dashboard screen to reposition."},
        )
        logger.debug(f"Current state: {droneStatus.state}")
        return

    if not droneStatus.drone:
        return notConnectedError(action="reposition")

    alt = data.get("alt", None)
    if alt is None or alt < 0:
        socketio.emit(
            "params_error",
            {"message": f"Reposition altitude must be a positive number, got {alt}."},
        )
        return

    lat = data.get("lat", None)
    lon = data.get("lon", None)

    if lat is None or lon is None:
        socketio.emit(
            "params_error",
            {"message": "Reposition latitude and longitude must be specified."},
        )
        return

    result = droneStatus.drone.navController.reposition(lat, lon, alt)

    socketio.emit("nav_reposition_result", result)


@socketio.on("get_loiter_radius")
def getLoiterRadius() -> None:
    """
    Gets the loiter radius of the drone, only works when the dashboard page is loaded.
    """
    if droneStatus.state not in ["dashboard"]:
        socketio.emit(
            "params_error",
            {
                "message": "You must be on the dashboard screen to get the loiter radius."
            },
        )
        logger.debug(f"Current state: {droneStatus.state}")
        return

    if not droneStatus.drone:
        return notConnectedError(action="get loiter radius")

    result = droneStatus.drone.navController.getLoiterRadius()

    socketio.emit("nav_get_loiter_radius_result", result)


@socketio.on("set_loiter_radius")
def setLoiterRadius(data: LoiterRadiusDataType) -> None:
    """
    Sets the loiter radius of the drone, only works when the dashboard page is loaded.
    """
    if droneStatus.state != "dashboard":
        socketio.emit(
            "params_error",
            {
                "message": "You must be on the dashboard screen to set the loiter radius."
            },
        )
        logger.debug(f"Current state: {droneStatus.state}")
        return

    if not droneStatus.drone:
        return notConnectedError(action="set loiter radius")

    radius = data.get("radius", None)
    if radius is None or radius < 0:
        socketio.emit(
            "params_error",
            {"message": f"Loiter radius must be a positive number, got {radius}."},
        )
        return

    result = droneStatus.drone.navController.setLoiterRadius(radius)

    socketio.emit("nav_set_loiter_radius_result", result)


@socketio.on("set_waypoint_radius")
def setWaypointRadius(data: WaypointRadiusDataType) -> None:
    """
    Sets the waypoint radius parameter on the drone from the missions or dashboard page.
    """
    if droneStatus.state not in ["dashboard", "missions"]:
        socketio.emit(
            "params_error",
            {
                "message": "You must be on the dashboard or missions screen to set the waypoint radius."
            },
        )
        logger.debug(f"Current state: {droneStatus.state}")
        return

    if not droneStatus.drone:
        return notConnectedError(action="set waypoint radius")

    value = data.get("value", None)
    if value is None or not isinstance(value, (int, float)) or value <= 0:
        socketio.emit(
            "params_error",
            {"message": f"Waypoint radius must be a positive number, got {value}."},
        )
        return

    result = droneStatus.drone.navController.setWpRadius(value)

    socketio.emit("set_waypoint_radius_result", result)


@socketio.on("get_waypoint_radius")
def getWaypointRadius() -> None:
    """
    Gets the waypoint radius of the drone, only works when the dashboard or missions page is loaded.
    """
    if droneStatus.state not in ["dashboard", "missions"]:
        socketio.emit(
            "params_error",
            {
                "message": "You must be on the dashboard or missions screen to get the waypoint radius."
            },
        )
        logger.debug(f"Current state: {droneStatus.state}")
        return

    if not droneStatus.drone:
        return notConnectedError(action="get waypoint radius")

    result = droneStatus.drone.navController.getWpRadius()

    socketio.emit("get_waypoint_radius_result", result)
