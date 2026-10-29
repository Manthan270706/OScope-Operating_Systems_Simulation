"""Focused unit and integration tests for Virtual Memory & Address Translation GUI module."""

import json
import os
import pytest

from PySide6.QtWidgets import QLabel

from oscope_gui.backend.executor import AddressTranslationWorker
from oscope_gui.backend.parser import (
    generate_paging_ops_stdin,
    parse_address_translation_output,
)
from oscope_gui.backend.runner import ExecutionResult
from oscope_gui.models.address_translation import (
    AddressTranslationConfig,
    AddressTranslationSimulationResultModel,
    DemandPagingResultModel,
    DemandPagingStepModel,
    PageTableEntryModel,
    ThrashingPointModel,
    ThrashingResultModel,
    TranslationResultModel,
)
from oscope_gui.pages.address_translation_page import AddressTranslationPage
from oscope_gui.widgets.address_translation_viz import (
    DemandPagingTraceWidget,
    PageTableMappingWidget,
    ThrashingCurvePlotWidget,
    VirtualAddressDecomposerWidget,
)


class DummyAddressTranslationRunner:
    """Mock backend runner returning realistic C++ simulation JSON and text."""

    def __init__(self, mode: str = "json") -> None:
        self.mode = mode
        self.last_args = None
        self.last_stdin = None

    def execute(self, args, stdin_data=None, timeout=10.0):
        self.last_args = args
        self.last_stdin = stdin_data

        if self.mode == "json":
            sample_data = [
                {
                    "schema_version": "1.0.0",
                    "category": "paging_virtual_memory",
                    "experiment": "address_translation",
                    "status": "success",
                    "success": True,
                    "result": {
                        "virtual_address": 4100,
                        "page_number": 1,
                        "offset": 4,
                        "page_fault": False,
                        "frame_number": 2,
                        "physical_address": 8196,
                        "message": "Address translated successfully.",
                    },
                    "error": None,
                },
                {
                    "schema_version": "1.0.0",
                    "category": "paging_virtual_memory",
                    "experiment": "demand_paging",
                    "status": "success",
                    "success": True,
                    "result": {
                        "page_size": 4096,
                        "total_frames": 3,
                        "total_accesses": 5,
                        "page_faults": 5,
                        "page_hits": 0,
                        "fault_rate": "1.000000",
                        "steps": [
                            {
                                "virtual_address": 4106,
                                "page_number": 1,
                                "offset": 10,
                                "page_fault": True,
                                "frame_number": 0,
                                "physical_address": 10,
                                "victim_page": -1,
                                "frame_contents": [1, -1, -1],
                            },
                            {
                                "virtual_address": 8212,
                                "page_number": 2,
                                "offset": 20,
                                "page_fault": True,
                                "frame_number": 1,
                                "physical_address": 4116,
                                "victim_page": -1,
                                "frame_contents": [1, 2, -1],
                            },
                        ],
                    },
                    "error": None,
                },
                {
                    "schema_version": "1.0.0",
                    "category": "paging_virtual_memory",
                    "experiment": "thrashing_curve",
                    "status": "success",
                    "success": True,
                    "result": {
                        "thrashing_threshold_frames": 4,
                        "points": [
                            {"frames": 1, "page_faults": 12, "fault_rate": "1.000000"},
                            {"frames": 2, "page_faults": 12, "fault_rate": "1.000000"},
                            {"frames": 3, "page_faults": 12, "fault_rate": "1.000000"},
                            {"frames": 4, "page_faults": 4, "fault_rate": "0.333333"},
                        ],
                        "reference_string": [1, 2, 3, 4, 1, 2, 3, 4],
                    },
                    "error": None,
                },
            ]
            return ExecutionResult(
                exit_code=0,
                stdout=json.dumps(sample_data, indent=2),
                stderr="",
                duration=0.05,
                is_timeout=False,
                command=["dummy_oscope"] + args,
            )
        else:
            sample_text = """
=== Virtual Address Translation & Demand Paging Demo ===
Configured Page Size: 4096 bytes (Offset width: 12 bits)

1. Virtual Address Translation Example:
  Virtual Address:   4100 (0x1004)
  Page Number:       1
  Page Offset:       4 (preserved across translation)
  Page Table Lookup: Present in Frame 2
  Physical Address:  8196 (0x2004)

3. Demand Paging Event Trace (3 Frames, FIFO Replacement):
  Step | Virtual Addr | Page | Offset | Fault? | Frame | Victim Page
  -----+--------------+------+--------+--------+-------+------------
     1 |         4106 |    1 |     10 |  YES   |     0 | -
     2 |         8212 |    2 |     20 |  YES   |     1 | -
  Summary: 2 accesses, 2 faults, 0 hits (Fault Rate: 100.00%)

4. Thrashing Curve Analysis (Faults vs Available Frames):
  Frames: 1 -> Faults: 12 (100.0% fault rate)
  Frames: 4 -> Faults: 4 (33.3% fault rate)
  Working Set Knee (Thrashing Threshold): 4 frames.
"""
            return ExecutionResult(
                exit_code=0,
                stdout=sample_text,
                stderr="",
                duration=0.05,
                is_timeout=False,
                command=["dummy_oscope"] + args,
            )

    def cancel(self):
        pass


def test_address_translation_config_validation():
    # Valid config
    cfg = AddressTranslationConfig(page_size=4096, mode="demo")
    assert cfg.validate() is None

    # Invalid page size (not power of 2)
    bad_cfg = AddressTranslationConfig(page_size=1000)
    assert bad_cfg.validate() is not None

    # Invalid custom mappings
    bad_map = AddressTranslationConfig(mode="custom", custom_mappings=[(-1, 2)])
    assert bad_map.validate() is not None

    # Invalid frame count
    bad_f = AddressTranslationConfig(mode="custom", demand_paging_frames=0)
    assert bad_f.validate() is not None


def test_generate_paging_ops_stdin():
    cfg = AddressTranslationConfig(
        page_size=4096,
        mode="custom",
        custom_mappings=[(0, 5), (1, 2)],
        virtual_addresses_to_translate=[4100, 8192],
        demand_paging_frames=3,
        demand_paging_addresses=[4106, 8212],
        thrashing_reference_string=[1, 2, 3, 4],
        thrashing_min_frames=1,
        thrashing_max_frames=4,
    )
    stdin_data = generate_paging_ops_stdin(cfg)
    assert "pagesize 4096" in stdin_data
    assert "map 0 5" in stdin_data
    assert "map 1 2" in stdin_data
    assert "translate 4100" in stdin_data
    assert "demand 3 4106 8212" in stdin_data
    assert "thrash 1 4 1 2 3 4" in stdin_data


def test_parse_address_translation_json_output():
    runner = DummyAddressTranslationRunner(mode="json")
    res = runner.execute(["--demo-paging", "--json"])
    parsed = parse_address_translation_output(res.stdout)

    assert parsed.page_size == 4096
    assert len(parsed.translations) == 1
    t = parsed.translations[0]
    assert t.virtual_address == 4100
    assert t.page_number == 1
    assert t.offset == 4
    assert not t.page_fault
    assert t.frame_number == 2
    assert t.physical_address == 8196

    assert parsed.demand_paging is not None
    assert parsed.demand_paging.total_accesses == 5
    assert parsed.demand_paging.page_faults == 5
    assert len(parsed.demand_paging.steps) == 2

    assert parsed.thrashing is not None
    assert parsed.thrashing.thrashing_threshold_frames == 4
    assert len(parsed.thrashing.points) == 4


def test_parse_address_translation_text_output():
    runner = DummyAddressTranslationRunner(mode="text")
    res = runner.execute(["--demo-paging"])
    parsed = parse_address_translation_output(res.stdout)

    assert parsed.page_size == 4096
    assert len(parsed.translations) >= 1
    assert parsed.translations[0].virtual_address == 4100
    assert parsed.translations[0].page_number == 1
    assert parsed.translations[0].frame_number == 2

    assert parsed.demand_paging is not None
    assert parsed.demand_paging.total_accesses == 2

    assert parsed.thrashing is not None
    assert parsed.thrashing.thrashing_threshold_frames == 4


def test_address_translation_widgets(qapp):
    decomposer = VirtualAddressDecomposerWidget()
    t = TranslationResultModel(
        virtual_address=4100,
        page_number=1,
        offset=4,
        page_fault=False,
        frame_number=2,
        physical_address=8196,
        message="OK",
    )
    decomposer.update_translation(t, 4096)
    assert "0x1004" in decomposer.va_box.findChild(QLabel, "mainValueLabel").text()

    # Fault update
    t_fault = TranslationResultModel(
        virtual_address=12308,
        page_number=3,
        offset=20,
        page_fault=True,
        frame_number=-1,
        physical_address=0,
        message="Fault",
    )
    decomposer.update_translation(t_fault, 4096)
    assert "PAGE FAULT" in decomposer.outcome_box.findChild(QLabel, "mainValueLabel").text()

    # Page Table Mapping Widget
    pt_widget = PageTableMappingWidget()
    entries = [
        PageTableEntryModel(page_number=0, frame_number=5, valid=True),
        PageTableEntryModel(page_number=1, frame_number=2, valid=True),
    ]
    pt_widget.populate(entries, 4096, highlight_page=1)
    assert pt_widget.table.rowCount() == 2

    # Demand Paging Trace Widget
    dp_widget = DemandPagingTraceWidget()
    dp_result = DemandPagingResultModel(
        page_size=4096,
        total_frames=3,
        total_accesses=2,
        page_faults=2,
        page_hits=0,
        fault_rate=1.0,
        steps=[
            DemandPagingStepModel(
                virtual_address=4106,
                page_number=1,
                offset=10,
                page_fault=True,
                frame_number=0,
                physical_address=10,
                victim_page=-1,
            )
        ],
    )
    dp_widget.populate(dp_result)
    assert dp_widget.table.rowCount() == 1

    # Thrashing Curve Plot Widget
    th_plot = ThrashingCurvePlotWidget()
    th_res = ThrashingResultModel(
        reference_string=[1, 2, 3, 4],
        points=[
            ThrashingPointModel(frames=1, page_faults=4, fault_rate=1.0),
            ThrashingPointModel(frames=2, page_faults=2, fault_rate=0.5),
        ],
        thrashing_threshold_frames=2,
    )
    th_plot.set_data(th_res)
    assert th_plot._data is not None


def test_address_translation_page_execution(qapp):
    runner = DummyAddressTranslationRunner(mode="json")
    page = AddressTranslationPage(runner=runner)

    # Check initial default state
    assert page.combo_mode.currentIndex() == 0
    assert not page.custom_panel.isVisible()
    assert page.card_page_size.value_label.text() == "4,096 B"

    # Switch to custom mode
    page.combo_mode.setCurrentIndex(1)
    assert not page.custom_panel.isHidden()

    # Run simulation
    page.run_simulation()
    assert page.worker is not None
    page.worker.wait(2000)
    qapp.processEvents()

    assert page._last_result is not None
    assert len(page._last_result.translations) == 1
    assert page.status_badge.label.text() == "Completed"

    page.cleanup()
