from .address_translation_page import AddressTranslationPage
from .dashboard_page import DashboardPage
from .deadlock_page import DeadlockPage
from .disk_page import DiskPage
from .filesystem_page import FilesystemPage
from .host_monitor_page import HostMonitorPage
from .linux_page import LinuxExperimentsPage
from .memory_page import MemoryAllocationPage
from .paging_page import PageReplacementPage
from .process_lifecycle_page import ProcessLifecyclePage
from .scheduling_page import SchedulingPage

__all__ = [
    "DashboardPage",
    "SchedulingPage",
    "MemoryAllocationPage",
    "PageReplacementPage",
    "DeadlockPage",
    "DiskPage",
    "LinuxExperimentsPage",
    "HostMonitorPage",
    "FilesystemPage",
    "AddressTranslationPage",
    "ProcessLifecyclePage",
]

