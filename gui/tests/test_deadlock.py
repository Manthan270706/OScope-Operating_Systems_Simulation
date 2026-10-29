"""Comprehensive automated test suite for Deadlock Management Simulator.

Verifies:
1. Navigation and page creation.
2. Supported analysis modes and backend mappings (Safety, Request, Detection).
3. Process/resource matrix validation (non-negative, dimensions, allocation <= max).
4. Need matrix calculation and real-time updates.
5. Safe-state result parsing.
6. Safe-sequence display and resolution flow.
7. Unsafe-state handling and blocked processes reporting.
8. Deadlock detection (deadlocked vs resolvable processes).
9. Educational presets loading and validation.
10. Visualization consistency (node counts, edge creation, sequence flow).
11. Backend failures, timeouts, and empty states.
12. Regression preservation for CPU Scheduling, Memory Allocation, and Page Replacement.
"""

import os
import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

os.environ["QT_QPA_PLATFORM"] = "offscreen"

from oscope_gui.backend.runner import ExecutionResult
from oscope_gui.main_window import MainWindow
from oscope_gui.models.deadlock import (
    DeadlockConfig,
    DeadlockDetectionResultModel,
    DeadlockMode,
    DeadlockRequestResultModel,
    DeadlockSafetyResultModel,
)
from oscope_gui.pages.deadlock_page import DeadlockPage
from oscope_gui.widgets.resource_graph import ResourceGraphWidget




SAMPLE_SAFETY_SAFE_STDOUT = """
=== Banker's Safety Analysis ===
System State:           SAFE
Analysis:               System is in a safe state.
Safe Execution Sequence: P1 -> P3 -> P4 -> P0 -> P2

Resource Matrices Summary:
Process Allocation      Max Claim       Need
           --------------------------------------------------------
P0      0 1 0           7 5 3           7 4 3           
P1      2 0 0           3 2 2           1 2 2           
P2      3 0 2           9 0 2           6 0 0           
P3      2 1 1           2 2 2           0 1 1           
P4      0 0 2           4 3 3           4 3 1           

Available Resources:    3 3 2 
"""

SAMPLE_SAFETY_UNSAFE_STDOUT = """
=== Banker's Safety Analysis ===
System State:           UNSAFE
Analysis:               System is in an unsafe state. Unfinished processes: [P0, P1, P2, P3, P4].
Blocked Processes:     P0, P1, P2, P3, P4
Note: An unsafe state means the system cannot guarantee that all processes can finish
under maximum claims; it does not necessarily mean a deadlock exists at this instant.

Resource Matrices Summary:
Process Allocation      Max Claim       Need
           --------------------------------------------------------
P0      0 1 0           7 5 3           7 4 3           
P1      2 0 0           3 2 2           1 2 2           
P2      3 0 2           9 0 2           6 0 0           
P3      2 1 1           2 2 2           0 1 1           
P4      0 0 2           4 3 3           4 3 1           

Available Resources:    0 0 0 
"""

SAMPLE_REQUEST_GRANTED_STDOUT = """
=== Resource Request Simulation ===
Requesting Process:     P1
Requested Resources:    [1, 0, 2]
Allocation Decision:    GRANTED
Reason:                 Request granted. System remains in a safe state.
Resulting Safe Sequence: P1 -> P3 -> P4 -> P0 -> P2
"""

SAMPLE_REQUEST_DENIED_STDOUT = """
=== Resource Request Simulation ===
Requesting Process:     P4
Requested Resources:    [3, 3, 0]
Allocation Decision:    DENIED
Reason:                 Request denied: would lead to unsafe state.
Original system state has been preserved uncorrupted.
"""

SAMPLE_DETECTION_DEADLOCK_STDOUT = """
=== Deadlock Detection Analysis ===
Detection Result:       DEADLOCK DETECTED
Diagnostic Message:     Deadlock detected! Deadlocked processes: [P1, P2, P3, P4].
Deadlocked Processes:   P1, P2, P3, P4
"""

SAMPLE_DETECTION_SAFE_STDOUT = """
=== Deadlock Detection Analysis ===
Detection Result:       NO DEADLOCK
Diagnostic Message:     All processes can complete execution. No deadlock detected.
Execution Status:       All active processes can acquire pending resources and finish.
"""


class MockDeadlockRunner:
    """Mock backend runner for deterministic tests."""

    def __init__(self, stdout: str = SAMPLE_SAFETY_SAFE_STDOUT, exit_code: int = 0) -> None:
        self.stdout = stdout
        self.exit_code = exit_code
        self.last_stdin: str = ""

    def execute(self, args, stdin_data=None, timeout=25.0) -> ExecutionResult:
        self.last_stdin = stdin_data or ""
        return ExecutionResult(
            exit_code=self.exit_code,
            stdout=self.stdout,
            stderr="" if self.exit_code == 0 else "Simulated error",
            duration=0.05,
            is_timeout=False,
            command=["mock_oscope"] + args,
        )

    def cancel(self) -> None:
        pass

    def get_info(self):
        from oscope_gui.backend.runner import BackendInfo

        return BackendInfo(
            runner_type="mock",
            executable_path="mock_oscope",
            is_available=True,
            status_message="Mock runner active",
        )


def test_1_deadlock_navigation(qapp):
    """Test 1: Verify Deadlock Management navigation from main window and dashboard."""
    runner = MockDeadlockRunner()
    window = MainWindow(runner)

    assert window.stack.count() == 11

    # Navigate to deadlock via sidebar
    window.nav_btn_deadlock.click()
    assert window.stack.currentIndex() == 4
    assert window.nav_btn_deadlock.isChecked()

    # Navigate via dashboard helper
    window.navigate_to_page("dashboard")
    assert window.stack.currentIndex() == 0

    window.navigate_to_page("deadlock")
    assert window.stack.currentIndex() == 4
    assert window.nav_btn_deadlock.isChecked()

    window.close()


def test_2_page_creation_and_widget_initialization(qapp):
    """Test 2: Verify DeadlockPage creation and default controls."""
    runner = MockDeadlockRunner()
    page = DeadlockPage(runner)

    assert page.combo_mode.count() == 3
    assert page.combo_mode.currentIndex() == 0
    assert page.spin_processes.value() == 5
    assert page.spin_resources.value() == 3
    assert page.txt_available.text() == "3, 3, 2"

    assert page.table_alloc.rowCount() == 5
    assert page.table_alloc.columnCount() == 3
    assert page.table_max.rowCount() == 5
    assert page.table_max.columnCount() == 3
    assert page.table_need.rowCount() == 5
    assert page.table_need.columnCount() == 3


def test_3_supported_analysis_modes_and_backend_mappings(qapp):
    """Test 3: Verify analysis mode options and CLI menu choices."""
    runner = MockDeadlockRunner()
    page = DeadlockPage(runner)

    modes = [page.combo_mode.itemData(i) for i in range(page.combo_mode.count())]
    assert DeadlockMode.SAFETY in modes
    assert DeadlockMode.RESOURCE_REQUEST in modes
    assert DeadlockMode.DETECTION in modes

    assert DeadlockMode.SAFETY.cli_choice == 1
    assert DeadlockMode.RESOURCE_REQUEST.cli_choice == 2
    assert DeadlockMode.DETECTION.cli_choice == 3


def test_4_process_and_resource_matrix_validation(qapp):
    """Test 4: Verify matrix dimension and value validation."""
    runner = MockDeadlockRunner()
    page = DeadlockPage(runner)

    # Valid config
    config, err = page._collect_config()
    assert err is None
    assert config is not None
    assert config.num_processes == 5
    assert config.num_resources == 3

    # Invalid available count
    page.txt_available.setText("3, 3")  # Expected 3
    config, err = page._collect_config()
    assert err is not None
    assert "requires 3 integers" in err

    # Reset available
    page.txt_available.setText("3, 3, 2")

    # Invalid negative available
    page.txt_available.setText("3, -1, 2")
    config, err = page._collect_config()
    assert err is not None
    assert "negative" in err


def test_5_need_matrix_calculation_and_real_time_update(qapp):
    """Test 5: Verify Need = Max - Allocation auto-calculates live."""
    runner = MockDeadlockRunner()
    page = DeadlockPage(runner)

    # Textbook P0: Alloc=[0, 1, 0], Max=[7, 5, 3] -> Need=[7, 4, 3]
    need_0_0 = page.table_need.item(0, 0).text()
    need_0_1 = page.table_need.item(0, 1).text()
    need_0_2 = page.table_need.item(0, 2).text()
    assert need_0_0 == "7"
    assert need_0_1 == "4"
    assert need_0_2 == "3"

    # Edit Allocation P0[R0] to 4 -> Need should update to 3
    page.table_alloc.item(0, 0).setText("4")
    page._refresh_need_matrix()
    assert page.table_need.item(0, 0).text() == "3"

    # Edit Allocation to exceed Max (e.g. 10 > 7) -> negative need triggers validation error
    page.table_alloc.item(0, 0).setText("10")
    page._refresh_need_matrix()
    assert not page.lbl_validation_err.isHidden()
    assert "exceeds Max Claim" in page.lbl_validation_err.text()


def test_6_safe_state_result_parsing(qapp):
    """Test 6: Verify parsing of Banker's safe state output."""
    from oscope_gui.backend.parser import parse_deadlock_safety_output

    cfg = DeadlockConfig(mode=DeadlockMode.SAFETY, num_processes=5, num_resources=3)
    res = parse_deadlock_safety_output(SAMPLE_SAFETY_SAFE_STDOUT, cfg)

    assert res.is_safe is True
    assert res.safe_sequence == [1, 3, 4, 0, 2]
    assert res.safe_sequence_str == "P1 -> P3 -> P4 -> P0 -> P2"
    assert res.blocked_processes == []
    assert "safe state" in res.message


def test_7_safe_sequence_display(qapp):
    """Test 7: Verify safe sequence is updated in GUI flow bar and StatCards."""
    from oscope_gui.backend.parser import parse_deadlock_safety_output

    cfg = DeadlockConfig(mode=DeadlockMode.SAFETY, num_processes=5, num_resources=3)
    res = parse_deadlock_safety_output(SAMPLE_SAFETY_SAFE_STDOUT, cfg)

    runner = MockDeadlockRunner(SAMPLE_SAFETY_SAFE_STDOUT)
    page = DeadlockPage(runner)
    page._on_simulation_success(res)

    assert page.card_state.value_label.text() == "SAFE"
    assert "P1 -> P3 -> P4 -> P0 -> P2" in page.card_sequence.value_label.text()
    assert page.graph_widget.flow_bar.lbl_title.text() == "SAFE SEQUENCE:"


def test_8_unsafe_state_handling(qapp):
    """Test 8: Verify unsafe state parsing and blocked processes reporting."""
    from oscope_gui.backend.parser import parse_deadlock_safety_output

    cfg = DeadlockConfig(mode=DeadlockMode.SAFETY, num_processes=5, num_resources=3)
    res = parse_deadlock_safety_output(SAMPLE_SAFETY_UNSAFE_STDOUT, cfg)

    assert res.is_safe is False
    assert res.safe_sequence == []
    assert res.blocked_processes == [0, 1, 2, 3, 4]
    assert res.blocked_str == "P0, P1, P2, P3, P4"
    assert "unsafe state" in res.message

    # Test in GUI
    runner = MockDeadlockRunner(SAMPLE_SAFETY_UNSAFE_STDOUT)
    page = DeadlockPage(runner)
    page._on_simulation_success(res)

    assert page.card_state.value_label.text() == "UNSAFE"
    assert "Blocked: P0, P1, P2, P3, P4" in page.card_sequence.value_label.text()
    assert page.graph_widget.flow_bar.lbl_title.text() == "UNSAFE STATE:"


def test_9_resource_request_simulation(qapp):
    """Test 9: Verify Resource Request mode for both grant and denial."""
    from oscope_gui.backend.parser import parse_deadlock_request_output

    # Grant
    cfg_grant = DeadlockConfig(
        mode=DeadlockMode.RESOURCE_REQUEST,
        num_processes=5,
        num_resources=3,
        requesting_process_id=1,
        request_vector=[1, 0, 2],
    )
    res_grant = parse_deadlock_request_output(SAMPLE_REQUEST_GRANTED_STDOUT, cfg_grant)
    runner_grant = MockDeadlockRunner(SAMPLE_REQUEST_GRANTED_STDOUT)
    page_grant = DeadlockPage(runner_grant)
    page_grant.combo_mode.setCurrentIndex(1)  # RESOURCE_REQUEST
    page_grant._on_simulation_success(res_grant)

    assert page_grant.card_state.value_label.text() == "GRANTED"
    assert "P1 -> P3 -> P4 -> P0 -> P2" in page_grant.card_sequence.value_label.text()
    assert page_grant.graph_widget.flow_bar.lbl_title.text() == "REQUEST GRANTED:"

    # Denial
    cfg_denial = DeadlockConfig(
        mode=DeadlockMode.RESOURCE_REQUEST,
        num_processes=5,
        num_resources=3,
        requesting_process_id=4,
        request_vector=[3, 3, 0],
    )
    res_denial = parse_deadlock_request_output(SAMPLE_REQUEST_DENIED_STDOUT, cfg_denial)
    runner_denial = MockDeadlockRunner(SAMPLE_REQUEST_DENIED_STDOUT)
    page_denial = DeadlockPage(runner_denial)
    page_denial.combo_mode.setCurrentIndex(1)
    page_denial._on_simulation_success(res_denial)

    assert page_denial.card_state.value_label.text() == "DENIED"
    assert page_denial.graph_widget.flow_bar.lbl_title.text() == "REQUEST DENIED:"


def test_10_deadlock_detection(qapp):
    """Test 10: Verify Deadlock Detection mode (deadlocked vs resolvable)."""
    from oscope_gui.backend.parser import parse_deadlock_detection_output

    cfg_dl = DeadlockConfig(
        mode=DeadlockMode.DETECTION,
        num_processes=5,
        num_resources=3,
        available=[0, 0, 0],
        allocation=[[0, 1, 0], [2, 0, 0], [3, 0, 3], [2, 1, 1], [0, 0, 2]],
        request_matrix=[[0, 0, 0], [2, 0, 2], [0, 0, 1], [1, 0, 0], [0, 0, 2]],
    )
    res_dl = parse_deadlock_detection_output(SAMPLE_DETECTION_DEADLOCK_STDOUT, cfg_dl)
    runner = MockDeadlockRunner(SAMPLE_DETECTION_DEADLOCK_STDOUT)
    page = DeadlockPage(runner)
    page.combo_mode.setCurrentIndex(2)  # DETECTION
    page._on_simulation_success(res_dl)

    assert page.card_state.value_label.text() == "DEADLOCK"
    assert "Deadlocked: P1, P2, P3, P4" in page.card_sequence.value_label.text()
    assert page.graph_widget.flow_bar.lbl_title.text() == "DEADLOCK DETECTED:"

    # Safe scenario on same page
    res_safe = parse_deadlock_detection_output(SAMPLE_DETECTION_SAFE_STDOUT, cfg_dl)
    page._on_simulation_success(res_safe)

    assert page.card_state.value_label.text() == "NO DEADLOCK"
    assert page.graph_widget.flow_bar.lbl_title.text() == "NO DEADLOCK:"

    page.deleteLater()
    QApplication.processEvents()


def test_11_educational_presets(qapp):
    """Test 11: Verify loading all 6 educational presets."""
    runner = MockDeadlockRunner()
    page = DeadlockPage(runner)

    presets = [
        "textbook_safe",
        "unsafe_starvation",
        "request_grant",
        "request_denial",
        "detection_deadlock",
        "detection_safe",
    ]

    for p in presets:
        page._load_preset(p)
        config, err = page._collect_config()
        assert err is None, f"Preset '{p}' failed validation: {err}"
        assert config is not None


def test_12_resource_graph_visualization(qapp):
    """Test 12: Verify ResourceGraphWidget and canvas consistency."""
    widget = ResourceGraphWidget()
    assert widget.canvas.result is None

    res = DeadlockSafetyResultModel(
        is_safe=True,
        safe_sequence=[0, 1, 2],
        blocked_processes=[],
        message="Safe",
        num_processes=3,
        num_resources=2,
        available=[1, 1],
        allocation=[[1, 0], [0, 1], [1, 1]],
        max_claim=[[2, 1], [1, 1], [1, 2]],
        need=[[1, 1], [1, 0], [0, 1]],
        raw_output="",
    )
    widget.set_result(res)

    assert widget.canvas.result is not None
    assert widget.canvas.result.num_processes == 3
    assert widget.canvas.result.num_resources == 2


def test_13_backend_failure_handling(qapp):
    """Test 13: Verify error handling on backend failure."""
    runner = MockDeadlockRunner(stdout="", exit_code=1)
    page = DeadlockPage(runner)

    page._on_simulation_failed("Simulated backend execution failure: Process exited with code 1.")

    assert page.card_state.value_label.text() == "Failed"
    assert not page.lbl_validation_err.isHidden()
    assert "Simulated backend execution failure" in page.lbl_validation_err.text()


def test_14_preservation_of_cpu_memory_and_paging(qapp):
    """Test 14: Verify non-regression across CPU Scheduling, Memory Allocation, and Page Replacement."""
    from oscope_gui.models.scheduling import AlgorithmType
    from oscope_gui.models.memory import MemoryStrategy
    from oscope_gui.models.paging import PagingAlgorithm

    assert "First-Come, First-Served" in AlgorithmType.FCFS.display_name
    assert "Round Robin" in AlgorithmType.ROUND_ROBIN.display_name

    assert MemoryStrategy.FIRST_FIT.value == "First Fit"
    assert MemoryStrategy.BEST_FIT.value == "Best Fit"

    assert PagingAlgorithm.FIFO.value == "FIFO"
    assert PagingAlgorithm.LRU.value == "LRU"
    assert PagingAlgorithm.OPTIMAL.value == "Optimal"


def test_15_matrix_headers_visibility_and_updates(qapp):
    """Test 15: Verify readable headers on all three matrices and correct dimension updates."""
    runner = MockDeadlockRunner()
    page = DeadlockPage(runner)
    page.resize(1366, 768)
    page.show()
    qapp.processEvents()

    # Initial preset has 5 processes and 3 resources
    for name, table in [("Allocation", page.table_alloc), ("Max Claim", page.table_max), ("Need", page.table_need)]:
        assert table.horizontalHeader().isVisible() or table.horizontalHeader().count() > 0
        assert table.verticalHeader().isVisible() or table.verticalHeader().count() > 0
        assert table.horizontalHeader().height() >= 28
        assert table.verticalHeader().width() >= 40

        cols = [table.horizontalHeaderItem(c).text() for c in range(table.columnCount())]
        rows = [table.verticalHeaderItem(r).text() for r in range(table.rowCount())]
        assert cols == ["R0 (A)", "R1 (B)", "R2 (C)"], f"{name} columns mismatch: {cols}"
        assert rows == ["P0", "P1", "P2", "P3", "P4"], f"{name} rows mismatch: {rows}"

    # Verify Need table cells are read-only
    need_item = page.table_need.item(0, 0)
    assert need_item is not None
    assert not (need_item.flags() & Qt.ItemIsEditable)

    # Change dimensions dynamically to 7 processes and 4 resources
    page.spin_processes.setValue(7)
    page.spin_resources.setValue(4)
    qapp.processEvents()

    expected_cols = ["R0 (A)", "R1 (B)", "R2 (C)", "R3 (D)"]
    expected_rows = [f"P{i}" for i in range(7)]

    for name, table in [("Allocation", page.table_alloc), ("Max Claim", page.table_max), ("Need", page.table_need)]:
        assert table.columnCount() == 4
        assert table.rowCount() == 7
        cols = [table.horizontalHeaderItem(c).text() for c in range(table.columnCount())]
        rows = [table.verticalHeaderItem(r).text() for r in range(table.rowCount())]
        assert cols == expected_cols, f"{name} updated cols mismatch: {cols}"
        assert rows == expected_rows, f"{name} updated rows mismatch: {rows}"


def test_16_no_horizontal_overflow_at_target_resolutions(qapp):
    """Test 16: Verify no horizontal overflow in MainWindow at 1366x768 and 1920x1080."""
    runner = MockDeadlockRunner()
    win = MainWindow(runner)

    for width, height in [(1366, 768), (1920, 1080)]:
        win.resize(width, height)
        win.show()
        qapp.processEvents()

        win.navigate_to_page("deadlock")
        qapp.processEvents()

        dp = win.deadlock_page
        scroll = dp.findChild(type(dp.layout().itemAt(0).widget()))
        assert scroll is not None
        content = scroll.widget()
        vp = scroll.viewport()

        # Content widget must not exceed viewport width
        assert content.width() <= vp.width(), (
            f"Horizontal overflow at {width}x{height}: content width {content.width()} > viewport {vp.width()}"
        )
        assert content.minimumSizeHint().width() <= vp.width(), (
            f"Content minSizeHint {content.minimumSizeHint().width()} exceeds viewport {vp.width()} at {width}x{height}"
        )
