"""Asynchronous workers for executing backend simulations off the GUI thread."""

from typing import List, Optional

from PySide6.QtCore import QObject, QThread, Signal

from ..models.address_translation import (
    AddressTranslationConfig,
    AddressTranslationSimulationResultModel,
)
from ..models.deadlock import (
    DeadlockConfig,
    DeadlockDetectionResultModel,
    DeadlockMode,
    DeadlockRequestResultModel,
    DeadlockSafetyResultModel,
)
from ..models.disk import (
    DiskAlgorithm,
    DiskComparisonResultModel,
    DiskConfig,
    DiskSchedulingResultModel,
)
from ..models.filesystem import (
    FilesystemConfig,
    FilesystemPreset,
    FilesystemSimulationResultModel,
)
from ..models.host_monitor import HostMonitoringSnapshotModel
from ..models.linux_experiments import (
    LinuxExperimentCategory,
    LinuxExperimentsResultModel,
)
from ..models.memory import (
    MemoryComparisonResultModel,
    MemoryConfig,
    MemoryOperationInput,
    MemorySimulationResultModel,
    MemoryStrategy,
)
from ..models.paging import (
    PagingAlgorithm,
    PagingComparisonResultModel,
    PagingConfig,
    PagingSimulationResultModel,
)
from ..models.process_lifecycle import (
    ProcessLifecycleConfig,
    ProcessLifecycleSimulationResultModel,
)
from ..models.scheduling import AlgorithmConfig, AlgorithmType, ProcessInput
from .parser import (
    generate_deadlock_stdin,
    generate_disk_stdin,
    generate_filesystem_stdin,
    generate_linux_experiments_stdin,
    generate_memory_stdin,
    generate_paging_ops_stdin,
    generate_paging_stdin,
    generate_process_ops_stdin,
    generate_scheduling_stdin,
    parse_address_translation_output,
    parse_comparison_output,
    parse_deadlock_detection_output,
    parse_deadlock_request_output,
    parse_process_lifecycle_output,
    parse_deadlock_safety_output,
    parse_disk_comparison_output,
    parse_disk_output,
    parse_filesystem_output,
    parse_host_monitoring_output,
    parse_linux_experiments_output,
    parse_memory_comparison_output,
    parse_memory_output,
    parse_paging_comparison_output,
    parse_paging_output,
    parse_scheduling_output,
)
from .runner import BaseBackendRunner, ExecutionResult



class WorkerSignals(QObject):
    """Signal proxy for workers to support .signals.completed / .signals.failed style."""
    completed = Signal(object)
    failed = Signal(str)


class SchedulingWorker(QThread):
    """Executes CPU scheduling backend process in a separate background thread."""

    started_exec = Signal()
    finished_exec = Signal(object)  # Emits SchedulingResultModel or SchedulingComparisonResultModel
    failed_exec = Signal(str)       # Emits error description string

    def __init__(
        self,
        runner: BaseBackendRunner,
        config: AlgorithmConfig,
        processes: List[ProcessInput],
        parent: Optional[QThread] = None,
    ) -> None:
        super().__init__(parent)
        self.runner = runner
        self.config = config
        self.processes = processes
        self._is_cancelled = False
        self.signals = WorkerSignals()

        # Connect internal signals to signal proxy
        self.finished_exec.connect(self.signals.completed)
        self.failed_exec.connect(self.signals.failed)

    def run(self) -> None:
        self.started_exec.emit()

        # Validate process list
        if not self.processes:
            self.failed_exec.emit("Process list is empty. Add at least one process to simulate.")
            return

        # Validate configuration
        cfg_err = self.config.validate()
        if cfg_err:
            self.failed_exec.emit(cfg_err)
            return

        for p in self.processes:
            err = p.validate()
            if err:
                self.failed_exec.emit(err)
                return

        # Prepare stdin
        try:
            stdin_data = generate_scheduling_stdin(self.config, self.processes)
        except Exception as e:
            self.failed_exec.emit(f"Failed to generate backend input: {e}")
            return

        if self._is_cancelled:
            return

        # Execute backend process
        result: ExecutionResult = self.runner.execute(
            args=[],
            stdin_data=stdin_data,
            timeout=25.0,
        )

        if self._is_cancelled:
            return

        if result.is_timeout:
            self.failed_exec.emit("Simulation timed out. The backend process exceeded 25 seconds.")
            return

        if not result.stdout:
            err_msg = result.stderr.strip() or f"Process exited with code {result.exit_code} and produced no output."
            self.failed_exec.emit(f"Backend execution failure: {err_msg}")
            return

        # Parse output
        try:
            if self.config.algorithm == AlgorithmType.COMPARE_ALL:
                parsed_comparison = parse_comparison_output(result.stdout)
                if not parsed_comparison.entries:
                    self.failed_exec.emit("Backend ran but produced no parseable comparison entries.")
                    return
                self.finished_exec.emit(parsed_comparison)
            else:
                parsed_res = parse_scheduling_output(result.stdout, self.config.algorithm.display_name)
                if not parsed_res.process_results and not parsed_res.timeline:
                    self.failed_exec.emit("Backend completed but produced no simulation results or timeline.")
                    return
                self.finished_exec.emit(parsed_res)
        except Exception as e:
            self.failed_exec.emit(f"Output parsing error: {e}")

    def cancel(self) -> None:
        self._is_cancelled = True
        self.runner.cancel()


class MemoryWorker(QThread):
    """Executes Memory Allocation backend process in a separate background thread."""

    started_exec = Signal()
    finished_exec = Signal(object)  # Emits MemorySimulationResultModel or MemoryComparisonResultModel
    failed_exec = Signal(str)       # Emits error description string

    def __init__(
        self,
        runner: BaseBackendRunner,
        config: MemoryConfig,
        operations: List[MemoryOperationInput],
        parent: Optional[QThread] = None,
    ) -> None:
        super().__init__(parent)
        self.runner = runner
        self.config = config
        self.operations = operations
        self._is_cancelled = False
        self.signals = WorkerSignals()

        self.finished_exec.connect(self.signals.completed)
        self.failed_exec.connect(self.signals.failed)

    def run(self) -> None:
        self.started_exec.emit()

        # Validate configuration
        cfg_err = self.config.validate()
        if cfg_err:
            self.failed_exec.emit(cfg_err)
            return

        # Validate operations list
        if not self.operations:
            self.failed_exec.emit("Operation list is empty. Add at least one memory operation to simulate.")
            return

        for op in self.operations:
            err = op.validate()
            if err:
                self.failed_exec.emit(err)
                return

        # Prepare stdin
        try:
            stdin_data = generate_memory_stdin(self.config, self.operations)
        except Exception as e:
            self.failed_exec.emit(f"Failed to generate backend memory input: {e}")
            return

        if self._is_cancelled:
            return

        # Execute backend process
        result: ExecutionResult = self.runner.execute(
            args=[],
            stdin_data=stdin_data,
            timeout=25.0,
        )

        if self._is_cancelled:
            return

        if result.is_timeout:
            self.failed_exec.emit("Memory simulation timed out. The backend process exceeded 25 seconds.")
            return

        if not result.stdout:
            err_msg = result.stderr.strip() or f"Process exited with code {result.exit_code} and produced no output."
            self.failed_exec.emit(f"Backend execution failure: {err_msg}")
            return

        # Parse output
        try:
            if self.config.strategy == MemoryStrategy.COMPARE_ALL:
                parsed_comparison = parse_memory_comparison_output(result.stdout)
                if not parsed_comparison.entries:
                    self.failed_exec.emit("Backend ran but produced no parseable memory comparison entries.")
                    return
                self.finished_exec.emit(parsed_comparison)
            else:
                parsed_res = parse_memory_output(result.stdout, self.config.strategy.value)
                self.finished_exec.emit(parsed_res)
        except Exception as e:
            self.failed_exec.emit(f"Memory output parsing error: {e}")

    def cancel(self) -> None:
        self._is_cancelled = True
        self.runner.cancel()


class PagingWorker(QThread):
    """Executes Virtual Memory Page Replacement simulation in a background thread."""

    started_exec = Signal()
    finished_exec = Signal(object)  # Emits PagingSimulationResultModel or PagingComparisonResultModel
    failed_exec = Signal(str)       # Emits error string

    def __init__(
        self,
        runner: BaseBackendRunner,
        config: PagingConfig,
        parent: Optional[QObject] = None,
    ) -> None:
        super().__init__(parent)
        self.runner = runner
        self.config = config
        self._is_cancelled = False
        self.signals = WorkerSignals()
        self.finished_exec.connect(self.signals.completed)
        self.failed_exec.connect(self.signals.failed)

    def run(self) -> None:
        self.started_exec.emit()

        # Validate configuration
        cfg_err = self.config.validate()
        if cfg_err:
            self.failed_exec.emit(cfg_err)
            return

        # Prepare stdin
        try:
            stdin_data = generate_paging_stdin(self.config)
        except Exception as e:
            self.failed_exec.emit(f"Failed to generate backend paging input: {e}")
            return

        if self._is_cancelled:
            return

        # Execute backend process
        result: ExecutionResult = self.runner.execute(
            args=[],
            stdin_data=stdin_data,
            timeout=25.0,
        )

        if self._is_cancelled:
            return

        if result.is_timeout:
            self.failed_exec.emit("Page replacement simulation timed out. The backend exceeded 25 seconds.")
            return

        if not result.stdout:
            err_msg = result.stderr.strip() or f"Process exited with code {result.exit_code} and produced no output."
            self.failed_exec.emit(f"Backend execution failure: {err_msg}")
            return

        # Parse output
        try:
            if self.config.algorithm == PagingAlgorithm.COMPARE_ALL:
                parsed_comparison = parse_paging_comparison_output(result.stdout)
                if not parsed_comparison.entries:
                    self.failed_exec.emit("Backend ran but produced no parseable page replacement comparison entries.")
                    return
                self.finished_exec.emit(parsed_comparison)
            else:
                parsed_res = parse_paging_output(
                    result.stdout,
                    self.config.algorithm.value,
                    self.config.frame_count,
                    self.config.reference_string,
                )
                self.finished_exec.emit(parsed_res)
        except Exception as e:
            self.failed_exec.emit(f"Paging output parsing error: {e}")

    def cancel(self) -> None:
        self._is_cancelled = True
        self.runner.cancel()


class DeadlockWorker(QThread):
    """Executes Deadlock Management backend process in a separate background thread."""

    started_exec = Signal()
    finished_exec = Signal(object)  # Emits DeadlockSafetyResultModel, DeadlockRequestResultModel, or DeadlockDetectionResultModel
    failed_exec = Signal(str)       # Emits error description string

    def __init__(
        self,
        runner: BaseBackendRunner,
        config: DeadlockConfig,
        parent: Optional[QObject] = None,
    ) -> None:
        super().__init__(parent)
        self.runner = runner
        self.config = config
        self._is_cancelled = False
        self.signals = WorkerSignals()
        self.finished_exec.connect(self.signals.completed)
        self.failed_exec.connect(self.signals.failed)

    def run(self) -> None:
        self.started_exec.emit()

        # Validate configuration
        cfg_err = self.config.validate()
        if cfg_err:
            self.failed_exec.emit(cfg_err)
            return

        # Prepare stdin
        try:
            stdin_data = generate_deadlock_stdin(self.config)
        except Exception as e:
            self.failed_exec.emit(f"Failed to generate backend deadlock input: {e}")
            return

        if self._is_cancelled:
            return

        # Execute backend process
        result: ExecutionResult = self.runner.execute(
            args=[],
            stdin_data=stdin_data,
            timeout=25.0,
        )

        if self._is_cancelled:
            return

        if result.is_timeout:
            self.failed_exec.emit("Deadlock analysis timed out. The backend exceeded 25 seconds.")
            return

        if not result.stdout:
            err_msg = result.stderr.strip() or f"Process exited with code {result.exit_code} and produced no output."
            self.failed_exec.emit(f"Backend execution failure: {err_msg}")
            return

        # Parse output according to mode
        try:
            if self.config.mode == DeadlockMode.SAFETY:
                parsed_res = parse_deadlock_safety_output(result.stdout, self.config)
                self.finished_exec.emit(parsed_res)
            elif self.config.mode == DeadlockMode.RESOURCE_REQUEST:
                parsed_res = parse_deadlock_request_output(result.stdout, self.config)
                self.finished_exec.emit(parsed_res)
            elif self.config.mode == DeadlockMode.DETECTION:
                parsed_res = parse_deadlock_detection_output(result.stdout, self.config)
                self.finished_exec.emit(parsed_res)
        except Exception as e:
            self.failed_exec.emit(f"Deadlock output parsing error: {e}")

    def cancel(self) -> None:
        self._is_cancelled = True
        self.runner.cancel()


class DiskWorker(QThread):
    """Executes Disk Scheduling simulation in a separate background thread."""

    started_exec = Signal()
    finished_exec = Signal(object)  # DiskSchedulingResultModel or DiskComparisonResultModel
    failed_exec = Signal(str)

    def __init__(
        self,
        runner: BaseBackendRunner,
        config: DiskConfig,
        parent: Optional[QThread] = None,
    ) -> None:
        super().__init__(parent)
        self.runner = runner
        self.config = config
        self._is_cancelled = False
        self.signals = WorkerSignals()

        self.finished_exec.connect(self.signals.completed)
        self.failed_exec.connect(self.signals.failed)

    def run(self) -> None:
        self.started_exec.emit()

        cfg_err = self.config.validate()
        if cfg_err:
            self.failed_exec.emit(cfg_err)
            return

        try:
            stdin_data = generate_disk_stdin(self.config)
        except Exception as e:
            self.failed_exec.emit(f"Failed to generate backend disk input: {e}")
            return

        if self._is_cancelled:
            return

        result: ExecutionResult = self.runner.execute(
            args=[],
            stdin_data=stdin_data,
            timeout=25.0,
        )

        if self._is_cancelled:
            return

        if result.is_timeout:
            self.failed_exec.emit("Disk scheduling simulation timed out. The backend exceeded 25 seconds.")
            return

        if not result.stdout:
            err_msg = result.stderr.strip() or f"Process exited with code {result.exit_code} and produced no output."
            self.failed_exec.emit(f"Backend execution failure: {err_msg}")
            return

        try:
            if self.config.algorithm == DiskAlgorithm.COMPARE_ALL:
                parsed_res = parse_disk_comparison_output(result.stdout, self.config)
            else:
                parsed_res = parse_disk_output(result.stdout, self.config)
            self.finished_exec.emit(parsed_res)
        except Exception as e:
            self.failed_exec.emit(f"Disk scheduling output parsing error: {e}")

    def cancel(self) -> None:
        self._is_cancelled = True
        self.runner.cancel()


class LinuxExperimentsWorker(QThread):
    """Executes Linux / POSIX system experiments in a background thread."""

    started_exec = Signal()
    finished_exec = Signal(object)  # LinuxExperimentsResultModel
    failed_exec = Signal(str)

    def __init__(
        self,
        runner: BaseBackendRunner,
        category: LinuxExperimentCategory = LinuxExperimentCategory.ALL,
        parent: Optional[QThread] = None,
    ) -> None:
        super().__init__(parent)
        self.runner = runner
        self.category = category
        self._is_cancelled = False
        self.signals = WorkerSignals()

        self.finished_exec.connect(self.signals.completed)
        self.failed_exec.connect(self.signals.failed)

    def run(self) -> None:
        self.started_exec.emit()

        if self._is_cancelled:
            return

        # Prefer running with dedicated CLI demo flag and --json
        args = [self.category.cli_flag, "--json"]
        stdin_data = None

        result: ExecutionResult = self.runner.execute(
            args=args,
            stdin_data=stdin_data,
            timeout=25.0,
        )

        if self._is_cancelled:
            return

        if result.is_timeout:
            self.failed_exec.emit("Linux / POSIX experiment timed out. The backend exceeded 25 seconds.")
            return

        if not result.stdout:
            # Fallback to interactive stdin menu if demo flag was not available
            try:
                stdin_data = generate_linux_experiments_stdin(self.category)
                result = self.runner.execute(args=[], stdin_data=stdin_data, timeout=25.0)
            except Exception:
                pass

        if not result.stdout:
            err_msg = result.stderr.strip() or f"Process exited with code {result.exit_code} and produced no output."
            self.failed_exec.emit(f"Backend execution failure: {err_msg}")
            return

        try:
            parsed = parse_linux_experiments_output(
                result.stdout,
                self.category,
                exit_code=result.exit_code,
                duration_ms=result.duration * 1000.0,
            )
            self.finished_exec.emit(parsed)
        except Exception as e:
            self.failed_exec.emit(f"Linux experiments parsing error: {e}")

    def cancel(self) -> None:
        self._is_cancelled = True
        self.runner.cancel()


class HostMonitorWorker(QThread):
    """Executes live Linux / WSL host resource monitoring either as single-shot or background polling."""

    sample_received = Signal(object)  # HostMonitoringSnapshotModel
    failed_sample = Signal(str)
    monitoring_started = Signal()
    monitoring_stopped = Signal()

    def __init__(
        self,
        runner: BaseBackendRunner,
        poll_interval_ms: int = 2000,
        continuous: bool = False,
        parent: Optional[QThread] = None,
    ) -> None:
        super().__init__(parent)
        self.runner = runner
        self.poll_interval_ms = max(500, poll_interval_ms)
        self.continuous = continuous
        self._is_cancelled = False

    def run(self) -> None:
        if self._is_cancelled:
            return

        if self.continuous:
            self.monitoring_started.emit()

        while not self._is_cancelled:
            result = self.runner.execute(
                args=["--demo-monitor", "--json"],
                stdin_data=None,
                timeout=10.0,
            )

            if self._is_cancelled:
                break

            if result.is_timeout:
                self.failed_sample.emit("Host monitoring sample timed out after 10s.")
            elif not result.stdout:
                # Fallback to human-readable mode if json flag failed
                result = self.runner.execute(args=["--demo-monitor"], timeout=10.0)
                if not result.stdout:
                    err_msg = result.stderr.strip() or f"Process exited with code {result.exit_code}."
                    self.failed_sample.emit(f"Host monitoring failed: {err_msg}")
                else:
                    try:
                        snapshot = parse_host_monitoring_output(
                            result.stdout,
                            exit_code=result.exit_code,
                            duration_ms=result.duration * 1000.0,
                        )
                        self.sample_received.emit(snapshot)
                    except Exception as e:
                        self.failed_sample.emit(f"Failed to parse host telemetry: {e}")
            else:
                try:
                    snapshot = parse_host_monitoring_output(
                        result.stdout,
                        exit_code=result.exit_code,
                        duration_ms=result.duration * 1000.0,
                    )
                    self.sample_received.emit(snapshot)
                except Exception as e:
                    self.failed_sample.emit(f"Failed to parse host telemetry: {e}")

            if not self.continuous or self._is_cancelled:
                break

            # Responsive sleep loop
            sleep_slices = max(1, self.poll_interval_ms // 100)
            for _ in range(sleep_slices):
                if self._is_cancelled:
                    break
                self.msleep(100)

        if self.continuous:
            self.monitoring_stopped.emit()

    def stop(self) -> None:
        """Gracefully stop continuous polling."""
        self._is_cancelled = True

    def cancel(self) -> None:
        """Immediately stop and cancel backend runner process."""
        self._is_cancelled = True
        self.runner.cancel()


class FilesystemWorker(QThread):
    """Executes educational file system simulation in a background thread."""

    started_exec = Signal()
    finished_exec = Signal(object)  # Emits FilesystemSimulationResultModel
    failed_exec = Signal(str)       # Emits error description

    def __init__(
        self,
        runner: BaseBackendRunner,
        config: FilesystemConfig,
        parent: Optional[QThread] = None,
    ) -> None:
        super().__init__(parent)
        self.runner = runner
        self.config = config
        self._is_cancelled = False
        self.signals = WorkerSignals()

        self.finished_exec.connect(self.signals.completed)
        self.failed_exec.connect(self.signals.failed)

    def run(self) -> None:
        self.started_exec.emit()

        cfg_err = self.config.validate()
        if cfg_err:
            self.failed_exec.emit(cfg_err)
            return

        stdin_data: Optional[str] = None
        if self.config.preset == FilesystemPreset.STANDARD_DEMO:
            args = ["--demo-fs", "--json"]
        elif self.config.preset == FilesystemPreset.FRAGMENTATION:
            args = ["--demo-fs-frag", "--json"]
        elif self.config.preset == FilesystemPreset.CAPACITY_LIMIT:
            args = ["--demo-fs-full", "--json"]
        elif self.config.preset == FilesystemPreset.CUSTOM_WORKLOAD:
            args = ["--fs-ops", "--json"]
            try:
                stdin_data = generate_filesystem_stdin(self.config)
            except Exception as e:
                self.failed_exec.emit(f"Failed to generate filesystem input: {e}")
                return
        else:
            args = ["--demo-fs", "--json"]

        result = self.runner.execute(args=args, stdin_data=stdin_data, timeout=10.0)

        if self._is_cancelled:
            return

        if result.is_timeout:
            self.failed_exec.emit("Filesystem simulation timed out after 10.0 seconds.")
            return

        if not result.stdout:
            # Fallback to human-readable output if JSON output is empty
            fallback_args = [a for a in args if a != "--json"]
            result = self.runner.execute(args=fallback_args, stdin_data=stdin_data, timeout=10.0)
            if not result.stdout:
                err = result.stderr.strip() or f"Process exited with code {result.exit_code}"
                self.failed_exec.emit(f"Filesystem backend execution failed: {err}")
                return

        try:
            parsed = parse_filesystem_output(
                result.stdout,
                preset=self.config.preset,
                exit_code=result.exit_code,
                duration_ms=result.duration * 1000.0,
            )
            self.finished_exec.emit(parsed)
        except Exception as e:
            self.failed_exec.emit(f"Failed to parse filesystem simulation output: {e}")

    def cancel(self) -> None:
        self._is_cancelled = True
        self.runner.cancel()


class AddressTranslationWorker(QThread):
    """Executes virtual address translation, demand paging, and thrashing simulation."""

    started_exec = Signal()
    finished_exec = Signal(object)
    failed_exec = Signal(str)

    def __init__(
        self,
        runner: BaseBackendRunner,
        config: AddressTranslationConfig,
        parent: Optional[QObject] = None,
    ) -> None:
        super().__init__(parent)
        self.runner = runner
        self.config = config
        self._is_cancelled = False
        self.signals = WorkerSignals()

    def run(self) -> None:
        if self._is_cancelled:
            return

        self.started_exec.emit()

        if self.config.mode == "custom":
            try:
                stdin_data = generate_paging_ops_stdin(self.config)
            except Exception as e:
                self.failed_exec.emit(f"Failed to generate paging operations input: {e}")
                self.signals.failed.emit(f"Failed to generate paging operations input: {e}")
                return
            args = ["--paging-ops", "--json"]
        else:
            stdin_data = None
            args = ["--demo-paging", "--json"]

        result = self.runner.execute(args=args, stdin_data=stdin_data, timeout=10.0)

        if self._is_cancelled:
            return

        if result.is_timeout:
            msg = "Address translation simulation timed out after 10.0 seconds."
            self.failed_exec.emit(msg)
            self.signals.failed.emit(msg)
            return

        if not result.stdout:
            fallback_args = [a for a in args if a != "--json"]
            result = self.runner.execute(args=fallback_args, stdin_data=stdin_data, timeout=10.0)
            if not result.stdout:
                err = result.stderr.strip() or f"Process exited with code {result.exit_code}"
                msg = f"Address translation backend failed: {err}"
                self.failed_exec.emit(msg)
                self.signals.failed.emit(msg)
                return

        try:
            parsed = parse_address_translation_output(result.stdout, config=self.config)
            self.finished_exec.emit(parsed)
            self.signals.completed.emit(parsed)
        except Exception as e:
            msg = f"Failed to parse address translation output: {e}"
            self.failed_exec.emit(msg)
            self.signals.failed.emit(msg)

    def cancel(self) -> None:
        self._is_cancelled = True
        self.runner.cancel()


class ProcessLifecycleWorker(QThread):
    """Executes process lifecycle state machine simulation via authoritative C++ ProcessManager."""

    started_exec = Signal()
    finished_exec = Signal(object)
    failed_exec = Signal(str)

    def __init__(
        self,
        runner: BaseBackendRunner,
        config: ProcessLifecycleConfig,
        parent: Optional[QObject] = None,
    ) -> None:
        super().__init__(parent)
        self.runner = runner
        self.config = config
        self._is_cancelled = False
        self.signals = WorkerSignals()

    def run(self) -> None:
        if self._is_cancelled:
            return

        self.started_exec.emit()

        if self.config.mode == "custom":
            try:
                stdin_data = generate_process_ops_stdin(self.config)
            except Exception as e:
                msg = f"Failed to generate process operations input: {e}"
                self.failed_exec.emit(msg)
                self.signals.failed.emit(msg)
                return
            args = ["--process-ops", "--json"]
        else:
            stdin_data = None
            args = ["--demo-process", "--json"]

        result = self.runner.execute(args=args, stdin_data=stdin_data, timeout=10.0)

        if self._is_cancelled:
            return

        if result.is_timeout:
            msg = "Process lifecycle simulation timed out after 10.0 seconds."
            self.failed_exec.emit(msg)
            self.signals.failed.emit(msg)
            return

        if not result.stdout:
            fallback_args = [a for a in args if a != "--json"]
            result = self.runner.execute(args=fallback_args, stdin_data=stdin_data, timeout=10.0)
            if not result.stdout:
                err = result.stderr.strip() or f"Process exited with code {result.exit_code}"
                msg = f"Process lifecycle backend failed: {err}"
                self.failed_exec.emit(msg)
                self.signals.failed.emit(msg)
                return

        try:
            parsed = parse_process_lifecycle_output(result.stdout)
            self.finished_exec.emit(parsed)
            self.signals.completed.emit(parsed)
        except Exception as e:
            msg = f"Failed to parse process lifecycle output: {e}"
            self.failed_exec.emit(msg)
            self.signals.failed.emit(msg)

    def cancel(self) -> None:
        self._is_cancelled = True
        self.runner.cancel()






