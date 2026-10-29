"""Unit tests for backend runners, path translation, and execution handling."""

import os
from pathlib import Path
import pytest

from oscope_gui.backend.runner import (
    BackendInfo,
    BaseBackendRunner,
    ExecutionResult,
    NativeBackendRunner,
    WSLBackendRunner,
    discover_backend,
    to_wsl_path,
)


def test_to_wsl_path():
    assert to_wsl_path("D:\\College\\3rd_Year\\OS\\OS_CP") == "/mnt/d/College/3rd_Year/OS/OS_CP"
    assert to_wsl_path("C:\\Users\\Nitish Sahu\\repo") == "/mnt/c/Users/Nitish Sahu/repo"


def test_wsl_runner_command_construction():
    runner = WSLBackendRunner(
        repo_dir="D:\\College\\3rd_Year\\OS\\OS_CP",
        rel_exe_path="./build/oscope",
        distro="Ubuntu",
        wsl_binary="wsl.exe",
    )
    cmd = runner._build_cmd(["--demo-all", "--json"])
    assert cmd == [
        "wsl.exe",
        "-d",
        "Ubuntu",
        "--cd",
        "/mnt/d/College/3rd_Year/OS/OS_CP",
        "./build/oscope",
        "--demo-all",
        "--json",
    ]


class MockRunner(BaseBackendRunner):
    """Test double for verifying error handling without spawning child processes."""

    def __init__(self, exit_code: int = 0, stdout: str = "", stderr: str = "", is_timeout: bool = False):
        self.exit_code = exit_code
        self.stdout = stdout
        self.stderr = stderr
        self.is_timeout = is_timeout
        self.last_stdin = None

    def execute(self, args, stdin_data=None, timeout=15.0):
        self.last_stdin = stdin_data
        return ExecutionResult(
            exit_code=self.exit_code,
            stdout=self.stdout,
            stderr=self.stderr,
            duration=0.05,
            is_timeout=self.is_timeout,
            command=["mock_oscope"] + args,
        )

    def verify(self):
        return (self.exit_code == 0, "Mock runner active")

    def get_info(self):
        return BackendInfo(
            runner_type="mock",
            executable_path="mock_oscope",
            is_available=(self.exit_code == 0),
            status_message="Mock runner for testing",
        )


def test_mock_runner_execution_success():
    mock = MockRunner(exit_code=0, stdout="Simulation completed successfully.")
    res = mock.execute(["--help"])
    assert res.is_success
    assert res.exit_code == 0
    assert "Simulation completed" in res.stdout
    assert not res.is_timeout


def test_mock_runner_execution_timeout():
    mock = MockRunner(exit_code=-1, stdout="", stderr="Process timed out.", is_timeout=True)
    res = mock.execute([])
    assert not res.is_success
    assert res.is_timeout
    assert res.exit_code == -1


def test_mock_runner_execution_failure():
    mock = MockRunner(exit_code=1, stdout="", stderr="Error: invalid argument")
    res = mock.execute(["--invalid"])
    assert not res.is_success
    assert res.exit_code == 1
    assert "invalid argument" in res.stderr


def test_discover_backend():
    repo_root = str(Path(__file__).resolve().parent.parent.parent)
    runner, info = discover_backend(repo_root)

    assert runner is not None
    assert info is not None
    assert info.runner_type in ("wsl", "native", "none")
    # If WSL is available, info.is_available should be True
    if info.runner_type == "wsl":
        assert "oscope" in info.executable_path
