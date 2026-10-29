"""Data models for simulated file system simulation."""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


class FilesystemAllocationStrategy(str, Enum):
    """File allocation strategies simulated by C++ backend."""
    CONTIGUOUS = "Contiguous"
    LINKED = "Linked"
    INDEXED = "Indexed"

    @classmethod
    def from_str(cls, val: str) -> "FilesystemAllocationStrategy":
        v = val.strip().lower()
        if "contig" in v:
            return cls.CONTIGUOUS
        if "link" in v:
            return cls.LINKED
        return cls.INDEXED


class FilesystemPreset(str, Enum):
    """Preset simulations for educational file-system demonstrations."""
    STANDARD_DEMO = "standard_demo"
    FRAGMENTATION = "fragmentation"
    CAPACITY_LIMIT = "capacity_limit"
    CUSTOM_WORKLOAD = "custom_workload"


class FilesystemOperationType(str, Enum):
    """Supported file system operations."""
    CONFIG = "config"
    FORMAT = "format"
    MKDIR = "mkdir"
    CREATE = "create"
    DELETE = "delete"
    RMDIR = "rmdir"


@dataclass
class FilesystemOperationInput:
    """User-specified operation input for custom workload."""
    op_type: FilesystemOperationType
    path: str
    size_bytes: int = 512
    strategy: FilesystemAllocationStrategy = FilesystemAllocationStrategy.INDEXED

    def validate(self) -> Optional[str]:
        if self.op_type in (FilesystemOperationType.MKDIR, FilesystemOperationType.CREATE,
                            FilesystemOperationType.DELETE, FilesystemOperationType.RMDIR):
            if not self.path or not self.path.strip():
                return "Operation path cannot be empty."
            if not self.path.startswith("/"):
                return "Path must start with a leading slash ('/')."
        if self.op_type == FilesystemOperationType.CREATE:
            if self.size_bytes <= 0:
                return "File size must be greater than 0 bytes."
            if self.size_bytes > 1_000_000:
                return "Simulated file size cannot exceed 1 MB."
        return None

    def to_cli_command(self) -> str:
        if self.op_type == FilesystemOperationType.MKDIR:
            return f"mkdir {self.path.strip()}"
        if self.op_type == FilesystemOperationType.CREATE:
            strat_str = self.strategy.value.lower()
            return f"create {self.path.strip()} {self.size_bytes} {strat_str}"
        if self.op_type == FilesystemOperationType.DELETE:
            return f"delete {self.path.strip()}"
        if self.op_type == FilesystemOperationType.RMDIR:
            return f"rmdir {self.path.strip()}"
        if self.op_type == FilesystemOperationType.FORMAT:
            return "format"
        return ""


@dataclass
class FilesystemConfig:
    """Configuration for simulated file system execution."""
    total_blocks: int = 32
    block_size: int = 512
    preset: FilesystemPreset = FilesystemPreset.STANDARD_DEMO
    operations: List[FilesystemOperationInput] = field(default_factory=list)

    def validate(self) -> Optional[str]:
        if self.total_blocks < 4 or self.total_blocks > 256:
            return "Total blocks must be between 4 and 256."
        if self.block_size < 64 or self.block_size > 8192:
            return "Block size must be between 64 and 8192 bytes."
        for idx, op in enumerate(self.operations):
            err = op.validate()
            if err:
                return f"Operation #{idx + 1} ({op.op_type.value}): {err}"
        return None


@dataclass
class FileInodeModel:
    """Inode metadata entry returned by the C++ backend."""
    inode_id: int
    name: str
    path: str
    is_directory: bool
    size_bytes: int
    strategy: str = "Indexed"
    start_block: int = -1
    index_block: int = -1
    block_count: int = 0
    allocated_blocks: List[int] = field(default_factory=list)


@dataclass
class AllocationTraceModel:
    """File allocation trace entry returned by the backend."""
    name: str
    path: str
    strategy: str
    start_block: int
    index_block: int
    block_count: int
    allocated_blocks: List[int] = field(default_factory=list)


@dataclass
class FilesystemStatusModel:
    """Full simulated filesystem state snapshot."""
    total_blocks: int = 32
    block_size: int = 512
    used_blocks: int = 0
    free_blocks: int = 32
    file_count: int = 0
    directory_count: int = 1
    block_bitmap: List[bool] = field(default_factory=list)
    inodes: List[FileInodeModel] = field(default_factory=list)
    allocation_traces: List[AllocationTraceModel] = field(default_factory=list)
    operation_logs: List[str] = field(default_factory=list)

    @property
    def utilization_percent(self) -> float:
        if self.total_blocks <= 0:
            return 0.0
        return (self.used_blocks / self.total_blocks) * 100.0

    @property
    def total_capacity_bytes(self) -> int:
        return self.total_blocks * self.block_size

    @property
    def used_bytes(self) -> int:
        return self.used_blocks * self.block_size

    @property
    def free_bytes(self) -> int:
        return self.free_blocks * self.block_size

    def get_entries_under(self, dir_path: str) -> List[FileInodeModel]:
        """Returns direct children of dir_path."""
        clean = dir_path.rstrip("/")
        if not clean:
            clean = "/"
        children: List[FileInodeModel] = []
        for in_obj in self.inodes:
            if in_obj.path == clean or in_obj.path == "/":
                continue
            parent = in_obj.path.rsplit("/", 1)[0]
            if not parent:
                parent = "/"
            if parent == clean:
                children.append(in_obj)
        return children


@dataclass
class FilesystemSimulationResultModel:
    """Complete simulation result wrapper."""
    status: FilesystemStatusModel
    preset: FilesystemPreset = FilesystemPreset.STANDARD_DEMO
    raw_stdout: str = ""
    exit_code: int = 0
    duration_ms: float = 0.0
    error_message: Optional[str] = None
    is_success: bool = True
