"""Unit and integration tests for OScope Web API handlers."""

import pytest
from web.api import OScopeApiHandler
from oscope_gui.backend.runner import WSLBackendRunner, discover_backend


@pytest.fixture(scope="module")
def api_handler():
    runner, info = discover_backend()
    return OScopeApiHandler(runner=runner)


def test_api_status(api_handler):
    status = api_handler.get_status()
    assert "is_available" in status
    assert "runner_type" in status
    assert "executable_path" in status


def test_api_scheduling_validation_error(api_handler):
    with pytest.raises(ValueError):
        api_handler.run_scheduling({"algorithm": "FCFS", "processes": []})


def test_api_paging_validation_error(api_handler):
    with pytest.raises(ValueError):
        api_handler.run_paging({"algorithm": "FIFO", "num_frames": 0, "reference_string": [1, 2]})


def test_api_deadlock_validation_error(api_handler):
    with pytest.raises(ValueError):
        api_handler.run_deadlock({
            "mode": "safety",
            "num_processes": 1,
            "num_resources": 1,
            "available": [],
            "allocation": [],
            "max_claim": []
        })
