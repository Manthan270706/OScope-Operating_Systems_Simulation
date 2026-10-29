"""Integration tests for the OScope Web HTTP Server."""

import json
import threading
import time
from urllib.request import Request, urlopen
from urllib.error import HTTPError
import pytest

from web.server import ThreadingHTTPServer, OScopeRequestHandler
from web.api import OScopeApiHandler
from oscope_gui.backend.runner import discover_backend


@pytest.fixture(scope="module")
def server_url():
    """Start the test server on a local ephemeral port and shut it down after tests."""
    runner, _ = discover_backend()
    OScopeRequestHandler.api_handler = OScopeApiHandler(runner=runner)

    server = ThreadingHTTPServer(("127.0.0.1", 0), OScopeRequestHandler)
    port = server.server_port
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()

    time.sleep(0.1)
    base_url = f"http://127.0.0.1:{port}"
    yield base_url

    server.shutdown()
    server.server_close()


def test_server_serves_index_html(server_url):
    with urlopen(f"{server_url}/") as resp:
        assert resp.status == 200
        content = resp.read().decode("utf-8")
        assert "<title>OScope — Operating Systems Simulation & Experimentation Laboratory</title>" in content
        assert 'id="view-overview"' in content
        assert 'id="view-scheduling"' in content


def test_server_serves_light_theme_css(server_url):
    with urlopen(f"{server_url}/static/css/main.css") as resp:
        assert resp.status == 200
        content = resp.read().decode("utf-8")
        assert "--bg-canvas: #f8fafc;" in content
        assert "--border: #e2e8f0;" in content
        assert "--primary: #0f172a;" in content


def test_server_serves_visualizations_js(server_url):
    with urlopen(f"{server_url}/static/js/visualizations.js") as resp:
        assert resp.status == 200
        content = resp.read().decode("utf-8")
        assert "renderGanttChart" in content
        assert "renderMemoryMap" in content
        assert "renderDiskPlot" in content


def test_server_serves_app_js(server_url):
    with urlopen(f"{server_url}/static/js/app.js") as resp:
        assert resp.status == 200
        content = resp.read().decode("utf-8")
        assert "routeMetadata" in content
        assert "navigateTo" in content


def test_api_status_endpoint(server_url):
    with urlopen(f"{server_url}/api/status") as resp:
        assert resp.status == 200
        data = json.loads(resp.read().decode("utf-8"))
        assert "is_available" in data
        assert "runner_type" in data


def test_api_scheduling_simulation(server_url):
    req_body = json.dumps({
        "algorithm": "FCFS",
        "quantum": 2,
        "processes": [
            {"pid": 1, "arrival_time": 0, "burst_time": 4, "priority": 1},
            {"pid": 2, "arrival_time": 1, "burst_time": 3, "priority": 2}
        ]
    }).encode("utf-8")
    req = Request(f"{server_url}/api/scheduling/run", data=req_body, headers={"Content-Type": "application/json"})
    with urlopen(req) as resp:
        assert resp.status == 200
        res = json.loads(resp.read().decode("utf-8"))
        assert "timeline" in res
        assert "averages" in res
        assert len(res["timeline"]) > 0
        assert res["averages"]["average_turnaround_time"] > 0
