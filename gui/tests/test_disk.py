"""Comprehensive automated test suite for Disk Scheduling Simulator in OScope GUI.

Covers:
1. All seven algorithm mappings (FCFS, SSTF, SCAN, C-SCAN, LOOK, C-LOOK, LIFO) + Compare All.
2. Correct generation of backend input (stdin sequences with menu choice, range, head, direction, requests).
3. Parsing representative actual backend output (textbook 53 -> [98, 183, 37, 122, 14, 124, 65, 67]).
4. Correct extraction of service order, step coordinates, and movement metrics.
5. Invalid cylinder values and initial head position validation.
6. Invalid or empty request queues validation.
7. Direction validation (required for directional algorithms, ignored/hidden for non-directional).
8. SCAN and C-SCAN boundary behavior ([199] boundary hit, circular jump).
9. LOOK and C-LOOK behavior (stop at highest/lowest request, jump directly without boundary hit).
10. LIFO service order (servicing in reverse arrival order).
11. Comparison results, consistent workloads, and rankings.
12. Backend timeout, failure, and malformed output handling.
13. Sidebar and dashboard navigation to Disk Scheduling page.
14. No regressions across CPU Scheduling, Memory Allocation, Page Replacement, and Deadlock Management.
"""

import os
import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

os.environ["QT_QPA_PLATFORM"] = "offscreen"

from oscope_gui.backend.runner import ExecutionResult
from oscope_gui.backend.parser import (
    generate_disk_stdin,
    parse_disk_output,
    parse_disk_comparison_output,
)
from oscope_gui.models.disk import (
    DiskAlgorithm,
    DiskDirection,
    DiskConfig,
    DiskStepModel,
    DiskSchedulingResultModel,
    DiskComparisonEntryModel,
    DiskComparisonResultModel,
)
from oscope_gui.widgets.disk_plot import DiskHeadPlotWidget, DiskHeadPlotCanvas, DiskSequenceFlowBar
from oscope_gui.pages.disk_page import DiskPage
from oscope_gui.main_window import MainWindow


class DummyDiskRunner:
    """Mock backend runner for deterministic UI and parser tests."""

    def __init__(self, sample_stdout: str = "", exit_code: int = 0, is_timeout: bool = False):
        self.sample_stdout = sample_stdout
        self.exit_code = exit_code
        self.is_timeout = is_timeout
        self.last_args = None
        self.last_stdin = None

    def execute(self, args, stdin_data=None, timeout=15.0):
        self.last_args = args
        self.last_stdin = stdin_data
        return ExecutionResult(
            exit_code=self.exit_code,
            stdout=self.sample_stdout,
            stderr="" if self.exit_code == 0 else "Execution failed",
            duration=0.08,
            is_timeout=self.is_timeout,
            command=["wsl", "build/oscope"] + args,
        )

    def verify(self):
        return True, "Mock backend online"

    def get_info(self):
        from oscope_gui.backend.runner import BackendInfo
        return BackendInfo(
            runner_type="mock",
            executable_path="mock_oscope",
            is_available=True,
            status_message="Mock backend online",
        )

    def cancel(self):
        pass


SAMPLE_FCFS_STDOUT = """
=== Disk Scheduling Result: First-Come, First-Served (FCFS) ===
Serviced Requests:      [98, 183, 37, 122, 14, 124, 65, 67]
Head Movement Path:     53 -> 98 -> 183 -> 37 -> 122 -> 14 -> 124 -> 65 -> 67
Total Head Movement:    640 cylinders
Average Head Movement:  80.00 cylinders/request
Initial Head Position:  53
Final Head Position:    67
"""

SAMPLE_SSTF_STDOUT = """
=== Disk Scheduling Result: Shortest Seek Time First (SSTF) ===
Serviced Requests:      [65, 67, 37, 14, 98, 122, 124, 183]
Head Movement Path:     53 -> 65 -> 67 -> 37 -> 14 -> 98 -> 122 -> 124 -> 183
Total Head Movement:    236 cylinders
Average Head Movement:  29.50 cylinders/request
Initial Head Position:  53
Final Head Position:    183
"""

SAMPLE_SCAN_STDOUT = """
=== Disk Scheduling Result: SCAN (Elevator) ===
Serviced Requests:      [65, 67, 98, 122, 124, 183, 37, 14]
Head Movement Path:     53 -> 65 -> 67 -> 98 -> 122 -> 124 -> 183 -> 199 -> 37 -> 14
Total Head Movement:    345 cylinders
Average Head Movement:  43.12 cylinders/request
Initial Head Position:  53
Final Head Position:    14
"""

SAMPLE_CSCAN_STDOUT = """
=== Disk Scheduling Result: Circular SCAN (C-SCAN) ===
Serviced Requests:      [65, 67, 98, 122, 124, 183, 14, 37]
Head Movement Path:     53 -> 65 -> 67 -> 98 -> 122 -> 124 -> 183 -> 199 -> 0 -> 14 -> 37
Total Head Movement:    382 cylinders
  (Includes circular wraparound traversal: 199 cylinders)
Average Head Movement:  47.75 cylinders/request
Initial Head Position:  53
Final Head Position:    37
"""

SAMPLE_LOOK_STDOUT = """
=== Disk Scheduling Result: LOOK ===
Serviced Requests:      [65, 67, 98, 122, 124, 183, 37, 14]
Head Movement Path:     53 -> 65 -> 67 -> 98 -> 122 -> 124 -> 183 -> 37 -> 14
Total Head Movement:    299 cylinders
Average Head Movement:  37.38 cylinders/request
Initial Head Position:  53
Final Head Position:    14
"""

SAMPLE_CLOOK_STDOUT = """
=== Disk Scheduling Result: Circular LOOK (C-LOOK) ===
Serviced Requests:      [65, 67, 98, 122, 124, 183, 14, 37]
Head Movement Path:     53 -> 65 -> 67 -> 98 -> 122 -> 124 -> 183 -> 14 -> 37
Total Head Movement:    322 cylinders
  (Includes circular wraparound traversal: 169 cylinders)
Average Head Movement:  40.25 cylinders/request
Initial Head Position:  53
Final Head Position:    37
"""

SAMPLE_LIFO_STDOUT = """
=== Disk Scheduling Result: Last-In, First-Out (LIFO) ===
Serviced Requests:      [67, 65, 124, 14, 122, 37, 183, 98]
Head Movement Path:     53 -> 67 -> 65 -> 124 -> 14 -> 122 -> 37 -> 183 -> 98
Total Head Movement:    609 cylinders
Average Head Movement:  76.12 cylinders/request
Initial Head Position:  53
Final Head Position:    98
"""

SAMPLE_COMPARISON_STDOUT = """
========================================================================================
                            Disk Scheduling Comparison                                  
========================================================================================
Algorithm                             Total Movement (cyl)    Avg Movement/Req    Final Head
----------------------------------------------------------------------------------------
Shortest Seek Time First (SSTF)                        236               29.50           183
LOOK                                                   299               37.38            14
Circular LOOK (C-LOOK)                                 322               40.25            37
SCAN (Elevator)                                        345               43.12            14
Circular SCAN (C-SCAN)                                 382               47.75            37
Last-In, First-Out (LIFO)                              609               76.12            98
First-Come, First-Served (FCFS)                        640               80.00            67
========================================================================================
Note: C-SCAN and C-LOOK include wraparound circular return seek distance in total movement.
"""


# ---------------------------------------------------------------------------
# Requirement 1: All seven algorithm mappings + Compare All
# ---------------------------------------------------------------------------

def test_1_algorithm_mappings():
    """Verify all 7 algorithm enums, choices, and directional requirements."""
    algorithms = [
        DiskAlgorithm.FCFS,
        DiskAlgorithm.SSTF,
        DiskAlgorithm.SCAN,
        DiskAlgorithm.CSCAN,
        DiskAlgorithm.LOOK,
        DiskAlgorithm.CLOOK,
        DiskAlgorithm.LIFO,
    ]
    assert len(algorithms) == 7

    assert DiskAlgorithm.FCFS.cli_choice == "1"
    assert DiskAlgorithm.SSTF.cli_choice == "2"
    assert DiskAlgorithm.SCAN.cli_choice == "3"
    assert DiskAlgorithm.CSCAN.cli_choice == "4"
    assert DiskAlgorithm.LOOK.cli_choice == "5"
    assert DiskAlgorithm.CLOOK.cli_choice == "6"
    assert DiskAlgorithm.LIFO.cli_choice == "7"
    assert DiskAlgorithm.COMPARE_ALL.cli_choice == "8"

    assert not DiskAlgorithm.FCFS.requires_direction
    assert not DiskAlgorithm.SSTF.requires_direction
    assert not DiskAlgorithm.LIFO.requires_direction
    assert DiskAlgorithm.SCAN.requires_direction
    assert DiskAlgorithm.CSCAN.requires_direction
    assert DiskAlgorithm.LOOK.requires_direction
    assert DiskAlgorithm.CLOOK.requires_direction
    assert DiskAlgorithm.COMPARE_ALL.requires_direction


# ---------------------------------------------------------------------------
# Requirement 2: Correct generation of backend input (stdin sequences)
# ---------------------------------------------------------------------------

def test_2_generate_stdin_non_directional():
    """Test stdin generation for non-directional algorithms (FCFS)."""
    cfg = DiskConfig(
        algorithm=DiskAlgorithm.FCFS,
        min_cylinder=0,
        max_cylinder=199,
        initial_head=53,
        requests=[98, 183, 37, 122, 14, 124, 65, 67],
    )
    stdin_str = generate_disk_stdin(cfg)
    lines = stdin_str.strip().splitlines()

    # Main menu 12 -> Sub-menu 1 (FCFS) -> min -> max -> head -> requests line -> 9 (exit sub) -> 13 (exit main)
    assert lines[0] == "12"
    assert lines[1] == "1"
    assert lines[2] == "0"
    assert lines[3] == "199"
    assert lines[4] == "53"
    assert lines[5] == "98 183 37 122 14 124 65 67"
    assert lines[6] == "9"
    assert lines[7] == "13"


def test_2_generate_stdin_directional():
    """Test stdin generation for directional algorithms (SCAN with direction)."""
    cfg = DiskConfig(
        algorithm=DiskAlgorithm.SCAN,
        direction=DiskDirection.INCREASING,
        min_cylinder=0,
        max_cylinder=199,
        initial_head=53,
        requests=[98, 183, 37],
    )
    stdin_str = generate_disk_stdin(cfg)
    lines = stdin_str.strip().splitlines()

    # Main menu 12 -> Sub-menu 3 (SCAN) -> min -> max -> head -> direction (1) -> requests line -> 9 -> 13
    assert lines[0] == "12"
    assert lines[1] == "3"
    assert lines[2] == "0"
    assert lines[3] == "199"
    assert lines[4] == "53"
    assert lines[5] == "1"  # 1 for Increasing
    assert lines[6] == "98 183 37"
    assert lines[7] == "9"
    assert lines[8] == "13"


def test_2_generate_stdin_compare_all():
    """Test stdin generation for Compare All."""
    cfg = DiskConfig(
        algorithm=DiskAlgorithm.COMPARE_ALL,
        direction=DiskDirection.DECREASING,
        min_cylinder=0,
        max_cylinder=299,
        initial_head=100,
        requests=[50, 150, 250],
    )
    stdin_str = generate_disk_stdin(cfg)
    lines = stdin_str.strip().splitlines()

    assert lines[0] == "12"
    assert lines[1] == "8"
    assert lines[2] == "0"
    assert lines[3] == "299"
    assert lines[4] == "100"
    assert lines[5] == "2"  # 2 for Decreasing
    assert lines[6] == "50 150 250"
    assert lines[7] == "9"
    assert lines[8] == "13"


# ---------------------------------------------------------------------------
# Requirement 3 & 4: Parsing actual backend output & extracting metrics
# ---------------------------------------------------------------------------

def test_3_4_parse_fcfs_output():
    """Verify parsing representative FCFS output."""
    cfg = DiskConfig(
        algorithm=DiskAlgorithm.FCFS,
        min_cylinder=0,
        max_cylinder=199,
        initial_head=53,
        requests=[98, 183, 37, 122, 14, 124, 65, 67],
    )
    res = parse_disk_output(SAMPLE_FCFS_STDOUT, cfg)
    assert res.total_head_movement == 640
    assert res.average_seek == pytest.approx(80.0, rel=1e-2)
    assert res.service_order == [53, 98, 183, 37, 122, 14, 124, 65, 67]
    assert len(res.steps) == 8
    assert res.steps[0].step_number == 1
    assert res.steps[0].from_cylinder == 53
    assert res.steps[0].to_cylinder == 98
    assert res.steps[0].seek_distance == 45
    assert res.steps[0].cumulative_movement == 45
    assert res.steps[-1].to_cylinder == 67
    assert res.steps[-1].cumulative_movement == 640


def test_3_4_parse_sstf_output():
    """Verify parsing representative SSTF output (236 cylinders)."""
    cfg = DiskConfig(
        algorithm=DiskAlgorithm.SSTF,
        min_cylinder=0,
        max_cylinder=199,
        initial_head=53,
        requests=[98, 183, 37, 122, 14, 124, 65, 67],
    )
    res = parse_disk_output(SAMPLE_SSTF_STDOUT, cfg)
    assert res.total_head_movement == 236
    assert res.average_seek == pytest.approx(29.50, rel=1e-2)
    assert res.service_order == [53, 65, 67, 37, 14, 98, 122, 124, 183]


# ---------------------------------------------------------------------------
# Requirement 5 & 6: Input Validation
# ---------------------------------------------------------------------------

def test_5_6_validation_in_page(qapp):
    """Verify page input validation flags out-of-range, empty, and inverted ranges."""
    page = DiskPage()

    # 1. Valid textbook default passes validation
    cfg, err = page._validate_inputs()
    assert cfg is not None
    assert err is None

    # 2. Empty requests fails
    page.txt_requests.setText("")
    cfg, err = page._validate_inputs()
    assert cfg is None
    assert "empty" in err.lower()

    # 3. Non-numeric requests fails
    page.txt_requests.setText("98, abc, 37")
    cfg, err = page._validate_inputs()
    assert cfg is None
    assert "integer" in err.lower()

    # 4. Out-of-range request fails
    page.txt_requests.setText("98, 250, 37")  # 250 > max 199
    cfg, err = page._validate_inputs()
    assert cfg is None
    assert "range" in err.lower()

    # 5. Out-of-range initial head fails
    page.txt_requests.setText("98, 183, 37")
    page.spin_head.setValue(250)
    cfg, err = page._validate_inputs()
    assert cfg is None
    assert "initial head" in err.lower()

    # 6. Inverted range (min >= max) fails
    page.spin_head.setValue(50)
    page.spin_min.setValue(200)
    page.spin_max.setValue(100)
    cfg, err = page._validate_inputs()
    assert cfg is None
    assert "greater than" in err.lower() or "minimum" in err.lower()


# ---------------------------------------------------------------------------
# Requirement 7: Direction validation
# ---------------------------------------------------------------------------

def test_7_direction_ui_logic(qapp):
    """Verify direction dropdown is enabled only when directional algorithm is selected."""
    page = DiskPage()

    # FCFS does not require direction
    idx_fcfs = page.combo_algo.findData(DiskAlgorithm.FCFS)
    page.combo_algo.setCurrentIndex(idx_fcfs)
    assert not page.combo_dir.isEnabled()

    # SSTF does not require direction
    idx_sstf = page.combo_algo.findData(DiskAlgorithm.SSTF)
    page.combo_algo.setCurrentIndex(idx_sstf)
    assert not page.combo_dir.isEnabled()

    # SCAN requires direction
    idx_scan = page.combo_algo.findData(DiskAlgorithm.SCAN)
    page.combo_algo.setCurrentIndex(idx_scan)
    assert page.combo_dir.isEnabled()

    # C-SCAN requires direction
    idx_cscan = page.combo_algo.findData(DiskAlgorithm.CSCAN)
    page.combo_algo.setCurrentIndex(idx_cscan)
    assert page.combo_dir.isEnabled()

    # Compare All requires direction
    idx_comp = page.combo_algo.findData(DiskAlgorithm.COMPARE_ALL)
    page.combo_algo.setCurrentIndex(idx_comp)
    assert page.combo_dir.isEnabled()


# ---------------------------------------------------------------------------
# Requirement 8: SCAN and C-SCAN boundary behavior
# ---------------------------------------------------------------------------

def test_8_scan_boundary_behavior():
    """Verify SCAN records boundary traversal to cylinder 199 and reverses."""
    cfg = DiskConfig(
        algorithm=DiskAlgorithm.SCAN,
        direction=DiskDirection.INCREASING,
        min_cylinder=0,
        max_cylinder=199,
        initial_head=53,
        requests=[98, 183, 37, 122, 14, 124, 65, 67],
    )
    res = parse_disk_output(SAMPLE_SCAN_STDOUT, cfg)
    assert res.total_head_movement == 345
    assert 199 in res.service_order
    # Find boundary step
    boundary_steps = [s for s in res.steps if s.is_boundary]
    assert len(boundary_steps) >= 1
    assert boundary_steps[0].to_cylinder == 199
    assert boundary_steps[0].action_type == "Boundary Reversal"


def test_8_cscan_wraparound_behavior():
    """Verify C-SCAN records boundary traversal and rapid circular wraparound."""
    cfg = DiskConfig(
        algorithm=DiskAlgorithm.CSCAN,
        direction=DiskDirection.INCREASING,
        min_cylinder=0,
        max_cylinder=199,
        initial_head=53,
        requests=[98, 183, 37, 122, 14, 124, 65, 67],
    )
    res = parse_disk_output(SAMPLE_CSCAN_STDOUT, cfg)
    assert res.total_head_movement == 382
    wraparound_steps = [s for s in res.steps if s.is_wraparound]
    assert len(wraparound_steps) >= 1
    assert wraparound_steps[0].action_type == "Circular Wraparound"
    assert wraparound_steps[0].from_cylinder == 199
    assert wraparound_steps[0].to_cylinder == 0


# ---------------------------------------------------------------------------
# Requirement 9: LOOK and C-LOOK behavior
# ---------------------------------------------------------------------------

def test_9_look_and_clook_behavior():
    """Verify LOOK and C-LOOK stop at max requested cylinder (183) without hitting boundary 199."""
    cfg = DiskConfig(
        algorithm=DiskAlgorithm.LOOK,
        direction=DiskDirection.INCREASING,
        min_cylinder=0,
        max_cylinder=199,
        initial_head=53,
        requests=[98, 183, 37, 122, 14, 124, 65, 67],
    )
    res_look = parse_disk_output(SAMPLE_LOOK_STDOUT, cfg)
    assert res_look.total_head_movement == 299
    assert 199 not in res_look.service_order
    assert 0 not in res_look.service_order
    assert res_look.service_order == [53, 65, 67, 98, 122, 124, 183, 37, 14]

    # C-LOOK wraparound directly from 183 to lowest requested cylinder 14
    cfg_clook = DiskConfig(
        algorithm=DiskAlgorithm.CLOOK,
        direction=DiskDirection.INCREASING,
        min_cylinder=0,
        max_cylinder=199,
        initial_head=53,
        requests=[98, 183, 37, 122, 14, 124, 65, 67],
    )
    res_clook = parse_disk_output(SAMPLE_CLOOK_STDOUT, cfg_clook)
    assert res_clook.total_head_movement == 322
    assert 199 not in res_clook.service_order
    assert 0 not in res_clook.service_order
    wraparounds = [s for s in res_clook.steps if s.is_wraparound]
    assert len(wraparounds) >= 1
    assert wraparounds[0].from_cylinder == 183
    assert wraparounds[0].to_cylinder == 14


# ---------------------------------------------------------------------------
# Requirement 10: LIFO service order
# ---------------------------------------------------------------------------

def test_10_lifo_service_order():
    """Verify LIFO services requests in reverse arrival order."""
    cfg = DiskConfig(
        algorithm=DiskAlgorithm.LIFO,
        min_cylinder=0,
        max_cylinder=199,
        initial_head=53,
        requests=[98, 183, 37, 122, 14, 124, 65, 67],
    )
    res = parse_disk_output(SAMPLE_LIFO_STDOUT, cfg)
    assert res.total_head_movement == 609
    expected_order = [53, 67, 65, 124, 14, 122, 37, 183, 98]
    assert res.service_order == expected_order


# ---------------------------------------------------------------------------
# Requirement 11: Comparison results & consistent workloads
# ---------------------------------------------------------------------------

def test_11_comparison_results():
    """Verify parsing full 7-algorithm comparison results."""
    cfg = DiskConfig(
        algorithm=DiskAlgorithm.COMPARE_ALL,
        direction=DiskDirection.INCREASING,
        min_cylinder=0,
        max_cylinder=199,
        initial_head=53,
        requests=[98, 183, 37, 122, 14, 124, 65, 67],
    )
    comp = parse_disk_comparison_output(SAMPLE_COMPARISON_STDOUT, cfg)
    assert len(comp.entries) == 7
    assert "SSTF" in comp.best_algorithm
    assert comp.workload_size == 8

    # Verify best is SSTF with 236 cylinders
    sstf_entry = next(e for e in comp.entries if "SSTF" in e.algorithm_name)
    assert sstf_entry.total_head_movement == 236

    # Verify FCFS baseline has 640 cylinders
    fcfs_entry = next(e for e in comp.entries if "FCFS" in e.algorithm_name)
    assert fcfs_entry.total_head_movement == 640


# ---------------------------------------------------------------------------
# Requirement 12: Backend timeout, failure, and malformed output handling
# ---------------------------------------------------------------------------

def test_12_backend_failure_handling(qapp):
    """Verify GUI safely handles backend errors without crashing."""
    runner = DummyDiskRunner(sample_stdout="", exit_code=1)
    page = DiskPage(runner=runner)

    # Trigger run
    page._run_simulation()
    qapp.processEvents()
    if page._active_worker:
        page._active_worker.wait(2000)
    qapp.processEvents()
    qapp.processEvents()

    assert page.btn_run.isEnabled()
    assert page.card_movement.value_label.text() == "Failed"
    assert "failed" in page.lbl_validation_err.text().lower() or "error" in page.lbl_validation_err.text().lower()


def test_12_backend_timeout_handling(qapp):
    """Verify GUI safely handles backend timeouts."""
    runner = DummyDiskRunner(sample_stdout="", exit_code=-1, is_timeout=True)
    page = DiskPage(runner=runner)

    page._run_simulation()
    qapp.processEvents()
    if page._active_worker:
        page._active_worker.wait(2000)
    qapp.processEvents()
    qapp.processEvents()

    assert "timeout" in page.lbl_validation_err.text().lower() or "timed out" in page.lbl_validation_err.text().lower()


def test_12_malformed_output_fallback():
    """Verify fallback parser handles non-JSON stdout gracefully."""
    cfg = DiskConfig(
        algorithm=DiskAlgorithm.FCFS,
        min_cylinder=0,
        max_cylinder=199,
        initial_head=53,
        requests=[98, 183],
    )
    raw_text = """
    === FCFS Disk Scheduling ===
    Total Head Movement: 175 cylinders
    Average Seek: 87.50 cylinders/request
    Service Order: 53 -> 98 -> 183
    """
    res = parse_disk_output(raw_text, cfg)
    assert res.total_head_movement == 175
    assert res.service_order == [53, 98, 183]
    assert len(res.steps) == 2


# ---------------------------------------------------------------------------
# Requirement 13: Sidebar & dashboard navigation
# ---------------------------------------------------------------------------

def test_13_navigation_to_disk(qapp):
    """Verify MainWindow sidebar and dashboard can navigate directly to Disk page."""
    runner = DummyDiskRunner(SAMPLE_FCFS_STDOUT)
    window = MainWindow(runner=runner)

    # Verify Disk button in sidebar
    assert hasattr(window, "nav_btn_disk")
    window.nav_btn_disk.click()
    assert window.stack.currentWidget() == window.disk_page

    # Verify Dashboard card navigation
    window.navigate_to_page("dashboard")
    assert window.stack.currentWidget() == window.dashboard_page
    assert hasattr(window.dashboard_page, "btn_launch_disk")
    window.dashboard_page.btn_launch_disk.click()
    assert window.stack.currentWidget() == window.disk_page

    window.close()


# ---------------------------------------------------------------------------
# Requirement 14: Non-regression across CPU, Memory, Paging, and Deadlock
# ---------------------------------------------------------------------------

def test_14_non_regression_all_pages(qapp):
    """Verify all 6 pages exist in MainWindow stack and can be navigated without errors."""
    runner = DummyDiskRunner()
    window = MainWindow(runner=runner)

    assert window.stack.count() == 11

    # Test navigating to each page
    pages = ["dashboard", "scheduling", "memory", "paging", "deadlock", "disk"]
    for page_key in pages:
        window.navigate_to_page(page_key)
        assert window.current_page == page_key

    # Verify previous pages still have their core widgets
    assert hasattr(window.scheduling_page, "gantt_chart")
    assert hasattr(window.memory_page, "memory_map")
    assert hasattr(window.paging_page, "frame_grid")
    assert hasattr(window.deadlock_page, "graph_widget")
    assert hasattr(window.disk_page, "plot_widget")

    window.close()


# ---------------------------------------------------------------------------
# Visualization & Preset Tests
# ---------------------------------------------------------------------------

def test_plot_widget_and_presets(qapp):
    """Verify DiskHeadPlotWidget and preset configurations."""
    page = DiskPage()

    # Verify presets
    assert page.combo_presets.count() >= 6
    page.combo_presets.setCurrentIndex(1)  # Boundary Traversal
    assert "199" in page.txt_requests.text() or "0" in page.txt_requests.text()

    # Load result into plot widget
    cfg = DiskConfig(
        algorithm=DiskAlgorithm.SCAN,
        direction=DiskDirection.INCREASING,
        min_cylinder=0,
        max_cylinder=199,
        initial_head=53,
        requests=[98, 183, 37, 122, 14, 124, 65, 67],
    )
    result = parse_disk_output(SAMPLE_SCAN_STDOUT, cfg)
    page.plot_widget.set_result(result)

    # Canvas should have 10 nodes (initial + 8 requests + 1 boundary)
    assert len(page.plot_widget.canvas.nodes) == 10
    assert page.plot_widget.sequence_bar.count() > 0
    assert len(result.serviced_requests) == 8
