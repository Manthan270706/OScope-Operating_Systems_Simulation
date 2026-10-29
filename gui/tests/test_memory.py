"""Comprehensive automated tests for Memory Allocation Simulator in OScope GUI.

Covers:
1. Memory Allocation navigation and page creation.
2. Algorithm dropdown contents and descriptions.
3. Input validation.
4. First Fit backend mapping.
5. Best Fit backend mapping.
6. Worst Fit backend mapping.
7. Correct result parsing.
8. Allocation failure handling.
9. Memory visualization for genuine results.
10. Empty, running, success, and error states.
11. Preservation of existing CPU Scheduling functionality.
"""

import os
import pytest
from PySide6.QtCore import Qt

os.environ["QT_QPA_PLATFORM"] = "offscreen"

from oscope_gui.models.memory import (
    MemoryBlockModel,
    MemoryComparisonResultModel,
    MemoryConfig,
    MemoryMetricsModel,
    MemoryOperationInput,
    MemoryOperationResultModel,
    MemoryOperationType,
    MemorySimulationResultModel,
    MemoryStrategy,
)
from oscope_gui.backend.parser import (
    generate_memory_stdin,
    parse_memory_comparison_output,
    parse_memory_output,
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


SAMPLE_BACKEND_SUCCESS = """
=== OScope CLI Menu ===
Choice: 9
Memory Allocation Strategy Menu:
Choice: 1
Total memory size: 1000
Number of operations: 3
Allocation successful: Request ID 1 allocated at address 0 (200 bytes, Internal ID: 1)
Allocation successful: Request ID 2 allocated at address 200 (300 bytes, Internal ID: 2)
Deallocation successful: Request ID 1 (Internal ID: 1) freed

=== Memory Block Layout ===
Block   Start Address   Size (B)    Status      Alloc ID    PID
----------------------------------------------------------------------
1       0               200         Free        -           -
2       200             300         Allocated   2           2
3       500             500         Free        -           -

=== Memory Allocation Metrics ===
Total Memory:           1000 bytes
Allocated Memory:       300 bytes
Free Memory:            700 bytes
Largest Free Block:     500 bytes
External Fragmentation: 28.57% (0.29)
"""

SAMPLE_BACKEND_FAILURE = """
Allocation successful: Request ID 1 allocated at address 0 (600 bytes, Internal ID: 1)
Allocation failed for request ID 2: No contiguous block large enough for 500 bytes

=== Memory Block Layout ===
Block   Start Address   Size (B)    Status      Alloc ID    PID
----------------------------------------------------------------------
1       0               600         Allocated   1           1
2       600             400         Free        -           -

=== Memory Allocation Metrics ===
Total Memory:           1000 bytes
Allocated Memory:       600 bytes
Free Memory:            400 bytes
Largest Free Block:     400 bytes
External Fragmentation: 0.00% (0.00)
"""




def test_1_memory_navigation_and_page_creation(qapp):
    from oscope_gui.main_window import MainWindow

    runner = DummyBackendRunner(SAMPLE_BACKEND_SUCCESS)
    window = MainWindow(runner)

    assert window.stack.count() == 11


    # Navigate to memory via sidebar
    window.nav_btn_mem.click()
    assert window.stack.currentIndex() == 2
    assert window.nav_btn_mem.isChecked()

    # Dashboard action card navigation
    window.navigate_to_page("dashboard")
    assert window.stack.currentIndex() == 0
    window.navigate_to_page("memory")
    assert window.stack.currentIndex() == 2

    window.close()


def test_2_algorithm_dropdown_contents_and_descriptions(qapp):
    from oscope_gui.pages.memory_page import MemoryAllocationPage

    runner = DummyBackendRunner()
    page = MemoryAllocationPage(runner)

    # Check items in dropdown
    assert page.strategy_combo.count() == 4
    items = [page.strategy_combo.itemText(i) for i in range(page.strategy_combo.count())]
    assert items == [
        "First Fit",
        "Best Fit",
        "Worst Fit",
        "Compare All Strategies",
    ]

    # Check First Fit description
    page.strategy_combo.setCurrentIndex(0)
    assert "First Fit: Selects the first free block" in page.strategy_info_label.text()

    # Check Best Fit description
    page.strategy_combo.setCurrentIndex(1)
    assert "Best Fit: Searches the entire memory pool to find the smallest suitable free block" in page.strategy_info_label.text()

    # Check Worst Fit description
    page.strategy_combo.setCurrentIndex(2)
    assert "Worst Fit: Allocates from the largest available free block" in page.strategy_info_label.text()

    # Check Compare All description
    page.strategy_combo.setCurrentIndex(3)
    assert "Compare All: Evaluates First Fit, Best Fit, and Worst Fit side-by-side" in page.strategy_info_label.text()


def test_3_input_validation(qapp):
    from oscope_gui.pages.memory_page import MemoryAllocationPage

    runner = DummyBackendRunner()
    page = MemoryAllocationPage(runner)

    # Test empty table validation
    page.clear_all_rows()
    cfg, ops, err = page.collect_inputs()
    assert err is not None
    assert "No memory operations entered" in err

    # Test invalid request ID (0 or negative)
    page.add_operation_row(MemoryOperationType.ALLOCATE, request_id=0, size=100, process_id=1)
    cfg, ops, err = page.collect_inputs()
    assert err is not None
    assert "must be positive (> 0)" in err

    # Fix request ID, but invalid size <= 0
    page.clear_all_rows()
    page.add_operation_row(MemoryOperationType.ALLOCATE, request_id=1, size=-50, process_id=1)
    cfg, ops, err = page.collect_inputs()
    assert err is not None
    assert "Allocation size must be positive (> 0)" in err

    # Valid inputs
    page.clear_all_rows()
    page.add_operation_row(MemoryOperationType.ALLOCATE, request_id=1, size=200, process_id=1)
    page.add_operation_row(MemoryOperationType.DEALLOCATE, request_id=1)
    cfg, ops, err = page.collect_inputs()
    assert err is None
    assert len(ops) == 2
    assert cfg.total_memory == 1000


def test_4_first_fit_backend_mapping():
    config = MemoryConfig(strategy=MemoryStrategy.FIRST_FIT, total_memory=1000)
    ops = [MemoryOperationInput(op_type=MemoryOperationType.ALLOCATE, request_id=1, size=200, process_id=1)]
    stdin_str = generate_memory_stdin(config, ops)
    lines = stdin_str.strip().splitlines()

    assert lines[0] == "9"  # Choice 9: Memory Allocation
    assert lines[1] == "1"  # Strategy: 1 for First Fit
    assert lines[2] == "1000"
    assert lines[3] == "1"
    assert lines[4:8] == ["1", "1", "200", "1"]
    assert lines[8] == "5"  # Return to menu
    assert lines[9] == "13" # Exit


def test_5_best_fit_backend_mapping():
    config = MemoryConfig(strategy=MemoryStrategy.BEST_FIT, total_memory=2048)
    ops = [MemoryOperationInput(op_type=MemoryOperationType.ALLOCATE, request_id=5, size=512, process_id=2)]
    stdin_str = generate_memory_stdin(config, ops)
    lines = stdin_str.strip().splitlines()

    assert lines[0] == "9"
    assert lines[1] == "2"  # Strategy: 2 for Best Fit
    assert lines[2] == "2048"


def test_6_worst_fit_backend_mapping():
    config = MemoryConfig(strategy=MemoryStrategy.WORST_FIT, total_memory=4096)
    ops = [MemoryOperationInput(op_type=MemoryOperationType.DEALLOCATE, request_id=3)]
    stdin_str = generate_memory_stdin(config, ops)
    lines = stdin_str.strip().splitlines()

    assert lines[0] == "9"
    assert lines[1] == "3"  # Strategy: 3 for Worst Fit
    assert lines[2] == "4096"
    assert lines[3] == "1"
    assert lines[4:6] == ["2", "3"]  # Deallocate op: 2, req_id 3


def test_7_correct_result_parsing():
    res = parse_memory_output(SAMPLE_BACKEND_SUCCESS, "First Fit")
    assert res.total_memory == 1000
    assert len(res.blocks) == 3
    assert len(res.operations) == 3

    # Operations
    assert res.operations[0].success
    assert res.operations[0].start_address == 0
    assert res.operations[0].size == 200
    assert res.operations[1].start_address == 200
    assert res.operations[2].op_type == "Deallocate"

    # Blocks
    assert not res.blocks[0].is_allocated
    assert res.blocks[0].size == 200
    assert res.blocks[1].is_allocated
    assert res.blocks[1].process_id == 2
    assert res.blocks[1].size == 300
    assert not res.blocks[2].is_allocated
    assert res.blocks[2].size == 500

    # Metrics
    assert res.metrics.allocated_memory == 300
    assert res.metrics.free_memory == 700
    assert res.metrics.largest_free_block == 500
    assert pytest.approx(res.metrics.external_fragmentation, 0.01) == 0.29


def test_8_allocation_failure_handling(qapp):
    from oscope_gui.pages.memory_page import MemoryAllocationPage

    runner = DummyBackendRunner(SAMPLE_BACKEND_FAILURE)
    page = MemoryAllocationPage(runner)

    res = parse_memory_output(SAMPLE_BACKEND_FAILURE, "First Fit")
    page.display_results(res)

    # Check that failure was captured in operation log
    assert len(res.operations) == 2
    assert res.operations[0].success is True
    assert res.operations[1].success is False
    assert "No contiguous block large enough" in res.operations[1].message

    # Verify operations table shows failure badge
    assert page.ops_table.rowCount() == 2
    status_item = page.ops_table.item(1, 3)
    assert status_item.text() == "Failed"


def test_9_memory_visualization_for_genuine_results(qapp):
    from oscope_gui.widgets.memory_map import MemoryMapWidget

    widget = MemoryMapWidget()
    blocks = [
        MemoryBlockModel(block_index=1, start_address=0, size=200, is_allocated=False),
        MemoryBlockModel(block_index=2, start_address=200, size=300, is_allocated=True, allocation_id=2, process_id=2),
        MemoryBlockModel(block_index=3, start_address=500, size=500, is_allocated=False),
    ]
    widget.set_memory_state(1000, blocks)

    assert len(widget._blocks) == 3
    assert widget._blocks[0].start_address == 0
    assert widget._blocks[0].end_address == 200
    assert widget._blocks[1].is_allocated
    assert widget._blocks[1].process_id == 2
    assert widget._blocks[2].size == 500


def test_10_empty_running_success_error_states(qapp):
    from oscope_gui.pages.memory_page import MemoryAllocationPage

    runner = DummyBackendRunner(SAMPLE_BACKEND_SUCCESS)
    page = MemoryAllocationPage(runner)

    # Ready / initial state
    assert page.btn_run.isEnabled()
    assert "Ready to simulate" in page.status_banner.text()

    # Success state after display_results
    res = parse_memory_output(SAMPLE_BACKEND_SUCCESS, "First Fit")
    page.display_results(res)
    assert "simulation completed successfully" in page.status_banner.text().lower()
    assert "300" in page.card_allocated.value_label.text()
    assert "700" in page.card_free.value_label.text()

    # Reset state
    page.reset_results()
    assert page.card_allocated.value_label.text() == "--"
    assert page.card_free.value_label.text() == "--"
    assert page.blocks_table.rowCount() == 0
    assert "Memory layout and results cleared" in page.status_banner.text()


    # Error state
    page.show_error("Validation test error: Total memory exhausted.")
    assert "Validation test error" in page.status_banner.text()
    assert page.btn_run.isEnabled()


def test_11_preservation_of_existing_cpu_scheduling(qapp):
    from oscope_gui.main_window import MainWindow

    runner = DummyBackendRunner(SAMPLE_BACKEND_SUCCESS)
    window = MainWindow(runner)

    # Verify scheduling page is fully functional
    window.navigate_to_page("scheduling")
    assert window.stack.currentIndex() == 1
    sched_page = window.scheduling_page
    assert sched_page.proc_table.rowCount() > 0

    # Switch back and forth between scheduling and memory
    window.navigate_to_page("memory")
    assert window.stack.currentIndex() == 2
    mem_page = window.memory_page
    assert mem_page.op_table.rowCount() > 0

    window.navigate_to_page("scheduling")
    assert window.stack.currentIndex() == 1
    assert sched_page.proc_table.rowCount() > 0

    window.close()
