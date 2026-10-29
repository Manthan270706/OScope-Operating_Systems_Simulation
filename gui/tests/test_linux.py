"""Unit and integration tests for Linux / POSIX IPC and Synchronization module."""

import json
import os
import pytest

os.environ["QT_QPA_PLATFORM"] = "offscreen"

from oscope_gui.backend.parser import (
    generate_linux_experiments_stdin,
    parse_linux_experiments_output,
)
from oscope_gui.models.linux_experiments import (
    FifoIpcResultModel,
    LinuxExperimentCategory,
    LinuxExperimentsResultModel,
    MessageQueueIpcResultModel,
    MutexSyncResultModel,
    OrphanResultModel,
    PetersonResultModel,
    PipeIpcResultModel,
    PosixSemaphoreResultModel,
    ProcessExecResultModel,
    ProducerConsumerResultModel,
    SharedMemoryIpcResultModel,
    ThreadCreationResultModel,
    ZombieResultModel,
)


class DummyLinuxBackendRunner:
    def __init__(self, sample_stdout="", exit_code=0):
        self.sample_stdout = sample_stdout
        self.exit_code = exit_code
        self.last_args = None
        self.last_stdin = None

    def execute(self, args, stdin_data=None, timeout=25.0):
        from oscope_gui.backend.runner import ExecutionResult

        self.last_args = args
        self.last_stdin = stdin_data
        return ExecutionResult(
            exit_code=self.exit_code,
            stdout=self.sample_stdout,
            stderr="" if self.exit_code == 0 else "Simulation failed",
            duration=0.25,
            is_timeout=False,
            command=["build/oscope"] + args,
        )

    def verify(self):
        return True, "Linux engine ready"

    def get_info(self):
        from oscope_gui.backend.runner import BackendInfo

        return BackendInfo(
            runner_type="wsl",
            executable_path="build/oscope",
            is_available=True,
            status_message="Linux engine available",
        )

    def cancel(self):
        pass


SAMPLE_JSON_BACKEND_OUTPUT = json.dumps([
    {
        "experiment": "process_exec",
        "result": {
            "child_pid": 1201,
            "program_executed": "/bin/echo",
            "image_replaced": True,
            "captured_output": "Hello from POSIX execve",
            "child_exit_code": 0,
            "details": "Image successfully replaced",
        },
        "success": True,
    },
    {
        "experiment": "zombie_demonstration",
        "result": {
            "child_pid": 1202,
            "observed_state": "Z",
            "zombie_observed": True,
            "reaped_successfully": True,
            "details": "Child reaped cleanly via waitpid",
        },
        "success": True,
    },
    {
        "experiment": "orphan_demonstration",
        "result": {
            "child_pid": 1204,
            "initial_parent_pid": 1203,
            "adopted_parent_pid": 1,
            "reparented_to_init_or_subreaper": True,
            "details": "Reparented to systemd/init",
        },
        "success": True,
    },
    {
        "experiment": "thread_creation",
        "result": {
            "requested_threads": 4,
            "started_threads": 4,
            "completed_threads": 4,
            "worker_results": [1, 2, 3, 4],
        },
        "success": True,
    },
    {
        "experiment": "thread_synchronization",
        "result": {
            "num_threads": 4,
            "iterations_per_thread": 10000,
            "threads_completed": 4,
            "expected_counter": 40000,
            "actual_counter": 40000,
        },
        "success": True,
    },
    {
        "experiment": "posix_semaphore",
        "result": {
            "num_threads": 4,
            "iterations_per_thread": 5000,
            "threads_completed": 4,
            "expected_counter": 20000,
            "actual_counter": 20000,
            "initial_value": 1,
            "counter_match": True,
        },
        "success": True,
    },
    {
        "experiment": "petersons_algorithm",
        "result": {
            "mutual_exclusion_maintained": True,
            "p0_critical_entries": 2,
            "p1_critical_entries": 2,
            "total_steps": 26,
            "explanation": "Memory barriers guarantee order",
        },
        "success": True,
    },
    {
        "experiment": "producer_consumer",
        "result": {
            "buffer_capacity": 5,
            "total_items": 50,
            "num_producers": 2,
            "num_consumers": 2,
            "items_produced": 50,
            "items_consumed": 50,
            "items_preserved": True,
            "max_buffer_occupancy_observed": 5,
        },
        "success": True,
    },
    {
        "experiment": "pipe_ipc",
        "result": {
            "parent_pid": 1200,
            "child_pid": 1205,
            "child_exit_code": 0,
            "sent_message": "Hello pipe",
            "received_message": "Hello pipe",
        },
        "success": True,
    },
    {
        "experiment": "fifo_ipc",
        "result": {
            "fifo_path": "/tmp/oscope_fifo_test",
            "message_sent": "Hello FIFO",
            "message_received": "Hello FIFO",
            "details": "FIFO unlinked",
        },
        "success": True,
    },
    {
        "experiment": "shared_memory_ipc",
        "result": {
            "segment_name": "/oscope_shm_test",
            "size_bytes": 4096,
            "message_written": "Shared Memory Payload",
            "message_read": "Shared Memory Payload",
            "details": "SHM unlinked",
        },
        "success": True,
    },
    {
        "experiment": "message_queue_ipc",
        "result": {
            "queue_name": "/oscope_mq_test",
            "messages_sent": 5,
            "messages_received": 5,
            "message_content": "MQ Payload",
            "details": "MQ closed",
        },
        "success": True,
    },
])


SAMPLE_TEXT_BACKEND_OUTPUT = """
=== OScope Linux Experiments Demo ===
Child PID: 1411
Image Replaced: YES
Captured Output: Hello from POSIX execve
Exit Code: 0

Zombie Process Demonstration:
Child PID: 1412
Observed /proc State: 'Z'
Reaped by Parent: SUCCESS cleanly via waitpid

Orphan Process Demonstration:
Child PID: 1414
Original Parent: PID 1410
Adopted Parent: PID 1

Thread Synchronization Demo:
Concurrent Threads: 4
Iterations Per Thread: 10000
Expected Counter: 40000
Actual Counter: 40000

POSIX Semaphore Synchronization:
Threads: 4
Expected Counter: 20000
Actual Counter: 20000

Producer-Consumer Bounded Buffer Simulation:
Buffer Capacity: 5
Items Produced: 50
Items Consumed: 50

Pipe-based IPC:
Parent PID: 1410
Child PID: 1415
Sent Message: "Hello pipe"
Received Message: "Hello pipe"

POSIX Named Pipe (FIFO):
FIFO Path: /tmp/oscope_fifo_test
Message Sent: "Hello FIFO"
Message Received: "Hello FIFO"

POSIX Shared Memory:
Segment Name: /oscope_shm_test
Message Written: "SHM Payload"
Message Read: "SHM Payload"

POSIX Message Queue:
Queue Name: /oscope_mq_test
Messages Sent: 5
Messages Received: 5
Payload: "MQ Payload"
"""


def test_linux_models():
    """Verify all Linux dataclasses instantiate properly."""
    f_res = ProcessExecResultModel(child_pid=11, program_executed="/bin/echo", child_exit_code=0)
    assert f_res.child_pid == 11
    assert f_res.program_executed == "/bin/echo"

    z_res = ZombieResultModel(child_pid=12, observed_state="Z", reaped_successfully=True)
    assert z_res.reaped_successfully is True

    o_res = OrphanResultModel(initial_parent_pid=10, child_pid=13, adopted_parent_pid=1)
    assert o_res.adopted_parent_pid == 1

    pc_res = ProducerConsumerResultModel(
        buffer_capacity=5,
        total_items=50,
        items_produced=50,
        items_consumed=50,
        num_producers=2,
        num_consumers=2,
        items_preserved=True,
    )
    assert pc_res.items_preserved is True

    mq_res = MessageQueueIpcResultModel(
        queue_name="/test_mq",
        messages_sent=5,
        messages_received=5,
        message_content="Test message",
    )
    assert mq_res.messages_sent == 5


def test_linux_stdin_generation():
    """Verify stdin generator outputs expected menu sequences."""
    stdin_all = generate_linux_experiments_stdin(LinuxExperimentCategory.ALL)
    assert "10\n" in stdin_all
    assert "1\n" in stdin_all
    assert "2\n" in stdin_all
    assert "3\n" in stdin_all
    assert "4\n" in stdin_all
    assert "5\n13\n" in stdin_all

    stdin_life = generate_linux_experiments_stdin(LinuxExperimentCategory.LIFECYCLE)
    assert "10\n" in stdin_life
    assert "1\n" in stdin_life
    assert "5\n13\n" in stdin_life


def test_linux_parser_json():
    """Verify parsing C++ --json output."""
    parsed = parse_linux_experiments_output(
        SAMPLE_JSON_BACKEND_OUTPUT,
        category=LinuxExperimentCategory.ALL,
    )
    assert parsed.category == LinuxExperimentCategory.ALL

    # Lifecycle
    assert parsed.process_exec is not None
    assert parsed.process_exec.child_pid == 1201
    assert parsed.zombie_demo is not None
    assert parsed.zombie_demo.reaped_successfully is True
    assert parsed.orphan_demo is not None
    assert parsed.orphan_demo.adopted_parent_pid == 1

    # Sync
    assert parsed.mutex_sync is not None
    assert parsed.mutex_sync.actual_counter == 40000
    assert parsed.posix_semaphore is not None
    assert parsed.posix_semaphore.actual_counter == 20000
    assert parsed.petersons_algo is not None
    assert parsed.petersons_algo.mutual_exclusion_maintained is True

    # Producer-Consumer
    assert parsed.producer_consumer is not None
    assert parsed.producer_consumer.items_produced == 50
    assert parsed.producer_consumer.items_preserved is True

    # IPC
    assert parsed.pipe_ipc is not None
    assert parsed.pipe_ipc.received_message == "Hello pipe"
    assert parsed.fifo_ipc is not None
    assert parsed.fifo_ipc.message_received == "Hello FIFO"
    assert parsed.shared_memory_ipc is not None
    assert parsed.shared_memory_ipc.size_bytes == 4096
    assert parsed.message_queue_ipc is not None
    assert parsed.message_queue_ipc.messages_sent == 5


def test_linux_parser_text_fallback():
    """Verify fallback text parsing from terminal output."""
    parsed = parse_linux_experiments_output(
        SAMPLE_TEXT_BACKEND_OUTPUT,
        category=LinuxExperimentCategory.ALL,
    )
    assert parsed.process_exec is not None
    assert parsed.process_exec.child_pid == 1411
    assert parsed.zombie_demo is not None
    assert parsed.zombie_demo.reaped_successfully is True

    assert parsed.mutex_sync is not None
    assert parsed.mutex_sync.actual_counter == 40000

    assert parsed.producer_consumer is not None
    assert parsed.producer_consumer.items_produced == 50

    assert parsed.pipe_ipc is not None
    assert parsed.pipe_ipc.received_message == "Hello pipe"
    assert parsed.shared_memory_ipc is not None
    assert parsed.shared_memory_ipc.segment_name == "/oscope_shm_test"


def test_linux_widgets(qapp):
    """Verify all visualizer widgets can be instantiated and populated."""
    from oscope_gui.widgets.linux_viz import (
        IpcChannelsWidget,
        ProcessLifecycleTreeWidget,
        ProducerConsumerBufferWidget,
        SyncVisualizationWidget,
    )

    # 1. Lifecycle Tree Widget
    w_life = ProcessLifecycleTreeWidget()
    assert w_life is not None
    w_life.set_results(
        exec_res=ProcessExecResultModel(child_pid=101, program_executed="/bin/echo", child_exit_code=0),
        zombie_res=ZombieResultModel(child_pid=102, observed_state="Z", reaped_successfully=True),
        orphan_res=OrphanResultModel(initial_parent_pid=100, child_pid=103, adopted_parent_pid=1),
    )

    # 2. Sync Widget
    w_sync = SyncVisualizationWidget()
    assert w_sync is not None
    w_sync.set_results(
        mutex_res=MutexSyncResultModel(num_threads=4, iterations_per_thread=10000, expected_counter=40000, actual_counter=40000),
        sem_res=PosixSemaphoreResultModel(num_threads=4, iterations_per_thread=5000, expected_counter=20000, actual_counter=20000),
        peterson_res=PetersonResultModel(mutual_exclusion_maintained=True, p0_critical_entries=2, p1_critical_entries=2, total_steps=26),
    )

    # 3. Producer Consumer Widget
    w_pc = ProducerConsumerBufferWidget()
    assert w_pc is not None
    w_pc.set_result(ProducerConsumerResultModel(
        buffer_capacity=5,
        total_items=50,
        items_produced=50,
        items_consumed=50,
        num_producers=2,
        num_consumers=2,
        items_preserved=True,
        max_buffer_occupancy_observed=5,
    ))

    # 4. IPC Channels Widget
    w_ipc = IpcChannelsWidget()
    assert w_ipc is not None
    w_ipc.set_results(
        pipe_res=PipeIpcResultModel(parent_pid=100, child_pid=101, sent_message="Test", received_message="Test"),
        fifo_res=FifoIpcResultModel(fifo_path="/tmp/f", message_sent="Test", message_received="Test"),
        shm_res=SharedMemoryIpcResultModel(segment_name="/shm", size_bytes=4096, message_written="SHM", message_read="SHM"),
        mq_res=MessageQueueIpcResultModel(queue_name="/mq", messages_sent=5, messages_received=5, message_content="MQ"),
    )


def test_linux_page_execution(qapp):
    """Verify LinuxExperimentsPage runs worker, updates UI, and switches tabs."""
    from oscope_gui.pages.linux_page import LinuxExperimentsPage

    runner = DummyLinuxBackendRunner(sample_stdout=SAMPLE_JSON_BACKEND_OUTPUT, exit_code=0)
    page = LinuxExperimentsPage(runner=runner)

    assert page.btn_run_all.isEnabled()
    assert page.btn_cancel.isEnabled() is False

    # Run All
    page.run_category(LinuxExperimentCategory.ALL)
    assert page._active_worker is not None
    page._active_worker.wait(2000)
    qapp.processEvents()

    assert page._last_result is not None
    assert page._last_result.process_exec is not None
    assert page._last_result.mutex_sync is not None
    assert page._last_result.producer_consumer is not None
    assert page._last_result.pipe_ipc is not None

    # Check that tabs and diagnostics updated
    assert "Child PID 1201" in page.lifecycle_widget.lbl_exec_flow.text()
    assert "Simulation completed successfully" in page.runner_status_label.text()

    # Test individual category run
    page.run_category(LinuxExperimentCategory.LIFECYCLE)
    page._active_worker.wait(2000)
    qapp.processEvents()
    assert page.tabs_container.currentIndex() == 0  # Process Lifecycle tab
