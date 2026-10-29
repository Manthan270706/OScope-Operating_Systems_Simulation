"""Data models for Virtual Memory Address Translation and MMU Paging simulation."""

from dataclasses import dataclass, field
from typing import List, Optional, Tuple


@dataclass
class PageTableEntryModel:
    """Represents a single entry in the page table."""
    page_number: int
    frame_number: int
    valid: bool = True
    dirty: bool = False
    referenced: bool = False


@dataclass
class TranslationResultModel:
    """Result of translating a single virtual address to a physical address."""
    virtual_address: int
    page_number: int
    offset: int
    page_fault: bool
    frame_number: int
    physical_address: int
    message: str = ""

    @property
    def hex_va(self) -> str:
        return f"0x{self.virtual_address:X}"

    @property
    def hex_pa(self) -> str:
        if self.page_fault:
            return "N/A (Fault)"
        return f"0x{self.physical_address:X}"


@dataclass
class DemandPagingStepModel:
    """Trace event for a single address access in demand paging."""
    virtual_address: int
    page_number: int
    offset: int
    page_fault: bool
    frame_number: int
    physical_address: int
    victim_page: int = -1
    frame_contents: List[int] = field(default_factory=list)


@dataclass
class DemandPagingResultModel:
    """Overall results of demand paging simulation."""
    page_size: int
    total_frames: int
    total_accesses: int
    page_faults: int
    page_hits: int
    fault_rate: float
    steps: List[DemandPagingStepModel] = field(default_factory=list)


@dataclass
class ThrashingPointModel:
    """A data point on the thrashing curve (frames vs faults)."""
    frames: int
    page_faults: int
    fault_rate: float


@dataclass
class ThrashingResultModel:
    """Thrashing curve simulation results."""
    reference_string: List[int] = field(default_factory=list)
    points: List[ThrashingPointModel] = field(default_factory=list)
    thrashing_threshold_frames: int = 0


@dataclass
class AddressTranslationSimulationResultModel:
    """Aggregated simulation result returned from C++ backend."""
    page_size: int = 4096
    page_table: List[PageTableEntryModel] = field(default_factory=list)
    translations: List[TranslationResultModel] = field(default_factory=list)
    demand_paging: Optional[DemandPagingResultModel] = None
    thrashing: Optional[ThrashingResultModel] = None
    logs: List[str] = field(default_factory=list)


@dataclass
class AddressTranslationConfig:
    """Configuration passed from GUI to backend execution."""
    page_size: int = 4096
    mode: str = "demo"  # "demo" or "custom"
    custom_mappings: List[Tuple[int, int]] = field(default_factory=list)  # (page, frame)
    virtual_addresses_to_translate: List[int] = field(default_factory=list)
    demand_paging_frames: int = 3
    demand_paging_addresses: List[int] = field(default_factory=list)
    thrashing_reference_string: List[int] = field(default_factory=list)
    thrashing_min_frames: int = 1
    thrashing_max_frames: int = 6

    def validate(self) -> Optional[str]:
        if self.page_size not in (512, 1024, 2048, 4096, 8192, 16384, 65536):
            return f"Page size must be a valid power of 2 (e.g., 512, 1024, 2048, 4096), got {self.page_size}."
        if self.mode == "custom":
            for p, f in self.custom_mappings:
                if p < 0 or f < 0:
                    return f"Page and frame numbers must be non-negative, got page={p}, frame={f}."
            if self.demand_paging_frames <= 0:
                return f"Demand paging frame count must be > 0, got {self.demand_paging_frames}."
            if self.thrashing_min_frames <= 0 or self.thrashing_max_frames < self.thrashing_min_frames:
                return f"Invalid thrashing frame range [{self.thrashing_min_frames}, {self.thrashing_max_frames}]."
        return None
