"""Data models for Secondary Storage Disk Scheduling simulation."""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


class DiskAlgorithm(str, Enum):
    """Supported disk arm scheduling algorithms."""
    FCFS = "FCFS"
    SSTF = "SSTF"
    SCAN = "SCAN"
    CSCAN = "C-SCAN"
    LOOK = "LOOK"
    CLOOK = "C-LOOK"
    LIFO = "LIFO"
    COMPARE_ALL = "Compare All"

    @property
    def menu_choice(self) -> int:
        """Map to C++ CLI sub-menu choice."""
        mapping = {
            DiskAlgorithm.FCFS: 1,
            DiskAlgorithm.SSTF: 2,
            DiskAlgorithm.SCAN: 3,
            DiskAlgorithm.CSCAN: 4,
            DiskAlgorithm.LOOK: 5,
            DiskAlgorithm.CLOOK: 6,
            DiskAlgorithm.LIFO: 7,
            DiskAlgorithm.COMPARE_ALL: 8,
        }
        return mapping[self]

    @property
    def display_name(self) -> str:
        """User-facing descriptive name matching backend."""
        names = {
            DiskAlgorithm.FCFS: "First-Come, First-Served (FCFS)",
            DiskAlgorithm.SSTF: "Shortest Seek Time First (SSTF)",
            DiskAlgorithm.SCAN: "SCAN (Elevator)",
            DiskAlgorithm.CSCAN: "Circular SCAN (C-SCAN)",
            DiskAlgorithm.LOOK: "LOOK",
            DiskAlgorithm.CLOOK: "Circular LOOK (C-LOOK)",
            DiskAlgorithm.LIFO: "Last-In, First-Out (LIFO)",
            DiskAlgorithm.COMPARE_ALL: "Compare All Disk Algorithms",
        }
        return names[self]

    @property
    def needs_direction(self) -> bool:
        """True if algorithm arm movement depends on initial direction."""
        return self in (
            DiskAlgorithm.SCAN,
            DiskAlgorithm.CSCAN,
            DiskAlgorithm.LOOK,
            DiskAlgorithm.CLOOK,
            DiskAlgorithm.COMPARE_ALL,
        )

    @property
    def cli_choice(self) -> str:
        """String representation of menu choice."""
        return str(self.menu_choice)

    @property
    def requires_direction(self) -> bool:
        """Alias for needs_direction."""
        return self.needs_direction

    @property
    def description(self) -> str:
        """Educational explanation of algorithm mechanics and boundary semantics."""
        if self == DiskAlgorithm.FCFS:
            return (
                "First-Come, First-Served (FCFS): Requests are serviced strictly in arrival order. "
                "Fair and completely starvation-free, but may induce excessive seek latency and arm thrashing across wide cylinder spans."
            )
        elif self == DiskAlgorithm.SSTF:
            return (
                "Shortest Seek Time First (SSTF): Greedily selects the pending request closest to the current head position. "
                "Substantially reduces overall seek time compared to FCFS, but distant requests may suffer from starvation under high queue loads."
            )
        elif self == DiskAlgorithm.SCAN:
            return (
                "SCAN (Elevator Algorithm): The disk arm moves in the specified direction servicing all requests until reaching the physical disk boundary "
                "(min or max cylinder), where it reverses direction and services requests on the return sweep."
            )
        elif self == DiskAlgorithm.CSCAN:
            return (
                "Circular SCAN (C-SCAN): Arm moves in the initial direction servicing requests up to the disk boundary. "
                "Upon reaching the boundary, it wraps around directly to the opposite disk boundary without servicing requests on the return trip, "
                "providing a more uniform waiting time distribution."
            )
        elif self == DiskAlgorithm.LOOK:
            return (
                "LOOK: Similar to SCAN, but the head travels only as far as the final pending request in the current direction. "
                "It reverses immediately without traveling to the unnecessary physical disk boundary, saving significant seek movement."
            )
        elif self == DiskAlgorithm.CLOOK:
            return (
                "Circular LOOK (C-LOOK): Similar to C-SCAN, but the head moves only to the highest (or lowest) requested cylinder, "
                "then immediately jumps directly to the lowest (or highest) requested cylinder without touching either physical disk boundary."
            )
        elif self == DiskAlgorithm.LIFO:
            return (
                "Last-In, First-Out (LIFO): Requests are serviced in reverse order of arrival (stack order). "
                "Maximizes locality for newly arriving requests in transaction processing, but risks severe starvation for older pending requests."
            )
        else:
            return (
                "Compare All: Evaluates all 7 disk scheduling algorithms on the exact same request sequence and cylinder range, "
                "highlighting total head travel, seek efficiency, and traversal differences."
            )


class DiskDirection(str, Enum):
    """Initial arm movement direction."""
    INCREASING = "Increasing"
    DECREASING = "Decreasing"

    @property
    def cli_value(self) -> int:
        """Map to C++ CLI direction choice (1=Increasing, 2=Decreasing)."""
        return 1 if self == DiskDirection.INCREASING else 2

    @property
    def display_name(self) -> str:
        if self == DiskDirection.INCREASING:
            return "Increasing (Higher cylinders / Up)"
        return "Decreasing (Lower cylinders / Down)"


@dataclass
class DiskConfig:
    """User-configured parameters for disk scheduling simulation."""
    algorithm: DiskAlgorithm = DiskAlgorithm.FCFS
    min_cylinder: int = 0
    max_cylinder: int = 199
    initial_head: int = 53
    direction: DiskDirection = DiskDirection.INCREASING
    requests: List[int] = field(default_factory=list)

    def validate(self) -> Optional[str]:
        if self.min_cylinder < 0:
            return f"Minimum cylinder cannot be negative (< 0), got {self.min_cylinder}."
        if self.max_cylinder <= self.min_cylinder:
            return (
                f"Maximum cylinder ({self.max_cylinder}) must be strictly greater than "
                f"minimum cylinder ({self.min_cylinder})."
            )
        if self.initial_head < self.min_cylinder or self.initial_head > self.max_cylinder:
            return (
                f"Initial head position ({self.initial_head}) must be within the disk range "
                f"[{self.min_cylinder}, {self.max_cylinder}]."
            )
        if not self.requests:
            return "Cylinder request queue cannot be empty. Please enter at least one cylinder number."

        for idx, req in enumerate(self.requests):
            if req < self.min_cylinder or req > self.max_cylinder:
                return (
                    f"Request #{idx + 1} cylinder ({req}) is out of disk range "
                    f"[{self.min_cylinder}, {self.max_cylinder}]."
                )
        return None


@dataclass
class DiskStepModel:
    """Represents a single head movement step in the disk arm trajectory."""
    step_number: int
    from_cylinder: int
    to_cylinder: int
    movement: int
    cumulative_movement: int
    is_request: bool
    is_boundary: bool
    is_wraparound: bool
    action_description: str

    @property
    def step_type_label(self) -> str:
        if self.is_wraparound:
            return "Circular Wraparound"
        elif self.is_boundary:
            return "Boundary Reversal"
        elif self.is_request:
            return "Request Serviced"
        return "Head Seek"

    @property
    def seek_distance(self) -> int:
        return self.movement

    @property
    def action_type(self) -> str:
        return self.step_type_label


@dataclass
class DiskSchedulingResultModel:
    """Structured result of executing a single disk scheduling algorithm."""
    algorithm: DiskAlgorithm
    algorithm_name: str
    serviced_requests: List[int]
    head_path: List[int]
    total_head_movement: int
    wraparound_movement: int = 0
    average_head_movement: float = 0.0
    initial_head_position: int = 0
    final_head_position: int = 0
    message: str = ""
    steps: List[DiskStepModel] = field(default_factory=list)
    raw_output: str = ""

    @property
    def request_count(self) -> int:
        return len(self.serviced_requests)

    @property
    def average_seek(self) -> float:
        return self.average_head_movement

    @property
    def service_order(self) -> List[int]:
        return self.head_path


@dataclass
class DiskComparisonEntryModel:
    """Summary metrics for one algorithm inside a comparison run."""
    algorithm_name: str
    total_head_movement: int
    average_head_movement: float
    final_head_position: int
    wraparound_movement: int = 0
    serviced_requests: List[int] = field(default_factory=list)
    head_path: List[int] = field(default_factory=list)
    improvement_vs_fcfs: float = 0.0

    @property
    def average_seek(self) -> float:
        return self.average_head_movement


@dataclass
class DiskComparisonResultModel:
    """Result of running all disk scheduling algorithms on the same workload."""
    original_requests: List[int]
    min_cylinder: int
    max_cylinder: int
    initial_head: int
    direction: str
    entries: List[DiskComparisonEntryModel] = field(default_factory=list)
    raw_output: str = ""

    @property
    def workload_size(self) -> int:
        return len(self.original_requests)

    @property
    def best_algorithm(self) -> str:
        if not self.entries:
            return "N/A"
        best_entry = min(self.entries, key=lambda e: e.total_head_movement)
        return best_entry.algorithm_name

