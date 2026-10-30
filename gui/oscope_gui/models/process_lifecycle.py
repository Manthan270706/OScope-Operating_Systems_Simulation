"""Data models for Process Lifecycle State Machine simulation."""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Tuple


class ProcessLifecycleState(str, Enum):
    """Educational lifecycle states supported by authoritative C++ ProcessManager."""

    NEW = "New"
    READY = "Ready"
    RUNNING = "Running"
    WAITING = "Waiting"
    TERMINATED = "Terminated"

    @property
    def description(self) -> str:
        if self == ProcessLifecycleState.NEW:
            return "The process is being created and its Process Control Block (PCB) is initialized."
        elif self == ProcessLifecycleState.READY:
            return "The process is loaded into memory and waiting to be assigned to the CPU core."
        elif self == ProcessLifecycleState.RUNNING:
            return "Instructions are currently executing on the CPU core."
        elif self == ProcessLifecycleState.WAITING:
            return "The process is blocked waiting for an I/O completion or signal event."
        else:
            return "The process has finished execution and its resources are reaped by the OS kernel."


@dataclass
class ProcessInstanceModel:
    """Represents a simulated process in the process table."""

    pid: int
    arrival_time: int
    burst_time: int
    priority: int = 1
    state: str = "New"

    @property
    def current_state(self) -> ProcessLifecycleState:
        try:
            return ProcessLifecycleState(self.state)
        except ValueError:
            return ProcessLifecycleState.NEW


@dataclass
class ProcessTransitionModel:
    """Record of a requested lifecycle transition and its backend validation outcome."""

    pid: int
    from_state: str
    requested_state: str
    success: bool
    to_state: str
    message: str = ""
    action: str = ""
    process_id: Optional[int] = None

    def __post_init__(self) -> None:
        if self.process_id is None:
            self.process_id = self.pid
        if not self.action:
            self.action = self._derive_action()

    def _derive_action(self) -> str:
        if not self.success:
            return "reject"
        f = (self.from_state or "").lower()
        t = (self.to_state or self.requested_state or "").lower()
        if f == "none" and t == "new":
            return "create"
        if f == "new" and t == "ready":
            return "admit"
        if f == "ready" and t == "running":
            return "dispatch"
        if f == "running" and t == "ready":
            return "interrupt"
        if f == "running" and t == "waiting":
            return "wait"
        if f == "waiting" and t == "ready":
            return "wakeup"
        if f == "running" and t == "terminated":
            return "exit"
        if t == "terminated":
            return "exit"
        return "transition"

    @property
    def detail(self) -> str:
        return self.message

    @property
    def resulting_state(self) -> str:
        return self.to_state


@dataclass
class ProcessLifecycleSimulationResultModel:
    """Aggregated result returned from authoritative C++ ProcessManager execution."""

    total_processes: int = 0
    processes: List[ProcessInstanceModel] = field(default_factory=list)
    transitions: List[ProcessTransitionModel] = field(default_factory=list)
    logs: List[str] = field(default_factory=list)


@dataclass
class ProcessLifecycleConfig:
    """Configuration passed from GUI to backend execution."""

    mode: str = "demo"  # "demo", "preset", or "interactive"
    # List of operations: ("create", pid, arrival, burst, priority) or ("transition", pid, target_state)
    operations: List[Tuple] = field(default_factory=list)

    def validate(self) -> Tuple[bool, Optional[str]]:
        if self.mode in ("demo", "preset"):
            return True, None
        if self.mode in ("interactive", "custom"):
            if not self.operations:
                return False, "No operations provided for interactive state machine simulation."
            for op in self.operations:
                if not op or len(op) < 2:
                    return False, "Malformed operation tuple in config."
                cmd = op[0]
                if cmd not in ("create", "transition", "clear"):
                    return False, f"Unknown operation command '{cmd}'."
                if cmd == "create":
                    if len(op) < 4:
                        return False, f"create requires (pid, arrival, burst), got {op}."
                    pid, arr, burst = op[1], op[2], op[3]
                    if pid <= 0 or arr < 0 or burst <= 0:
                        return False, f"Invalid process attributes: pid={pid}, arrival={arr}, burst={burst}."
                elif cmd == "transition":
                    if len(op) < 3:
                        return False, f"transition requires (pid, target_state), got {op}."
            return True, None
        return False, f"Unknown mode '{self.mode}'."
