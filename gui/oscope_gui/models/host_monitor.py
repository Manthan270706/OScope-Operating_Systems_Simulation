"""Data models for Host Resource Monitoring (Real Linux / WSL Host Observations)."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class HostCpuModel:
    """CPU observation from /proc/stat."""
    total_usage_percent: float = 0.0
    user_percent: float = 0.0
    system_percent: float = 0.0
    idle_percent: float = 0.0
    valid: bool = False


@dataclass
class HostMemoryModel:
    """Memory observation from /proc/meminfo."""
    total_kb: int = 0
    used_kb: int = 0
    available_kb: int = 0
    free_kb: int = 0
    used_percent: float = 0.0
    valid: bool = False

    @property
    def total_mb(self) -> float:
        return self.total_kb / 1024.0

    @property
    def used_mb(self) -> float:
        return self.used_kb / 1024.0

    @property
    def available_mb(self) -> float:
        return self.available_kb / 1024.0


@dataclass
class HostSystemModel:
    """System-wide telemetry from /proc/uptime, /proc/loadavg, and statvfs."""
    uptime_seconds: float = 0.0
    load_1min: float = 0.0
    load_5min: float = 0.0
    load_15min: float = 0.0
    total_processes: int = 0
    running_processes: int = 0
    disk_total_bytes: int = 0
    disk_used_bytes: int = 0
    disk_available_bytes: int = 0
    disk_used_percent: float = 0.0
    root_mount: str = "/"
    valid: bool = False

    @property
    def disk_total_gb(self) -> float:
        return self.disk_total_bytes / (1024.0 ** 3)

    @property
    def disk_used_gb(self) -> float:
        return self.disk_used_bytes / (1024.0 ** 3)

    @property
    def disk_available_gb(self) -> float:
        return self.disk_available_bytes / (1024.0 ** 3)

    @property
    def uptime_formatted(self) -> str:
        s = int(self.uptime_seconds)
        hours = s // 3600
        mins = (s % 3600) // 60
        secs = s % 60
        if hours > 0:
            return f"{hours}h {mins}m {secs}s"
        elif mins > 0:
            return f"{mins}m {secs}s"
        return f"{secs}s"


@dataclass
class HostProcessModel:
    """Process observation from /proc/[pid]/stat."""
    pid: int = 0
    ppid: int = 0
    comm: str = ""
    state: str = "?"
    utime_ticks: int = 0
    stime_ticks: int = 0
    rss_kb: int = 0
    vm_size_bytes: int = 0
    valid: bool = False

    @property
    def state_description(self) -> str:
        states = {
            "R": "Running (R)",
            "S": "Sleeping (S)",
            "D": "Disk Sleep / Uninterruptible (D)",
            "Z": "Zombie (Z)",
            "T": "Stopped (T)",
            "t": "Tracing Stop (t)",
            "X": "Dead (X)",
        }
        return states.get(self.state, f"State '{self.state}'")


@dataclass
class HostDiskIoModel:
    """Block device I/O observation from /proc/diskstats."""
    device_name: str = ""
    reads_completed: int = 0
    sectors_read: int = 0
    writes_completed: int = 0
    sectors_written: int = 0
    valid: bool = False


@dataclass
class HostMonitoringSnapshotModel:
    """Complete snapshot of live Linux host resource monitoring."""
    source: str = "real_linux_host"
    environment: str = "WSL Linux Host Kernel"
    timestamp: str = ""
    cpu: HostCpuModel = field(default_factory=HostCpuModel)
    memory: HostMemoryModel = field(default_factory=HostMemoryModel)
    system: HostSystemModel = field(default_factory=HostSystemModel)
    self_process: HostProcessModel = field(default_factory=HostProcessModel)
    disks: List[HostDiskIoModel] = field(default_factory=list)
    success: bool = True
    error_message: Optional[str] = None
    raw_output: str = ""
    raw_json: Optional[Dict[str, Any]] = None
