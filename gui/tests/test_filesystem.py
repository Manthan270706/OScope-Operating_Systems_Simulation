"""Focused unit and integration tests for Simulated File System GUI module."""

import json
import os
import pytest

os.environ["QT_QPA_PLATFORM"] = "offscreen"

from oscope_gui.backend.executor import FilesystemWorker
from oscope_gui.backend.parser import (
    generate_filesystem_stdin,
    parse_filesystem_output,
)
from oscope_gui.backend.runner import ExecutionResult
from oscope_gui.models.filesystem import (
    AllocationTraceModel,
    FileInodeModel,
    FilesystemAllocationStrategy,
    FilesystemConfig,
    FilesystemOperationInput,
    FilesystemOperationType,
    FilesystemPreset,
    FilesystemSimulationResultModel,
    FilesystemStatusModel,
)
from oscope_gui.pages.filesystem_page import FilesystemPage
from oscope_gui.widgets.filesystem_viz import (
    BlockAllocationMapWidget,
    DirectoryTreeBrowserWidget,
    FileMetadataPanel,
    FilesystemStatsBar,
)


class DummyFilesystemRunner:
    """Mock backend runner returning realistic C++ simulation JSON and text."""

    def __init__(self, mode: str = "json") -> None:
        self.mode = mode
        self.last_args = None
        self.last_stdin = None

    def execute(self, args, stdin_data=None, timeout=10.0):
        self.last_args = args
        self.last_stdin = stdin_data

        if self.mode == "json":
            sample_data = {
                "schema_version": "1.0.0",
                "category": "filesystem_simulation",
                "experiment": "simple_filesystem",
                "status": "success",
                "success": True,
                "result": {
                    "total_blocks": 32,
                    "block_size": 512,
                    "used_blocks": 8,
                    "free_blocks": 24,
                    "file_count": 3,
                    "directory_count": 3,
                    "block_bitmap": [True] * 8 + [False] * 24,
                    "inodes": [
                        {
                            "inode_id": 0,
                            "name": "/",
                            "path": "/",
                            "is_directory": True,
                            "size_bytes": 0,
                            "strategy": "Indexed",
                            "start_block": -1,
                            "index_block": -1,
                            "block_count": 0,
                            "allocated_blocks": [],
                        },
                        {
                            "inode_id": 1,
                            "name": "home",
                            "path": "/home",
                            "is_directory": True,
                            "size_bytes": 0,
                            "strategy": "Indexed",
                            "start_block": -1,
                            "index_block": -1,
                            "block_count": 0,
                            "allocated_blocks": [],
                        },
                        {
                            "inode_id": 2,
                            "name": "docs",
                            "path": "/home/docs",
                            "is_directory": True,
                            "size_bytes": 0,
                            "strategy": "Indexed",
                            "start_block": -1,
                            "index_block": -1,
                            "block_count": 0,
                            "allocated_blocks": [],
                        },
                        {
                            "inode_id": 3,
                            "name": "file_contiguous.bin",
                            "path": "/home/file_contiguous.bin",
                            "is_directory": False,
                            "size_bytes": 1500,
                            "strategy": "Contiguous",
                            "start_block": 0,
                            "index_block": -1,
                            "block_count": 3,
                            "allocated_blocks": [0, 1, 2],
                        },
                        {
                            "inode_id": 4,
                            "name": "file_linked.txt",
                            "path": "/home/file_linked.txt",
                            "is_directory": False,
                            "size_bytes": 1000,
                            "strategy": "Linked",
                            "start_block": 3,
                            "index_block": -1,
                            "block_count": 2,
                            "allocated_blocks": [3, 4],
                        },
                        {
                            "inode_id": 5,
                            "name": "file_indexed.dat",
                            "path": "/home/file_indexed.dat",
                            "is_directory": False,
                            "size_bytes": 1000,
                            "strategy": "Indexed",
                            "start_block": 5,
                            "index_block": 5,
                            "block_count": 3,
                            "allocated_blocks": [6, 7],
                        },
                    ],
                    "allocation_traces": [
                        {
                            "name": "file_contiguous.bin",
                            "path": "/home/file_contiguous.bin",
                            "strategy": "Contiguous",
                            "start_block": 0,
                            "index_block": -1,
                            "block_count": 3,
                            "allocated_blocks": [0, 1, 2],
                        },
                    ],
                    "operation_logs": ["mkdir /home: SUCCESS"],
                },
                "error": None,
            }
            stdout = json.dumps(sample_data, indent=2)
        elif self.mode == "text":
            stdout = """
=== Educational File System Simulation ===
Total Blocks: 32 (Block Size: 512 bytes)
Used Blocks:  8 | Free Blocks: 24
Directories:  3 | Files: 3

Directory Hierarchy Traversal (/home):
  [DIR ]                      docs (Inode 2, 0 bytes)
  [FILE]       file_contiguous.bin (Inode 3, 1500 bytes)
  [FILE]           file_linked.txt (Inode 4, 1000 bytes)
  [FILE]          file_indexed.dat (Inode 5, 1000 bytes)

Allocation Strategy Comparison:
  1. Contiguous:  file_contiguous.bin -> Start Block: 0, Count: 3 [Consecutive block range]
  2. Linked:      file_linked.txt -> Blocks: 3 4 [Pointers link arbitrary free blocks]
  3. Indexed:     file_indexed.dat -> Index Block: 5, Data Blocks: 6 7 [Direct index block table]

Disk Block Free Space Bitmap (0 = Free, 1 = Allocated):
  11111111 00000000 00000000 00000000 
"""
        elif self.mode == "error":
            return ExecutionResult(exit_code=1, stdout="", stderr="Capacity exceeded", duration=0.05, is_timeout=False, command=[])
        else:
            stdout = ""

        return ExecutionResult(exit_code=0, stdout=stdout, stderr="", duration=0.08, is_timeout=False, command=args)

    def cancel(self):
        pass


def test_filesystem_models_validation():
    cfg = FilesystemConfig(total_blocks=32, block_size=512)
    assert cfg.validate() is None

    # Invalid blocks
    cfg_bad = FilesystemConfig(total_blocks=2, block_size=512)
    assert "Total blocks must be between 4 and 256" in cfg_bad.validate()

    # Invalid block size
    cfg_bad_bs = FilesystemConfig(total_blocks=32, block_size=32)
    assert "Block size must be between 64 and 8192" in cfg_bad_bs.validate()

    # Operation validation
    op = FilesystemOperationInput(FilesystemOperationType.CREATE, "no_slash", 500)
    assert "leading slash" in op.validate()

    op_ok = FilesystemOperationInput(FilesystemOperationType.CREATE, "/file.txt", 500, FilesystemAllocationStrategy.LINKED)
    assert op_ok.validate() is None
    assert op_ok.to_cli_command() == "create /file.txt 500 linked"


def test_generate_filesystem_stdin():
    config = FilesystemConfig(
        total_blocks=16,
        block_size=512,
        operations=[
            FilesystemOperationInput(FilesystemOperationType.MKDIR, "/sub"),
            FilesystemOperationInput(FilesystemOperationType.CREATE, "/sub/test.bin", 1024, FilesystemAllocationStrategy.CONTIGUOUS),
            FilesystemOperationInput(FilesystemOperationType.DELETE, "/sub/test.bin"),
        ],
    )
    stdin_str = generate_filesystem_stdin(config)
    assert "config 16 512" in stdin_str
    assert "mkdir /sub" in stdin_str
    assert "create /sub/test.bin 1024 contiguous" in stdin_str
    assert "delete /sub/test.bin" in stdin_str


def test_parse_filesystem_json_output():
    runner = DummyFilesystemRunner(mode="json")
    res = runner.execute(["--demo-fs", "--json"])
    parsed = parse_filesystem_output(res.stdout, FilesystemPreset.STANDARD_DEMO)

    assert parsed.is_success
    assert parsed.status.total_blocks == 32
    assert parsed.status.used_blocks == 8
    assert parsed.status.free_blocks == 24
    assert parsed.status.file_count == 3
    assert parsed.status.directory_count == 3
    assert len(parsed.status.inodes) == 6
    assert parsed.status.utilization_percent == 25.0
    assert parsed.status.total_capacity_bytes == 32 * 512
    assert parsed.status.free_bytes == 24 * 512

    # Check child query
    children = parsed.status.get_entries_under("/home")
    assert len(children) == 4
    names = [c.name for c in children]
    assert "docs" in names
    assert "file_contiguous.bin" in names


def test_parse_filesystem_text_fallback():
    runner = DummyFilesystemRunner(mode="text")
    res = runner.execute(["--demo-fs"])
    parsed = parse_filesystem_output(res.stdout, FilesystemPreset.STANDARD_DEMO)

    assert parsed.is_success
    assert parsed.status.total_blocks == 32
    assert parsed.status.used_blocks == 8
    assert parsed.status.free_blocks == 24
    assert len(parsed.status.allocation_traces) >= 3


def test_filesystem_worker_success():
    runner = DummyFilesystemRunner(mode="json")
    cfg = FilesystemConfig(preset=FilesystemPreset.STANDARD_DEMO)
    worker = FilesystemWorker(runner, cfg)

    emitted_result = []
    worker.finished_exec.connect(lambda res: emitted_result.append(res))

    worker.run()
    assert len(emitted_result) == 1
    assert emitted_result[0].status.total_blocks == 32


def test_filesystem_page_and_widgets(qapp):
    runner = DummyFilesystemRunner(mode="json")
    page = FilesystemPage(runner=runner)

    # Check subwidgets instantiated
    assert isinstance(page.stats_bar, FilesystemStatsBar)
    assert isinstance(page.block_map, BlockAllocationMapWidget)
    assert isinstance(page.tree_browser, DirectoryTreeBrowserWidget)
    assert isinstance(page.metadata_panel, FileMetadataPanel)

    # Wait for initial background worker to finish and process Qt signals
    if page._active_worker:
        page._active_worker.wait(2000)
    qapp.processEvents()

    # Initial run executed automatically
    assert page._last_result is not None
    assert page._last_result.status.total_blocks == 32

    # Verify inspector populated
    assert page.metadata_panel.lbl_size.text() != "0 bytes"

    # Switch preset to Fragmentation
    page.combo_preset.setCurrentIndex(1)
    assert page.spin_blocks.value() == 6

    # Switch preset to Custom Workload
    page.combo_preset.setCurrentIndex(3)
    assert not page.custom_ops_widget.isHidden()
    assert page.table_ops.rowCount() > 0

    # Clear custom ops
    page._clear_custom_ops()
    assert page.table_ops.rowCount() == 0

    # Clean close
    page.cancel_simulation()
