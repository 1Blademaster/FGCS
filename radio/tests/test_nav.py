from types import SimpleNamespace

import app.droneStatus as droneStatus
import pytest
from flask_socketio.test_client import SocketIOTestClient

from app.controllers.navController import NavController


class FakeParamsController:
    def __init__(self):
        self.last_call = None

    def setParam(self, param_name, param_value):
        self.last_call = {
            "param_name": param_name,
            "param_value": param_value,
        }
        return True

    def getSingleParam(self, _param_name):
        return {}


def _make_fake_drone(aircraft_type, flight_sw_version):
    params = FakeParamsController()
    logger = SimpleNamespace(
        info=lambda *a, **kw: None,
        warning=lambda *a, **kw: None,
        error=lambda *a, **kw: None,
        debug=lambda *a, **kw: None,
    )
    drone = SimpleNamespace(
        aircraft_type=aircraft_type,
        flight_sw_version=flight_sw_version,
        paramsController=params,
        logger=logger,
    )
    drone.navController = NavController(drone)
    return drone


@pytest.fixture(autouse=True)
def restore_drone(monkeypatch):
    original_drone = droneStatus.drone
    yield
    droneStatus.drone = original_drone


def _get_last_response(socketio_client):
    received = socketio_client.get_received()
    return received[-1] if received else None


def test_set_waypoint_radius_uses_wp_radius_for_plane(
    socketio_client: SocketIOTestClient, monkeypatch
):
    fake_drone = _make_fake_drone(aircraft_type=1, flight_sw_version=(4, 6, 0, 0))
    monkeypatch.setattr(droneStatus, "drone", fake_drone)
    droneStatus.state = "missions"

    socketio_client.emit("set_waypoint_radius", {"value": 5})
    response = _get_last_response(socketio_client)

    assert response is not None
    assert response["name"] == "set_waypoint_radius_result"
    assert response["args"][0]["success"] is True
    assert response["args"][0]["message"] == "Waypoint radius set to 5m"
    assert response["args"][0]["data"]["param_id"] == "WP_RADIUS"
    assert response["args"][0]["data"]["param_value"] == 5
    assert fake_drone.paramsController.last_call["param_name"] == "WP_RADIUS"


@pytest.mark.copter_only
@pytest.mark.parametrize(
    "flight_sw_version,expected_param",
    [
        ((4, 6, 9, 0), "WPNAV_RADIUS"),
        ((4, 7, 0, 0), "WP_RADIUS_M"),
        ((4, 8, 1, 0), "WP_RADIUS_M"),
    ],
)
def test_set_waypoint_radius_chooses_correct_copter_param(
    socketio_client: SocketIOTestClient,
    monkeypatch,
    flight_sw_version,
    expected_param,
):
    fake_drone = _make_fake_drone(aircraft_type=2, flight_sw_version=flight_sw_version)
    monkeypatch.setattr(droneStatus, "drone", fake_drone)
    droneStatus.state = "missions"

    socketio_client.emit("set_waypoint_radius", {"value": 7})
    response = _get_last_response(socketio_client)

    assert response is not None
    assert response["name"] == "set_waypoint_radius_result"
    assert response["args"][0]["success"] is True
    assert response["args"][0]["message"] == "Waypoint radius set to 7m"
    assert response["args"][0]["data"]["param_id"] == expected_param
    assert response["args"][0]["data"]["param_value"] == 7
    assert fake_drone.paramsController.last_call["param_name"] == expected_param


def test_set_waypoint_radius_returns_error_when_invalid_value(
    socketio_client: SocketIOTestClient, monkeypatch
):
    fake_drone = _make_fake_drone(aircraft_type=1, flight_sw_version=(4, 7, 0, 0))
    monkeypatch.setattr(droneStatus, "drone", fake_drone)
    droneStatus.state = "missions"

    socketio_client.emit("set_waypoint_radius", {"value": -1})
    response = _get_last_response(socketio_client)

    assert response is not None
    assert response["name"] == "params_error"
    assert "Waypoint radius must be a positive number" in response["args"][0]["message"]
