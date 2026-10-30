"""Disk Scheduling interactive simulation and visualization page.

Supports all seven secondary storage scheduling algorithms (FCFS, SSTF, SCAN,
C-SCAN, LOOK, C-LOOK, LIFO) and comprehensive side-by-side comparison using
the verified C++ backend.
"""

from typing import Callable, List, Optional, Tuple, Union

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpinBox,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from ..backend.executor import DiskWorker
from ..backend.runner import BaseBackendRunner
from ..models.disk import (
    DiskAlgorithm,
    DiskComparisonEntryModel,
    DiskComparisonResultModel,
    DiskConfig,
    DiskDirection,
    DiskSchedulingResultModel,
    DiskStepModel,
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
    BG_CANVAS,
    BG_ELEVATED,
    BG_INPUT,
    BG_SURFACE,
    BORDER,
    BORDER_LIGHT,
    FONT_FAMILY,
    TEXT_MUTED,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
)
from ..widgets.disk_plot import DiskHeadPlotWidget
from ..widgets.stat_card import StatCard

AnyDiskResult = Union[DiskSchedulingResultModel, DiskComparisonResultModel]


class DiskPage(QWidget):
    """Main interactive Disk Arm Scheduling simulation and trajectory visualization page."""

    def __init__(
        self,
        runner: Optional[BaseBackendRunner] = None,
        on_execution_completed: Optional[Callable[[str, int, float, float, bool], None]] = None,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.runner = runner
        self.on_execution_completed = on_execution_completed
        self._active_worker: Optional[DiskWorker] = None
        self._last_result: Optional[AnyDiskResult] = None

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet(f"background-color: {BG_APP}; border: none;")

        content = QWidget()
        content.setStyleSheet(f"background-color: {BG_APP};")
        self.content_layout = QVBoxLayout(content)
        self.content_layout.setContentsMargins(36, 28, 36, 32)
        self.content_layout.setSpacing(20)

        # 1. Page Header
        header = self._build_header()
        self.content_layout.addLayout(header)

        # 2. Algorithm & Direction Selector Card
        mode_card = self._build_mode_selector_card()
        self.content_layout.addWidget(mode_card)

        # 3. Educational Guidance Concepts Section
        guidance = self._build_guidance_section()
        self.content_layout.addWidget(guidance)

        # 4. Configuration Card (Disk range, initial head, request queue, presets, run buttons)
        config_card = self._build_config_card()
        self.content_layout.addWidget(config_card)

        # 5. Execution Summary Stat Cards
        self.stats_layout = self._build_stats_row()
        self.content_layout.addLayout(self.stats_layout)

        # 6. Centerpiece: Interactive Disk Head Trajectory Plot
        self.plot_widget = DiskHeadPlotWidget(self)
        self.content_layout.addWidget(self.plot_widget)

        # 7. Detailed Analysis Results Tabs (Step Table, Comparison, Report, Raw Output)
        self.tabs_container = self._build_results_tabs()
        self.tabs = self.tabs_container
        self.content_layout.addWidget(self.tabs_container)

        scroll.setWidget(content)
        main_layout.addWidget(scroll)

        # Initialize with standard textbook workload
        self._load_preset("textbook")

    def _build_header(self) -> QVBoxLayout:
        layout = QVBoxLayout()
        layout.setSpacing(4)

        title = QLabel("Disk Scheduling Simulator")
        title.setStyleSheet("font-size: 24px; font-weight: 800; color: #ffffff; letter-spacing: 0.5px;")

        subtitle = QLabel(
            "Explore secondary storage seek latency optimization, boundary reversals, and circular wraparound head trajectories."
        )
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet(f"font-size: 13px; color: {TEXT_SECONDARY};")

        layout.addWidget(title)
        layout.addWidget(subtitle)
        return layout

    def _build_mode_selector_card(self) -> QFrame:
        card = QFrame()
        card.setProperty("card", True)
        card.setObjectName("DiskModeCard")
        card.setStyleSheet(
            f"""
            QFrame#DiskModeCard {{
                background-color: {BG_SURFACE};
                border: 1px solid {BORDER};
                border-radius: 10px;
                padding: 16px;
            }}
            """
        )
        layout = QVBoxLayout(card)
        layout.setSpacing(12)

        top_row = QHBoxLayout()
        top_row.setSpacing(16)

        # Algorithm Choice
        lbl_algo = QLabel("Scheduling Algorithm:")
        lbl_algo.setStyleSheet("font-weight: 700; font-size: 13px; color: #ffffff;")

        self.combo_algo = QComboBox()
        for algo in (
            DiskAlgorithm.FCFS,
            DiskAlgorithm.SSTF,
            DiskAlgorithm.SCAN,
            DiskAlgorithm.CSCAN,
            DiskAlgorithm.LOOK,
            DiskAlgorithm.CLOOK,
            DiskAlgorithm.LIFO,
            DiskAlgorithm.COMPARE_ALL,
        ):
            self.combo_algo.addItem(algo.display_name, algo)

        self.combo_algo.setFixedWidth(330)
        self.combo_algo.setStyleSheet(
            f"""
            QComboBox {{
                background-color: {BG_INPUT};
                border: 1px solid {BORDER_LIGHT};
                border-radius: 6px;
                padding: 6px 12px;
                color: #ffffff;
                font-weight: 600;
            }}
            QComboBox QAbstractItemView {{
                background-color: {BG_ELEVATED};
                color: #ffffff;
                selection-background-color: {ACCENT};
            }}
            """
        )
        self.combo_algo.currentIndexChanged.connect(self._on_algorithm_changed)

        # Direction Choice (for directional algorithms)
        self.lbl_dir = QLabel("Arm Direction:")
        self.lbl_dir.setStyleSheet("font-weight: 700; font-size: 13px; color: #ffffff;")

        self.combo_dir = QComboBox()
        self.combo_dir.addItem(DiskDirection.INCREASING.display_name, DiskDirection.INCREASING)
        self.combo_dir.addItem(DiskDirection.DECREASING.display_name, DiskDirection.DECREASING)
        self.combo_dir.setFixedWidth(260)
        self.combo_dir.setStyleSheet(
            f"""
            QComboBox {{
                background-color: {BG_INPUT};
                border: 1px solid {BORDER_LIGHT};
                border-radius: 6px;
                padding: 6px 12px;
                color: #ffffff;
                font-weight: 600;
            }}
            QComboBox:disabled {{
                background-color: rgba(30, 41, 59, 0.4);
                color: {TEXT_MUTED};
                border-color: {BORDER};
            }}
            QComboBox QAbstractItemView {{
                background-color: {BG_ELEVATED};
                color: #ffffff;
                selection-background-color: {ACCENT};
            }}
            """
        )
        self.combo_dir.currentIndexChanged.connect(self._on_input_changed)

        top_row.addWidget(lbl_algo)
        top_row.addWidget(self.combo_algo)
        top_row.addSpacing(16)
        top_row.addWidget(self.lbl_dir)
        top_row.addWidget(self.combo_dir)
        top_row.addStretch()

        # Dynamic Description Banner
        self.banner_desc = QFrame()
        self.banner_desc.setObjectName("DiskBannerDesc")
        self.banner_desc.setStyleSheet(
            f"""
            QFrame#DiskBannerDesc {{
                background-color: rgba(56, 189, 248, 0.08);
                border-left: 3px solid {ACCENT};
                border-radius: 4px;
                padding: 10px 14px;
            }}
            """
        )
        banner_layout = QVBoxLayout(self.banner_desc)
        banner_layout.setContentsMargins(0, 0, 0, 0)
        self.lbl_explanation = QLabel()
        self.lbl_explanation.setWordWrap(True)
        self.lbl_explanation.setStyleSheet(f"font-size: 12px; color: {TEXT_PRIMARY}; line-height: 1.4;")
        banner_layout.addWidget(self.lbl_explanation)

        layout.addLayout(top_row)
        layout.addWidget(self.banner_desc)

        self._update_algorithm_ui()
        return card

    def _build_guidance_section(self) -> QFrame:
        container = QFrame()
        container.setObjectName("GuidanceContainer")
        container.setStyleSheet(
            f"""
            QFrame#GuidanceContainer {{
                background-color: {BG_SURFACE};
                border: 1px solid {BORDER};
                border-radius: 10px;
                padding: 14px;
            }}
            """
        )
        layout = QVBoxLayout(container)
        layout.setSpacing(10)

        header = QLabel("Understanding Disk Arm Scheduling Mechanics & Boundaries")
        header.setStyleSheet("font-size: 13px; font-weight: 700; color: #ffffff;")
        layout.addWidget(header)

        grid = QGridLayout()
        grid.setSpacing(10)

        concepts = [
            (
                "Seek Latency Optimization",
                "Total Travel",
                "Moving the physical disk arm between cylinders dominates mechanical storage access times. Minimizing total cylinder delta boosts I/O throughput.",
                ACCENT,
            ),
            (
                "Boundary Semantics (SCAN)",
                "Full Sweep",
                "SCAN sweeps all the way to physical disk limits (cylinder 0 or max) before reversing, preventing starvation at opposing ends.",
                ACCENT_AMBER,
            ),
            (
                "Circular Wraparound (C-SCAN/C-LOOK)",
                "Uniform Wait",
                "Wraparound sweeps quickly return the head without servicing, giving equal opportunity to new requests accumulating at the start.",
                ACCENT_VIOLET,
            ),
            (
                "Look-Ahead Reversal (LOOK/C-LOOK)",
                "Boundary Savings",
                "Reverses arm sweep immediately after the final requested cylinder, avoiding wasteful seeks to empty disk edges.",
                ACCENT_EMERALD,
            ),
        ]

        for idx, (title, tag, desc, color) in enumerate(concepts):
            c = QFrame()
            c.setObjectName(f"ConceptCard_{idx}")
            c.setStyleSheet(
                f"""
                QFrame#ConceptCard_{idx} {{
                    background-color: {BG_ELEVATED};
                    border: 1px solid {BORDER};
                    border-radius: 6px;
                    padding: 10px;
                }}
                """
            )
            c_layout = QVBoxLayout(c)
            c_layout.setSpacing(4)

            top = QHBoxLayout()
            lbl_t = QLabel(title)
            lbl_t.setStyleSheet("font-size: 11px; font-weight: 700; color: #ffffff;")
            badge = QLabel(tag)
            badge.setStyleSheet(
                f"font-size: 9px; font-weight: 700; color: {color}; "
                f"background-color: rgba(255,255,255,0.06); padding: 2px 6px; border-radius: 3px;"
            )
            top.addWidget(lbl_t)
            top.addStretch()
            top.addWidget(badge)

            lbl_d = QLabel(desc)
            lbl_d.setWordWrap(True)
            lbl_d.setStyleSheet(f"font-size: 10.5px; color: {TEXT_SECONDARY}; line-height: 1.3;")

            c_layout.addLayout(top)
            c_layout.addWidget(lbl_d)

            row = idx // 2
            col = idx % 2
            grid.addWidget(c, row, col)

        layout.addLayout(grid)
        return container

    def _build_config_card(self) -> QFrame:
        card = QFrame()
        card.setProperty("card", True)
        card.setObjectName("DiskConfigCard")
        card.setStyleSheet(
            f"""
            QFrame#DiskConfigCard {{
                background-color: {BG_SURFACE};
                border: 1px solid {BORDER};
                border-radius: 10px;
                padding: 18px;
            }}
            """
        )
        layout = QVBoxLayout(card)
        layout.setSpacing(14)

        # Row 1: Cylinder Boundaries and Head Position
        row1 = QHBoxLayout()
        row1.setSpacing(16)

        # Min Cylinder
        min_box = QHBoxLayout()
        lbl_min = QLabel("Min Cylinder:")
        lbl_min.setStyleSheet("font-weight: 600; color: #ffffff; font-size: 12px;")
        self.spin_min = QSpinBox()
        self.spin_min.setRange(0, 100000)
        self.spin_min.setValue(0)
        self.spin_min.setFixedWidth(75)
        self.spin_min.setStyleSheet(f"background-color: {BG_INPUT}; border: 1px solid {BORDER_LIGHT}; color: #ffffff; padding: 5px;")
        self.spin_min.valueChanged.connect(self._on_input_changed)
        min_box.addWidget(lbl_min)
        min_box.addWidget(self.spin_min)

        # Max Cylinder
        max_box = QHBoxLayout()
        lbl_max = QLabel("Max Cylinder:")
        lbl_max.setStyleSheet("font-weight: 600; color: #ffffff; font-size: 12px;")
        self.spin_max = QSpinBox()
        self.spin_max.setRange(1, 100000)
        self.spin_max.setValue(199)
        self.spin_max.setFixedWidth(85)
        self.spin_max.setStyleSheet(f"background-color: {BG_INPUT}; border: 1px solid {BORDER_LIGHT}; color: #ffffff; padding: 5px;")
        self.spin_max.valueChanged.connect(self._on_input_changed)
        max_box.addWidget(lbl_max)
        max_box.addWidget(self.spin_max)

        # Initial Head
        head_box = QHBoxLayout()
        lbl_head = QLabel("Initial Head Position:")
        lbl_head.setStyleSheet("font-weight: 600; color: #ffffff; font-size: 12px;")
        self.spin_head = QSpinBox()
        self.spin_head.setRange(0, 100000)
        self.spin_head.setValue(53)
        self.spin_head.setFixedWidth(85)
        self.spin_head.setStyleSheet(f"background-color: {BG_INPUT}; border: 1px solid {BORDER_LIGHT}; color: {ACCENT_AMBER}; font-weight: 700; padding: 5px;")
        self.spin_head.valueChanged.connect(self._on_input_changed)
        head_box.addWidget(lbl_head)
        head_box.addWidget(self.spin_head)

        row1.addLayout(min_box)
        row1.addLayout(max_box)
        row1.addLayout(head_box)
        row1.addStretch()

        layout.addLayout(row1)

        # Row 2: Request Queue and Presets
        row2 = QHBoxLayout()
        row2.setSpacing(16)

        # Request queue input
        req_box = QVBoxLayout()
        req_box.setSpacing(4)
        lbl_req = QLabel("Cylinder Request Queue (Space- or comma-separated integers):")
        lbl_req.setStyleSheet("font-weight: 600; color: #ffffff; font-size: 12px;")
        self.txt_requests = QLineEdit("98 183 37 122 14 124 65 67")
        self.txt_requests.setStyleSheet(
            f"""
            QLineEdit {{
                background-color: {BG_INPUT};
                border: 1px solid {BORDER_LIGHT};
                border-radius: 6px;
                color: {ACCENT_CYAN};
                font-weight: 700;
                font-family: monospace;
                padding: 6px 10px;
                font-size: 12px;
            }}
            """
        )
        self.txt_requests.textChanged.connect(self._on_input_changed)
        req_box.addWidget(lbl_req)
        req_box.addWidget(self.txt_requests)

        # Presets dropdown
        preset_box = QVBoxLayout()
        preset_box.setSpacing(4)
        lbl_pre = QLabel("Educational Workload Presets:")
        lbl_pre.setStyleSheet("font-weight: 600; color: #ffffff; font-size: 12px;")
        self.combo_presets = QComboBox()
        self.combo_presets.addItem("Textbook Benchmark (Silberschatz 8-Req: 98..67, Head 53)", "textbook")
        self.combo_presets.addItem("High Boundary Locality (0, 195, 10, 180, 5, 199, Head 100)", "boundary")
        self.combo_presets.addItem("Clustered High Cylinders (150, 165, 172, 188, 190, Head 140)", "high_cluster")
        self.combo_presets.addItem("Clustered Low Cylinders (5, 12, 18, 25, 33, 40, Head 50)", "low_cluster")
        self.combo_presets.addItem("Ascending Sequential Sweeps (10, 30, 60, 90, 120, 150, Head 50)", "ascending")
        self.combo_presets.addItem("Large Span Oscillating (10, 190, 20, 180, 30, 170, Head 100)", "oscillating")
        self.combo_presets.setFixedWidth(340)
        self.combo_presets.setStyleSheet(
            f"""
            QComboBox {{
                background-color: {BG_INPUT};
                border: 1px solid {BORDER_LIGHT};
                border-radius: 6px;
                color: #ffffff;
                padding: 6px 10px;
                font-size: 12px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {BG_ELEVATED};
                color: #ffffff;
                selection-background-color: {ACCENT};
            }}
            """
        )
        self.combo_presets.currentIndexChanged.connect(self._on_preset_selected)
        preset_box.addWidget(lbl_pre)
        preset_box.addWidget(self.combo_presets)

        row2.addLayout(req_box, stretch=1)
        row2.addLayout(preset_box)

        layout.addLayout(row2)

        # Actions & Error Feedback Row
        action_row = QHBoxLayout()
        action_row.setSpacing(12)

        self.btn_run = QPushButton("Run Simulation")
        self.btn_run.setProperty("class", "btn-primary")
        self.btn_run.setFixedWidth(160)
        self.btn_run.setFixedHeight(36)
        self.btn_run.setStyleSheet(
            f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {ACCENT}, stop:1 {ACCENT_INDIGO});
                color: #ffffff;
                font-weight: 700;
                font-size: 13px;
                border-radius: 6px;
                border: 1px solid rgba(56, 189, 248, 0.4);
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {ACCENT_HOVER}, stop:1 #818cf8);
                border-color: #7dd3fc;
            }}
            QPushButton:disabled {{
                background-color: {BG_ELEVATED};
                color: {TEXT_MUTED};
                border: 1px solid {BORDER};
            }}
            """
        )
        self.btn_run.clicked.connect(self._run_simulation)

        self.btn_compare = QPushButton("Compare All Algorithms")
        self.btn_compare.setFixedWidth(190)
        self.btn_compare.setFixedHeight(36)
        self.btn_compare.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {BG_ELEVATED};
                color: {ACCENT_EMERALD};
                border: 1px solid rgba(16, 185, 129, 0.4);
                border-radius: 6px;
                font-weight: 700;
                font-size: 12.5px;
            }}
            QPushButton:hover {{
                background-color: rgba(16, 185, 129, 0.15);
                border-color: {ACCENT_EMERALD};
            }}
            """
        )
        self.btn_compare.clicked.connect(self._run_comparison)

        self.btn_reset = QPushButton("Reset Defaults")
        self.btn_reset.setFixedWidth(120)
        self.btn_reset.setFixedHeight(36)
        self.btn_reset.setStyleSheet(
            f"background-color: {BG_ELEVATED}; color: {TEXT_PRIMARY}; border: 1px solid {BORDER}; border-radius: 6px; font-weight: 600;"
        )
        self.btn_reset.clicked.connect(lambda: self._load_preset("textbook"))

        self.lbl_validation_err = QLabel()
        self.lbl_validation_err.setStyleSheet(f"color: {ACCENT_ROSE}; font-weight: 600; font-size: 11px;")
        self.lbl_validation_err.hide()

        action_row.addWidget(self.btn_run)
        action_row.addWidget(self.btn_compare)
        action_row.addWidget(self.btn_reset)
        action_row.addSpacing(12)
        action_row.addWidget(self.lbl_validation_err, stretch=1)

        layout.addLayout(action_row)
        return card

    def _build_stats_row(self) -> QHBoxLayout:
        layout = QHBoxLayout()
        layout.setSpacing(14)

        self.card_movement = StatCard("Total Head Movement", "Ready", "info")
        self.card_avg = StatCard("Average Seek / Req", "-", "neutral")
        self.card_requests = StatCard("Requests Serviced", "8", "neutral")
        self.card_final = StatCard("Final Head Position", "-", "neutral")

        for card in (self.card_movement, self.card_avg, self.card_requests, self.card_final):
            card.setMinimumWidth(120)
            card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        layout.addWidget(self.card_movement)
        layout.addWidget(self.card_avg)
        layout.addWidget(self.card_requests)
        layout.addWidget(self.card_final)
        return layout

    def _build_results_tabs(self) -> QTabWidget:
        tabs = QTabWidget()
        tabs.setObjectName("DiskResultsTabs")
        tabs.setMinimumHeight(240)
        tabs.setStyleSheet(
            f"""
            QTabWidget#DiskResultsTabs::pane {{
                border: 1px solid {BORDER};
                border-radius: 8px;
                background-color: {BG_SURFACE};
            }}
            QTabBar::tab {{
                background-color: {BG_SURFACE};
                color: {TEXT_SECONDARY};
                padding: 8px 20px;
                font-weight: 600;
                border: 1px solid {BORDER};
                border-bottom: none;
                margin-right: 4px;
            }}
            QTabBar::tab:selected {{
                background-color: {BG_ELEVATED};
                color: {ACCENT};
                border-top: 2px solid {ACCENT};
            }}
            """
        )

        # Tab 1: Step-by-Step Movement Timeline Table
        self.table_steps = QTableWidget()
        self.table_steps.setColumnCount(6)
        self.table_steps.setHorizontalHeaderLabels([
            "Step",
            "From Cylinder",
            "To Cylinder",
            "Seek Movement (cyl)",
            "Cumulative Movement",
            "Action / Traversal Type",
        ])
        self.table_steps.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_steps.verticalHeader().setVisible(False)
        self.table_steps.setStyleSheet(
            f"""
            QTableWidget {{
                background-color: {BG_SURFACE};
                color: #ffffff;
                gridline-color: {BORDER};
                border: none;
                font-size: 12px;
            }}
            QHeaderView::section {{
                background-color: {BG_ELEVATED};
                color: {TEXT_SECONDARY};
                font-weight: 700;
                padding: 6px;
                border: 1px solid {BORDER};
            }}
            """
        )
        tabs.addTab(self.table_steps, "Step-by-Step Trajectory")

        # Tab 2: Comparison Breakdown Table
        self.table_comparison = QTableWidget()
        self.table_comparison.setColumnCount(5)
        self.table_comparison.setHorizontalHeaderLabels([
            "Algorithm",
            "Total Movement (cyl)",
            "Avg Seek / Req",
            "Final Head Position",
            "Efficiency Rating",
        ])
        self.table_comparison.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_comparison.verticalHeader().setVisible(False)
        self.table_comparison.setStyleSheet(
            f"""
            QTableWidget {{
                background-color: {BG_SURFACE};
                color: #ffffff;
                gridline-color: {BORDER};
                border: none;
                font-size: 12px;
            }}
            QHeaderView::section {{
                background-color: {BG_ELEVATED};
                color: {TEXT_SECONDARY};
                font-weight: 700;
                padding: 6px;
                border: 1px solid {BORDER};
            }}
            """
        )
        tabs.addTab(self.table_comparison, "Comparison Breakdown")

        # Tab 3: Detailed Diagnostic Report
        self.txt_diagnostics = QTextEdit()
        self.txt_diagnostics.setReadOnly(True)
        self.txt_diagnostics.setStyleSheet(
            f"""
            QTextEdit {{
                background-color: {BG_CANVAS};
                color: {TEXT_PRIMARY};
                border: none;
                font-family: monospace;
                font-size: 12px;
                padding: 12px;
            }}
            """
        )
        self.txt_diagnostics.setPlaceholderText("Diagnostic report will appear here after running simulation...")
        tabs.addTab(self.txt_diagnostics, "Diagnostic Report")

        # Tab 4: Raw C++ CLI Output
        self.txt_raw = QTextEdit()
        self.txt_raw.setReadOnly(True)
        self.txt_raw.setStyleSheet(
            f"""
            QTextEdit {{
                background-color: {BG_CANVAS};
                color: #38bdf8;
                border: none;
                font-family: monospace;
                font-size: 11px;
                padding: 12px;
            }}
            """
        )
        self.txt_raw.setPlaceholderText("Raw terminal output from C++ engine will appear here...")
        tabs.addTab(self.txt_raw, "Raw C++ Output")

        return tabs

    def _on_algorithm_changed(self) -> None:
        self._update_algorithm_ui()
        self._clear_previous_results()

    def _update_algorithm_ui(self) -> None:
        algo_data = self.combo_algo.currentData()
        if not algo_data:
            return
        algo = DiskAlgorithm(algo_data) if isinstance(algo_data, str) else algo_data

        self.lbl_explanation.setText(algo.description)

        # Enable direction dropdown only for directional algorithms
        if algo.needs_direction:
            self.combo_dir.setEnabled(True)
            self.lbl_dir.setStyleSheet("font-weight: 700; font-size: 13px; color: #ffffff;")
        else:
            self.combo_dir.setEnabled(False)
            self.lbl_dir.setStyleSheet(f"font-weight: 700; font-size: 13px; color: {TEXT_MUTED};")

    def _on_input_changed(self) -> None:
        self._clear_previous_results()
        self._validate_inputs()

    def _clear_previous_results(self) -> None:
        self._last_result = None
        self.card_movement.set_value("Pending", "neutral")
        self.card_avg.set_value("-", "neutral")
        self.card_final.set_value("-", "neutral")

    def _validate_inputs(self) -> Tuple[Optional[DiskConfig], Optional[str]]:
        algo_data = self.combo_algo.currentData()
        algo = DiskAlgorithm(algo_data) if isinstance(algo_data, str) else algo_data
        min_c = self.spin_min.value()
        max_c = self.spin_max.value()
        head_c = self.spin_head.value()
        dir_data = self.combo_dir.currentData()
        dir_val = DiskDirection(dir_data) if isinstance(dir_data, str) else dir_data

        # Parse request string
        raw_text = self.txt_requests.text().strip()
        if not raw_text:
            err = "Cylinder request queue cannot be empty. Please enter at least one cylinder number."
            self.lbl_validation_err.setText(err)
            self.lbl_validation_err.show()
            return None, err

        tokens = raw_text.replace(",", " ").split()
        reqs: List[int] = []
        for t in tokens:
            try:
                v = int(t)
                reqs.append(v)
            except ValueError:
                err = f"Invalid non-integer token '{t}' in request queue."
                self.lbl_validation_err.setText(err)
                self.lbl_validation_err.show()
                return None, err

        cfg = DiskConfig(
            algorithm=algo,
            min_cylinder=min_c,
            max_cylinder=max_c,
            initial_head=head_c,
            direction=dir_val,
            requests=reqs,
        )

        validation_err = cfg.validate()
        if validation_err:
            self.lbl_validation_err.setText(validation_err)
            self.lbl_validation_err.show()
            return None, validation_err

        self.lbl_validation_err.hide()
        return cfg, None

    def _on_preset_selected(self, index: int) -> None:
        preset_key = self.combo_presets.currentData()
        if preset_key:
            self._load_preset(preset_key)

    def _load_preset(self, preset_key: str) -> None:
        if preset_key == "textbook":
            self.spin_min.setValue(0)
            self.spin_max.setValue(199)
            self.spin_head.setValue(53)
            self.txt_requests.setText("98 183 37 122 14 124 65 67")
            self.combo_dir.setCurrentIndex(0)  # Increasing
        elif preset_key == "boundary":
            self.spin_min.setValue(0)
            self.spin_max.setValue(199)
            self.spin_head.setValue(100)
            self.txt_requests.setText("0 195 10 180 5 199 12")
            self.combo_dir.setCurrentIndex(0)
        elif preset_key == "high_cluster":
            self.spin_min.setValue(0)
            self.spin_max.setValue(200)
            self.spin_head.setValue(140)
            self.txt_requests.setText("150 165 172 188 190 195")
            self.combo_dir.setCurrentIndex(0)
        elif preset_key == "low_cluster":
            self.spin_min.setValue(0)
            self.spin_max.setValue(200)
            self.spin_head.setValue(50)
            self.txt_requests.setText("5 12 18 25 33 40")
            self.combo_dir.setCurrentIndex(1)  # Decreasing
        elif preset_key == "ascending":
            self.spin_min.setValue(0)
            self.spin_max.setValue(200)
            self.spin_head.setValue(50)
            self.txt_requests.setText("10 30 60 90 120 150")
            self.combo_dir.setCurrentIndex(0)
        elif preset_key == "oscillating":
            self.spin_min.setValue(0)
            self.spin_max.setValue(200)
            self.spin_head.setValue(100)
            self.txt_requests.setText("10 190 20 180 30 170")
            self.combo_dir.setCurrentIndex(0)

        self._clear_previous_results()

    def _run_simulation(self) -> None:
        cfg, err = self._validate_inputs()
        if err or not cfg:
            return

        self._start_worker(cfg)

    def _run_comparison(self) -> None:
        cfg, err = self._validate_inputs()
        if err or not cfg:
            return

        # Override algorithm to COMPARE_ALL
        comp_cfg = DiskConfig(
            algorithm=DiskAlgorithm.COMPARE_ALL,
            min_cylinder=cfg.min_cylinder,
            max_cylinder=cfg.max_cylinder,
            initial_head=cfg.initial_head,
            direction=cfg.direction,
            requests=list(cfg.requests),
        )
        self._start_worker(comp_cfg)

    def _start_worker(self, config: DiskConfig) -> None:
        if self._active_worker and self._active_worker.isRunning():
            self._active_worker.cancel()
            self._active_worker.wait()

        self.btn_run.setEnabled(False)
        self.btn_compare.setEnabled(False)
        self.btn_run.setText("Simulating...")

        self.card_movement.set_value("Running...", "pending")
        self.card_avg.set_value("-", "neutral")
        self.card_final.set_value("-", "neutral")

        self._active_worker = DiskWorker(self.runner, config)
        self._active_worker.finished_exec.connect(self._on_simulation_success)
        self._active_worker.failed_exec.connect(self._on_simulation_failed)
        self._active_worker.start()

    def _on_simulation_success(self, result: AnyDiskResult) -> None:
        self.btn_run.setEnabled(True)
        self.btn_compare.setEnabled(True)
        self.btn_run.setText("Run Simulation")
        self.lbl_validation_err.hide()
        self._last_result = result

        min_c = self.spin_min.value()
        max_c = self.spin_max.value()

        if isinstance(result, DiskSchedulingResultModel):
            # Update Stat Cards
            self.card_movement.set_value(f"{result.total_head_movement} cyl", "success")
            self.card_avg.set_value(f"{result.average_head_movement:.2f} cyl/req", "info")
            self.card_requests.set_value(f"{len(result.serviced_requests)}", "neutral")
            self.card_final.set_value(f"Cyl {result.final_head_position}", "neutral")

            # Update Plot & Flow Bar
            self.plot_widget.set_result(result, min_c, max_c)

            # Populate Step Table
            self._populate_step_table(result.steps)

            # Populate Diagnostics
            self._populate_diagnostics(result)

            # Switch to Step Table tab
            self.tabs_container.setCurrentIndex(0)

            # Raw output
            self.txt_raw.setPlainText(result.raw_output)

            # Record execution
            if self.on_execution_completed:
                self.on_execution_completed(
                    f"Disk - {result.algorithm.value}",
                    len(result.serviced_requests),
                    float(result.total_head_movement),
                    float(result.average_head_movement),
                    True,
                )

        elif isinstance(result, DiskComparisonResultModel):
            # Best algorithm
            best = min(result.entries, key=lambda x: x.total_head_movement) if result.entries else None
            best_mov = f"{best.total_head_movement} cyl ({best.algorithm_name.split()[0]})" if best else "Done"

            self.card_movement.set_value(best_mov, "success")
            self.card_avg.set_value(f"{best.average_head_movement:.2f} cyl/req" if best else "-", "info")
            self.card_requests.set_value(f"{len(result.original_requests)}", "neutral")
            self.card_final.set_value("All Algorithms", "neutral")

            # Populate Comparison Table
            self._populate_comparison_table(result)

            # Raw output
            self.txt_raw.setPlainText(result.raw_output)

            # Switch to comparison tab
            self.tabs_container.setCurrentIndex(1)

            if self.on_execution_completed:
                self.on_execution_completed(
                    "Disk - Compare All",
                    len(result.original_requests),
                    float(best.total_head_movement) if best else 0.0,
                    float(best.average_head_movement) if best else 0.0,
                    True,
                )

    def _on_simulation_failed(self, error_message: str) -> None:
        self.btn_run.setEnabled(True)
        self.btn_compare.setEnabled(True)
        self.btn_run.setText("Run Simulation")

        self.card_movement.set_value("Failed", "danger")
        self.lbl_validation_err.setText(error_message)
        self.lbl_validation_err.show()
        self.txt_raw.setPlainText(f"Simulation Error:\n{error_message}")

    def _populate_step_table(self, steps: List[DiskStepModel]) -> None:
        self.table_steps.setRowCount(len(steps))
        for r_idx, step in enumerate(steps):
            # Step #
            item_step = QTableWidgetItem(f"Step {step.step_number}")
            item_step.setTextAlignment(Qt.AlignCenter)
            item_step.setFlags(item_step.flags() & ~Qt.ItemIsEditable)

            # From Cyl
            item_from = QTableWidgetItem(str(step.from_cylinder))
            item_from.setTextAlignment(Qt.AlignCenter)
            item_from.setFlags(item_from.flags() & ~Qt.ItemIsEditable)

            # To Cyl
            item_to = QTableWidgetItem(str(step.to_cylinder))
            item_to.setTextAlignment(Qt.AlignCenter)
            item_to.setFlags(item_to.flags() & ~Qt.ItemIsEditable)

            # Seek Movement
            item_mov = QTableWidgetItem(f"+{step.movement} cyl")
            item_mov.setTextAlignment(Qt.AlignCenter)
            item_mov.setFlags(item_mov.flags() & ~Qt.ItemIsEditable)
            if step.is_wraparound:
                item_mov.setForeground(QColor(ACCENT_AMBER))
            elif step.is_boundary:
                item_mov.setForeground(QColor(ACCENT_VIOLET))
            else:
                item_mov.setForeground(QColor(ACCENT_EMERALD))

            # Cumulative
            item_cum = QTableWidgetItem(f"{step.cumulative_movement} cyl")
            item_cum.setTextAlignment(Qt.AlignCenter)
            item_cum.setFlags(item_cum.flags() & ~Qt.ItemIsEditable)

            # Action / Description
            item_desc = QTableWidgetItem(step.action_description)
            item_desc.setFlags(item_desc.flags() & ~Qt.ItemIsEditable)
            if step.is_wraparound:
                item_desc.setForeground(QColor(ACCENT_AMBER))
            elif step.is_boundary:
                item_desc.setForeground(QColor(ACCENT_VIOLET))
            else:
                item_desc.setForeground(QColor(TEXT_PRIMARY))

            self.table_steps.setItem(r_idx, 0, item_step)
            self.table_steps.setItem(r_idx, 1, item_from)
            self.table_steps.setItem(r_idx, 2, item_to)
            self.table_steps.setItem(r_idx, 3, item_mov)
            self.table_steps.setItem(r_idx, 4, item_cum)
            self.table_steps.setItem(r_idx, 5, item_desc)

    def _populate_comparison_table(self, result: DiskComparisonResultModel) -> None:
        entries = result.entries
        self.table_comparison.setRowCount(len(entries))

        min_mov = min((e.total_head_movement for e in entries), default=0)

        for r_idx, entry in enumerate(entries):
            # Algorithm
            item_algo = QTableWidgetItem(entry.algorithm_name)
            item_algo.setFlags(item_algo.flags() & ~Qt.ItemIsEditable)

            # Total Movement
            item_mov = QTableWidgetItem(f"{entry.total_head_movement} cyl")
            item_mov.setTextAlignment(Qt.AlignCenter)
            item_mov.setFlags(item_mov.flags() & ~Qt.ItemIsEditable)
            if entry.total_head_movement == min_mov and min_mov > 0:
                item_mov.setForeground(QColor(ACCENT_EMERALD))

            # Avg Movement
            item_avg = QTableWidgetItem(f"{entry.average_head_movement:.2f} cyl/req")
            item_avg.setTextAlignment(Qt.AlignCenter)
            item_avg.setFlags(item_avg.flags() & ~Qt.ItemIsEditable)

            # Final Head
            item_fin = QTableWidgetItem(f"Cylinder {entry.final_head_position}")
            item_fin.setTextAlignment(Qt.AlignCenter)
            item_fin.setFlags(item_fin.flags() & ~Qt.ItemIsEditable)

            # Rating
            diff = entry.total_head_movement - min_mov
            if entry.total_head_movement == min_mov:
                rating_str = "Optimal (Lowest Seek)"
                r_color = ACCENT_EMERALD
            elif diff < 50:
                rating_str = f"+{diff} cyl (High Efficiency)"
                r_color = ACCENT
            elif diff < 150:
                rating_str = f"+{diff} cyl (Moderate Seek)"
                r_color = ACCENT_AMBER
            else:
                rating_str = f"+{diff} cyl (Elevated Latency)"
                r_color = ACCENT_ROSE

            item_rating = QTableWidgetItem(rating_str)
            item_rating.setTextAlignment(Qt.AlignCenter)
            item_rating.setForeground(QColor(r_color))
            item_rating.setFlags(item_rating.flags() & ~Qt.ItemIsEditable)

            self.table_comparison.setItem(r_idx, 0, item_algo)
            self.table_comparison.setItem(r_idx, 1, item_mov)
            self.table_comparison.setItem(r_idx, 2, item_avg)
            self.table_comparison.setItem(r_idx, 3, item_fin)
            self.table_comparison.setItem(r_idx, 4, item_rating)

    def _populate_diagnostics(self, result: DiskSchedulingResultModel) -> None:
        lines = [
            f"=== Disk Arm Scheduling Diagnostic Report ===",
            f"Algorithm:               {result.algorithm_name}",
            f"Total Cylinders Range:   [{self.spin_min.value()}, {self.spin_max.value()}]",
            f"Initial Head Position:   Cylinder {result.initial_head_position}",
            f"Final Head Position:     Cylinder {result.final_head_position}",
            f"Original Requests:       [{', '.join(str(r) for r in self._validate_inputs()[0].requests)}]",
            f"Serviced Order:          [{', '.join(str(r) for r in result.serviced_requests)}]",
            f"Head Trajectory:         {' -> '.join(str(p) for p in result.head_path)}",
            f"Total Head Movement:     {result.total_head_movement} cylinders",
        ]
        if result.wraparound_movement > 0:
            lines.append(f"Wraparound Seek:         {result.wraparound_movement} cylinders (Rapid circular return seek)")
        lines.extend([
            f"Average Seek / Request:  {result.average_head_movement:.2f} cylinders per I/O request",
            f"Total Steps Executed:    {len(result.steps)}",
            f"\nStatus:                  {result.message}",
        ])
        self.txt_diagnostics.setPlainText("\n".join(lines))
