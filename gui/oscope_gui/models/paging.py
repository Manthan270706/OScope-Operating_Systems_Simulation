"""Data models for Virtual Memory Page Replacement simulation."""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


class PagingAlgorithm(str, Enum):
    """Supported page replacement algorithms."""
    FIFO = "FIFO"
    LRU = "LRU"
    OPTIMAL = "Optimal"
    COMPARE_ALL = "Compare All"

    @property
    def menu_choice(self) -> int:
        """Map to C++ CLI sub-menu choice."""
        mapping = {
            PagingAlgorithm.FIFO: 1,
            PagingAlgorithm.LRU: 2,
            PagingAlgorithm.OPTIMAL: 3,
            PagingAlgorithm.COMPARE_ALL: 4,
        }
        return mapping[self]

    @property
    def description(self) -> str:
        """Educational plain-language explanation of the algorithm."""
        if self == PagingAlgorithm.FIFO:
            return (
                "FIFO (First-In, First-Out): Replaces the page that has resided in memory the longest. "
                "Simple to implement using a queue, but subject to Belady's Anomaly where allocating more frames can yield more faults."
            )
        elif self == PagingAlgorithm.LRU:
            return (
                "LRU (Least Recently Used): Replaces the page that has not been referenced for the longest period of time. "
                "An effective approximation of optimal behavior exploiting temporal locality, but requires hardware tracking."
            )
        elif self == PagingAlgorithm.OPTIMAL:
            return (
                "Optimal (OPT / MIN / Belady's): Replaces the page whose next reference occurs farthest in the future, or is never referenced again. "
                "Guarantees the lowest possible page fault rate; serves as a theoretical performance benchmark requiring future knowledge."
            )
        else:
            return (
                "Compare All: Evaluates FIFO, LRU, and Optimal side-by-side using the identical frame count and reference sequence."
            )


@dataclass
class PagingConfig:
    """User-configured parameters for page replacement simulation."""
    algorithm: PagingAlgorithm
    frame_count: int
    reference_string: List[int]

    def validate(self) -> Optional[str]:
        if self.frame_count <= 0:
            return f"Number of frames must be a positive integer (> 0), got {self.frame_count}."
        if self.frame_count > 64:
            return f"Number of frames cannot exceed 64, got {self.frame_count}."
        if not self.reference_string:
            return "Page reference string cannot be empty. Enter space- or comma-separated page numbers."
        for idx, page in enumerate(self.reference_string):
            if page < 0:
                return f"Page numbers must be non-negative (>= 0). Found invalid page '{page}' at index {idx + 1}."
            if page > 1000000:
                return f"Page number {page} at index {idx + 1} exceeds maximum allowable page range (1,000,000)."
        return None


@dataclass
class PagingStepModel:
    """Represents a single reference step in the page replacement timeline."""
    step_number: int
    page: int
    is_fault: bool
    frames: List[int] = field(default_factory=list)
    evicted_page: Optional[int] = None

    @property
    def result_str(self) -> str:
        return "Fault" if self.is_fault else "Hit"


@dataclass
class PagingMetricsModel:
    """Summary metrics from page replacement execution."""
    total_references: int = 0
    page_faults: int = 0
    page_hits: int = 0
    fault_rate: float = 0.0
    hit_rate: float = 0.0

    @property
    def fault_percentage(self) -> float:
        return self.fault_rate * 100.0

    @property
    def hit_percentage(self) -> float:
        return self.hit_rate * 100.0


@dataclass
class PagingSimulationResultModel:
    """Complete result of a single page replacement algorithm execution."""
    algorithm_name: str
    frame_count: int
    reference_string: List[int]
    steps: List[PagingStepModel] = field(default_factory=list)
    metrics: PagingMetricsModel = field(default_factory=PagingMetricsModel)
    raw_output: str = ""


@dataclass
class PagingComparisonEntryModel:
    """Performance entry for an individual algorithm in a multi-strategy comparison."""
    algorithm_name: str
    total_references: int
    page_faults: int
    page_hits: int
    fault_rate: float
    hit_rate: float


@dataclass
class PagingComparisonResultModel:
    """Comprehensive comparison across FIFO, LRU, and Optimal."""
    frame_count: int
    total_references: int
    entries: List[PagingComparisonEntryModel] = field(default_factory=list)
    raw_output: str = ""
