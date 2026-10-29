"""Unit tests for scheduling data models and validation logic."""

import pytest
from oscope_gui.models.scheduling import (
    AlgorithmConfig,
    AlgorithmType,
    AverageMetricsModel,
    ExecutionSegmentModel,
    ProcessInput,
    ProcessResultModel,
    SchedulingComparisonResultModel,
    SchedulingResultModel,
)


def test_process_input_validation_valid():
    proc = ProcessInput(pid=1, arrival_time=0, burst_time=5, priority=2)
    assert proc.validate() is None


def test_process_input_validation_negative_pid():
    proc = ProcessInput(pid=-1, arrival_time=0, burst_time=5, priority=0)
    err = proc.validate()
    assert err is not None
    assert "must be non-negative" in err


def test_process_input_validation_negative_arrival():
    proc = ProcessInput(pid=1, arrival_time=-3, burst_time=5, priority=0)
    err = proc.validate()
    assert err is not None
    assert "non-negative" in err


def test_process_input_validation_zero_burst():
    proc = ProcessInput(pid=1, arrival_time=0, burst_time=0, priority=0)
    err = proc.validate()
    assert err is not None
    assert "positive (> 0)" in err


def test_process_input_validation_negative_burst():
    proc = ProcessInput(pid=1, arrival_time=0, burst_time=-4, priority=0)
    err = proc.validate()
    assert err is not None
    assert "positive (> 0)" in err


def test_algorithm_config_validation():
    # FCFS does not require quantum
    cfg_fcfs = AlgorithmConfig(algorithm=AlgorithmType.FCFS, rr_quantum=0)
    assert cfg_fcfs.validate() is None

    # Round Robin requires positive quantum
    cfg_rr_valid = AlgorithmConfig(algorithm=AlgorithmType.ROUND_ROBIN, rr_quantum=3)
    assert cfg_rr_valid.validate() is None

    cfg_rr_invalid = AlgorithmConfig(algorithm=AlgorithmType.ROUND_ROBIN, rr_quantum=0)
    assert cfg_rr_invalid.validate() is not None

    # MLFQ requires positive quanta for Q0, Q1, Q2
    cfg_mlfq_valid = AlgorithmConfig(algorithm=AlgorithmType.MLFQ, mlfq_q0=2, mlfq_q1=4, mlfq_q2=8)
    assert cfg_mlfq_valid.validate() is None

    cfg_mlfq_invalid = AlgorithmConfig(algorithm=AlgorithmType.MLFQ, mlfq_q0=0, mlfq_q1=4, mlfq_q2=8)
    assert cfg_mlfq_invalid.validate() is not None


def test_execution_segment_duration():
    seg = ExecutionSegmentModel(start_time=5, end_time=12, pid=2, is_idle=False)
    assert seg.duration == 7
    assert not seg.is_idle
    assert seg.pid == 2

    idle_seg = ExecutionSegmentModel(start_time=0, end_time=3, pid=None, is_idle=True)
    assert idle_seg.duration == 3
    assert idle_seg.is_idle
    assert idle_seg.pid is None


def test_memory_operation_input_validation():
    from oscope_gui.models.memory import MemoryOperationInput, MemoryOperationType

    # Valid allocate
    op_alloc = MemoryOperationInput(op_type=MemoryOperationType.ALLOCATE, request_id=1, size=200, process_id=1)
    assert op_alloc.validate() is None

    # Invalid negative/zero request_id
    op_bad_id = MemoryOperationInput(op_type=MemoryOperationType.ALLOCATE, request_id=0, size=200, process_id=1)
    assert op_bad_id.validate() is not None
    assert "positive integer" in op_bad_id.validate()

    # Invalid size <= 0
    op_zero_size = MemoryOperationInput(op_type=MemoryOperationType.ALLOCATE, request_id=1, size=0, process_id=1)
    assert op_zero_size.validate() is not None
    assert "positive (> 0)" in op_zero_size.validate()

    # Invalid negative PID
    op_bad_pid = MemoryOperationInput(op_type=MemoryOperationType.ALLOCATE, request_id=1, size=100, process_id=-5)
    assert op_bad_pid.validate() is not None
    assert "non-negative" in op_bad_pid.validate()

    # Valid deallocate (size and process_id not required)
    op_dealloc = MemoryOperationInput(op_type=MemoryOperationType.DEALLOCATE, request_id=1)
    assert op_dealloc.validate() is None


def test_memory_config_validation():
    from oscope_gui.models.memory import MemoryConfig, MemoryStrategy

    cfg_valid = MemoryConfig(strategy=MemoryStrategy.FIRST_FIT, total_memory=1000)
    assert cfg_valid.validate() is None

    cfg_invalid = MemoryConfig(strategy=MemoryStrategy.BEST_FIT, total_memory=0)
    assert cfg_invalid.validate() is not None
    assert "positive (> 0)" in cfg_invalid.validate()


def test_memory_block_and_metrics_properties():
    from oscope_gui.models.memory import MemoryBlockModel, MemoryMetricsModel

    block = MemoryBlockModel(block_index=0, start_address=100, size=250, is_allocated=True, allocation_id=1, process_id=2)
    assert block.end_address == 350

    metrics = MemoryMetricsModel(
        total_memory=1000,
        allocated_memory=400,
        free_memory=600,
        largest_free_block=300,
        external_fragmentation=0.5,
    )
    assert metrics.utilization_percentage == 40.0


def test_paging_models_validation_and_properties():
    from oscope_gui.models.paging import (
        PagingAlgorithm,
        PagingConfig,
        PagingMetricsModel,
        PagingStepModel,
    )

    # Valid config
    cfg_valid = PagingConfig(
        algorithm=PagingAlgorithm.FIFO,
        frame_count=3,
        reference_string=[7, 0, 1, 2, 0, 3],
    )
    assert cfg_valid.validate() is None

    # Invalid frame count
    cfg_bad_frames = PagingConfig(
        algorithm=PagingAlgorithm.LRU,
        frame_count=0,
        reference_string=[1, 2],
    )
    assert cfg_bad_frames.validate() is not None
    assert "positive integer" in cfg_bad_frames.validate()

    # Empty reference string
    cfg_empty_ref = PagingConfig(
        algorithm=PagingAlgorithm.OPTIMAL,
        frame_count=3,
        reference_string=[],
    )
    assert cfg_empty_ref.validate() is not None
    assert "empty" in cfg_empty_ref.validate()

    # Negative page in reference string
    cfg_neg_page = PagingConfig(
        algorithm=PagingAlgorithm.FIFO,
        frame_count=3,
        reference_string=[1, -4, 2],
    )
    assert cfg_neg_page.validate() is not None
    assert "non-negative" in cfg_neg_page.validate()

    # Metrics percentages and rates
    metrics = PagingMetricsModel(
        total_references=10,
        page_faults=7,
        page_hits=3,
        fault_rate=0.70,
        hit_rate=0.30,
    )
    assert pytest.approx(metrics.fault_percentage, 0.1) == 70.0
    assert pytest.approx(metrics.hit_percentage, 0.1) == 30.0

    # Step model properties
    step = PagingStepModel(step_number=1, page=7, is_fault=True, frames=[7, -1, -1])
    assert step.result_str == "Fault"
    hit_step = PagingStepModel(step_number=2, page=7, is_fault=False, frames=[7, -1, -1])
    assert hit_step.result_str == "Hit"


def test_deadlock_models_validation_and_properties():
    from oscope_gui.models.deadlock import (
        DeadlockConfig,
        DeadlockDetectionResultModel,
        DeadlockMode,
        DeadlockRequestResultModel,
        DeadlockSafetyResultModel,
    )

    # Valid textbook config
    cfg_valid = DeadlockConfig(
        mode=DeadlockMode.SAFETY,
        num_processes=3,
        num_resources=2,
        available=[1, 1],
        allocation=[[1, 0], [0, 1], [1, 1]],
        max_claim=[[2, 1], [1, 1], [1, 2]],
    )
    assert cfg_valid.validate() is None
    need = cfg_valid.compute_need()
    assert need == [[1, 1], [1, 0], [0, 1]]

    # Allocation exceeds Max
    cfg_bad_alloc = DeadlockConfig(
        mode=DeadlockMode.SAFETY,
        num_processes=2,
        num_resources=1,
        available=[1],
        allocation=[[5], [0]],
        max_claim=[[3], [1]],
    )
    assert cfg_bad_alloc.validate() is not None
    assert "exceeds Maximum Claim" in cfg_bad_alloc.validate()

    # Negative available
    cfg_bad_avail = DeadlockConfig(
        mode=DeadlockMode.SAFETY,
        num_processes=2,
        num_resources=1,
        available=[-1],
        allocation=[[0], [0]],
        max_claim=[[1], [1]],
    )
    assert cfg_bad_avail.validate() is not None
    assert "cannot be negative" in cfg_bad_avail.validate()

    # Resource Request validation
    cfg_req_valid = DeadlockConfig(
        mode=DeadlockMode.RESOURCE_REQUEST,
        num_processes=3,
        num_resources=2,
        available=[2, 2],
        allocation=[[1, 0], [0, 1], [1, 1]],
        max_claim=[[2, 1], [1, 1], [1, 2]],
        requesting_process_id=0,
        request_vector=[1, 0],
    )
    assert cfg_req_valid.validate() is None

    # Invalid process ID for request
    cfg_req_bad_p = DeadlockConfig(
        mode=DeadlockMode.RESOURCE_REQUEST,
        num_processes=3,
        num_resources=2,
        available=[2, 2],
        allocation=[[1, 0], [0, 1], [1, 1]],
        max_claim=[[2, 1], [1, 1], [1, 2]],
        requesting_process_id=5,
        request_vector=[1, 0],
    )
    assert cfg_req_bad_p.validate() is not None
    assert "between 0 and 2" in cfg_req_bad_p.validate()

    # Detection validation
    cfg_det_valid = DeadlockConfig(
        mode=DeadlockMode.DETECTION,
        num_processes=2,
        num_resources=1,
        available=[0],
        allocation=[[1], [1]],
        request_matrix=[[1], [1]],
    )
    assert cfg_det_valid.validate() is None

    # Result Model properties
    safe_res = DeadlockSafetyResultModel(
        is_safe=True,
        safe_sequence=[1, 0, 2],
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
    assert safe_res.safe_sequence_str == "P1 -> P0 -> P2"
    assert safe_res.blocked_str == "None"

    unsafe_res = DeadlockSafetyResultModel(
        is_safe=False,
        safe_sequence=[],
        blocked_processes=[0, 1],
        message="Unsafe",
        num_processes=2,
        num_resources=1,
        available=[0],
        allocation=[[1], [1]],
        max_claim=[[2], [2]],
        need=[[1], [1]],
        raw_output="",
    )
    assert unsafe_res.safe_sequence_str == "None"
    assert unsafe_res.blocked_str == "P0, P1"



