"""Comprehensive automated tests for Page Replacement Simulator in OScope GUI.

Covers:
1. Page Replacement navigation.
2. Page creation and widget initialization.
3. Algorithm dropdown options.
4. Input validation for frame count and reference string.
5. FIFO backend mapping.
6. LRU backend mapping.
7. Optimal backend mapping.
8. Correct parsing of frame states.
9. Page-hit and page-fault counts.
10. Rate calculations.
11. Empty input and backend failure handling.
12. Visualization updates when navigating between references.
13. Comparison behavior.
14. Preservation of CPU Scheduling and Memory Allocation functionality.
"""

import os
import pytest
from PySide6.QtCore import Qt

os.environ["QT_QPA_PLATFORM"] = "offscreen"

from oscope_gui.models.paging import (
    PagingAlgorithm,
    PagingComparisonEntryModel,
    PagingComparisonResultModel,
    PagingConfig,
    PagingMetricsModel,
    PagingSimulationResultModel,
    PagingStepModel,
)
from oscope_gui.backend.parser import (
    generate_paging_stdin,
    parse_paging_comparison_output,
    parse_paging_output,
)


class DummyBackendRunner:
    """Mock backend runner for deterministic UI and parser testing."""

    def __init__(self, sample_stdout: str = "", exit_code: int = 0):
        self.last_args = None
        self.last_stdin = None
        self.sample_stdout = sample_stdout
        self.exit_code = exit_code

    def execute(self, args, stdin_data=None, timeout=15.0):
        from oscope_gui.backend.runner import ExecutionResult

        self.last_args = args
        self.last_stdin = stdin_data
        return ExecutionResult(
            exit_code=self.exit_code,
            stdout=self.sample_stdout,
            stderr="",
            duration=0.05,
            is_timeout=False,
            command=["dummy_oscope"] + args,
        )

    def verify(self):
        return True, "Mock engine online"

    def get_info(self):
        from oscope_gui.backend.runner import BackendInfo

        return BackendInfo(
            runner_type="mock",
            executable_path="dummy_oscope",
            is_available=True,
            status_message="Mock engine online",
        )

    def cancel(self):
        pass


SAMPLE_PAGING_SUCCESS = """
[FIFO Page Replacement Simulation]
Simulation completed successfully with 13 reference(s) across 3 frame(s).

=== Page Replacement Step-by-Step Execution ===
  Step    Page    Result    Evicted  Frames
-------------------------------------------------------
     1       7     Fault       None  [7, -1, -1]
     2       0     Fault       None  [7, 0, -1]
     3       1     Fault       None  [7, 0, 1]
     4       2     Fault          7  [2, 0, 1]
     5       0       Hit       None  [2, 0, 1]
     6       3     Fault          0  [2, 3, 1]
     7       0     Fault          1  [2, 3, 0]
     8       4     Fault          2  [4, 3, 0]
     9       2     Fault          3  [4, 2, 0]
    10       3     Fault          0  [4, 2, 3]
    11       0     Fault          4  [0, 2, 3]
    12       3       Hit       None  [0, 2, 3]
    13       2       Hit       None  [0, 2, 3]

=== Page Replacement Metrics ===
Total Page References: 13
Page Faults:           10
Page Hits:             3
Page-Fault Rate:       76.92% (0.77)
Page-Hit Rate:         23.08% (0.23)
"""

SAMPLE_PAGING_COMPARISON = """
Comparison completed successfully across 3 page replacement algorithm(s).

=== Page Replacement Algorithm Comparison ===
Frame Count: 3 | Total References: 13

Algorithm         References    Faults    Hits     Fault Rate       Hit Rate
----------------------------------------------------------------------------
FIFO                      13        10       3         76.92%         23.08%
LRU                       13         9       4         69.23%         30.77%
Optimal                   13         7       6         53.85%         46.15%
"""




def test_1_paging_navigation(qapp):
    from oscope_gui.main_window import MainWindow

    runner = DummyBackendRunner(SAMPLE_PAGING_SUCCESS)
    window = MainWindow(runner)

    assert window.stack.count() == 11

    # Navigate to paging via sidebar
    window.nav_btn_page.click()
    assert window.stack.currentIndex() == 3
    assert window.nav_btn_page.isChecked()

    # Navigate via dashboard helper
    window.navigate_to_page("dashboard")
    assert window.stack.currentIndex() == 0
    window.navigate_to_page("paging")
    assert window.stack.currentIndex() == 3

    window.close()


def test_2_page_creation_and_widget_initialization(qapp):
    from oscope_gui.pages.paging_page import PageReplacementPage

    runner = DummyBackendRunner()
    page = PageReplacementPage(runner)

    # Ensure title and controls initialized
    assert page.spin_frames.value() == 3
    assert "7, 0, 1, 2" in page.input_ref_string.text()
    assert page.btn_run.isEnabled()
    assert "Ready to simulate" in page.status_banner.text()


def test_3_algorithm_dropdown_options(qapp):
    from oscope_gui.pages.paging_page import PageReplacementPage

    runner = DummyBackendRunner()
    page = PageReplacementPage(runner)

    assert page.algo_combo.count() == 4
    items = [page.algo_combo.itemText(i) for i in range(page.algo_combo.count())]
    assert any("FIFO" in item for item in items)
    assert any("LRU" in item for item in items)
    assert any("Optimal" in item for item in items)
    assert any("Compare All" in item for item in items)

    # Descriptions
    page.algo_combo.setCurrentIndex(0)
    assert "FIFO (First-In, First-Out)" in page.algo_info_label.text()

    page.algo_combo.setCurrentIndex(1)
    assert "LRU (Least Recently Used)" in page.algo_info_label.text()

    page.algo_combo.setCurrentIndex(2)
    assert "Optimal" in page.algo_info_label.text()
    assert "theoretical performance benchmark" in page.algo_info_label.text().lower()


def test_4_input_validation(qapp):
    from oscope_gui.pages.paging_page import PageReplacementPage

    runner = DummyBackendRunner()
    page = PageReplacementPage(runner)

    # Empty reference string
    page.input_ref_string.setText("")
    cfg, err = page.collect_inputs()
    assert err is not None
    assert "empty" in err.lower()

    # Negative page
    page.input_ref_string.setText("7, -1, 3")
    cfg, err = page.collect_inputs()
    assert err is not None
    assert "negative" in err.lower()

    # Non-numeric token
    page.input_ref_string.setText("7, foo, 3")
    cfg, err = page.collect_inputs()
    assert err is not None
    assert "invalid token" in err.lower()

    # Valid input with mixed commas and spaces
    page.input_ref_string.setText("7, 0 1,  2 0, 3")
    cfg, err = page.collect_inputs()
    assert err is None
    assert cfg.reference_string == [7, 0, 1, 2, 0, 3]


def test_5_fifo_backend_mapping():
    cfg = PagingConfig(algorithm=PagingAlgorithm.FIFO, frame_count=3, reference_string=[7, 0, 1])
    stdin = generate_paging_stdin(cfg)
    lines = stdin.strip().splitlines()

    assert lines[0] == "8"  # Menu: Paging
    assert lines[1] == "1"  # Sub-menu: FIFO
    assert lines[2] == "3"  # Frame count
    assert lines[3] == "7 0 1"
    assert lines[4] == "5"  # Return to menu
    assert lines[5] == "13" # Exit


def test_6_lru_backend_mapping():
    cfg = PagingConfig(algorithm=PagingAlgorithm.LRU, frame_count=4, reference_string=[2, 3, 1])
    stdin = generate_paging_stdin(cfg)
    lines = stdin.strip().splitlines()

    assert lines[0] == "8"
    assert lines[1] == "2"  # Sub-menu: LRU
    assert lines[2] == "4"


def test_7_optimal_backend_mapping():
    cfg = PagingConfig(algorithm=PagingAlgorithm.OPTIMAL, frame_count=5, reference_string=[1, 2, 3])
    stdin = generate_paging_stdin(cfg)
    lines = stdin.strip().splitlines()

    assert lines[0] == "8"
    assert lines[1] == "3"  # Sub-menu: Optimal
    assert lines[2] == "5"


def test_8_correct_parsing_of_frame_states():
    res = parse_paging_output(SAMPLE_PAGING_SUCCESS, "FIFO", frame_count=3)
    assert len(res.steps) == 13

    # Step 1: [7, -1, -1]
    assert res.steps[0].frames == [7, -1, -1]
    assert res.steps[0].evicted_page is None

    # Step 3: [7, 0, 1]
    assert res.steps[2].frames == [7, 0, 1]

    # Step 4: Eviction of 7 -> [2, 0, 1]
    assert res.steps[3].evicted_page == 7
    assert res.steps[3].frames == [2, 0, 1]


def test_9_page_hit_and_fault_counts():
    res = parse_paging_output(SAMPLE_PAGING_SUCCESS, "FIFO", frame_count=3)
    assert res.metrics.total_references == 13
    assert res.metrics.page_faults == 10
    assert res.metrics.page_hits == 3
    assert res.metrics.page_faults + res.metrics.page_hits == res.metrics.total_references


def test_10_rate_calculations():
    res = parse_paging_output(SAMPLE_PAGING_SUCCESS, "FIFO", frame_count=3)
    assert pytest.approx(res.metrics.fault_rate, 0.01) == 0.7692
    assert pytest.approx(res.metrics.hit_rate, 0.01) == 0.2308
    # Rates must be complementary
    assert pytest.approx(res.metrics.fault_rate + res.metrics.hit_rate, 0.01) == 1.0


def test_11_empty_input_and_backend_failure_handling(qapp):
    from oscope_gui.pages.paging_page import PageReplacementPage

    runner = DummyBackendRunner()
    page = PageReplacementPage(runner)

    # Empty input
    page.input_ref_string.setText("")
    page.run_simulation()
    assert "Input validation error" in page.status_banner.text()
    assert page.btn_run.isEnabled()

    # Backend error simulation
    page.show_error("WSL execution error: Frame allocation failed.")
    assert "Execution failed" in page.status_banner.text()
    assert page.btn_run.isEnabled()


def test_12_visualization_updates_and_step_navigation(qapp):
    from oscope_gui.pages.paging_page import PageReplacementPage

    runner = DummyBackendRunner(SAMPLE_PAGING_SUCCESS)
    page = PageReplacementPage(runner)

    res = parse_paging_output(SAMPLE_PAGING_SUCCESS, "FIFO", frame_count=3)
    page.display_results(res)

    grid = page.frame_grid
    assert len(grid._steps) == 13
    assert grid._current_step_idx == 0
    assert "Step 1 of 13" in grid.lbl_counter.text()

    # Navigate forward
    grid.go_to_next()
    assert grid._current_step_idx == 1
    assert "Step 2 of 13" in grid.lbl_counter.text()

    # Navigate to Step 4 (Eviction)
    grid.go_to_step(3)
    assert grid._current_step_idx == 3
    assert "P7 was evicted" in grid.lbl_insp_narrative.text() or "evicted" in grid.lbl_insp_narrative.text().lower()

    # Navigate to Step 5 (Hit)
    grid.go_to_step(4)
    assert "PAGE HIT" in grid.lbl_insp_narrative.text()

    # Reset
    page.reset_results()
    assert len(grid._steps) == 0
    assert page.card_faults.value_label.text() == "--"


def test_13_comparison_behavior(qapp):
    from oscope_gui.pages.paging_page import PageReplacementPage

    runner = DummyBackendRunner(SAMPLE_PAGING_COMPARISON)
    page = PageReplacementPage(runner)

    comp = parse_paging_comparison_output(SAMPLE_PAGING_COMPARISON)
    page.display_comparison(comp)

    assert page.comp_table.rowCount() == 3
    assert page.comp_table.item(0, 0).text() == "FIFO"
    assert page.comp_table.item(0, 2).text() == "10"
    assert page.comp_table.item(1, 0).text() == "LRU"
    assert page.comp_table.item(1, 2).text() == "9"
    assert page.comp_table.item(2, 0).text() == "Optimal"
    assert page.comp_table.item(2, 2).text() == "7"


def test_14_preservation_of_cpu_scheduling_and_memory(qapp):
    from oscope_gui.main_window import MainWindow

    runner = DummyBackendRunner(SAMPLE_PAGING_SUCCESS)
    window = MainWindow(runner)

    # CPU Scheduling check
    window.navigate_to_page("scheduling")
    assert window.stack.currentIndex() == 1
    assert window.scheduling_page.proc_table.rowCount() > 0

    # Memory Allocation check
    window.navigate_to_page("memory")
    assert window.stack.currentIndex() == 2
    assert window.memory_page.op_table.rowCount() > 0

    # Paging check
    window.navigate_to_page("paging")
    assert window.stack.currentIndex() == 3
    assert window.paging_page.spin_frames.value() > 0

    # Switch back to CPU scheduling
    window.navigate_to_page("scheduling")
    assert window.stack.currentIndex() == 1

    window.close()
