"""Virtual Memory & Address Translation interactive page.

Visualizes authoritative C++ MMU virtual-to-physical address translation,
bit decomposition, page table lookup, demand paging event trace, FIFO eviction,
and thrashing curve knee analysis.
"""

import math
import os
from typing import Callable, List, Optional, Tuple

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpinBox,
    QSplitter,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from ..backend.executor import AddressTranslationWorker
from ..backend.runner import BaseBackendRunner
from ..models.address_translation import (
    AddressTranslationConfig,
    AddressTranslationSimulationResultModel,
    PageTableEntryModel,
    TranslationResultModel,
)
from ..theme import (
    ACCENT,
    ACCENT_CYAN,
    ACCENT_EMERALD,
    ACCENT_HOVER,
    ACCENT_INDIGO,
    ACCENT_ROSE,
    ACCENT_VIOLET,
    BG_CARD,
    BG_DARK,
    BG_ELEVATED,
    BG_SURFACE,
    BORDER,
    BORDER_LIGHT,
    DANGER,
    SUCCESS,
    TEXT_MUTED,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    WARNING,
)
from ..widgets.address_translation_viz import (
    DemandPagingTraceWidget,
    PageTableMappingWidget,
    ThrashingCurvePlotWidget,
    VirtualAddressDecomposerWidget,
)
from ..widgets.stat_card import StatCard
from ..widgets.status_badge import StatusBadge


class AddressTranslationPage(QWidget):
    """Virtual Memory, MMU Translation, Demand Paging, and Thrashing GUI page."""

    def __init__(
        self,
        runner: Optional[BaseBackendRunner] = None,
        runner_factory: Optional[Callable[[], BaseBackendRunner]] = None,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        if runner_factory is not None:
            self.runner_factory = runner_factory
        elif runner is not None:
            self.runner_factory = lambda: runner
        else:
            from ..backend.runner import discover_backend
            self.runner_factory = discover_backend
        self.worker: Optional[AddressTranslationWorker] = None
        self._last_result: Optional[AddressTranslationSimulationResultModel] = None

        self._init_ui()
        self._set_default_inputs()

    def _init_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(14)

        # 1. Header Section
        header_layout = QHBoxLayout()
        header_text_layout = QVBoxLayout()
        header_text_layout.setSpacing(4)

        title = QLabel("Virtual Memory & Address Translation")
        title.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {TEXT_PRIMARY};")
        header_text_layout.addWidget(title)

        subtitle = QLabel(
            "Authoritative MMU virtual-to-physical address translation, bit-level decomposition, "
            "demand paging event trace, and thrashing working-set analysis."
        )
        subtitle.setStyleSheet(f"font-size: 13px; color: {TEXT_SECONDARY};")
        header_text_layout.addWidget(subtitle)
        header_layout.addLayout(header_text_layout)

        header_layout.addStretch()

        self.status_badge = StatusBadge("Ready", "neutral")
        header_layout.addWidget(self.status_badge)
        main_layout.addLayout(header_layout)

        # 2. Control Bar (Mode, Page Size, Run, Reset)
        control_card = QFrame()
        control_card.setStyleSheet(
            f"""
            QFrame {{
                background-color: {BG_CARD};
                border: 1px solid {BORDER};
                border-radius: 8px;
                padding: 10px;
            }}
            """
        )
        ctrl_layout = QHBoxLayout(control_card)
        ctrl_layout.setContentsMargins(10, 8, 10, 8)
        ctrl_layout.setSpacing(12)

        # Mode Selector
        mode_lbl = QLabel("Mode:")
        mode_lbl.setStyleSheet(f"font-weight: bold; color: {TEXT_PRIMARY};")
        ctrl_layout.addWidget(mode_lbl)

        self.combo_mode = QComboBox()
        self.combo_mode.addItems(["Educational Demo Preset", "Interactive Custom MMU"])
        self.combo_mode.currentIndexChanged.connect(self._on_mode_changed)
        self.combo_mode.setStyleSheet(self._input_style())
        ctrl_layout.addWidget(self.combo_mode)

        # Page Size
        ps_lbl = QLabel("Page Size:")
        ps_lbl.setStyleSheet(f"font-weight: bold; color: {TEXT_PRIMARY};")
        ctrl_layout.addWidget(ps_lbl)

        self.combo_page_size = QComboBox()
        self.combo_page_size.addItems(["512 B", "1024 B (1 KB)", "2048 B (2 KB)", "4096 B (4 KB)", "8192 B (8 KB)"])
        self.combo_page_size.setCurrentIndex(3)  # default 4096
        self.combo_page_size.setStyleSheet(self._input_style())
        ctrl_layout.addWidget(self.combo_page_size)

        ctrl_layout.addStretch()

        # Action Buttons
        self.btn_run = QPushButton("Simulate MMU Paging")
        self.btn_run.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {ACCENT};
                color: #ffffff;
                font-weight: bold;
                font-size: 13px;
                border: none;
                border-radius: 6px;
                padding: 7px 18px;
            }}
            QPushButton:hover {{
                background-color: {ACCENT_HOVER};
            }}
            QPushButton:disabled {{
                background-color: {BG_DARK};
                color: {TEXT_MUTED};
            }}
            """
        )
        self.btn_run.clicked.connect(self.run_simulation)
        ctrl_layout.addWidget(self.btn_run)

        self.btn_reset = QPushButton("Reset Defaults")
        self.btn_reset.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {BG_DARK};
                color: {TEXT_SECONDARY};
                border: 1px solid {BORDER};
                border-radius: 6px;
                padding: 7px 14px;
            }}
            QPushButton:hover {{
                color: {TEXT_PRIMARY};
                border-color: {BORDER_LIGHT};
            }}
            """
        )
        self.btn_reset.clicked.connect(self._set_default_inputs)
        ctrl_layout.addWidget(self.btn_reset)

        main_layout.addWidget(control_card)

        # 3. Custom Inputs Panel (Visible in Custom Mode)
        self.custom_panel = QFrame()
        self.custom_panel.setStyleSheet(
            f"background-color: {BG_CARD}; border: 1px solid {BORDER}; border-radius: 8px; padding: 10px;"
        )
        cust_layout = QVBoxLayout(self.custom_panel)
        cust_layout.setContentsMargins(8, 8, 8, 8)
        cust_layout.setSpacing(8)

        cust_title = QLabel("Custom MMU Parameters & Query")
        cust_title.setStyleSheet(f"font-size: 12px; font-weight: bold; color: {ACCENT_CYAN};")
        cust_layout.addWidget(cust_title)

        inputs_grid = QHBoxLayout()
        inputs_grid.setSpacing(10)

        # Query Virtual Address
        va_box = QVBoxLayout()
        va_box.setSpacing(2)
        va_box.addWidget(QLabel("Virtual Address to Translate (dec or 0xhex):"))
        self.txt_query_va = QLineEdit("4100")
        self.txt_query_va.setStyleSheet(self._input_style())
        va_box.addWidget(self.txt_query_va)
        inputs_grid.addLayout(va_box)

        # Page Mappings
        map_box = QVBoxLayout()
        map_box.setSpacing(2)
        map_box.addWidget(QLabel("Page-to-Frame Mappings (e.g. 0:5, 1:2, 7:10):"))
        self.txt_mappings = QLineEdit("0:5, 1:2, 7:10")
        self.txt_mappings.setStyleSheet(self._input_style())
        map_box.addWidget(self.txt_mappings)
        inputs_grid.addLayout(map_box)

        # Demand Paging Access Sequence
        dp_box = QVBoxLayout()
        dp_box.setSpacing(2)
        dp_box.addWidget(QLabel("Demand Paging Sequence (space-separated VAs):"))
        self.txt_dp_seq = QLineEdit("4106 8212 12318 16424 4146")
        self.txt_dp_seq.setStyleSheet(self._input_style())
        dp_box.addWidget(self.txt_dp_seq)
        inputs_grid.addLayout(dp_box)

        # Demand Paging Frame Count
        f_box = QVBoxLayout()
        f_box.setSpacing(2)
        f_box.addWidget(QLabel("Physical Frames:"))
        self.spin_frames = QSpinBox()
        self.spin_frames.setRange(1, 16)
        self.spin_frames.setValue(3)
        self.spin_frames.setStyleSheet(self._input_style())
        f_box.addWidget(self.spin_frames)
        inputs_grid.addLayout(f_box)

        cust_layout.addLayout(inputs_grid)
        self.custom_panel.setVisible(False)
        main_layout.addWidget(self.custom_panel)

        # 4. Progress Bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet(
            f"""
            QProgressBar {{
                border: 1px solid {BORDER};
                border-radius: 4px;
                background-color: {BG_DARK};
                height: 6px;
            }}
            QProgressBar::chunk {{
                background-color: {ACCENT};
            }}
            """
        )
        main_layout.addWidget(self.progress_bar)

        # 5. Stat Cards Bar
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(10)

        self.card_page_size = StatCard("Configured Page Size", "4,096 B", "Offset width: 12 bits")
        self.card_status = StatCard("Translation Outcome", "Ready", "No translation active")
        self.card_fault_rate = StatCard("Demand Paging Fault Rate", "0.0%", "0 faults / 0 accesses")
        self.card_knee = StatCard("Thrashing Working-Set Knee", "4 Frames", "Spike below threshold")

        stats_layout.addWidget(self.card_page_size)
        stats_layout.addWidget(self.card_status)
        stats_layout.addWidget(self.card_fault_rate)
        stats_layout.addWidget(self.card_knee)
        main_layout.addLayout(stats_layout)

        # 6. Tabbed Visualizations Area
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(
            f"""
            QTabWidget::pane {{
                border: 1px solid {BORDER};
                border-radius: 8px;
                background-color: {BG_CARD};
            }}
            QTabBar::tab {{
                background-color: {BG_DARK};
                color: {TEXT_SECONDARY};
                padding: 8px 16px;
                font-weight: bold;
                font-size: 12px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                margin-right: 4px;
            }}
            QTabBar::tab:selected {{
                background-color: {BG_CARD};
                color: {ACCENT_CYAN};
                border-bottom: 2px solid {ACCENT_CYAN};
            }}
            QTabBar::tab:hover:!selected {{
                color: {TEXT_PRIMARY};
            }}
            """
        )

        # Tab 1: Address Translation & Page Table
        tab1 = QWidget()
        tab1_layout = QVBoxLayout(tab1)
        tab1_layout.setContentsMargins(10, 10, 10, 10)
        tab1_layout.setSpacing(10)

        self.decomposer_widget = VirtualAddressDecomposerWidget()
        tab1_layout.addWidget(self.decomposer_widget)

        self.page_table_widget = PageTableMappingWidget()
        tab1_layout.addWidget(self.page_table_widget)

        self.tabs.addTab(tab1, "Address Translation & Page Table")

        # Tab 2: Demand Paging Trace
        tab2 = QWidget()
        tab2_layout = QVBoxLayout(tab2)
        tab2_layout.setContentsMargins(10, 10, 10, 10)
        tab2_layout.setSpacing(10)

        self.demand_trace_widget = DemandPagingTraceWidget()
        tab2_layout.addWidget(self.demand_trace_widget)

        self.tabs.addTab(tab2, "Demand Paging Access Trace")

        # Tab 3: Thrashing Curve Analysis
        tab3 = QWidget()
        tab3_layout = QVBoxLayout(tab3)
        tab3_layout.setContentsMargins(10, 10, 10, 10)
        tab3_layout.setSpacing(10)

        self.thrashing_plot = ThrashingCurvePlotWidget()
        tab3_layout.addWidget(self.thrashing_plot)

        # Educational theory card
        theory_card = QFrame()
        theory_card.setStyleSheet(f"background-color: {BG_DARK}; border: 1px solid {BORDER}; border-radius: 6px; padding: 10px;")
        th_vbox = QVBoxLayout(theory_card)
        th_vbox.setContentsMargins(6, 6, 6, 6)
        th_vbox.setSpacing(4)
        th_title = QLabel("Understanding Thrashing & Working-Set Dynamics")
        th_title.setStyleSheet(f"font-size: 12px; font-weight: bold; color: {ACCENT_VIOLET};")
        th_vbox.addWidget(th_title)
        th_desc = QLabel(
            "Thrashing occurs when the physical memory allocated to a process is smaller than its active Working Set (W(t, Δ)). "
            "Because necessary pages cannot all reside in memory simultaneously, every page reference causes a page fault, "
            "evicting a page that will be needed immediately. CPU utilization drops drastically as the system spends almost all "
            "its cycles handling I/O page faults. The 'Knee' on the curve represents the working set threshold where page fault "
            "frequency stabilizes."
        )
        th_desc.setWordWrap(True)
        th_desc.setStyleSheet(f"font-size: 11px; color: {TEXT_SECONDARY}; line-height: 1.4;")
        th_vbox.addWidget(th_desc)
        tab3_layout.addWidget(theory_card)

        self.tabs.addTab(tab3, "Thrashing Curve Analysis")

        # Tab 4: Backend Logs
        tab4 = QWidget()
        tab4_layout = QVBoxLayout(tab4)
        tab4_layout.setContentsMargins(10, 10, 10, 10)
        self.txt_logs = QTextEdit()
        self.txt_logs.setReadOnly(True)
        self.txt_logs.setStyleSheet(
            f"background-color: {BG_DARK}; border: 1px solid {BORDER}; border-radius: 6px; color: {TEXT_PRIMARY}; font-family: monospace; font-size: 11px;"
        )
        tab4_layout.addWidget(self.txt_logs)
        self.tabs.addTab(tab4, "Backend Execution Logs")

        main_layout.addWidget(self.tabs, stretch=1)

    def _input_style(self) -> str:
        return f"""
            background-color: {BG_DARK};
            color: {TEXT_PRIMARY};
            border: 1px solid {BORDER};
            border-radius: 6px;
            padding: 4px 8px;
            font-size: 12px;
        """

    def _on_mode_changed(self, index: int) -> None:
        is_custom = index == 1
        self.custom_panel.setVisible(is_custom)

    def _set_default_inputs(self) -> None:
        self.combo_mode.setCurrentIndex(0)
        self.combo_page_size.setCurrentIndex(3)  # 4096
        self.txt_query_va.setText("4100")
        self.txt_mappings.setText("0:5, 1:2, 7:10")
        self.txt_dp_seq.setText("4106 8212 12318 16424 4146")
        self.spin_frames.setValue(3)
        self.custom_panel.setVisible(False)
        self.status_badge.set_status("Ready", "neutral")

    def _parse_page_size(self) -> int:
        idx = self.combo_page_size.currentIndex()
        mapping = {0: 512, 1: 1024, 2: 2048, 3: 4096, 4: 8192}
        return mapping.get(idx, 4096)

    def _parse_custom_mappings(self) -> List[Tuple[int, int]]:
        raw = self.txt_mappings.text().strip()
        if not raw:
            return []
        mappings: List[Tuple[int, int]] = []
        tokens = raw.replace(";", ",").split(",")
        for t in tokens:
            t = t.strip()
            if not t:
                continue
            parts = t.split(":")
            if len(parts) == 2:
                try:
                    p = int(parts[0].strip())
                    f = int(parts[1].strip())
                    mappings.append((p, f))
                except ValueError:
                    pass
        return mappings

    def _parse_virtual_address(self, raw: str) -> Optional[int]:
        raw = raw.strip()
        if not raw:
            return None
        try:
            if raw.lower().startswith("0x"):
                return int(raw, 16)
            return int(raw)
        except ValueError:
            return None

    def run_simulation(self) -> None:
        """Invokes the authoritative C++ backend via WSL."""
        if self.worker and self.worker.isRunning():
            return

        page_size = self._parse_page_size()
        is_custom = self.combo_mode.currentIndex() == 1

        if is_custom:
            va_query = self._parse_virtual_address(self.txt_query_va.text())
            if va_query is None:
                QMessageBox.warning(self, "Invalid Input", "Please provide a valid virtual address to translate.")
                return

            mappings = self._parse_custom_mappings()
            dp_vas: List[int] = []
            for token in self.txt_dp_seq.text().strip().split():
                v = self._parse_virtual_address(token)
                if v is not None:
                    dp_vas.append(v)

            config = AddressTranslationConfig(
                page_size=page_size,
                mode="custom",
                custom_mappings=mappings,
                virtual_addresses_to_translate=[va_query],
                demand_paging_frames=self.spin_frames.value(),
                demand_paging_addresses=dp_vas,
                thrashing_reference_string=[1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4],
                thrashing_min_frames=1,
                thrashing_max_frames=4,
            )
        else:
            config = AddressTranslationConfig(
                page_size=4096,
                mode="demo",
                custom_mappings=[(0, 5), (1, 2), (7, 10)],
                virtual_addresses_to_translate=[4100, 12308],
                demand_paging_frames=3,
                demand_paging_addresses=[4106, 8212, 12318, 16424, 4146],
                thrashing_reference_string=[1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4],
                thrashing_min_frames=1,
                thrashing_max_frames=4,
            )

        err = config.validate()
        if err:
            QMessageBox.warning(self, "Configuration Error", err)
            return

        # Prepare UI
        self.btn_run.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.status_badge.set_status("Simulating...", "running")

        # Launch Worker
        runner = self.runner_factory()
        self.worker = AddressTranslationWorker(runner, config, self)
        self.worker.finished_exec.connect(self._on_simulation_success)
        self.worker.failed_exec.connect(self._on_simulation_error)
        self.worker.start()

    def _on_simulation_success(self, result: AddressTranslationSimulationResultModel) -> None:
        self.btn_run.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.status_badge.set_status("Completed", "success")
        self._last_result = result

        # 1. Update Stat Cards
        self.card_page_size.set_value(f"{result.page_size:,} B", f"Offset: {int(math.log2(result.page_size))} bits")

        if result.translations:
            first_trans = result.translations[0]
            if not first_trans.page_fault:
                self.card_status.set_value("Translation Hit", f"VA 0x{first_trans.virtual_address:X} ➔ PA 0x{first_trans.physical_address:X}")
            else:
                self.card_status.set_value("Page Fault", f"Page {first_trans.page_number} Unmapped")
            self.decomposer_widget.update_translation(first_trans, result.page_size)

        if result.demand_paging:
            dp = result.demand_paging
            self.card_fault_rate.set_value(f"{dp.fault_rate * 100:.1f}%", f"{dp.page_faults} faults / {dp.total_accesses} accesses")
            self.demand_trace_widget.populate(dp)

        if result.thrashing:
            th = result.thrashing
            self.card_knee.set_value(f"{th.thrashing_threshold_frames} Frames", "Working Set Knee")
            self.thrashing_plot.set_data(th)

        # 2. Update Page Table Widget
        hl_page = result.translations[0].page_number if result.translations else None
        self.page_table_widget.populate(result.page_table, result.page_size, highlight_page=hl_page)

        # 3. Update Logs
        log_text = "\n".join(result.logs) if result.logs else "C++ Address Translation completed successfully with authoritative MMU output."
        self.txt_logs.setText(log_text)

    def _on_simulation_error(self, message: str) -> None:
        self.btn_run.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.status_badge.set_status("Error", "danger")
        if self.isVisible() and os.environ.get("QT_QPA_PLATFORM") != "offscreen":
            QMessageBox.critical(self, "Simulation Error", message)
        self.txt_logs.setText(f"ERROR: {message}")

    def cleanup(self) -> None:
        """Safely stops any background worker thread."""
        if self.worker and self.worker.isRunning():
            self.worker.cancel()
            self.worker.wait(1500)
            self.worker = None
