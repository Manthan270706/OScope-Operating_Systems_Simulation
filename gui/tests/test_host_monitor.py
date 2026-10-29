"""Unit and integration tests for Host Resource Monitoring GUI module."""

import json
import os
import pytest

os.environ["QT_QPA_PLATFORM"] = "offscreen"

from oscope_gui.backend.parser import parse_host_monitoring_output
from oscope_gui.models.host_monitor import (
    HostCpuModel,
    HostDiskIoModel,
    HostMemoryModel,
    HostMonitoringSnapshotModel,
    HostProcessModel,
    HostSystemModel,
)


class DummyHostRunner:
    def __init__(self, sample_stdout="", exit_code=0, is_timeout=False):
        self.sample_stdout = sample_stdout
        self.exit_code = exit_code
        self.is_timeout = is_timeout
        self.last_args = None

    def execute(self, args, stdin_data=None, timeout=10.0):
        from oscope_gui.backend.runner import ExecutionResult

        self.last_args = args
        return ExecutionResult(
            exit_code=self.exit_code,
            stdout=self.sample_stdout,
            stderr="" if self.exit_code == 0 else "Execution failed",
            duration=0.15,
            is_timeout=self.is_timeout,
            command=["build/oscope"] + args,
        )

    def verify(self):
        return True, "Host monitor runner ready"

    def get_info(self):
        from oscope_gui.backend.runner import BackendInfo

        return BackendInfo(
            runner_type="wsl",
            executable_path="build/oscope",
            is_available=True,
            status_message="WSL host monitoring available",
        )

    def cancel(self):
        pass


SAMPLE_MONITOR_JSON = json.dumps({
    "schema_version": "1.0.0",
    "category": "linux_monitoring",
    "experiment": "host_observation",
    "status": "success",
    "success": True,
    "result": {
        "source": "real_linux_host",
        "timestamp": "2026-10-29 03:39:35",
        "cpu_usage_percent": "14.50",
        "cpu_user_percent": "4.50",
        "cpu_system_percent": "6.00",
        "cpu_idle_percent": "85.50",
        "memory_total_kb": 8000000,
        "memory_used_kb": 2000000,
        "memory_available_kb": 6000000,
        "memory_free_kb": 5500000,
        "memory_used_percent": "25.00",
        "uptime_seconds": "3665.50",
        "load_1min": "0.75",
        "load_5min": "0.50",
        "load_15min": "0.25",
        "total_processes": 320,
        "running_processes": 2,
        "disk_total_bytes": 1073741824000,
        "disk_used_bytes": 268435456000,
        "disk_available_bytes": 805306368000,
        "disk_used_percent": "25.00",
        "self_pid": 420,
        "self_ppid": 419,
        "self_comm": "oscope",
        "self_state": "R",
        "self_rss_kb": 4096,
        "self_vm_size_bytes": 8192000,
        "disks": [
            {
                "device_name": "sdd",
                "reads_completed": 12000,
                "sectors_read": 96000,
                "writes_completed": 8500,
                "sectors_written": 68000,
            },
            {
                "device_name": "ram0",
                "reads_completed": 0,
                "sectors_read": 0,
                "writes_completed": 0,
                "sectors_written": 0,
            },
        ],
    },
    "error": None,
})


SAMPLE_MONITOR_TEXT = """
=== Linux Host Resource Monitoring (Real System Observations) ===
Source:     real_linux_host
Timestamp:  2026-10-29 03:45:00

1. Host CPU Metrics (/proc/stat):
  Total CPU Usage:  12.50 %
  User Space:       4.00 %
  Kernel / System:  5.50 %
  Idle:             87.50 %

2. Host Memory Metrics (/proc/meminfo):
  Total RAM:        8192000 kB (8000 MB)
  Used RAM:         2048000 kB (2000 MB)
  Available RAM:    6144000 kB (6000 MB)
  Utilization:      25.00 %

3. Self-Process Observation (/proc/self/stat):
  PID:              450
  Executable Name:  oscope
  Process State:    R
  User CPU Ticks:   12
  System CPU Ticks: 8
  Virtual Memory:   8192 kB
  Resident Set:     4096 kB

4. Host Block Device I/O (/proc/diskstats):
  Device:      sdd | Reads:   15000 | Sectors Read:   120000 | Writes:    9000 | Sectors Written: 72000

5. Host System & Filesystem Overview:
  Uptime:           7200.0 seconds
  Load Averages:    0.80 (1m), 0.60 (5m), 0.40 (15m)
  Process Count:    350 total (2 runnable)
  Root Mount:       /
  Disk Capacity:    1024000 MB
  Disk Used:        256000 MB (25.0 %)
  Disk Available:   768000 MB
"""


def test_host_models():
    """Verify all host telemetry dataclasses and helper properties."""
    cpu = HostCpuModel(total_usage_percent=15.0, user_percent=5.0, system_percent=6.0, idle_percent=85.0, valid=True)
    assert cpu.valid is True
    assert cpu.total_usage_percent == 15.0

    mem = HostMemoryModel(total_kb=8192000, used_kb=2048000, available_kb=6144000, free_kb=5000000, used_percent=25.0, valid=True)
    assert mem.total_mb == 8000.0
    assert mem.used_mb == 2000.0
    assert mem.available_mb == 6000.0

    sys_mod = HostSystemModel(
        uptime_seconds=3665.0,
        load_1min=0.5,
        total_processes=300,
        disk_total_bytes=100 * 1024 * 1024 * 1024,
        disk_used_bytes=25 * 1024 * 1024 * 1024,
        disk_available_bytes=75 * 1024 * 1024 * 1024,
        disk_used_percent=25.0,
        valid=True,
    )
    assert sys_mod.uptime_formatted == "1h 1m 5s"
    assert round(sys_mod.disk_total_gb, 1) == 100.0

    proc = HostProcessModel(pid=100, ppid=99, comm="bash", state="R", rss_kb=2048, valid=True)
    assert proc.state_description == "Running (R)"

    disk = HostDiskIoModel(device_name="sdd", reads_completed=100, sectors_read=800, writes_completed=50, sectors_written=400, valid=True)
    assert disk.device_name == "sdd"


def test_host_parser_json():
    """Verify parsing C++ --demo-monitor --json output."""
    snapshot = parse_host_monitoring_output(SAMPLE_MONITOR_JSON, exit_code=0, duration_ms=50.0)

    assert snapshot.success is True
    assert snapshot.source == "real_linux_host"
    assert snapshot.timestamp == "2026-10-29 03:39:35"

    # CPU
    assert snapshot.cpu.valid is True
    assert snapshot.cpu.total_usage_percent == 14.5
    assert snapshot.cpu.idle_percent == 85.5

    # Memory
    assert snapshot.memory.valid is True
    assert snapshot.memory.total_kb == 8000000
    assert snapshot.memory.used_percent == 25.0

    # System
    assert snapshot.system.valid is True
    assert snapshot.system.uptime_seconds == 3665.5
    assert snapshot.system.load_1min == 0.75
    assert snapshot.system.total_processes == 320

    # Self-Process
    assert snapshot.self_process.valid is True
    assert snapshot.self_process.pid == 420
    assert snapshot.self_process.comm == "oscope"
    assert snapshot.self_process.state == "R"

    # Disks
    assert len(snapshot.disks) == 2
    assert snapshot.disks[0].device_name == "sdd"
    assert snapshot.disks[0].reads_completed == 12000


def test_host_parser_text_fallback():
    """Verify parsing human-readable C++ terminal output."""
    snapshot = parse_host_monitoring_output(SAMPLE_MONITOR_TEXT, exit_code=0, duration_ms=50.0)

    assert snapshot.success is True
    assert snapshot.cpu.valid is True
    assert snapshot.cpu.total_usage_percent == 12.5

    assert snapshot.memory.valid is True
    assert snapshot.memory.total_kb == 8192000
    assert snapshot.memory.used_percent == 25.0

    assert snapshot.self_process.valid is True
    assert snapshot.self_process.pid == 450
    assert snapshot.self_process.comm == "oscope"

    assert snapshot.system.valid is True
    assert snapshot.system.uptime_seconds == 7200.0
    assert snapshot.system.load_1min == 0.8
    assert snapshot.system.total_processes == 350

    assert len(snapshot.disks) == 1
    assert snapshot.disks[0].device_name == "sdd"


def test_host_parser_failure():
    """Verify parsing non-zero exit code or empty output."""
    snap = parse_host_monitoring_output("Error accessing /proc", exit_code=1)
    assert snap.success is False
    assert "exit code 1" in snap.error_message


def test_host_widgets(qapp):
    """Verify HostMetricCard, Plot, and Tables instantiate and update."""
    from oscope_gui.widgets.host_monitor_viz import (
        HostDiskTableWidget,
        HostMetricCard,
        HostMetricHistoryPlotWidget,
        HostProcessTableWidget,
    )

    # Metric card
    card = HostMetricCard("TEST CPU")
    card.update_metric("25.0 %", 25.0, "Detail text", is_active=True)
    assert card.lbl_value.text() == "25.0 %"
    assert card.progress_bar.value() == 25

    # Stale state
    card.update_metric("25.0 %", 25.0, "Stale", is_active=False)
    assert card.lbl_badge.text() == "Stale / Paused"

    # Plot widget
    plot = HostMetricHistoryPlotWidget()
    plot.add_sample(10.0, 20.0, "00:01")
    plot.add_sample(15.0, 25.0, "00:02")
    assert len(plot.cpu_history) == 2
    plot.clear()
    assert len(plot.cpu_history) == 0

    # Process Table
    proc_table = HostProcessTableWidget()
    proc_table.update_process(HostProcessModel(pid=100, comm="test", state="R", rss_kb=4096, valid=True))
    assert proc_table.rowCount() == 1
    assert proc_table.item(0, 0).text() == "100"

    # Disk Table
    disk_table = HostDiskTableWidget()
    disk_table.update_disks([HostDiskIoModel(device_name="sdd", reads_completed=10, valid=True)])
    assert disk_table.rowCount() == 1
    assert disk_table.item(0, 0).text() == "sdd"


def test_host_page_and_worker(qapp):
    """Verify HostMonitorPage and HostMonitorWorker execution."""
    from oscope_gui.backend.executor import HostMonitorWorker
    from oscope_gui.pages.host_monitor_page import HostMonitorPage

    runner = DummyHostRunner(sample_stdout=SAMPLE_MONITOR_JSON, exit_code=0)

    # 1. Single shot worker test
    worker = HostMonitorWorker(runner=runner, continuous=False)
    received = []
    worker.sample_received.connect(lambda s: received.append(s))
    worker.start()
    worker.wait(1500)
    qapp.processEvents()
    assert len(received) == 1
    assert received[0].cpu.total_usage_percent == 14.5

    # 2. Page test
    page = HostMonitorPage(runner=runner)
    assert page.btn_toggle_live.text().strip() == "▶  Start Live Monitoring"

    # Sample once via page
    w = page.sample_once()
    assert w is not None
    w.wait(1500)
    qapp.processEvents()
    assert page.card_cpu.lbl_value.text() == "14.5 %"
    assert page.card_mem.lbl_value.text() != "—"

    # Start live monitoring
    page.start_monitoring()
    assert page._is_monitoring_active is True
    assert "Pause" in page.btn_toggle_live.text()

    # Pause live monitoring
    page.stop_monitoring()
    assert page._is_monitoring_active is False
    assert "Start" in page.btn_toggle_live.text()
