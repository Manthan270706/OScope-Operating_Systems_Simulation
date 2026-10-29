"""Data models for Dynamic Partition Memory Allocation simulation."""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


class MemoryStrategy(str, Enum):
    """Supported dynamic memory allocation strategies."""
    FIRST_FIT = "First Fit"
    BEST_FIT = "Best Fit"
    WORST_FIT = "Worst Fit"
    COMPARE_ALL = "Compare All"

    @property
    def menu_choice(self) -> int:
        """Map to C++ CLI sub-menu choice."""
        mapping = {
            MemoryStrategy.FIRST_FIT: 1,
            MemoryStrategy.BEST_FIT: 2,
            MemoryStrategy.WORST_FIT: 3,
            MemoryStrategy.COMPARE_ALL: 4,
        }
        return mapping[self]

    @property
    def description(self) -> str:
        """Concise plain-language explanation of strategy."""
        if self == MemoryStrategy.FIRST_FIT:
            return "First Fit: Selects the first free block from the start of memory that is large enough. Fast, but may accumulate small fragments at the beginning."
        elif self == MemoryStrategy.BEST_FIT:
            return "Best Fit: Searches the entire memory pool to find the smallest suitable free block. Minimizes wasted capacity per block, but can leave tiny unusable slivers."
        elif self == MemoryStrategy.WORST_FIT:
            return "Worst Fit: Allocates from the largest available free block. Leaves the largest possible remainder block, which may remain usable for future requests."
        else:
            return "Compare All: Evaluates First Fit, Best Fit, and Worst Fit side-by-side using the identical sequence of allocation and deallocation operations."


class MemoryOperationType(str, Enum):
    """Type of memory workload operation."""
    ALLOCATE = "Allocate"
    DEALLOCATE = "Deallocate"


@dataclass
class MemoryOperationInput:
    """User-configured memory allocation or deallocation operation."""
    op_type: MemoryOperationType
    request_id: int
    size: int = 0
    process_id: Optional[int] = None

    def validate(self) -> Optional[str]:
        if self.request_id <= 0:
            return f"Logical Request ID must be a positive integer (> 0), got {self.request_id}."
        if self.op_type == MemoryOperationType.ALLOCATE:
            if self.size <= 0:
                return f"Allocation size for Request ID {self.request_id} must be positive (> 0), got {self.size}."
            if self.process_id is not None and self.process_id < 0:
                return f"Process ID for Request ID {self.request_id} must be non-negative (>= 0), got {self.process_id}."
        return None


@dataclass
class MemoryConfig:
    """Configuration for memory allocation run."""
    strategy: MemoryStrategy
    total_memory: int = 1000

    def validate(self) -> Optional[str]:
        if self.total_memory <= 0:
            return f"Total memory size must be positive (> 0), got {self.total_memory}."
        return None


@dataclass
class MemoryBlockModel:
    """Represents a segment of memory within the contiguous pool."""
    block_index: int
    start_address: int
    size: int
    is_allocated: bool
    allocation_id: Optional[int] = None
    process_id: Optional[int] = None

    @property
    def end_address(self) -> int:
        return self.start_address + self.size


@dataclass
class MemoryOperationResultModel:
    """Outcome of a single memory operation reported by backend."""
    op_number: int
    op_type: str
    request_id: int
    success: bool
    message: str
    start_address: Optional[int] = None
    size: Optional[int] = None
    internal_id: Optional[int] = None


@dataclass
class MemoryMetricsModel:
    """Memory pool utilization and fragmentation metrics."""
    total_memory: int = 0
    allocated_memory: int = 0
    free_memory: int = 0
    largest_free_block: int = 0
    external_fragmentation: float = 0.0

    @property
    def utilization_percentage(self) -> float:
        if self.total_memory <= 0:
            return 0.0
        return (self.allocated_memory / self.total_memory) * 100.0


@dataclass
class MemorySimulationResultModel:
    """Complete results from a single memory allocation strategy simulation."""
    strategy_name: str
    total_memory: int
    operations: List[MemoryOperationResultModel] = field(default_factory=list)
    blocks: List[MemoryBlockModel] = field(default_factory=list)
    metrics: MemoryMetricsModel = field(default_factory=MemoryMetricsModel)
    raw_output: str = ""


@dataclass
class MemoryComparisonEntryModel:
    """Row in multi-strategy memory allocation comparison."""
    strategy_name: str
    attempts: int
    success: int
    failures: int
    success_rate: float
    allocated_bytes: int
    free_bytes: int
    largest_free_bytes: int
    external_fragmentation: float


@dataclass
class MemoryComparisonResultModel:
    """Complete results from comparing First Fit, Best Fit, and Worst Fit."""
    total_memory: int
    total_operations: int
    entries: List[MemoryComparisonEntryModel] = field(default_factory=list)
    raw_output: str = ""
