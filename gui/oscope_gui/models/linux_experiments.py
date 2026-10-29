"""Data models for Linux / POSIX System Experiments & Process Synchronization."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class LinuxExperimentCategory(str, Enum):
    """Categories of Linux / POSIX experiments supported by the C++ backend."""
    ALL = "all"
    LIFECYCLE = "lifecycle"
    SYNCHRONIZATION = "sync"
    PRODUCER_CONSUMER = "producer_consumer"
    IPC = "ipc"

    @property
    def cli_flag(self) -> str:
        """Map category to C++ CLI demo flag."""
        mapping = {
            LinuxExperimentCategory.ALL: "--demo-all",
            LinuxExperimentCategory.LIFECYCLE: "--demo-lifecycle",
            LinuxExperimentCategory.SYNCHRONIZATION: "--demo-sync",
            LinuxExperimentCategory.PRODUCER_CONSUMER: "--demo-sync",
            LinuxExperimentCategory.IPC: "--demo-ipc",
        }
        return mapping[self]

    @property
    def display_name(self) -> str:
        names = {
            LinuxExperimentCategory.ALL: "All Linux / POSIX Experiments",
            LinuxExperimentCategory.LIFECYCLE: "Process Lifecycle (Fork, Exec, Zombie, Orphan)",
            LinuxExperimentCategory.SYNCHRONIZATION: "Thread Synchronization & Semaphores",
            LinuxExperimentCategory.PRODUCER_CONSUMER: "Classical Producer-Consumer Bounded-Buffer",
            LinuxExperimentCategory.IPC: "Inter-Process Communication (Pipes, FIFO, SHM, MQ)",
        }
        return names[self]


@dataclass
class ProcessExecResultModel:
    """Represents a POSIX fork() + exec*() process image replacement experiment."""
    child_pid: int = 0
    program_executed: str = "/bin/echo"
    image_replaced: bool = True
    captured_output: str = ""
    child_exit_code: int = 0
    details: str = ""
    success: bool = True


@dataclass
class ZombieResultModel:
    """Represents a child process entering 'Z' (Zombie) state and parent waitpid() reaping."""
    child_pid: int = 0
    observed_state: str = "Z"
    zombie_observed: bool = True
    reaped_successfully: bool = True
    details: str = ""
    success: bool = True


@dataclass
class OrphanResultModel:
    """Represents an orphan child process adopted by init/systemd/subreaper."""
    child_pid: int = 0
    initial_parent_pid: int = 0
    adopted_parent_pid: int = 1
    reparented_to_init_or_subreaper: bool = True
    details: str = ""
    success: bool = True


@dataclass
class ThreadCreationResultModel:
    """Represents multithreaded worker creation and joining."""
    requested_threads: int = 4
    started_threads: int = 4
    completed_threads: int = 4
    worker_results: List[int] = field(default_factory=list)
    success: bool = True


@dataclass
class MutexSyncResultModel:
    """Represents concurrent threads updating a shared counter under std::mutex protection."""
    num_threads: int = 4
    iterations_per_thread: int = 10000
    threads_completed: int = 4
    expected_counter: int = 40000
    actual_counter: int = 40000
    success: bool = True

    @property
    def race_condition_detected(self) -> bool:
        return self.expected_counter != self.actual_counter


@dataclass
class PosixSemaphoreResultModel:
    """Represents POSIX unnamed semaphore synchronization across concurrent threads."""
    num_threads: int = 4
    iterations_per_thread: int = 5000
    threads_completed: int = 4
    expected_counter: int = 20000
    actual_counter: int = 20000
    initial_value: int = 1
    counter_match: bool = True
    success: bool = True


@dataclass
class PetersonResultModel:
    """Represents Peterson's two-process mutual exclusion guarantee."""
    mutual_exclusion_maintained: bool = True
    p0_critical_entries: int = 2
    p1_critical_entries: int = 2
    total_steps: int = 26
    explanation: str = ""
    success: bool = True


@dataclass
class ProducerConsumerResultModel:
    """Represents classical bounded-buffer producer-consumer synchronization."""
    buffer_capacity: int = 5
    total_items: int = 50
    num_producers: int = 2
    num_consumers: int = 2
    items_produced: int = 50
    items_consumed: int = 50
    items_preserved: bool = True
    max_buffer_occupancy_observed: int = 5
    success: bool = True


@dataclass
class PipeIpcResultModel:
    """Represents anonymous POSIX unidirectional pipe IPC (Child -> Parent)."""
    parent_pid: int = 0
    child_pid: int = 0
    child_exit_code: int = 0
    sent_message: str = ""
    received_message: str = ""
    success: bool = True


@dataclass
class FifoIpcResultModel:
    """Represents POSIX named pipe (FIFO) communication with filesystem cleanup."""
    fifo_path: str = ""
    message_sent: str = ""
    message_received: str = ""
    details: str = ""
    success: bool = True


@dataclass
class SharedMemoryIpcResultModel:
    """Represents POSIX shared memory (shm_open / ftruncate / mmap / munmap / shm_unlink)."""
    segment_name: str = ""
    size_bytes: int = 4096
    message_written: str = ""
    message_read: str = ""
    details: str = ""
    success: bool = True


@dataclass
class MessageQueueIpcResultModel:
    """Represents POSIX message queue (mq_open / mq_send / mq_receive / mq_unlink)."""
    queue_name: str = ""
    messages_sent: int = 1
    messages_received: int = 1
    message_content: str = ""
    details: str = ""
    success: bool = True


@dataclass
class LinuxExperimentsResultModel:
    """Consolidated outcome of executing Linux / POSIX system experiments."""
    category: LinuxExperimentCategory = LinuxExperimentCategory.ALL
    timestamp: str = ""
    exit_code: int = 0
    execution_duration_ms: float = 0.0

    # Process Lifecycle
    process_exec: Optional[ProcessExecResultModel] = None
    zombie_demo: Optional[ZombieResultModel] = None
    orphan_demo: Optional[OrphanResultModel] = None

    # Synchronization
    thread_creation: Optional[ThreadCreationResultModel] = None
    mutex_sync: Optional[MutexSyncResultModel] = None
    posix_semaphore: Optional[PosixSemaphoreResultModel] = None
    petersons_algo: Optional[PetersonResultModel] = None

    # Producer-Consumer
    producer_consumer: Optional[ProducerConsumerResultModel] = None

    # IPC
    pipe_ipc: Optional[PipeIpcResultModel] = None
    fifo_ipc: Optional[FifoIpcResultModel] = None
    shared_memory_ipc: Optional[SharedMemoryIpcResultModel] = None
    message_queue_ipc: Optional[MessageQueueIpcResultModel] = None

    raw_output: str = ""
    raw_json: Optional[List[Dict[str, Any]]] = None
    success: bool = True
    error_message: Optional[str] = None
