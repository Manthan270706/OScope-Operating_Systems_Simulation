"""Backend runners for executing the C++ OScope binary natively or via WSL."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
import os
from pathlib import Path
import shutil
import subprocess
import time
from typing import List, Optional, Tuple


@dataclass
class ExecutionResult:
    """Result of running the C++ backend process."""
    exit_code: int
    stdout: str
    stderr: str
    duration: float
    is_timeout: bool = False
    command: List[str] = field(default_factory=list)

    @property
    def is_success(self) -> bool:
        return self.exit_code == 0 and not self.is_timeout


@dataclass
class BackendInfo:
    """Metadata describing the active backend engine."""
    runner_type: str  # "native", "wsl", "mock", "none"
    executable_path: str
    is_available: bool
    status_message: str
    distro: Optional[str] = None
    wsl_repo_dir: Optional[str] = None


def to_wsl_path(win_path: str) -> str:
    """Convert Windows path (e.g. D:\\College\\...) to WSL path (/mnt/d/College/...)."""
    p = Path(win_path).resolve()
    drive = p.drive.rstrip(":").lower()
    if drive:
        tail = p.as_posix()[len(p.drive):]
        return f"/mnt/{drive}{tail}"
    return p.as_posix()


class BaseBackendRunner(ABC):
    """Abstract runner interface separating UI from backend execution strategy."""

    @abstractmethod
    def execute(
        self,
        args: List[str],
        stdin_data: Optional[str] = None,
        timeout: float = 15.0,
    ) -> ExecutionResult:
        """Run the backend executable with given args and optional stdin."""
        raise NotImplementedError

    @abstractmethod
    def verify(self) -> Tuple[bool, str]:
        """Verify that the backend binary is accessible and executable."""
        raise NotImplementedError

    @abstractmethod
    def get_info(self) -> BackendInfo:
        """Return backend metadata and configuration."""
        raise NotImplementedError

    def cancel(self) -> None:
        """Terminate active execution if supported."""
        pass


class WSLBackendRunner(BaseBackendRunner):
    """Executes the Linux ELF oscope executable inside WSL via wsl.exe."""

    def __init__(
        self,
        repo_dir: str,
        rel_exe_path: str = "./build/oscope",
        distro: Optional[str] = None,
        wsl_binary: Optional[str] = None,
    ) -> None:
        self.repo_dir = repo_dir
        self.rel_exe_path = rel_exe_path
        self.distro = distro
        self.wsl_binary = wsl_binary or shutil.which("wsl.exe") or "wsl.exe"
        self.wsl_repo_dir = to_wsl_path(repo_dir)
        self._current_process: Optional[subprocess.Popen] = None

    def _build_cmd(self, args: List[str]) -> List[str]:
        cmd = [self.wsl_binary]
        if self.distro:
            cmd.extend(["-d", self.distro])
        cmd.extend(["--cd", self.wsl_repo_dir, self.rel_exe_path])
        cmd.extend(args)
        return cmd

    def execute(
        self,
        args: List[str],
        stdin_data: Optional[str] = None,
        timeout: float = 15.0,
    ) -> ExecutionResult:
        cmd = self._build_cmd(args)
        start_time = time.perf_counter()
        try:
            # Normalize stdin newlines to standard UNIX \n for C++ std::getline
            normalized_stdin = stdin_data.replace("\r\n", "\n") if stdin_data else None

            proc = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE if normalized_stdin is not None else None,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            self._current_process = proc

            stdout, stderr = proc.communicate(input=normalized_stdin, timeout=timeout)
            duration = time.perf_counter() - start_time
            self._current_process = None
            return ExecutionResult(
                exit_code=proc.returncode,
                stdout=stdout,
                stderr=stderr,
                duration=duration,
                is_timeout=False,
                command=cmd,
            )
        except subprocess.TimeoutExpired:
            if self._current_process:
                try:
                    self._current_process.kill()
                    self._current_process.communicate()
                except Exception:
                    pass
                self._current_process = None
            return ExecutionResult(
                exit_code=-1,
                stdout="",
                stderr=f"Process timed out after {timeout:.1f} seconds.",
                duration=time.perf_counter() - start_time,
                is_timeout=True,
                command=cmd,
            )
        except Exception as e:
            self._current_process = None
            return ExecutionResult(
                exit_code=-1,
                stdout="",
                stderr=f"Failed to execute WSL command: {e}",
                duration=time.perf_counter() - start_time,
                is_timeout=False,
                command=cmd,
            )

    def verify(self) -> Tuple[bool, str]:
        """Check if wsl.exe and the build/oscope executable are both reachable."""
        res = self.execute(["--help"], timeout=5.0)
        if res.is_success and "OScope" in res.stdout:
            return True, f"WSL bridge active. C++ backend verified at {self.rel_exe_path}."
        err_msg = res.stderr.strip() or "Executable produced non-zero exit code or missing output."
        return False, f"WSL backend verification failed: {err_msg}"

    def cancel(self) -> None:
        if self._current_process:
            try:
                self._current_process.terminate()
            except Exception:
                pass

    def get_info(self) -> BackendInfo:
        ok, msg = self.verify()
        return BackendInfo(
            runner_type="wsl",
            executable_path=f"{self.wsl_repo_dir}/{self.rel_exe_path.lstrip('./')}",
            is_available=ok,
            status_message=msg,
            distro=self.distro or "Default WSL",
            wsl_repo_dir=self.wsl_repo_dir,
        )


class NativeBackendRunner(BaseBackendRunner):
    """Executes a native Windows build of oscope (oscope.exe)."""

    def __init__(self, exe_path: str, repo_dir: str) -> None:
        self.exe_path = exe_path
        self.repo_dir = repo_dir
        self._current_process: Optional[subprocess.Popen] = None

    def execute(
        self,
        args: List[str],
        stdin_data: Optional[str] = None,
        timeout: float = 15.0,
    ) -> ExecutionResult:
        cmd = [self.exe_path] + args
        start_time = time.perf_counter()
        try:
            normalized_stdin = stdin_data.replace("\r\n", "\n") if stdin_data else None

            proc = subprocess.Popen(
                cmd,
                cwd=self.repo_dir,
                stdin=subprocess.PIPE if normalized_stdin is not None else None,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            self._current_process = proc

            stdout, stderr = proc.communicate(input=normalized_stdin, timeout=timeout)
            duration = time.perf_counter() - start_time
            self._current_process = None
            return ExecutionResult(
                exit_code=proc.returncode,
                stdout=stdout,
                stderr=stderr,
                duration=duration,
                is_timeout=False,
                command=cmd,
            )
        except subprocess.TimeoutExpired:
            if self._current_process:
                try:
                    self._current_process.kill()
                    self._current_process.communicate()
                except Exception:
                    pass
                self._current_process = None
            return ExecutionResult(
                exit_code=-1,
                stdout="",
                stderr=f"Process timed out after {timeout:.1f} seconds.",
                duration=time.perf_counter() - start_time,
                is_timeout=True,
                command=cmd,
            )
        except Exception as e:
            self._current_process = None
            return ExecutionResult(
                exit_code=-1,
                stdout="",
                stderr=f"Failed to execute native binary: {e}",
                duration=time.perf_counter() - start_time,
                is_timeout=False,
                command=cmd,
            )

    def verify(self) -> Tuple[bool, str]:
        if not os.path.isfile(self.exe_path):
            return False, f"Native executable not found at '{self.exe_path}'."
        res = self.execute(["--help"], timeout=5.0)
        if res.is_success and "OScope" in res.stdout:
            return True, f"Native Windows backend verified at '{self.exe_path}'."
        return False, f"Native binary failed verification: {res.stderr.strip()}"

    def cancel(self) -> None:
        if self._current_process:
            try:
                self._current_process.terminate()
            except Exception:
                pass

    def get_info(self) -> BackendInfo:
        ok, msg = self.verify()
        return BackendInfo(
            runner_type="native",
            executable_path=self.exe_path,
            is_available=ok,
            status_message=msg,
        )


def discover_backend(repo_dir: Optional[str] = None) -> Tuple[BaseBackendRunner, BackendInfo]:
    """
    Auto-detect the appropriate backend runner:
    1. Check for explicit OSCOPE_BINARY env var or native build/oscope.exe
    2. Check for WSL availability and build/oscope binary inside WSL
    """
    if repo_dir is None:
        # Default to repo root (two levels up from this file)
        repo_dir = str(Path(__file__).resolve().parent.parent.parent.parent)

    # 1. Check for native Windows binary
    env_bin = os.environ.get("OSCOPE_BINARY")
    candidate_native_paths = [
        env_bin,
        os.path.join(repo_dir, "build", "oscope.exe"),
        os.path.join(repo_dir, "build", "Release", "oscope.exe"),
        os.path.join(repo_dir, "build", "Debug", "oscope.exe"),
    ]

    for cand in candidate_native_paths:
        if cand and os.path.isfile(cand):
            runner = NativeBackendRunner(cand, repo_dir)
            info = runner.get_info()
            if info.is_available:
                return runner, info

    # 2. Check for WSL bridge
    wsl_bin = shutil.which("wsl.exe") or "C:\\Windows\\System32\\wsl.exe"
    if os.path.isfile(wsl_bin) or shutil.which("wsl.exe"):
        runner = WSLBackendRunner(repo_dir, rel_exe_path="./build/oscope")
        info = runner.get_info()
        if info.is_available:
            return runner, info
        else:
            # WSL found but oscope binary may need to be compiled
            return runner, info

    # 3. Fallback: unavailable
    fallback_info = BackendInfo(
        runner_type="none",
        executable_path="",
        is_available=False,
        status_message="Neither native oscope.exe nor WSL wsl.exe found. Build C++ backend first.",
    )
    return WSLBackendRunner(repo_dir), fallback_info
