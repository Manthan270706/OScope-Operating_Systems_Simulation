"""Focused unit tests for Process Lifecycle State Machine Explorer.

Covers models, input generation, output parsing (JSON & fallback),
widgets (state diagram, process table, history table), and ProcessLifecyclePage.
"""

import json
import os
import pytest

os.environ["QT_QPA_PLATFORM"] = "offscreen"

from oscope_gui.backend.parser import (
    generate_process_ops_stdin,
    parse_process_lifecycle_output,
)
from oscope_gui.models.process_lifecycle import (
    ProcessInstanceModel,
    ProcessLifecycleConfig,
    ProcessLifecycleSimulationResultModel,
    ProcessLifecycleState,
    ProcessTransitionModel,
)
from oscope_gui.widgets.process_lifecycle_viz import (
    ProcessStateDiagramWidget,
    ProcessTableWidget,
    ProcessTransitionHistoryWidget,
)


class DummyBackendRunner:
    """Mock runner for headless GUI testing."""

    def __init__(self):
        self.last_stdin = None
        self.last_args = None

    def execute(self, args, stdin_data=None, timeout=15.0):
        from oscope_gui.backend.runner import ExecutionResult

        self.last_args = args
        self.last_stdin = stdin_data

        dummy_json = {
            "category": "process_lifecycle",
            "experiment": "process_state_machine",
            "processes": [
                {
                    "pid": 1,
                    "arrival_time": 0,
                    "burst_time": 10,
                    "priority": 1,
                    "current_state": "Running",
                },
                {
                    "pid": 2,
                    "arrival_time": 1,
                    "burst_time": 5,
                    "priority": 2,
                    "current_state": "Ready",
                },
            ],
            "transitions": [
                {
                    "pid": 1,
                    "from_state": "New",
                    "to_state": "Ready",
                    "success": True,
                    "resulting_state": "Ready",
                    "detail": "Admitted to Ready queue",
                },
                {
                    "pid": 1,
                    "from_state": "Ready",
                    "to_state": "Running",
                    "success": True,
                    "resulting_state": "Running",
                    "detail": "Dispatched to CPU",
                },
                {
                    "pid": 2,
                    "from_state": "New",
                    "to_state": "Ready",
                    "success": True,
                    "resulting_state": "Ready",
                    "detail": "Admitted to Ready queue",
                },
                {
                    "pid": 2,
                    "from_state": "Ready",
                    "to_state": "Terminated",
                    "success": False,
                    "resulting_state": "Ready",
                    "detail": "Illegal transition rejected by ProcessManager: Ready -> Terminated",
                },
            ],
            "logs": [
                "Process 1 created in New state.",
                "Process 1 transitioned from New to Ready.",
                "Process 1 transitioned from Ready to Running.",
                "Process 2 created in New state.",
                "Process 2 transitioned from New to Ready.",
                "REJECTED: Illegal transition for PID 2: Ready -> Terminated",
            ],
        }

        return ExecutionResult(
            exit_code=0,
            stdout=json.dumps(dummy_json, indent=2),
            stderr="",
            duration=0.05,
            is_timeout=False,
            command=["dummy_oscope"] + args,
        )

    def verify(self):
        return True, "Dummy backend active"

    def get_info(self):
        from oscope_gui.backend.runner import BackendInfo

        return BackendInfo(
            runner_type="dummy",
            executable_path="dummy_oscope",
            is_available=True,
            status_message="Dummy backend for testing",
        )

    def cancel(self):
        pass


def test_process_lifecycle_config_validation():
    # Valid demo config
    cfg_demo = ProcessLifecycleConfig(mode="demo")
    valid, err = cfg_demo.validate()
    assert valid is True
    assert err is None

    # Valid interactive config with operations
    cfg_inter = ProcessLifecycleConfig(
        mode="interactive",
        operations=[
            ("create", 1, 0, 8, 1),
            ("transition", 1, "Ready"),
        ],
    )
    valid, err = cfg_inter.validate()
    assert valid is True
    assert err is None

    # Invalid interactive config (no operations)
    cfg_empty = ProcessLifecycleConfig(mode="interactive", operations=[])
    valid, err = cfg_empty.validate()
    assert valid is False
    assert "No operations provided" in err

    # Invalid mode
    cfg_bad_mode = ProcessLifecycleConfig(mode="invalid_mode")
    valid, err = cfg_bad_mode.validate()
    assert valid is False
    assert "Unknown mode" in err


def test_generate_process_ops_stdin():
    ops = [
        ("create", 1, 0, 10, 1),
        ("transition", 1, "Ready"),
        ("transition", 1, "Running"),
        ("create", 2, 2, 5, 2),
        ("transition", 2, "Ready"),
    ]
    stdin_str = generate_process_ops_stdin(ops)
    lines = stdin_str.strip().split("\n")
    assert len(lines) == 5
    assert lines[0] == "create 1 0 10 1"
    assert lines[1] == "transition 1 Ready"
    assert lines[2] == "transition 1 Running"
    assert lines[3] == "create 2 2 5 2"
    assert lines[4] == "transition 2 Ready"


def test_parse_process_lifecycle_output_json():
    sample_json = {
        "category": "process_lifecycle",
        "experiment": "process_state_machine",
        "processes": [
            {
                "pid": 10,
                "arrival_time": 0,
                "burst_time": 8,
                "priority": 1,
                "current_state": "Waiting",
            }
        ],
        "transitions": [
            {
                "pid": 10,
                "from_state": "New",
                "to_state": "Ready",
                "success": True,
                "resulting_state": "Ready",
                "detail": "Admit",
            },
            {
                "pid": 10,
                "from_state": "Ready",
                "to_state": "Running",
                "success": True,
                "resulting_state": "Running",
                "detail": "Dispatch",
            },
            {
                "pid": 10,
                "from_state": "Running",
                "to_state": "Waiting",
                "success": True,
                "resulting_state": "Waiting",
                "detail": "I/O wait",
            },
            {
                "pid": 10,
                "from_state": "Waiting",
                "to_state": "Terminated",
                "success": False,
                "resulting_state": "Waiting",
                "detail": "Illegal transition rejected",
            },
        ],
        "logs": ["Log 1", "Log 2"],
    }

    result = parse_process_lifecycle_output(json.dumps(sample_json))
    assert len(result.processes) == 1
    p = result.processes[0]
    assert p.pid == 10
    assert p.current_state == ProcessLifecycleState.WAITING

    assert len(result.transitions) == 4
    t_last = result.transitions[3]
    assert t_last.pid == 10
    assert t_last.from_state == "Waiting"
    assert t_last.requested_state == "Terminated"
    assert t_last.success is False
    assert t_last.to_state == "Waiting"
    assert t_last.resulting_state == "Waiting"
    assert "Illegal" in t_last.detail

    assert len(result.logs) == 2


def test_parse_process_lifecycle_output_text_fallback():
    raw_text = """
=== OScope Process Lifecycle State Machine ===
PID 1: created arrival=0 burst=10 prio=1 state=New
Transition PID 1: New -> Ready [SUCCESS]
Transition PID 1: Ready -> Running [SUCCESS]
Transition PID 1: Running -> Waiting [SUCCESS]
REJECTED: Transition PID 1: Waiting -> Terminated is illegal
Final Process State:
PID 1: state=Waiting burst=10
"""
    result = parse_process_lifecycle_output(raw_text)
    assert len(result.processes) >= 1
    assert result.processes[0].pid == 1
    assert result.processes[0].current_state == ProcessLifecycleState.WAITING

    assert len(result.transitions) >= 3
    assert any(t.success is False for t in result.transitions)


def test_process_state_diagram_widget(qapp):
    widget = ProcessStateDiagramWidget()
    assert widget._active_state is None

    # Set active state to Running
    widget.set_active_state(ProcessLifecycleState.RUNNING)
    assert widget._active_state == "Running"

    # Set active state to Terminated
    widget.set_active_state(ProcessLifecycleState.TERMINATED)
    assert widget._active_state == "Terminated"

    # Clear
    widget.clear()
    assert widget._active_state is None


def test_process_table_widget(qapp):
    widget = ProcessTableWidget()
    assert widget.rowCount() == 0

    procs = [
        ProcessInstanceModel(pid=1, arrival_time=0, burst_time=8, priority=1, state="Ready"),
        ProcessInstanceModel(pid=2, arrival_time=2, burst_time=4, priority=2, state="Running"),
    ]
    widget.populate(procs)
    assert widget.rowCount() == 2
    assert widget.item(0, 0).text() == "PID 1"
    assert widget.item(0, 4).text() == "Ready"
    assert widget.item(1, 0).text() == "PID 2"
    assert widget.item(1, 4).text() == "Running"

    widget.clear()
    assert widget.rowCount() == 0


def test_process_transition_history_widget(qapp):
    widget = ProcessTransitionHistoryWidget()
    assert widget.rowCount() == 0

    transitions = [
        ProcessTransitionModel(
            pid=1,
            from_state="New",
            requested_state="Ready",
            success=True,
            to_state="Ready",
            message="Admitted",
        ),
        ProcessTransitionModel(
            pid=1,
            from_state="Ready",
            requested_state="Terminated",
            success=False,
            to_state="Ready",
            message="Illegal transition rejected",
        ),
    ]
    widget.populate(transitions)
    assert widget.rowCount() == 2
    assert widget.item(0, 1).text() == "PID 1"
    assert widget.item(0, 2).text() == "New ➔ Ready"
    assert widget.item(0, 3).text() == "SUCCESS"
    assert widget.item(0, 4).text() == "Ready"

    assert widget.item(1, 3).text() == "REJECTED"
    assert widget.item(1, 4).text() == "Ready"

    widget.clear()
    assert widget.rowCount() == 0


def test_process_lifecycle_page_initialization_and_run(qapp):
    from oscope_gui.pages.process_lifecycle_page import ProcessLifecyclePage

    runner = DummyBackendRunner()
    page = ProcessLifecyclePage(runner=runner)

    # Initial mode is demo preset
    assert page.combo_mode.currentIndex() == 0
    assert page.interactive_panel.isHidden()

    # Stat cards initialized
    assert "Processes" in page.card_total_procs.value_label.text()
    assert "Events" in page.card_transitions.value_label.text()

    # Switch to interactive mode
    page.combo_mode.setCurrentIndex(1)
    assert not page.interactive_panel.isHidden()
    assert len(page._known_pids) >= 1

    # Add a process
    page.spin_pid.setValue(5)
    page.spin_arrival.setValue(0)
    page.spin_burst.setValue(12)
    page.spin_priority.setValue(1)
    page._on_create_process_clicked()
    assert 5 in page._known_pids

    # Trigger a transition on PID 5
    page.combo_target_pid.setCurrentIndex(page.combo_target_pid.findData(5))
    page._on_transition_clicked("Ready")
    assert any(op[0] == "transition" and op[1] == 5 and op[2] == "Ready" for op in page._interactive_ops)

    # Clean up
    page.cleanup()
    assert page.worker is None or not page.worker.isRunning()
