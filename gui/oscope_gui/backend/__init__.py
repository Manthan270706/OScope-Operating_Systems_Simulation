"""Backend runner and execution modules."""

from .runner import (
    BaseBackendRunner,
    WSLBackendRunner,
    NativeBackendRunner,
    ExecutionResult,
    BackendInfo,
    discover_backend,
    to_wsl_path,
)
from .parser import (
    generate_scheduling_stdin,
    parse_scheduling_output,
    parse_comparison_output,
    generate_paging_ops_stdin,
    parse_address_translation_output,
    generate_process_ops_stdin,
    parse_process_lifecycle_output,
)

try:
    from .executor import SchedulingWorker, AddressTranslationWorker, ProcessLifecycleWorker
except ImportError:
    SchedulingWorker = None  # PySide6 not installed yet
    AddressTranslationWorker = None
    ProcessLifecycleWorker = None

__all__ = [
    "BaseBackendRunner",
    "WSLBackendRunner",
    "NativeBackendRunner",
    "ExecutionResult",
    "BackendInfo",
    "discover_backend",
    "to_wsl_path",
    "generate_scheduling_stdin",
    "parse_scheduling_output",
    "parse_comparison_output",
    "generate_paging_ops_stdin",
    "parse_address_translation_output",
    "generate_process_ops_stdin",
    "parse_process_lifecycle_output",
    "SchedulingWorker",
    "AddressTranslationWorker",
    "ProcessLifecycleWorker",
]
