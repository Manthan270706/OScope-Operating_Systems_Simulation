"""Offscreen smoke tests for OScope GUI components."""

import os
import sys
import pytest

# Ensure offscreen Qt platform for headless CI / testing environments
os.environ["QT_QPA_PLATFORM"] = "offscreen"

from oscope_gui.models.scheduling import AlgorithmType, ExecutionSegmentModel, ProcessInput




class DummyBackendRunner:
    def __init__(self):
        self.last_stdin = None

    def execute(self, args, stdin_data=None, timeout=15.0):
        from oscope_gui.backend.runner import ExecutionResult

        self.last_stdin = stdin_data
        sample_stdout = """
Simulation completed successfully.
Scheduled 2 process(es) across 2 timeline execution segment(s).

=== Execution Timeline ===
Total Simulation Interval: [0 -> 8] (Duration: 8)

Gantt Chart:
| [P1 0-5] | [P2 5-8] |

Execution Segments:
  [0 -> 5] Process PID 1
  [5 -> 8] Process PID 2

=== Process Metrics Table ===
   PID   Arrival     Burst   Completion   Turnaround    Waiting   Response
--------------------------------------------------------------------------
     1         0         5            5            5          0          0
     2         1         3            8            7          4          4

=== Average Metrics ===
Average Waiting Time:    2.00
Average Turnaround Time: 6.00
Average Response Time:   2.00
"""
        return ExecutionResult(
            exit_code=0,
            stdout=sample_stdout,
            stderr="",
            duration=0.1,
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


def test_main_window_creation(qapp):
    from oscope_gui.main_window import MainWindow

    runner = DummyBackendRunner()
    window = MainWindow(runner)

    assert window.windowTitle() == "OScope — Operating Systems Simulation Platform"
    assert window.stack.count() == 11
    assert window.stack.currentIndex() == 0  # Dashboard is default

    # Navigate to scheduling
    window.navigate_to_page("scheduling")
    assert window.stack.currentIndex() == 1
    assert window.nav_btn_sched.isChecked()

    # Navigate to memory
    window.navigate_to_page("memory")
    assert window.stack.currentIndex() == 2
    assert window.nav_btn_mem.isChecked()

    # Navigate to paging
    window.navigate_to_page("paging")
    assert window.stack.currentIndex() == 3
    assert window.nav_btn_page.isChecked()

    # Navigate to deadlock
    window.navigate_to_page("deadlock")
    assert window.stack.currentIndex() == 4
    assert window.nav_btn_deadlock.isChecked()

    # Navigate to disk
    window.navigate_to_page("disk")
    assert window.stack.currentIndex() == 5
    assert window.nav_btn_disk.isChecked()

    # Navigate to linux
    window.navigate_to_page("linux")
    assert window.stack.currentIndex() == 6
    assert window.nav_btn_linux.isChecked()

    # Navigate to monitor
    window.navigate_to_page("monitor")
    assert window.stack.currentIndex() == 7
    assert window.nav_btn_monitor.isChecked()

    # Navigate to filesystem
    window.navigate_to_page("filesystem")
    assert window.stack.currentIndex() == 8
    assert window.nav_btn_fs.isChecked()

    # Navigate to translation
    window.navigate_to_page("translation")
    assert window.stack.currentIndex() == 9
    assert window.nav_btn_vm.isChecked()

    # Navigate to lifecycle
    window.navigate_to_page("lifecycle")
    assert window.stack.currentIndex() == 10
    assert window.nav_btn_lifecycle.isChecked()

    # Navigate back to dashboard
    window.navigate_to_page("dashboard")
    assert window.stack.currentIndex() == 0
    assert window.nav_btn_dash.isChecked()

    window.close()



def test_paging_page_controls(qapp):
    from oscope_gui.pages.paging_page import PageReplacementPage
    from oscope_gui.models.paging import PagingAlgorithm

    runner = DummyBackendRunner()
    page = PageReplacementPage(runner)

    # Check preset loaded
    assert "7, 0, 1, 2" in page.input_ref_string.text()
    assert page.spin_frames.value() == 3

    # Collect valid inputs
    cfg, err = page.collect_inputs()
    assert err is None
    assert cfg.algorithm == PagingAlgorithm.FIFO
    assert cfg.frame_count == 3
    assert len(cfg.reference_string) == 13

    # Load Belady's Anomaly preset
    page.load_preset("Belady's Anomaly")
    assert "1, 2, 3, 4" in page.input_ref_string.text()
    cfg, err = page.collect_inputs()
    assert err is None
    assert len(cfg.reference_string) == 12

    # Validation errors on empty or invalid input
    page.input_ref_string.setText("")
    cfg, err = page.collect_inputs()
    assert err is not None
    assert "empty" in err.lower()

    page.input_ref_string.setText("7, -3, 2")
    cfg, err = page.collect_inputs()
    assert err is not None
    assert "negative" in err.lower()


def test_frame_grid_widget(qapp):
    from oscope_gui.widgets.frame_grid import FrameGridWidget
    from oscope_gui.models.paging import PagingStepModel

    widget = FrameGridWidget()
    assert widget._steps == []

    steps = [
        PagingStepModel(step_number=1, page=7, is_fault=True, frames=[7, -1, -1], evicted_page=None),
        PagingStepModel(step_number=2, page=0, is_fault=True, frames=[7, 0, -1], evicted_page=None),
        PagingStepModel(step_number=3, page=1, is_fault=True, frames=[7, 0, 1], evicted_page=None),
        PagingStepModel(step_number=4, page=2, is_fault=True, frames=[2, 0, 1], evicted_page=7),
    ]
    widget.set_simulation_result(3, steps)
    assert len(widget._steps) == 4
    assert widget._current_step_idx == 0

    # Step navigation
    widget.go_to_next()
    assert widget._current_step_idx == 1
    widget.go_to_last()
    assert widget._current_step_idx == 3
    widget.go_to_first()
    assert widget._current_step_idx == 0

    widget.clear()
    assert widget._steps == []



def test_memory_page_controls(qapp):
    from oscope_gui.pages.memory_page import MemoryAllocationPage
    from oscope_gui.models.memory import MemoryOperationType

    runner = DummyBackendRunner()
    page = MemoryAllocationPage(runner)

    # Initial state loads "Standard Partitioning" preset (4 operations)
    assert page.op_table.rowCount() == 4

    # Add allocate row
    page.add_operation_row(MemoryOperationType.ALLOCATE, request_id=10, size=250, process_id=10)
    assert page.op_table.rowCount() == 5

    # Add deallocate row
    page.add_operation_row(MemoryOperationType.DEALLOCATE, request_id=10)
    assert page.op_table.rowCount() == 6

    # Remove selected row
    page.op_table.selectRow(5)
    page.remove_selected_row()
    assert page.op_table.rowCount() == 5

    # Clear all rows
    page.clear_all_rows()
    assert page.op_table.rowCount() == 0

    # Load Fragmentation & Coalescing preset
    page.load_preset("Fragmentation & Coalescing")
    assert page.op_table.rowCount() == 6
    assert page.spin_total_memory.value() == 1200


def test_memory_map_widget(qapp):
    from oscope_gui.widgets.memory_map import MemoryMapWidget
    from oscope_gui.models.memory import MemoryBlockModel

    widget = MemoryMapWidget()
    assert widget._blocks == []

    blocks = [
        MemoryBlockModel(block_index=0, start_address=0, size=200, is_allocated=True, allocation_id=1, process_id=1),
        MemoryBlockModel(block_index=1, start_address=200, size=800, is_allocated=False),
    ]
    widget.set_memory_state(1000, blocks)
    assert len(widget._blocks) == 2
    assert widget._blocks[0].is_allocated
    assert not widget._blocks[1].is_allocated
    assert widget._blocks[1].size == 800

    widget.clear()
    assert widget._blocks == []



def test_scheduling_page_process_table_controls(qapp):
    from oscope_gui.pages.scheduling_page import SchedulingPage

    runner = DummyBackendRunner()
    page = SchedulingPage(runner)

    # Initial state has Standard 3-Process preset
    assert page.proc_table.rowCount() == 3

    # Add a process row
    page.add_process_row(pid=4, arrival=3, burst=6, priority=1)
    assert page.proc_table.rowCount() == 4

    # Remove selected row
    page.proc_table.selectRow(3)
    page.remove_selected_row()
    assert page.proc_table.rowCount() == 3

    # Clear all rows
    page.clear_all_rows()
    assert page.proc_table.rowCount() == 0

    # Load preset
    page.load_preset("Convoy Effect")
    assert page.proc_table.rowCount() == 3
    assert page.proc_table.item(0, 2).text() == "24"


def test_scheduling_input_validation(qapp):
    from oscope_gui.pages.scheduling_page import SchedulingPage

    runner = DummyBackendRunner()
    page = SchedulingPage(runner)

    # Clear table -> should error on empty table
    page.clear_all_rows()
    config, procs, err = page.collect_inputs()
    assert err is not None
    assert "No processes entered" in err

    # Add valid process
    page.add_process_row(pid=1, arrival=0, burst=5, priority=0)
    config, procs, err = page.collect_inputs()
    assert err is None
    assert len(procs) == 1
    assert procs[0].pid == 1

    # Add duplicate PID
    page.add_process_row(pid=1, arrival=1, burst=3, priority=0)
    config, procs, err = page.collect_inputs()
    assert err is not None
    assert "Duplicate PID 1" in err


def test_gantt_chart_widget(qapp):
    from oscope_gui.widgets.gantt_chart import GanttChartWidget

    chart = GanttChartWidget()
    assert chart._timeline == []

    timeline = [
        ExecutionSegmentModel(start_time=0, end_time=5, pid=1, is_idle=False),
        ExecutionSegmentModel(start_time=5, end_time=7, pid=None, is_idle=True),
        ExecutionSegmentModel(start_time=7, end_time=12, pid=2, is_idle=False),
    ]
    chart.set_timeline(timeline)
    assert len(chart._timeline) == 3
    assert chart._timeline[1].is_idle

    chart.clear()
    assert chart._timeline == []


def test_deadlock_page_controls(qapp):
    from oscope_gui.pages.deadlock_page import DeadlockPage
    from oscope_gui.models.deadlock import DeadlockMode

    runner = DummyBackendRunner()
    page = DeadlockPage(runner)

    assert page.combo_mode.count() == 3
    assert page.spin_processes.value() == 5
    assert page.spin_resources.value() == 3
    assert page.txt_available.text() == "3, 3, 2"

    # Check mode switching
    page.combo_mode.setCurrentIndex(1)  # RESOURCE_REQUEST
    assert page.combo_mode.currentData() == DeadlockMode.RESOURCE_REQUEST
    assert not page.request_panel.isHidden()

    page.combo_mode.setCurrentIndex(2)  # DETECTION
    assert page.combo_mode.currentData() == DeadlockMode.DETECTION
    assert page.request_panel.isHidden()

    page.combo_mode.setCurrentIndex(0)  # SAFETY
    assert page.combo_mode.currentData() == DeadlockMode.SAFETY

    # Check collection
    config, err = page._collect_config()
    assert err is None
    assert config is not None
    assert config.num_processes == 5
    assert config.num_resources == 3
    assert config.available == [3, 3, 2]


def test_resource_graph_widget(qapp):
    from oscope_gui.widgets.resource_graph import ResourceGraphWidget
    from oscope_gui.models.deadlock import DeadlockSafetyResultModel

    widget = ResourceGraphWidget()
    assert widget.canvas.result is None

    res = DeadlockSafetyResultModel(
        is_safe=True,
        safe_sequence=[1, 3, 4, 0, 2],
        blocked_processes=[],
        message="System is in a safe state.",
        num_processes=5,
        num_resources=3,
        available=[3, 3, 2],
        allocation=[[0, 1, 0], [2, 0, 0], [3, 0, 2], [2, 1, 1], [0, 0, 2]],
        max_claim=[[7, 5, 3], [3, 2, 2], [9, 0, 2], [2, 2, 2], [4, 3, 3]],
        need=[[7, 4, 3], [1, 2, 2], [6, 0, 0], [0, 1, 1], [4, 3, 1]],
        raw_output="=== Banker's Safety Analysis ===\nSystem State: SAFE\n",
    )

    widget.set_result(res)
    assert widget.canvas.result is not None
    assert widget.canvas.result.is_safe
    assert widget.canvas.result.safe_sequence == [1, 3, 4, 0, 2]
    assert widget.flow_bar.lbl_title.text() == "SAFE SEQUENCE:"


def test_disk_page_controls(qapp):
    from oscope_gui.pages.disk_page import DiskPage
    from oscope_gui.models.disk import DiskAlgorithm

    runner = DummyBackendRunner()
    page = DiskPage(runner)

    # Check textbook preset loaded
    assert "98" in page.txt_requests.text()
    assert page.spin_min.value() == 0
    assert page.spin_max.value() == 199
    assert page.spin_head.value() == 53

    # Check input validation
    cfg, err = page._validate_inputs()
    assert err is None
    assert cfg is not None
    assert cfg.algorithm == DiskAlgorithm.FCFS
    assert cfg.requests == [98, 183, 37, 122, 14, 124, 65, 67]

    # Invalidate on out of range
    page.txt_requests.setText("98 250")
    cfg, err = page._validate_inputs()
    assert err is not None
    assert "out of disk range" in err


def test_disk_head_plot_widget(qapp):
    from oscope_gui.widgets.disk_plot import DiskHeadPlotWidget
    from oscope_gui.models.disk import DiskAlgorithm, DiskSchedulingResultModel, DiskStepModel

    widget = DiskHeadPlotWidget()
    assert widget.canvas.result is None

    res = DiskSchedulingResultModel(
        algorithm=DiskAlgorithm.FCFS,
        algorithm_name="First-Come, First-Served (FCFS)",
        serviced_requests=[98, 183, 37],
        head_path=[53, 98, 183, 37],
        total_head_movement=276,
        average_head_movement=92.0,
        initial_head_position=53,
        final_head_position=37,
        steps=[
            DiskStepModel(1, 53, 98, 45, 45, True, False, False, "Serviced 98"),
            DiskStepModel(2, 98, 183, 85, 130, True, False, False, "Serviced 183"),
            DiskStepModel(3, 183, 37, 146, 276, True, False, False, "Serviced 37"),
        ],
    )
    widget.set_result(res, 0, 199)

    assert widget.canvas.result is not None
    assert widget.canvas.result.total_head_movement == 276
    assert "FCFS" in widget.flow_bar.lbl_title.text()


