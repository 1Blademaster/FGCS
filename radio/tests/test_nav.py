import app.droneStatus as droneStatus
import pytest
from flask_socketio.test_client import SocketIOTestClient


@pytest.fixture(autouse=True)
def restore_state():
    original_state = droneStatus.state
    yield
    droneStatus.state = original_state


@pytest.fixture()
def restore_wp_radius():
    drone = droneStatus.drone
    assert drone is not None
    original = drone.navController.getWpRadius().get("data")
    yield
    if original is not None:
        drone.navController.setWpRadius(original)


def test_set_waypoint_radius_success(
    socketio_client: SocketIOTestClient, restore_wp_radius
):
    drone = droneStatus.drone
    assert drone is not None
    droneStatus.state = "missions"
    expected_param = drone.navController._getWpRadiusParamName()

    socketio_client.emit("set_waypoint_radius", {"value": 5})
    response = socketio_client.get_received()[0]

    assert response["name"] == "set_waypoint_radius_result"
    assert response["args"][0]["success"] is True
    assert response["args"][0]["data"]["param_id"] == expected_param
    assert response["args"][0]["data"]["param_value"] == 5


def test_get_waypoint_radius_success(socketio_client: SocketIOTestClient):
    droneStatus.state = "missions"

    socketio_client.emit("get_waypoint_radius")
    response = socketio_client.get_received()[0]

    assert response["name"] == "get_waypoint_radius_result"
    assert response["args"][0]["success"] is True
    assert isinstance(response["args"][0]["data"], (int, float))


def test_set_waypoint_radius_returns_error_when_invalid_value(
    socketio_client: SocketIOTestClient,
):
    droneStatus.state = "missions"

    socketio_client.emit("set_waypoint_radius", {"value": -1})
    response = socketio_client.get_received()[0]

    assert response["name"] == "params_error"
    assert "Waypoint radius must be a positive number" in response["args"][0]["message"]
