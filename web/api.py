"""OScope Web API Bridge.

Connects the HTTP server to the C++ OScope simulation backend,
translating frontend JSON requests into domain models, generating stdin,
invoking the WSL/native runner, and returning structured JSON responses.
"""

import dataclasses
from enum import Enum
import os
from pathlib import Path
import sys
from typing import Any, Dict, List, Optional

# Ensure gui directory is on sys.path to access oscope_gui modules
repo_root = Path(__file__).resolve().parent.parent
gui_dir = repo_root / "gui"
if str(gui_dir) not in sys.path:
    sys.path.insert(0, str(gui_dir))

from oscope_gui.backend.runner import discover_backend, BaseBackendRunner, BackendInfo
from oscope_gui.backend.parser import (
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
    parse_process_lifecycle_output,
    parse_scheduling_output,
)

from oscope_gui.models.scheduling import AlgorithmConfig, AlgorithmType, ProcessInput
from oscope_gui.models.memory import MemoryConfig, MemoryStrategy, MemoryOperationInput
from oscope_gui.models.paging import PagingConfig, PagingAlgorithm
from oscope_gui.models.deadlock import DeadlockConfig, DeadlockMode
from oscope_gui.models.disk import DiskConfig, DiskAlgorithm, DiskDirection
from oscope_gui.models.linux_experiments import LinuxExperimentCategory
from oscope_gui.models.filesystem import (
    FilesystemConfig,
    FilesystemPreset,
    FilesystemAllocationStrategy,
    FilesystemOperationInput,
    FilesystemOperationType,
)
from oscope_gui.models.address_translation import AddressTranslationConfig
from oscope_gui.models.process_lifecycle import ProcessLifecycleConfig


def to_dict(obj: Any) -> Any:
    """Recursively convert dataclasses and enums into JSON-serializable primitives."""
    if dataclasses.is_dataclass(obj):
        return {k: to_dict(v) for k, v in dataclasses.asdict(obj).items()}
    elif isinstance(obj, Enum):
        return obj.value
    elif isinstance(obj, list):
        return [to_dict(x) for x in obj]
    elif isinstance(obj, dict):
        return {k: to_dict(v) for k, v in obj.items()}
    return obj


class OScopeApiHandler:
    """Handles API requests and routes them to the simulation runner."""

    def __init__(self, runner: Optional[BaseBackendRunner] = None) -> None:
        if runner is None:
            self.runner, self.info = discover_backend(str(repo_root))
        else:
            self.runner = runner
            self.info = runner.get_info()

    def get_status(self) -> Dict[str, Any]:
        """Return backend connection status and environment metadata."""
        info = self.runner.get_info()
        return {
            "is_available": info.is_available,
            "runner_type": info.runner_type,
            "executable_path": info.executable_path,
            "status_message": info.status_message,
            "distro": getattr(info, "distro", None),
        }

    # 1. CPU Scheduling
    def run_scheduling(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        algo_str = payload.get("algorithm", "FCFS")
        try:
            algo_type = AlgorithmType(algo_str)
        except ValueError:
            # Match by value or fallback
            matched = False
            for at in AlgorithmType:
                if at.value.lower() == algo_str.lower() or at.name.lower() == algo_str.lower():
                    algo_type = at
                    matched = True
                    break
            if not matched:
                raise ValueError(f"Unknown scheduling algorithm: '{algo_str}'")

        config = AlgorithmConfig(
            algorithm=algo_type,
            rr_quantum=int(payload.get("rr_quantum", 4)),
            mlfq_q0=int(payload.get("mlfq_q0", 4)),
            mlfq_q1=int(payload.get("mlfq_q1", 8)),
            mlfq_q2=int(payload.get("mlfq_q2", 16)),
        )

        cfg_err = config.validate()
        if cfg_err:
            raise ValueError(cfg_err)

        processes = []
        for p_data in payload.get("processes", []):
            p = ProcessInput(
                pid=int(p_data["pid"]),
                arrival_time=int(p_data["arrival_time"]),
                burst_time=int(p_data["burst_time"]),
                priority=int(p_data.get("priority", 0)),
            )
            p_err = p.validate()
            if p_err:
                raise ValueError(p_err)
            processes.append(p)

        if not processes:
            raise ValueError("Process list cannot be empty.")

        stdin_data = generate_scheduling_stdin(config, processes)
        res = self.runner.execute([], stdin_data=stdin_data, timeout=25.0)

        if not res.is_success:
            raise RuntimeError(res.stderr.strip() or f"Execution failed with code {res.exit_code}")

        if config.algorithm == AlgorithmType.COMPARE_ALL:
            model = parse_comparison_output(res.stdout)
        else:
            model = parse_scheduling_output(res.stdout, config.algorithm.display_name)

        return to_dict(model)

    # 2. Dynamic Memory Allocation
    def run_memory(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        strat_str = payload.get("strategy", "First Fit")
        try:
            strategy = MemoryStrategy(strat_str)
        except ValueError:
            matched = False
            for ms in MemoryStrategy:
                if ms.value.lower() == strat_str.lower() or ms.name.lower() == strat_str.lower():
                    strategy = ms
                    matched = True
                    break
            if not matched:
                raise ValueError(f"Unknown memory strategy: '{strat_str}'")

        total_mem = int(payload.get("total_memory", 1000))
        config = MemoryConfig(strategy=strategy, total_memory=total_mem)
        cfg_err = config.validate()
        if cfg_err:
            raise ValueError(cfg_err)

        from oscope_gui.models.memory import MemoryOperationType
        operations = []
        for i, op_data in enumerate(payload.get("operations", [])):
            op_t_str = str(op_data.get("op_type", op_data.get("operation_type", "alloc"))).lower()
            op_type = MemoryOperationType.ALLOCATE if "alloc" in op_t_str else MemoryOperationType.DEALLOCATE
            req_id = int(op_data.get("request_id", i + 1))
            pid_val = op_data.get("process_id", op_data.get("pid"))
            pid = int(pid_val) if pid_val is not None else None
            size = int(op_data.get("size", 0))

            op = MemoryOperationInput(
                op_type=op_type,
                request_id=req_id,
                size=size,
                process_id=pid,
            )
            op_err = op.validate()
            if op_err:
                raise ValueError(op_err)
            operations.append(op)

        if not operations:
            raise ValueError("Memory operations list cannot be empty.")

        stdin_data = generate_memory_stdin(config, operations)
        res = self.runner.execute([], stdin_data=stdin_data, timeout=25.0)

        if not res.is_success:
            raise RuntimeError(res.stderr.strip() or f"Execution failed with code {res.exit_code}")

        if config.strategy == MemoryStrategy.COMPARE_ALL:
            model = parse_memory_comparison_output(res.stdout)
        else:
            model = parse_memory_output(res.stdout, config.strategy.value)

        return to_dict(model)

    # 3. Page Replacement
    def run_paging(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        algo_str = payload.get("algorithm", "FIFO")
        try:
            algo = PagingAlgorithm(algo_str)
        except ValueError:
            matched = False
            for pa in PagingAlgorithm:
                if pa.value.lower() == algo_str.lower() or pa.name.lower() == algo_str.lower():
                    algo = pa
                    matched = True
                    break
            if not matched:
                raise ValueError(f"Unknown paging algorithm: '{algo_str}'")

        frame_count = int(payload.get("num_frames", payload.get("frame_count", 3)))
        ref_raw = payload.get("reference_string", [7, 0, 1, 2, 0, 3, 0, 4, 2, 3, 0, 3, 2, 1, 2, 0, 1, 7, 0, 1])
        ref_string = [int(x) for x in ref_raw]

        config = PagingConfig(algorithm=algo, frame_count=frame_count, reference_string=ref_string)
        cfg_err = config.validate()
        if cfg_err:
            raise ValueError(cfg_err)

        stdin_data = generate_paging_stdin(config)
        res = self.runner.execute([], stdin_data=stdin_data, timeout=25.0)

        if not res.is_success:
            raise RuntimeError(res.stderr.strip() or f"Execution failed with code {res.exit_code}")

        if config.algorithm == PagingAlgorithm.COMPARE_ALL:
            model = parse_paging_comparison_output(res.stdout, config.frame_count, config.reference_string)
        else:
            model = parse_paging_output(res.stdout, config.algorithm.value, config.frame_count, config.reference_string)

        return to_dict(model)

    # 4. Deadlock Management
    def run_deadlock(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        mode_str = payload.get("mode", "safety")
        mode = DeadlockMode(mode_str)
        num_p = int(payload.get("num_processes", 5))
        num_r = int(payload.get("num_resources", 3))

        available = [int(x) for x in payload.get("available", [])]
        allocation = [[int(x) for x in row] for row in payload.get("allocation", [])]
        max_claim = [[int(x) for x in row] for row in payload.get("max_claim", payload.get("max_matrix", []))]
        req_matrix = [[int(x) for x in row] for row in payload.get("request_matrix", [])]

        config = DeadlockConfig(
            mode=mode,
            num_processes=num_p,
            num_resources=num_r,
            available=available,
            allocation=allocation,
            max_claim=max_claim if mode != DeadlockMode.DETECTION else [[0]*num_r for _ in range(num_p)],
            request_matrix=req_matrix if mode == DeadlockMode.DETECTION else [],
            requesting_process_id=int(payload.get("requesting_process_id", payload.get("request_pid", 0))),
            request_vector=[int(x) for x in payload.get("request_vector", [])],
        )

        cfg_err = config.validate()
        if cfg_err:
            raise ValueError(cfg_err)

        stdin_data = generate_deadlock_stdin(config)
        res = self.runner.execute([], stdin_data=stdin_data, timeout=25.0)

        if not res.is_success:
            raise RuntimeError(res.stderr.strip() or f"Execution failed with code {res.exit_code}")

        if mode == DeadlockMode.SAFETY:
            model = parse_deadlock_safety_output(res.stdout, config)
        elif mode == DeadlockMode.REQUEST:
            model = parse_deadlock_request_output(res.stdout, config)
        else:
            model = parse_deadlock_detection_output(res.stdout, config)

        return to_dict(model)

    # 5. Disk Scheduling
    def run_disk(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        algo_str = payload.get("algorithm", "FCFS")
        try:
            algo = DiskAlgorithm(algo_str)
        except ValueError:
            matched = False
            for da in DiskAlgorithm:
                if da.value.lower() == algo_str.lower() or da.name.lower() == algo_str.lower():
                    algo = da
                    matched = True
                    break
            if not matched:
                raise ValueError(f"Unknown disk algorithm: '{algo_str}'")

        direction_str = str(payload.get("direction", "increasing")).lower()
        direction = DiskDirection.INCREASING if ("up" in direction_str or "high" in direction_str or "inc" in direction_str) else DiskDirection.DECREASING

        requests = [int(x) for x in payload.get("requests", payload.get("track_requests", [98, 183, 37, 122, 14, 124, 65, 67]))]
        init_head = int(payload.get("initial_head", payload.get("initial_cylinder", payload.get("head_start", 53))))
        min_cyl = int(payload.get("min_cylinder", 0))
        max_cyl = int(payload.get("max_cylinder", payload.get("total_cylinders", 200) - 1))

        config = DiskConfig(
            algorithm=algo,
            min_cylinder=min_cyl,
            max_cylinder=max_cyl,
            initial_head=init_head,
            direction=direction,
            requests=requests,
        )

        cfg_err = config.validate()
        if cfg_err:
            raise ValueError(cfg_err)

        stdin_data = generate_disk_stdin(config)
        res = self.runner.execute([], stdin_data=stdin_data, timeout=25.0)

        if not res.is_success:
            raise RuntimeError(res.stderr.strip() or f"Execution failed with code {res.exit_code}")

        if config.algorithm == DiskAlgorithm.COMPARE_ALL:
            model = parse_disk_comparison_output(res.stdout, config)
        else:
            model = parse_disk_output(res.stdout, config)

        return to_dict(model)

    # 6. Linux/POSIX Experiments
    def run_linux(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        cat_str = payload.get("category", "all")
        cat_map = {
            "all": LinuxExperimentCategory.ALL,
            "run_all": LinuxExperimentCategory.ALL,
            "lifecycle": LinuxExperimentCategory.LIFECYCLE,
            "sync": LinuxExperimentCategory.SYNCHRONIZATION,
            "synchronization": LinuxExperimentCategory.SYNCHRONIZATION,
            "producer_consumer": LinuxExperimentCategory.PRODUCER_CONSUMER,
            "ipc": LinuxExperimentCategory.IPC,
            "pipe": LinuxExperimentCategory.IPC,
            "shm": LinuxExperimentCategory.IPC,
        }
        category = cat_map.get(cat_str.lower(), LinuxExperimentCategory.ALL)
        args = [category.cli_flag, "--json"]
        res = self.runner.execute(args=args, timeout=25.0)

        if not res.stdout:
            fallback = [a for a in args if a != "--json"]
            res = self.runner.execute(args=fallback, timeout=25.0)

        if not res.stdout:
            raise RuntimeError(res.stderr.strip() or f"Linux experiment failed with code {res.exit_code}")

        model = parse_linux_experiments_output(res.stdout, category)
        return to_dict(model)

    # 7. Host Monitoring
    def run_host_monitor(self) -> Dict[str, Any]:
        res = self.runner.execute(["--demo-monitor", "-j"], timeout=10.0)
        if not res.stdout:
            # Fallback without -j
            res = self.runner.execute(["--demo-monitor"], timeout=10.0)
        if not res.stdout:
            raise RuntimeError(res.stderr.strip() or "Host monitor produced no output.")

        model = parse_host_monitoring_output(res.stdout)
        return to_dict(model)

    # 8. Simulated File System
    def run_filesystem(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        preset_str = payload.get("preset", "standard_demo")
        strat_str = payload.get("allocation_strategy", "Contiguous")
        strategy = FilesystemAllocationStrategy.from_str(strat_str)

        preset_map = {
            "standard_demo": FilesystemPreset.STANDARD_DEMO,
            "demo_educational": FilesystemPreset.STANDARD_DEMO,
            "fragmentation": FilesystemPreset.FRAGMENTATION,
            "demo_fragmentation": FilesystemPreset.FRAGMENTATION,
            "capacity_limit": FilesystemPreset.CAPACITY_LIMIT,
            "demo_full": FilesystemPreset.CAPACITY_LIMIT,
            "custom_workload": FilesystemPreset.CUSTOM_WORKLOAD,
            "custom": FilesystemPreset.CUSTOM_WORKLOAD,
        }
        preset = preset_map.get(preset_str, FilesystemPreset.STANDARD_DEMO)

        operations = []
        if preset == FilesystemPreset.CUSTOM_WORKLOAD:
            for op_d in payload.get("operations", []):
                operations.append(
                    FilesystemOperationInput(
                        op_type=FilesystemOperationType(op_d.get("operation_type", "create")),
                        path=op_d.get("path", "/file.txt"),
                        size_bytes=int(op_d.get("size_bytes", op_d.get("size", 512))),
                        strategy=strategy,
                    )
                )

        config = FilesystemConfig(
            preset=preset,
            total_blocks=int(payload.get("total_blocks", 32)),
            block_size=int(payload.get("block_size", payload.get("block_size_bytes", 512))),
            operations=operations,
        )

        args = []
        stdin_data = None
        if preset == FilesystemPreset.STANDARD_DEMO:
            args = ["--demo-fs", "--json"]
        elif preset == FilesystemPreset.FRAGMENTATION:
            args = ["--demo-fs-frag", "--json"]
        elif preset == FilesystemPreset.CAPACITY_LIMIT:
            args = ["--demo-fs-full", "--json"]
        else:
            args = ["--fs-ops", "--json"]
            stdin_data = generate_filesystem_stdin(config)

        res = self.runner.execute(args=args, stdin_data=stdin_data, timeout=15.0)
        if not res.stdout:
            fallback = [a for a in args if a != "--json"]
            res = self.runner.execute(args=fallback, stdin_data=stdin_data, timeout=15.0)

        if not res.stdout:
            raise RuntimeError(res.stderr.strip() or f"Filesystem backend failed with exit code {res.exit_code}")

        model = parse_filesystem_output(res.stdout, preset=preset, exit_code=res.exit_code, duration_ms=res.duration * 1000)
        return to_dict(model)

    # 9. Address Translation & MMU
    def run_address_translation(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        mode = payload.get("mode", "demo")
        page_size = int(payload.get("page_size", 4096))
        num_frames = int(payload.get("num_frames", 4))
        logical_addrs = [int(x) for x in payload.get("logical_addresses", [0, 4096, 8192, 12288, 16384])]

        config = AddressTranslationConfig(
            mode=mode,
            page_size=page_size,
            demand_paging_frames=num_frames,
            virtual_addresses_to_translate=logical_addrs,
        )

        args = ["--demo-paging", "--json"] if mode != "custom" else ["--paging-ops", "--json"]
        stdin_data = generate_paging_ops_stdin(config) if mode == "custom" else None

        res = self.runner.execute(args=args, stdin_data=stdin_data, timeout=15.0)
        if not res.stdout:
            fallback = [a for a in args if a != "--json"]
            res = self.runner.execute(args=fallback, stdin_data=stdin_data, timeout=15.0)

        if not res.stdout:
            raise RuntimeError(res.stderr.strip() or f"Address translation backend failed with exit code {res.exit_code}")

        model = parse_address_translation_output(res.stdout, config=config)
        return to_dict(model)

    # 10. Process Lifecycle
    def run_process_lifecycle(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        mode = payload.get("mode", "demo")
        config = ProcessLifecycleConfig(mode=mode)

        args = ["--demo-process", "--json"] if mode != "custom" else ["--process-ops", "--json"]
        stdin_data = generate_process_ops_stdin(config) if mode == "custom" else None

        res = self.runner.execute(args=args, stdin_data=stdin_data, timeout=15.0)
        if not res.stdout:
            fallback = [a for a in args if a != "--json"]
            res = self.runner.execute(args=fallback, stdin_data=stdin_data, timeout=15.0)

        if not res.stdout:
            raise RuntimeError(res.stderr.strip() or f"Process lifecycle backend failed with exit code {res.exit_code}")

        model = parse_process_lifecycle_output(res.stdout)
        return to_dict(model)
