"""Data models for Deadlock Management, Banker's Algorithm, and Deadlock Detection."""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


class DeadlockMode(Enum):
    """Analysis modes supported by the C++ oscope deadlock module."""

    SAFETY = "safety"
    RESOURCE_REQUEST = "request"
    DETECTION = "detection"

    @property
    def display_name(self) -> str:
        if self == DeadlockMode.SAFETY:
            return "Banker's Safety Algorithm"
        elif self == DeadlockMode.RESOURCE_REQUEST:
            return "Simulate Resource Request"
        elif self == DeadlockMode.DETECTION:
            return "Deadlock Detection Algorithm"
        return self.value

    @property
    def cli_choice(self) -> int:
        if self == DeadlockMode.SAFETY:
            return 1
        elif self == DeadlockMode.RESOURCE_REQUEST:
            return 2
        elif self == DeadlockMode.DETECTION:
            return 3
        return 1


@dataclass
class DeadlockConfig:
    """Configuration for a deadlock analysis execution."""

    mode: DeadlockMode = DeadlockMode.SAFETY
    num_processes: int = 5
    num_resources: int = 3
    available: List[int] = field(default_factory=lambda: [3, 3, 2])
    allocation: List[List[int]] = field(
        default_factory=lambda: [
            [0, 1, 0],
            [2, 0, 0],
            [3, 0, 2],
            [2, 1, 1],
            [0, 0, 2],
        ]
    )
    max_claim: List[List[int]] = field(
        default_factory=lambda: [
            [7, 5, 3],
            [3, 2, 2],
            [9, 0, 2],
            [2, 2, 2],
            [4, 3, 3],
        ]
    )
    request_matrix: List[List[int]] = field(
        default_factory=lambda: [
            [0, 0, 0],
            [2, 0, 2],
            [0, 0, 1],
            [1, 0, 0],
            [0, 0, 2],
        ]
    )
    requesting_process_id: int = 0
    request_vector: List[int] = field(default_factory=lambda: [1, 0, 2])

    def compute_need(self) -> List[List[int]]:
        """Compute Need matrix = Max - Allocation for each cell."""
        need: List[List[int]] = []
        for i in range(self.num_processes):
            row: List[int] = []
            for j in range(self.num_resources):
                max_val = self.max_claim[i][j] if i < len(self.max_claim) and j < len(self.max_claim[i]) else 0
                alloc_val = self.allocation[i][j] if i < len(self.allocation) and j < len(self.allocation[i]) else 0
                row.append(max(0, max_val - alloc_val))
            need.append(row)
        return need

    def validate(self) -> Optional[str]:
        """Validate dimensions, nonnegative bounds, and consistency."""
        if self.num_processes <= 0:
            return "Number of processes must be a positive integer (> 0)."
        if self.num_resources <= 0:
            return "Number of resource types must be a positive integer (> 0)."

        if len(self.available) != self.num_resources:
            return f"Available vector length ({len(self.available)}) does not match resource count ({self.num_resources})."
        for j, val in enumerate(self.available):
            if val < 0:
                return f"Available resource R{j} cannot be negative ({val})."

        if len(self.allocation) != self.num_processes:
            return f"Allocation matrix rows ({len(self.allocation)}) do not match process count ({self.num_processes})."
        for i, row in enumerate(self.allocation):
            if len(row) != self.num_resources:
                return f"Allocation matrix row P{i} has {len(row)} values, expected {self.num_resources}."
            for j, val in enumerate(row):
                if val < 0:
                    return f"Allocation P{i}[R{j}] cannot be negative ({val})."

        if self.mode in (DeadlockMode.SAFETY, DeadlockMode.RESOURCE_REQUEST):
            if len(self.max_claim) != self.num_processes:
                return f"Max Claim matrix rows ({len(self.max_claim)}) do not match process count ({self.num_processes})."
            for i, row in enumerate(self.max_claim):
                if len(row) != self.num_resources:
                    return f"Max Claim matrix row P{i} has {len(row)} values, expected {self.num_resources}."
                for j, val in enumerate(row):
                    if val < 0:
                        return f"Max Claim P{i}[R{j}] cannot be negative ({val})."
                    if self.allocation[i][j] > val:
                        return (
                            f"Validation Error: Allocation P{i}[R{j}] ({self.allocation[i][j]}) "
                            f"exceeds Maximum Claim ({val})."
                        )

        if self.mode == DeadlockMode.RESOURCE_REQUEST:
            if not (0 <= self.requesting_process_id < self.num_processes):
                return f"Requesting process ID must be between 0 and {self.num_processes - 1}."
            if len(self.request_vector) != self.num_resources:
                return f"Requested resources vector length ({len(self.request_vector)}) must equal resource count ({self.num_resources})."
            for j, val in enumerate(self.request_vector):
                if val < 0:
                    return f"Requested resource R{j} cannot be negative ({val})."

        if self.mode == DeadlockMode.DETECTION:
            if len(self.request_matrix) != self.num_processes:
                return f"Request matrix rows ({len(self.request_matrix)}) do not match process count ({self.num_processes})."
            for i, row in enumerate(self.request_matrix):
                if len(row) != self.num_resources:
                    return f"Request matrix row P{i} has {len(row)} values, expected {self.num_resources}."
                for j, val in enumerate(row):
                    if val < 0:
                        return f"Outstanding Request P{i}[R{j}] cannot be negative ({val})."

        return None


@dataclass
class DeadlockSafetyResultModel:
    """Parsed result of Banker's safety algorithm."""

    is_safe: bool
    safe_sequence: List[int]
    blocked_processes: List[int]
    message: str
    num_processes: int
    num_resources: int
    available: List[int]
    allocation: List[List[int]]
    max_claim: List[List[int]]
    need: List[List[int]]
    raw_output: str

    @property
    def safe_sequence_str(self) -> str:
        if not self.is_safe or not self.safe_sequence:
            return "None"
        return " -> ".join(f"P{p}" for p in self.safe_sequence)

    @property
    def blocked_str(self) -> str:
        if not self.blocked_processes:
            return "None"
        return ", ".join(f"P{p}" for p in self.blocked_processes)


@dataclass
class DeadlockRequestResultModel:
    """Parsed result of Banker's resource request algorithm."""

    process_id: int
    requested: List[int]
    granted: bool
    status_code: str
    message: str
    safe_sequence: List[int]
    num_processes: int
    num_resources: int
    available: List[int]
    allocation: List[List[int]]
    max_claim: List[List[int]]
    need: List[List[int]]
    raw_output: str

    @property
    def safe_sequence_str(self) -> str:
        if not self.granted or not self.safe_sequence:
            return "None"
        return " -> ".join(f"P{p}" for p in self.safe_sequence)


@dataclass
class DeadlockDetectionResultModel:
    """Parsed result of Deadlock Detection algorithm."""

    is_deadlocked: bool
    deadlocked_processes: List[int]
    finished_processes: List[int]
    message: str
    num_processes: int
    num_resources: int
    available: List[int]
    allocation: List[List[int]]
    request_matrix: List[List[int]]
    raw_output: str

    @property
    def deadlocked_str(self) -> str:
        if not self.is_deadlocked or not self.deadlocked_processes:
            return "None"
        return ", ".join(f"P{p}" for p in self.deadlocked_processes)
