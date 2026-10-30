"""Page Replacement interactive simulation and visualization page.

Supports FIFO, LRU, Optimal, and Multi-Strategy Comparison using real C++ backend execution.
Follows OScope dark design tokens, high contrast, and educational guidance.
"""

from typing import Callable, List, Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from ..backend.executor import PagingWorker
from ..backend.runner import BaseBackendRunner
from ..models.paging import (
    PagingAlgorithm,
    PagingComparisonResultModel,
    PagingConfig,
    PagingSimulationResultModel,
    PagingStepModel,
)
from ..theme import (
    ACCENT,
    ACCENT_AMBER,
    ACCENT_CYAN,
    ACCENT_EMERALD,
    ACCENT_HOVER,
    ACCENT_INDIGO,
    ACCENT_ROSE,
    ACCENT_VIOLET,
    BG_APP,
    BG_ELEVATED,
    BG_INPUT,
    BG_SURFACE,
    BORDER,
    BORDER_LIGHT,
    DANGER,
    DANGER_BG,
    DANGER_TEXT,
    SUCCESS,
    SUCCESS_BG,
    SUCCESS_TEXT,
    TEXT_MUTED,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
)
from ..widgets.frame_grid import FrameGridWidget
from ..widgets.stat_card import StatCard


class PageReplacementPage(QWidget):
    """Interactive Page Replacement simulation page with frame timeline and genuine C++ metrics."""

    def __init__(
        self,
        runner: BaseBackendRunner,
        on_execution_completed: Optional[Callable[[str, int, float, float, bool], None]] = None,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.runner = runner
        self.on_execution_completed = on_execution_completed
        self._active_worker: Optional[PagingWorker] = None

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Scroll area for responsive scaling at 1366x768 and 1920x1080
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet(f"background-color: {BG_APP}; border: none;")

        content = QWidget()
        content.setStyleSheet(f"background-color: {BG_APP};")
        self.content_layout = QVBoxLayout(content)
        self.content_layout.setContentsMargins(36, 28, 36, 32)
        self.content_layout.setSpacing(20)

        # 1. Header
        header = self._build_header()
        self.content_layout.addLayout(header)

        # 2. Algorithm Selector Card
        algo_card = self._build_algorithm_card()
        self.content_layout.addWidget(algo_card)

        # 3. Educational Guidance Card ("Understanding Virtual Memory & Paging")
        guidance_card = self._build_guidance_card()
        self.content_layout.addWidget(guidance_card)

        # 4. Workload Configuration Card (Frames & Reference String)
        config_card = self._build_config_card()
        self.content_layout.addWidget(config_card)

        # 5. Action Bar (Run / Reset)
        action_bar = self._build_action_bar()
        self.content_layout.addLayout(action_bar)

        # 6. Status Feedback Banner
        self.status_banner = QLabel()
        self.status_banner.setWordWrap(True)
        self.status_banner.setStyleSheet(
            f"background-color: rgba(14, 165, 233, 0.12); color: {ACCENT_HOVER}; border: 1px solid rgba(14, 165, 233, 0.3); border-radius: 6px; padding: 10px 14px; font-size: 12px; font-weight: 500;"
        )
        self.status_banner.setText("Ready to simulate. Select an algorithm, enter a page-reference string, and click 'Run Simulation'.")
        self.content_layout.addWidget(self.status_banner)

        # 7. Results Section (StatCards, FrameGridWidget, Tabbed Results)
        results_section = self._build_results_section()
        self.content_layout.addWidget(results_section)

        scroll.setWidget(content)
        main_layout.addWidget(scroll)

        # Load initial preset
        self.load_preset("Classic Textbook")

    def _build_header(self) -> QVBoxLayout:
        layout = QVBoxLayout()
        layout.setSpacing(3)

        title = QLabel("Page Replacement Simulator")
        title.setStyleSheet("font-size: 22px; font-weight: 800; color: #172033; letter-spacing: -0.3px;")

        subtitle = QLabel("Explore how virtual memory manages page references when physical memory has a limited number of frames.")
        subtitle.setStyleSheet(f"font-size: 13px; color: {TEXT_SECONDARY};")

        layout.addWidget(title)
        layout.addWidget(subtitle)
        return layout

    def _build_algorithm_card(self) -> QFrame:
        card = QFrame()
        card.setObjectName("AlgorithmCard")
        card.setProperty("card", True)
        card.setStyleSheet(
            f"""
            QFrame#AlgorithmCard {{
                background-color: {BG_SURFACE};
                border: 1px solid {BORDER};
                border-radius: 8px;
            }}
            """
        )
        layout = QVBoxLayout(card)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(10)

        row = QHBoxLayout()
        row.setSpacing(14)

        lbl_algo = QLabel("Page Replacement Algorithm:")
        lbl_algo.setStyleSheet("font-weight: 600; font-size: 13px; color: #172033;")

        self.algo_combo = QComboBox()
        self.algo_combo.setMinimumWidth(240)
        self.algo_combo.setFixedHeight(34)

        algos_display = [
            (PagingAlgorithm.FIFO, "FIFO — First-In, First-Out"),
            (PagingAlgorithm.LRU, "LRU — Least Recently Used"),
            (PagingAlgorithm.OPTIMAL, "Optimal — Theoretical Benchmark"),
            (PagingAlgorithm.COMPARE_ALL, "Compare All (FIFO, LRU, Optimal)"),
        ]
        for algo_enum, display_name in algos_display:
            self.algo_combo.addItem(display_name, algo_enum)

        self.algo_combo.currentIndexChanged.connect(self._on_algorithm_changed)

        row.addWidget(lbl_algo)
        row.addWidget(self.algo_combo)

        # Dynamic algorithm explanation banner
        self.algo_info_label = QLabel()
        self.algo_info_label.setWordWrap(True)
        self.algo_info_label.setStyleSheet(
            f"background-color: {BG_ELEVATED}; color: {TEXT_PRIMARY}; font-size: 12px; padding: 6px 12px; border-radius: 6px; border-left: 3px solid {ACCENT_HOVER};"
        )
        row.addWidget(self.algo_info_label, stretch=1)

        layout.addLayout(row)
        self._update_algorithm_description()
        return card

    def _build_guidance_card(self) -> QFrame:
        card = QFrame()
        card.setObjectName("GuidanceCard")
        card.setProperty("card", True)
        card.setStyleSheet(
            f"""
            QFrame#GuidanceCard {{
                background-color: {BG_SURFACE};
                border: 1px solid {BORDER};
                border-radius: 8px;
            }}
            """
        )
        layout = QVBoxLayout(card)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(10)

        hdr_row = QHBoxLayout()
        title = QLabel("Understanding Virtual Memory & Page Replacement")
        title.setStyleSheet("font-weight: 700; font-size: 13px; color: #172033;")
        hint = QLabel("Virtual memory principles implemented in the OScope paging manager.")
        hint.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 12px;")

        hdr_row.addWidget(title)
        hdr_row.addWidget(hint, stretch=1)
        layout.addLayout(hdr_row)

        defs_layout = QHBoxLayout()
        defs_layout.setSpacing(14)

        def_items = [
            ("Virtual Page", "A fixed-size logical block of address space requested by an executing process.", ACCENT_CYAN),
            ("Physical Frame", "A fixed-size physical RAM slot holding exactly one page at a time.", ACCENT_EMERALD),
            ("Page Hit vs Fault", "Hit = already resident in RAM. Fault = absent, requires disk I/O.", ACCENT_ROSE),
            ("Victim Selection", "When frames are full, the algorithm chooses an existing page to evict.", ACCENT_AMBER),
        ]

        for term, exp, col in def_items:
            box_frame = QFrame()
            box_frame.setStyleSheet(
                f"background-color: {BG_ELEVATED}; border: 1px solid {BORDER}; border-radius: 6px; padding: 6px 10px;"
            )
            box = QVBoxLayout(box_frame)
            box.setContentsMargins(4, 4, 4, 4)
            box.setSpacing(2)

            tag_row = QHBoxLayout()
            dot = QLabel()
            dot.setFixedSize(6, 6)
            dot.setStyleSheet(f"background-color: {col}; border-radius: 3px;")
            lbl_t = QLabel(term)
            lbl_t.setStyleSheet(f"color: {col}; font-size: 11px; font-weight: 700;")
            tag_row.addWidget(dot)
            tag_row.addWidget(lbl_t)
            tag_row.addStretch()

            lbl_e = QLabel(exp)
            lbl_e.setWordWrap(True)
            lbl_e.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 11px; line-height: 1.3;")

            box.addLayout(tag_row)
            box.addWidget(lbl_e)
            defs_layout.addWidget(box_frame, stretch=1)

        layout.addLayout(defs_layout)
        return card

    def _build_config_card(self) -> QFrame:
        card = QFrame()
        card.setObjectName("ConfigCard")
        card.setProperty("card", True)
        card.setStyleSheet(
            f"""
            QFrame#ConfigCard {{
                background-color: {BG_SURFACE};
                border: 1px solid {BORDER};
                border-radius: 8px;
            }}
            """
        )
        layout = QVBoxLayout(card)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(12)

        # Row 1: Frames & Presets Toolbar
        top_row = QHBoxLayout()
        top_row.setSpacing(14)

        lbl_frames = QLabel("Available Memory Frames:")
        lbl_frames.setStyleSheet("font-weight: 600; font-size: 13px; color: #172033;")

        self.spin_frames = QSpinBox()
        self.spin_frames.setRange(1, 32)
        self.spin_frames.setValue(3)
        self.spin_frames.setFixedWidth(80)
        self.spin_frames.setFixedHeight(30)

        lbl_f_hint = QLabel("(Physical RAM slots allocated to process)")
        lbl_f_hint.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 11px;")

        top_row.addWidget(lbl_frames)
        top_row.addWidget(self.spin_frames)
        top_row.addWidget(lbl_f_hint)
        top_row.addStretch()

        self.preset_combo = QComboBox()
        self.preset_combo.setFixedHeight(30)
        self.preset_combo.addItem("Presets: Classic Textbook (7 0 1 2 0 3 ...)")
        self.preset_combo.addItem("Presets: Belady's Anomaly (1 2 3 4 1 2 ...)")
        self.preset_combo.addItem("Presets: High Locality (1 2 1 3 1 2 ...)")
        self.preset_combo.addItem("Presets: Sequential Cyclic (1 2 3 4 1 2 ...)")
        self.preset_combo.currentIndexChanged.connect(self._on_preset_selected)
        top_row.addWidget(self.preset_combo)

        layout.addLayout(top_row)

        # Row 2: Page Reference String Input
        ref_row = QVBoxLayout()
        ref_row.setSpacing(4)

        lbl_ref_title = QLabel("Page-Reference String:")
        lbl_ref_title.setStyleSheet("font-weight: 600; font-size: 13px; color: #172033;")

        self.input_ref_string = QLineEdit()
        self.input_ref_string.setFixedHeight(34)
        self.input_ref_string.setPlaceholderText("Enter space- or comma-separated non-negative page integers (e.g., 7, 0, 1, 2, 0, 3, 0, 4, 2, 3, 0, 3, 2)")
        self.input_ref_string.setStyleSheet(
            f"""
            QLineEdit {{
                background-color: {BG_INPUT};
                color: #172033;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 13px;
                border: 1px solid {BORDER};
                border-radius: 6px;
                padding: 4px 10px;
            }}
            QLineEdit:focus {{
                border-color: {ACCENT_HOVER};
            }}
            """
        )

        lbl_ref_hint = QLabel(
            "Each number represents a virtual memory page requested sequentially. Comma or space separation is automatically supported."
        )
        lbl_ref_hint.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 11px;")

        ref_row.addWidget(lbl_ref_title)
        ref_row.addWidget(self.input_ref_string)
        ref_row.addWidget(lbl_ref_hint)

        layout.addLayout(ref_row)
        return card

    def _build_action_bar(self) -> QHBoxLayout:
        bar = QHBoxLayout()
        bar.setSpacing(12)

        self.btn_run = QPushButton("Run Simulation")
        self.btn_run.setFixedHeight(40)
        self.btn_run.setFixedWidth(180)
        self.btn_run.setStyleSheet(
            f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {ACCENT}, stop:1 {ACCENT_INDIGO});
                color: #172033;
                font-weight: 700;
                font-size: 13px;
                border-radius: 6px;
                border: 1px solid rgba(56, 189, 248, 0.4);
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {ACCENT_HOVER}, stop:1 #818cf8);
                border-color: #7dd3fc;
            }}
            """
        )
        self.btn_run.clicked.connect(self.run_simulation)

        self.btn_reset = QPushButton("Reset Results")
        self.btn_reset.setFixedHeight(40)
        self.btn_reset.setFixedWidth(120)
        self.btn_reset.setStyleSheet(
            f"background-color: {BG_ELEVATED}; color: {TEXT_PRIMARY}; font-weight: 500; font-size: 13px; border-radius: 6px; border: 1px solid {BORDER_LIGHT};"
        )
        self.btn_reset.clicked.connect(self.reset_results)

        bar.addWidget(self.btn_run)
        bar.addWidget(self.btn_reset)
        bar.addStretch()

        return bar

    def _build_results_section(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        # Section Heading
        res_header = QHBoxLayout()
        title = QLabel("Simulation Results & Frame Timeline")
        title.setStyleSheet("font-size: 17px; font-weight: 800; color: #172033;")
        res_header.addWidget(title)
        res_header.addStretch()
        layout.addLayout(res_header)

        # 4 Metric StatCards
        self.metrics_cards_layout = QHBoxLayout()
        self.metrics_cards_layout.setSpacing(12)

        self.card_faults = StatCard(
            "Page Faults",
            "--",
            "occurrences",
            tooltip="Number of memory accesses where requested page was not present in physical frames.",
            accent_color=ACCENT_ROSE,
        )
        self.card_hits = StatCard(
            "Page Hits",
            "--",
            "occurrences",
            tooltip="Number of memory accesses satisfied immediately from physical frames.",
            accent_color=ACCENT_EMERALD,
        )
        self.card_fault_rate = StatCard(
            "Page-Fault Rate",
            "--",
            "percentage",
            tooltip="Proportion of page references resulting in a fault: (Faults / Total References) × 100.",
            accent_color=ACCENT_AMBER,
        )
        self.card_hit_rate = StatCard(
            "Page-Hit Rate",
            "--",
            "percentage",
            tooltip="Proportion of page references satisfied in memory: (Hits / Total References) × 100.",
            accent_color=ACCENT_HOVER,
        )

        self.metrics_cards_layout.addWidget(self.card_faults)
        self.metrics_cards_layout.addWidget(self.card_hits)
        self.metrics_cards_layout.addWidget(self.card_fault_rate)
        self.metrics_cards_layout.addWidget(self.card_hit_rate)
        layout.addLayout(self.metrics_cards_layout)

        # Interactive Frame-by-Frame Timeline (The centerpiece)
        timeline_card = QFrame()
        timeline_card.setStyleSheet(
            f"""
            QFrame {{
                background-color: {BG_SURFACE};
                border: 1px solid {BORDER};
                border-radius: 8px;
            }}
            """
        )
        tl_layout = QVBoxLayout(timeline_card)
        tl_layout.setContentsMargins(18, 14, 18, 16)
        tl_layout.setSpacing(10)

        tl_header = QHBoxLayout()
        tl_title = QLabel("Frame-by-Frame Execution Timeline")
        tl_title.setStyleSheet("font-weight: 700; font-size: 13px; color: #172033;")
        tl_hint = QLabel("Step-by-step memory frame allocation, replacements, and hit/fault detection.")
        tl_hint.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 11px;")

        tl_header.addWidget(tl_title)
        tl_header.addWidget(tl_hint)
        tl_header.addStretch()

        self.frame_grid = FrameGridWidget()

        tl_layout.addLayout(tl_header)
        tl_layout.addWidget(self.frame_grid)
        layout.addWidget(timeline_card)

        # Tabbed Details: Step Table, Comparison Table, Raw Terminal Output
        self.tabs = QTabWidget()

        # Tab 1: Step-by-Step Table
        self.tab_steps = QWidget()
        t1_layout = QVBoxLayout(self.tab_steps)
        t1_layout.setContentsMargins(10, 10, 10, 10)
        t1_layout.setSpacing(8)

        self.steps_table = QTableWidget(0, 6)
        self.steps_table.setHorizontalHeaderLabels([
            "Step",
            "Page Reference",
            "Outcome",
            "Evicted Page",
            "Frame Contents",
            "Operation Analysis",
        ])
        h1 = self.steps_table.horizontalHeader()
        h1.setSectionResizeMode(0, QHeaderView.Fixed)
        self.steps_table.setColumnWidth(0, 60)
        h1.setSectionResizeMode(1, QHeaderView.Fixed)
        self.steps_table.setColumnWidth(1, 120)
        h1.setSectionResizeMode(2, QHeaderView.Fixed)
        self.steps_table.setColumnWidth(2, 100)
        h1.setSectionResizeMode(3, QHeaderView.Fixed)
        self.steps_table.setColumnWidth(3, 110)
        h1.setSectionResizeMode(4, QHeaderView.Fixed)
        self.steps_table.setColumnWidth(4, 180)
        h1.setSectionResizeMode(5, QHeaderView.Stretch)

        h1.setFixedHeight(34)
        self.steps_table.verticalHeader().setVisible(False)
        self.steps_table.verticalHeader().setDefaultSectionSize(34)
        self.steps_table.setEditTriggers(QTableWidget.NoEditTriggers)
        t1_layout.addWidget(self.steps_table)

        lbl_step_note = QLabel(
            "Step History: Complete record of memory transitions generated by verified C++ backend execution."
        )
        lbl_step_note.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 11px; padding: 2px 4px;")
        t1_layout.addWidget(lbl_step_note)
        self.tabs.addTab(self.tab_steps, "Step-by-Step History")

        # Tab 2: Comparison Table
        self.tab_comp = QWidget()
        t2_layout = QVBoxLayout(self.tab_comp)
        t2_layout.setContentsMargins(10, 10, 10, 10)
        t2_layout.setSpacing(8)

        self.comp_table = QTableWidget(0, 6)
        self.comp_table.setHorizontalHeaderLabels([
            "Algorithm",
            "Total References",
            "Page Faults",
            "Page Hits",
            "Fault Rate (%)",
            "Hit Rate (%)",
        ])
        self.comp_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.comp_table.horizontalHeader().setFixedHeight(34)
        self.comp_table.verticalHeader().setVisible(False)
        self.comp_table.verticalHeader().setDefaultSectionSize(34)
        self.comp_table.setEditTriggers(QTableWidget.NoEditTriggers)
        t2_layout.addWidget(self.comp_table)

        lbl_comp_note = QLabel(
            "Algorithm Comparison: Side-by-side benchmark of FIFO, LRU, and Optimal algorithms evaluated across the identical workload."
        )
        lbl_comp_note.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 11px; padding: 2px 4px;")
        t2_layout.addWidget(lbl_comp_note)
        self.tabs.addTab(self.tab_comp, "Multi-Algorithm Comparison")

        # Tab 3: Raw Terminal Output
        self.tab_raw = QWidget()
        t3_layout = QVBoxLayout(self.tab_raw)
        t3_layout.setContentsMargins(10, 10, 10, 10)
        self.raw_text = QTextEdit()
        self.raw_text.setReadOnly(True)
        t3_layout.addWidget(self.raw_text)
        self.tabs.addTab(self.tab_raw, "Raw Terminal Output")

        layout.addWidget(self.tabs)
        return widget

    def _on_algorithm_changed(self, index: int) -> None:
        self._update_algorithm_description()

    def _update_algorithm_description(self) -> None:
        algo_data = self.algo_combo.currentData()
        if not algo_data:
            return
        algo = PagingAlgorithm(algo_data) if isinstance(algo_data, str) else algo_data
        self.algo_info_label.setText(algo.description)

    def _on_preset_selected(self, index: int) -> None:
        text = self.preset_combo.currentText()
        if "Classic Textbook" in text:
            self.load_preset("Classic Textbook")
        elif "Belady's Anomaly" in text:
            self.load_preset("Belady's Anomaly")
        elif "High Locality" in text:
            self.load_preset("High Locality")
        elif "Sequential Cyclic" in text:
            self.load_preset("Sequential Cyclic")

    def load_preset(self, name: str) -> None:
        if name == "Classic Textbook":
            self.spin_frames.setValue(3)
            self.input_ref_string.setText("7, 0, 1, 2, 0, 3, 0, 4, 2, 3, 0, 3, 2")
        elif name == "Belady's Anomaly":
            self.spin_frames.setValue(3)
            self.input_ref_string.setText("1, 2, 3, 4, 1, 2, 5, 1, 2, 3, 4, 5")
        elif name == "High Locality":
            self.spin_frames.setValue(3)
            self.input_ref_string.setText("1, 2, 1, 3, 1, 2, 4, 1, 2, 1")
        elif name == "Sequential Cyclic":
            self.spin_frames.setValue(4)
            self.input_ref_string.setText("1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4")

    def collect_inputs(self) -> tuple[Optional[PagingConfig], Optional[str]]:
        """Parse and validate user inputs with student-friendly error messages."""
        algo_data = self.algo_combo.currentData()
        algo = PagingAlgorithm(algo_data) if isinstance(algo_data, str) else algo_data

        frame_count = self.spin_frames.value()
        raw_ref = self.input_ref_string.text().strip()

        if not raw_ref:
            return None, "Page reference string is empty. Please enter space- or comma-separated page numbers."

        # Parse string supporting commas or spaces
        clean_tokens = raw_ref.replace(",", " ").split()
        ref_pages: List[int] = []

        for idx, tok in enumerate(clean_tokens):
            try:
                page_val = int(tok)
            except ValueError:
                return None, f"Invalid token '{tok}' at position {idx + 1}. Page numbers must be integers."
            if page_val < 0:
                return None, f"Page number '{page_val}' at position {idx + 1} is negative. Page numbers must be non-negative (>= 0)."
            if page_val > 1000000:
                return None, f"Page number '{page_val}' at position {idx + 1} exceeds maximum allowable page range (1,000,000)."
            ref_pages.append(page_val)

        config = PagingConfig(
            algorithm=algo,
            frame_count=frame_count,
            reference_string=ref_pages,
        )

        cfg_err = config.validate()
        if cfg_err:
            return None, cfg_err

        return config, None

    def run_simulation(self) -> None:
        """Trigger backend execution with inline validation feedback."""
        config, err = self.collect_inputs()
        if err:
            self.status_banner.setStyleSheet(
                f"background-color: {DANGER_BG}; color: {DANGER_TEXT}; border: 1px solid {DANGER}; border-radius: 6px; padding: 10px 14px; font-weight: 500;"
            )
            self.status_banner.setText(f"Input validation error: {err}")
            return

        self.btn_run.setEnabled(False)
        self.status_banner.setStyleSheet(
            f"background-color: rgba(14, 165, 233, 0.15); color: {ACCENT_HOVER}; border: 1px solid rgba(14, 165, 233, 0.35); border-radius: 6px; padding: 10px 14px; font-weight: 500;"
        )
        self.status_banner.setText(f"Running {config.algorithm.value} page replacement simulation via C++ paging manager...")

        self._active_worker = PagingWorker(self.runner, config)
        self._active_worker.signals.completed.connect(self._on_simulation_success)
        self._active_worker.signals.failed.connect(self._on_simulation_failed)
        self._active_worker.start()

    def _on_simulation_success(self, result: object) -> None:
        self.btn_run.setEnabled(True)
        self.status_banner.setStyleSheet(
            f"background-color: {SUCCESS_BG}; color: {SUCCESS_TEXT}; border: 1px solid {SUCCESS}; border-radius: 6px; padding: 10px 14px; font-weight: 500;"
        )

        if isinstance(result, PagingComparisonResultModel):
            self.status_banner.setText("Page replacement comparison completed successfully across FIFO, LRU, and Optimal.")
            self._display_comparison_results(result)
            if self.on_execution_completed:
                self.on_execution_completed("Paging Comparison", len(result.entries), 0.0, 0.0, True)
        elif isinstance(result, PagingSimulationResultModel):
            self.status_banner.setText(
                f"{result.algorithm_name} simulation completed successfully: "
                f"{result.metrics.page_faults} faults, {result.metrics.page_hits} hits "
                f"({result.metrics.fault_percentage:.1f}% fault rate)."
            )
            self._display_single_result(result)
            if self.on_execution_completed:
                self.on_execution_completed(
                    f"{result.algorithm_name} Paging",
                    result.metrics.total_references,
                    float(result.metrics.page_faults),
                    float(result.metrics.page_hits),
                    True,
                )

    def _on_simulation_failed(self, error_message: str) -> None:
        self.btn_run.setEnabled(True)
        self.status_banner.setStyleSheet(
            f"background-color: {DANGER_BG}; color: {DANGER_TEXT}; border: 1px solid {DANGER}; border-radius: 6px; padding: 10px 14px; font-weight: 500;"
        )
        self.status_banner.setText(f"Execution failed: {error_message}")
        self.raw_text.setPlainText(error_message)

    def _display_single_result(self, result: PagingSimulationResultModel) -> None:
        m = result.metrics
        total = m.total_references

        self.card_faults.set_value(str(m.page_faults), f"{m.fault_percentage:.1f}% of references")
        self.card_hits.set_value(str(m.page_hits), f"{m.hit_percentage:.1f}% of references")
        self.card_fault_rate.set_value(f"{m.fault_percentage:.1f}%", f"ratio: {m.fault_rate:.2f}")
        self.card_hit_rate.set_value(f"{m.hit_percentage:.1f}%", f"ratio: {m.hit_rate:.2f}")

        # Update Frame-by-frame Grid Widget
        self.frame_grid.set_simulation_result(result.frame_count, result.steps)

        # Update Step-by-Step Table
        self.steps_table.setRowCount(0)
        for s in result.steps:
            row = self.steps_table.rowCount()
            self.steps_table.insertRow(row)

            frames_str = "[" + ", ".join(str(f) if f != -1 else "—" for f in s.frames) + "]"
            evicted_str = f"P{s.evicted_page}" if s.evicted_page is not None else "None"

            # Formulate narrative explanation
            if s.is_fault:
                if s.evicted_page is not None:
                    desc = f"Fault: Frames full. Page P{s.evicted_page} evicted, P{s.page} loaded."
                else:
                    desc = f"Fault: Loaded P{s.page} into available empty frame."
            else:
                desc = f"Hit: Page P{s.page} already present in memory."

            item_step = QTableWidgetItem(str(s.step_number))
            item_step.setTextAlignment(Qt.AlignCenter)

            item_page = QTableWidgetItem(f"P{s.page}")
            item_page.setTextAlignment(Qt.AlignCenter)
            item_page.setForeground(QColor("#ffffff"))

            item_out = QTableWidgetItem("Fault" if s.is_fault else "Hit")
            item_out.setTextAlignment(Qt.AlignCenter)
            item_out.setForeground(QColor(ACCENT_ROSE if s.is_fault else ACCENT_EMERALD))

            item_evict = QTableWidgetItem(evicted_str)
            item_evict.setTextAlignment(Qt.AlignCenter)
            if s.evicted_page is not None:
                item_evict.setForeground(QColor(ACCENT_AMBER))

            item_frames = QTableWidgetItem(frames_str)
            item_frames.setTextAlignment(Qt.AlignCenter)

            item_desc = QTableWidgetItem(desc)

            self.steps_table.setItem(row, 0, item_step)
            self.steps_table.setItem(row, 1, item_page)
            self.steps_table.setItem(row, 2, item_out)
            self.steps_table.setItem(row, 3, item_evict)
            self.steps_table.setItem(row, 4, item_frames)
            self.steps_table.setItem(row, 5, item_desc)

        self.raw_text.setPlainText(result.raw_output)
        self.tabs.setCurrentIndex(0)

    def _display_comparison_results(self, result: PagingComparisonResultModel) -> None:
        self.comp_table.setRowCount(0)
        for entry in result.entries:
            row = self.comp_table.rowCount()
            self.comp_table.insertRow(row)

            items = [
                QTableWidgetItem(entry.algorithm_name),
                QTableWidgetItem(str(entry.total_references)),
                QTableWidgetItem(str(entry.page_faults)),
                QTableWidgetItem(str(entry.page_hits)),
                QTableWidgetItem(f"{(entry.fault_rate * 100.0):.2f}%"),
                QTableWidgetItem(f"{(entry.hit_rate * 100.0):.2f}%"),
            ]
            for col, it in enumerate(items):
                if col > 0:
                    it.setTextAlignment(Qt.AlignCenter)
                if col == 4:
                    it.setForeground(QColor(ACCENT_ROSE))
                elif col == 5:
                    it.setForeground(QColor(ACCENT_EMERALD))
                self.comp_table.setItem(row, col, it)

        self.raw_text.setPlainText(result.raw_output)
        self.tabs.setCurrentIndex(1)

    def display_results(self, result: PagingSimulationResultModel) -> None:
        """Public display method for tests and direct callers."""
        self._on_simulation_success(result)

    def display_comparison(self, result: PagingComparisonResultModel) -> None:
        """Public display method for comparison test callers."""
        self._on_simulation_success(result)

    def show_error(self, error_message: str) -> None:
        """Display error banner and feedback."""
        self._on_simulation_failed(error_message)

    def reset_results(self) -> None:
        """Reset metric cards, clear frame timeline, and wipe tables."""
        if self._active_worker and self._active_worker.isRunning():
            self._active_worker.cancel()

        self.card_faults.set_value("--", "occurrences")
        self.card_hits.set_value("--", "occurrences")
        self.card_fault_rate.set_value("--", "percentage")
        self.card_hit_rate.set_value("--", "percentage")

        self.frame_grid.clear()
        self.steps_table.setRowCount(0)
        self.comp_table.setRowCount(0)
        self.raw_text.clear()

        self.status_banner.setStyleSheet(
            f"background-color: rgba(14, 165, 233, 0.12); color: {ACCENT_HOVER}; border: 1px solid rgba(14, 165, 233, 0.3); border-radius: 6px; padding: 10px 14px; font-size: 12px; font-weight: 500;"
        )
        self.status_banner.setText("Simulation results cleared. Configure frames and reference string to begin.")
