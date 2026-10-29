"""Deadlock Management interactive simulation and visualization page.

Supports Banker's Safety Algorithm, Resource Request Simulation, and Deadlock Detection
using the verified C++ backend.
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

from ..backend.executor import DeadlockWorker
from ..backend.runner import BaseBackendRunner
from ..models.deadlock import (
    DeadlockConfig,
    DeadlockDetectionResultModel,
    DeadlockMode,
    DeadlockRequestResultModel,
    DeadlockSafetyResultModel,
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
    DANGER,
    DANGER_BG,
    DANGER_TEXT,
    FONT_FAMILY,
    SUCCESS,
    SUCCESS_BG,
    SUCCESS_TEXT,
    TEXT_MUTED,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
)
from ..widgets.resource_graph import ResourceGraphWidget
from ..widgets.stat_card import StatCard

AnyDeadlockResult = Union[
    DeadlockSafetyResultModel,
    DeadlockRequestResultModel,
    DeadlockDetectionResultModel,
]


class DeadlockPage(QWidget):
    """Interactive Deadlock Management simulation page."""

    def __init__(
        self,
        runner: BaseBackendRunner,
        on_execution_completed: Optional[Callable[[str, int, float, float, bool], None]] = None,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.runner = runner
        self.on_execution_completed = on_execution_completed
        self._active_worker: Optional[DeadlockWorker] = None
        self._last_result: Optional[AnyDeadlockResult] = None
        self._is_updating_tables = False

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

        # 1. Header
        header = self._build_header()
        self.content_layout.addLayout(header)

        # 2. Mode Selector Card
        mode_card = self._build_mode_selector_card()
        self.content_layout.addWidget(mode_card)

        # 3. Educational Guidance Section
        guidance = self._build_guidance_section()
        self.content_layout.addWidget(guidance)

        # 4. Configuration Card (Dimensions, Available, Matrices, Presets)
        config_card = self._build_config_card()
        self.content_layout.addWidget(config_card)

        # 5. Execution Summary Stat Cards
        self.stats_layout = self._build_stats_row()
        self.content_layout.addLayout(self.stats_layout)

        # 6. Centerpiece: Resource Allocation Graph & Sequence Flow
        self.graph_widget = ResourceGraphWidget(self)
        self.content_layout.addWidget(self.graph_widget)

        # 7. Detailed Analysis Results Tabs
        self.tabs_container = self._build_results_tabs()
        self.content_layout.addWidget(self.tabs_container)

        scroll.setWidget(content)
        main_layout.addWidget(scroll)

        # Initialize with textbook preset
        self._load_preset("textbook_safe")

    def _build_header(self) -> QVBoxLayout:
        layout = QVBoxLayout()
        layout.setSpacing(4)

        title = QLabel("Deadlock Management Simulator")
        title.setStyleSheet("font-size: 24px; font-weight: 800; color: #ffffff; letter-spacing: 0.5px;")

        subtitle = QLabel("Explore how processes compete for resources and how operating systems determine whether execution can proceed safely.")
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet(f"font-size: 13px; color: {TEXT_SECONDARY};")

        layout.addWidget(title)
        layout.addWidget(subtitle)
        return layout

    def _build_mode_selector_card(self) -> QFrame:
        card = QFrame()
        card.setProperty("card", True)
        card.setObjectName("DeadlockModeCard")
        card.setStyleSheet(
            f"""
            QFrame#DeadlockModeCard {{
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
        lbl_mode = QLabel("Analysis Mode:")
        lbl_mode.setStyleSheet("font-weight: 700; font-size: 13px; color: #ffffff;")

        self.combo_mode = QComboBox()
        self.combo_mode.addItem("Banker's Safety Algorithm (Avoidance)", DeadlockMode.SAFETY)
        self.combo_mode.addItem("Simulate Resource Request (Banker's Algorithm)", DeadlockMode.RESOURCE_REQUEST)
        self.combo_mode.addItem("Deadlock Detection Algorithm (Recovery)", DeadlockMode.DETECTION)
        self.combo_mode.setFixedWidth(360)
        self.combo_mode.setStyleSheet(
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
        self.combo_mode.currentIndexChanged.connect(self._on_mode_changed)

        top_row.addWidget(lbl_mode)
        top_row.addWidget(self.combo_mode)
        top_row.addStretch()

        # Dynamic Description Banner
        self.banner_desc = QFrame()
        self.banner_desc.setObjectName("DeadlockBannerDesc")
        self.banner_desc.setStyleSheet(
            f"""
            QFrame#DeadlockBannerDesc {{
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

        self._update_mode_explanation()
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

        header = QLabel("Understanding Deadlock & Banker's Algorithm Concepts")
        header.setStyleSheet("font-size: 13px; font-weight: 700; color: #ffffff;")
        layout.addWidget(header)

        grid = QGridLayout()
        grid.setSpacing(10)

        concepts = [
            ("Available Resources", "Free Instances", "Resource instances currently unallocated in the physical system pool and available for immediate acquisition.", ACCENT_AMBER),
            ("Allocation Matrix", "Held Instances", "Resources currently held by each process. Process must retain these until maximum claim is met.", ACCENT),
            ("Maximum / Request", "Declared Claim", "Upper bound of resources a process may demand (Banker's) or immediate outstanding request (Detection).", ACCENT_VIOLET),
            ("Need = Max - Alloc", "Remaining Need", "Additional resources each process may still request before completing and releasing all held resources.", ACCENT_EMERALD),
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
            badge.setStyleSheet(f"font-size: 9px; font-weight: 700; color: {color}; background-color: rgba(255,255,255,0.06); padding: 2px 6px; border-radius: 3px;")
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
        card.setObjectName("DeadlockConfigCard")
        card.setStyleSheet(
            f"""
            QFrame#DeadlockConfigCard {{
                background-color: {BG_SURFACE};
                border: 1px solid {BORDER};
                border-radius: 10px;
                padding: 18px;
            }}
            """
        )
        layout = QVBoxLayout(card)
        layout.setSpacing(14)

        # Control Row 1: Dimensions and Available Resources
        row1 = QHBoxLayout()
        row1.setSpacing(16)

        # Process Count
        p_box = QHBoxLayout()
        lbl_p = QLabel("Processes (N):")
        lbl_p.setStyleSheet("font-weight: 600; color: #ffffff; font-size: 12px;")
        self.spin_processes = QSpinBox()
        self.spin_processes.setRange(1, 10)
        self.spin_processes.setValue(5)
        self.spin_processes.setFixedWidth(65)
        self.spin_processes.setStyleSheet(f"background-color: {BG_INPUT}; border: 1px solid {BORDER_LIGHT}; color: #ffffff; padding: 5px;")
        self.spin_processes.valueChanged.connect(self._on_dimensions_changed)
        p_box.addWidget(lbl_p)
        p_box.addWidget(self.spin_processes)

        # Resource Count
        r_box = QHBoxLayout()
        lbl_r = QLabel("Resource Types (M):")
        lbl_r.setStyleSheet("font-weight: 600; color: #ffffff; font-size: 12px;")
        self.spin_resources = QSpinBox()
        self.spin_resources.setRange(1, 6)
        self.spin_resources.setValue(3)
        self.spin_resources.setFixedWidth(65)
        self.spin_resources.setStyleSheet(f"background-color: {BG_INPUT}; border: 1px solid {BORDER_LIGHT}; color: #ffffff; padding: 5px;")
        self.spin_resources.valueChanged.connect(self._on_dimensions_changed)
        r_box.addWidget(lbl_r)
        r_box.addWidget(self.spin_resources)

        # Available Vector
        avail_box = QHBoxLayout()
        lbl_avail = QLabel("Available Resources:")
        lbl_avail.setStyleSheet("font-weight: 600; color: #ffffff; font-size: 12px;")
        self.txt_available = QLineEdit("3, 3, 2")
        self.txt_available.setFixedWidth(140)
        self.txt_available.setStyleSheet(f"background-color: {BG_INPUT}; border: 1px solid {BORDER_LIGHT}; color: {ACCENT_AMBER}; font-weight: 700; padding: 5px 8px;")
        avail_box.addWidget(lbl_avail)
        avail_box.addWidget(self.txt_available)

        row1.addLayout(p_box)
        row1.addLayout(r_box)
        row1.addLayout(avail_box)
        row1.addStretch()

        layout.addLayout(row1)

        # Control Row 2: Preset Workloads
        row2 = QHBoxLayout()
        row2.setSpacing(12)

        lbl_pre = QLabel("Preset Workloads:")
        lbl_pre.setStyleSheet("font-weight: 600; color: #ffffff; font-size: 12px;")
        self.combo_presets = QComboBox()
        self.combo_presets.addItem("Textbook Safe State (Silberschatz 5P/3R)", "textbook_safe")
        self.combo_presets.addItem("Unsafe State (Resource Starvation)", "unsafe_starvation")
        self.combo_presets.addItem("Resource Request: Eligible Safe Grant", "request_grant")
        self.combo_presets.addItem("Resource Request: Unsafe Denial", "request_denial")
        self.combo_presets.addItem("Deadlock Detection: Circular Wait (Deadlocked)", "detection_deadlock")
        self.combo_presets.addItem("Deadlock Detection: Fully Resolvable (No Deadlock)", "detection_safe")
        self.combo_presets.setMinimumWidth(320)
        self.combo_presets.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.combo_presets.setMaximumWidth(520)
        self.combo_presets.setStyleSheet(f"background-color: {BG_INPUT}; border: 1px solid {BORDER_LIGHT}; color: #ffffff; padding: 5px 10px;")
        self.combo_presets.currentIndexChanged.connect(self._on_preset_selected)

        row2.addWidget(lbl_pre)
        row2.addWidget(self.combo_presets)
        row2.addStretch()

        layout.addLayout(row2)

        # Resource Request Extra Panel (visible when mode == RESOURCE_REQUEST)
        self.request_panel = QFrame()
        self.request_panel.setObjectName("DeadlockRequestPanel")
        self.request_panel.setStyleSheet(
            f"""
            QFrame#DeadlockRequestPanel {{
                background-color: {BG_ELEVATED};
                border: 1px dashed {ACCENT};
                border-radius: 6px;
                padding: 8px 12px;
            }}
            """
        )
        req_layout = QHBoxLayout(self.request_panel)
        req_layout.setContentsMargins(4, 4, 4, 4)

        lbl_req_p = QLabel("Requesting Process:")
        lbl_req_p.setStyleSheet("font-weight: 600; color: #ffffff; font-size: 12px;")
        self.combo_req_proc = QComboBox()
        self.combo_req_proc.setFixedWidth(90)
        self.combo_req_proc.setStyleSheet(f"background-color: {BG_INPUT}; border: 1px solid {BORDER_LIGHT}; color: #ffffff; padding: 4px;")

        lbl_req_v = QLabel("Requested Resources (Vector):")
        lbl_req_v.setStyleSheet("font-weight: 600; color: #ffffff; font-size: 12px; margin-left: 12px;")
        self.txt_request_vec = QLineEdit("1, 0, 2")
        self.txt_request_vec.setFixedWidth(140)
        self.txt_request_vec.setStyleSheet(f"background-color: {BG_INPUT}; border: 1px solid {BORDER_LIGHT}; color: {ACCENT_EMERALD}; font-weight: 700; padding: 4px 8px;")

        req_layout.addWidget(lbl_req_p)
        req_layout.addWidget(self.combo_req_proc)
        req_layout.addWidget(lbl_req_v)
        req_layout.addWidget(self.txt_request_vec)
        req_layout.addStretch()

        self.request_panel.hide()
        layout.addWidget(self.request_panel)

        # Matrix Editors Section (Tabbed view for Allocation, Max Claim / Request, and Live Calculated Need)
        self.matrix_tabs = QTabWidget()
        self.matrix_tabs.setObjectName("MatrixTabs")
        self.matrix_tabs.setStyleSheet(
            f"""
            QTabWidget#MatrixTabs::pane {{
                border: 1px solid {BORDER};
                border-radius: 6px;
                background-color: {BG_SURFACE};
            }}
            QTabBar::tab {{
                background-color: {BG_SURFACE};
                color: {TEXT_SECONDARY};
                padding: 6px 16px;
                font-weight: 600;
                font-size: 12px;
                border: 1px solid {BORDER};
                border-bottom: none;
                margin-right: 2px;
            }}
            QTabBar::tab:selected {{
                background-color: {BG_ELEVATED};
                color: {ACCENT};
                border-top: 2px solid {ACCENT};
            }}
            """
        )

        self.table_alloc = self._create_matrix_table("Allocation")
        self.table_max = self._create_matrix_table("Maximum Claim")
        self.table_need = self._create_matrix_table("Need (Max - Alloc)", read_only=True)

        self.matrix_tabs.addTab(self.table_alloc, "Allocation Matrix")
        self.matrix_tabs.addTab(self.table_max, "Max Claim Matrix")
        self.matrix_tabs.addTab(self.table_need, "Calculated Need Matrix")

        layout.addWidget(self.matrix_tabs)

        # Actions & Error Feedback Row
        action_row = QHBoxLayout()
        self.btn_run = QPushButton("Run Analysis")
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

        self.btn_reset = QPushButton("Reset Defaults")
        self.btn_reset.setFixedWidth(120)
        self.btn_reset.setFixedHeight(36)
        self.btn_reset.setStyleSheet(f"background-color: {BG_ELEVATED}; color: {TEXT_PRIMARY}; border: 1px solid {BORDER}; border-radius: 6px; font-weight: 600;")
        self.btn_reset.clicked.connect(lambda: self._load_preset("textbook_safe"))

        self.lbl_validation_err = QLabel()
        self.lbl_validation_err.setStyleSheet(f"color: {ACCENT_ROSE}; font-weight: 600; font-size: 11px;")
        self.lbl_validation_err.hide()

        action_row.addWidget(self.btn_run)
        action_row.addWidget(self.btn_reset)
        action_row.addSpacing(16)
        action_row.addWidget(self.lbl_validation_err, stretch=1)

        layout.addLayout(action_row)
        return card

    def _create_matrix_table(self, title: str, read_only: bool = False) -> QTableWidget:
        table = QTableWidget()
        table.setMinimumHeight(180)
        table.setShowGrid(True)
        table.setStyleSheet(
            f"""
            QTableWidget {{
                background-color: {BG_CANVAS};
                color: {TEXT_PRIMARY};
                gridline-color: {BORDER};
                border: 1px solid {BORDER};
                border-radius: 6px;
                font-family: "{FONT_FAMILY}", -apple-system, sans-serif;
                font-size: 12px;
            }}
            QHeaderView {{
                background-color: {BG_SURFACE};
                border: none;
            }}
            QHeaderView::section {{
                background-color: {BG_ELEVATED};
                color: {TEXT_PRIMARY};
                font-weight: 700;
                font-size: 11px;
                border: 1px solid {BORDER};
                padding: 4px 6px;
            }}
            QTableCornerButton::section {{
                background-color: {BG_SURFACE};
                border: 1px solid {BORDER};
            }}
            """
        )
        h_header = table.horizontalHeader()
        h_header.setFixedHeight(32)
        h_header.setDefaultAlignment(Qt.AlignCenter)
        h_header.setSectionResizeMode(QHeaderView.Stretch)
        h_header.setMinimumSectionSize(55)

        v_header = table.verticalHeader()
        v_header.setVisible(True)
        v_header.setFixedWidth(54)
        v_header.setDefaultSectionSize(30)
        v_header.setDefaultAlignment(Qt.AlignCenter)

        if read_only:
            table.setEditTriggers(QTableWidget.NoEditTriggers)
        else:
            table.cellChanged.connect(self._on_table_cell_changed)
        return table

    def _build_stats_row(self) -> QHBoxLayout:
        layout = QHBoxLayout()
        layout.setSpacing(14)

        self.card_state = StatCard("Analysis Outcome", "Ready", "info")
        self.card_sequence = StatCard("Safe Sequence", "None", "neutral")
        self.card_processes = StatCard("Processes Analyzed", "5", "neutral")
        self.card_available = StatCard("Available Pool", "[3, 3, 2]", "neutral")

        for card in (self.card_state, self.card_sequence, self.card_processes, self.card_available):
            card.setMinimumWidth(120)
            card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        layout.addWidget(self.card_state)
        layout.addWidget(self.card_sequence)
        layout.addWidget(self.card_processes)
        layout.addWidget(self.card_available)
        return layout

    def _build_results_tabs(self) -> QTabWidget:
        tabs = QTabWidget()
        tabs.setObjectName("ResultsTabs")
        tabs.setMinimumHeight(240)
        tabs.setStyleSheet(
            f"""
            QTabWidget#ResultsTabs::pane {{
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

        # Tab 1: Resource Matrices Summary Table
        self.table_summary = QTableWidget()
        self.table_summary.setColumnCount(4)
        self.table_summary.setHorizontalHeaderLabels(["Process", "Allocation", "Max Claim / Request", "Calculated Need"])
        self.table_summary.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_summary.verticalHeader().setVisible(False)
        self.table_summary.setStyleSheet(
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
        tabs.addTab(self.table_summary, "Matrices Breakdown")

        # Tab 2: Detailed Analysis Diagnostics Log
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
        self.txt_diagnostics.setPlaceholderText("Analysis diagnostic log will appear here after execution...")
        tabs.addTab(self.txt_diagnostics, "Diagnostic Report")

        # Tab 3: Raw C++ CLI Output
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

    def _on_mode_changed(self) -> None:
        mode = self.combo_mode.currentData()
        self._update_mode_explanation()
        if mode == DeadlockMode.RESOURCE_REQUEST:
            self.request_panel.show()
            self.matrix_tabs.setTabText(1, "Max Claim Matrix")
            self.matrix_tabs.setTabVisible(2, True)
        elif mode == DeadlockMode.DETECTION:
            self.request_panel.hide()
            self.matrix_tabs.setTabText(1, "Request Matrix (Pending)")
            self.matrix_tabs.setTabVisible(2, False)  # Need is not used in detection
        else:
            self.request_panel.hide()
            self.matrix_tabs.setTabText(1, "Max Claim Matrix")
            self.matrix_tabs.setTabVisible(2, True)

        self._refresh_need_matrix()

    def _update_mode_explanation(self) -> None:
        mode = self.combo_mode.currentData()
        if mode == DeadlockMode.SAFETY:
            self.lbl_explanation.setText(
                "<b>Banker's Safety Algorithm:</b> Proactively analyzes declared maximum claims before granting resources. "
                "Evaluates Work and Finish vectors to determine whether at least one safe execution sequence exists that guarantees "
                "all processes can finish under maximum claims without deadlock."
            )
        elif mode == DeadlockMode.RESOURCE_REQUEST:
            self.lbl_explanation.setText(
                "<b>Simulate Resource Request:</b> Simulates an immediate resource acquisition request by a process. "
                "Tentatively updates Allocation and Available, then runs the Banker's safety check. "
                "If the resulting state is safe, the request is <b>GRANTED</b>; otherwise it is <b>DENIED</b> and original state preserved uncorrupted."
            )
        elif mode == DeadlockMode.DETECTION:
            self.lbl_explanation.setText(
                "<b>Deadlock Detection Algorithm:</b> Evaluates active allocations and outstanding unfulfilled requests. "
                "Finds processes that can complete with currently Available resources and held Allocations. "
                "Processes that cannot finish are identified as <b>DEADLOCKED</b>."
            )

    def _on_dimensions_changed(self) -> None:
        num_p = self.spin_processes.value()
        num_r = self.spin_resources.value()

        # Update process dropdown in request panel
        self.combo_req_proc.clear()
        for i in range(num_p):
            self.combo_req_proc.addItem(f"P{i}", i)

        self._resize_table(self.table_alloc, num_p, num_r)
        self._resize_table(self.table_max, num_p, num_r)
        self._resize_table(self.table_need, num_p, num_r)

        self._refresh_need_matrix()

    def _resize_table(self, table: QTableWidget, num_p: int, num_r: int) -> None:
        self._is_updating_tables = True
        table.setRowCount(num_p)
        table.setColumnCount(num_r)

        row_headers = [f"P{i}" for i in range(num_p)]
        col_headers = [f"R{j} ({chr(65 + j)})" if j < 26 else f"R{j}" for j in range(num_r)]

        table.setVerticalHeaderLabels(row_headers)
        table.setHorizontalHeaderLabels(col_headers)

        is_need_table = (table == getattr(self, "table_need", None))

        for i in range(num_p):
            for j in range(num_r):
                item = table.item(i, j)
                if not item:
                    item = QTableWidgetItem("0")
                    item.setTextAlignment(Qt.AlignCenter)
                    if is_need_table:
                        item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                    table.setItem(i, j, item)
                elif is_need_table:
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)
        self._is_updating_tables = False

    def _on_table_cell_changed(self, row: int, col: int) -> None:
        if self._is_updating_tables:
            return
        self._refresh_need_matrix()

    def _refresh_need_matrix(self) -> None:
        """Dynamically recalculate Need = Max - Allocation for every cell and update table."""
        num_p = self.spin_processes.value()
        num_r = self.spin_resources.value()
        mode = self.combo_mode.currentData()

        if mode == DeadlockMode.DETECTION:
            return

        self._is_updating_tables = True

        if self.table_need.rowCount() != num_p or self.table_need.columnCount() != num_r:
            self.table_need.setRowCount(num_p)
            self.table_need.setColumnCount(num_r)
            row_headers = [f"P{i}" for i in range(num_p)]
            col_headers = [f"R{j} ({chr(65 + j)})" if j < 26 else f"R{j}" for j in range(num_r)]
            self.table_need.setVerticalHeaderLabels(row_headers)
            self.table_need.setHorizontalHeaderLabels(col_headers)

        has_error = False
        error_msg = ""

        for i in range(num_p):
            for j in range(num_r):
                alloc_item = self.table_alloc.item(i, j)
                max_item = self.table_max.item(i, j)

                try:
                    alloc_val = int(alloc_item.text().strip()) if alloc_item and alloc_item.text().strip() else 0
                except ValueError:
                    alloc_val = 0

                try:
                    max_val = int(max_item.text().strip()) if max_item and max_item.text().strip() else 0
                except ValueError:
                    max_val = 0

                need_val = max_val - alloc_val

                need_item = self.table_need.item(i, j)
                if not need_item:
                    need_item = QTableWidgetItem()
                    need_item.setTextAlignment(Qt.AlignCenter)
                    need_item.setFlags(need_item.flags() & ~Qt.ItemIsEditable)
                    self.table_need.setItem(i, j, need_item)
                else:
                    need_item.setFlags(need_item.flags() & ~Qt.ItemIsEditable)

                need_item.setText(str(need_val))

                if need_val < 0:
                    has_error = True
                    error_msg = f"Allocation P{i}[R{j}] ({alloc_val}) exceeds Max Claim ({max_val})!"
                    need_item.setForeground(QColor(ACCENT_ROSE))
                else:
                    need_item.setForeground(QColor(ACCENT_EMERALD if need_val > 0 else TEXT_MUTED))

        if has_error:
            self.lbl_validation_err.setText(error_msg)
            self.lbl_validation_err.show()
        else:
            self.lbl_validation_err.hide()

        self._is_updating_tables = False

    def _on_preset_selected(self, index: int) -> None:
        preset_key = self.combo_presets.currentData()
        if preset_key:
            self._load_preset(preset_key)

    def _load_preset(self, preset_key: str) -> None:
        self._is_updating_tables = True

        if preset_key in ("textbook_safe", "unsafe_starvation", "request_grant", "request_denial"):
            self.combo_mode.setCurrentIndex(0 if preset_key in ("textbook_safe", "unsafe_starvation") else 1)
            self.spin_processes.setValue(5)
            self.spin_resources.setValue(3)
            self._on_dimensions_changed()

            if preset_key == "unsafe_starvation":
                self.txt_available.setText("0, 0, 0")
            else:
                self.txt_available.setText("3, 3, 2")

            allocations = [
                [0, 1, 0],
                [2, 0, 0],
                [3, 0, 2],
                [2, 1, 1],
                [0, 0, 2],
            ]
            max_claims = [
                [7, 5, 3],
                [3, 2, 2],
                [9, 0, 2],
                [2, 2, 2],
                [4, 3, 3],
            ]

            self._fill_matrix(self.table_alloc, allocations)
            self._fill_matrix(self.table_max, max_claims)

            if preset_key == "request_grant":
                self.combo_req_proc.setCurrentIndex(1)
                self.txt_request_vec.setText("1, 0, 2")
            elif preset_key == "request_denial":
                self.combo_req_proc.setCurrentIndex(4)
                self.txt_request_vec.setText("3, 3, 0")

        elif preset_key in ("detection_deadlock", "detection_safe"):
            self.combo_mode.setCurrentIndex(2)  # Deadlock Detection
            if preset_key == "detection_deadlock":
                self.spin_processes.setValue(5)
                self.spin_resources.setValue(3)
                self._on_dimensions_changed()
                self.txt_available.setText("0, 0, 0")
                allocations = [
                    [0, 1, 0],
                    [2, 0, 0],
                    [3, 0, 3],
                    [2, 1, 1],
                    [0, 0, 2],
                ]
                requests = [
                    [0, 0, 0],
                    [2, 0, 2],
                    [0, 0, 1],
                    [1, 0, 0],
                    [0, 0, 2],
                ]
            else:
                self.spin_processes.setValue(3)
                self.spin_resources.setValue(2)
                self._on_dimensions_changed()
                self.txt_available.setText("1, 1")
                allocations = [
                    [1, 0],
                    [0, 1],
                    [1, 1],
                ]
                requests = [
                    [0, 1],
                    [1, 0],
                    [0, 0],
                ]

            self._fill_matrix(self.table_alloc, allocations)
            self._fill_matrix(self.table_max, requests)

        self._is_updating_tables = False
        self._refresh_need_matrix()

    def _fill_matrix(self, table: QTableWidget, data: List[List[int]]) -> None:
        num_p = len(data)
        num_r = len(data[0]) if num_p > 0 else 0
        table.setRowCount(num_p)
        table.setColumnCount(num_r)

        row_headers = [f"P{i}" for i in range(num_p)]
        col_headers = [f"R{j} ({chr(65 + j)})" if j < 26 else f"R{j}" for j in range(num_r)]
        table.setVerticalHeaderLabels(row_headers)
        table.setHorizontalHeaderLabels(col_headers)

        for i in range(num_p):
            for j in range(num_r):
                item = QTableWidgetItem(str(data[i][j]))
                item.setTextAlignment(Qt.AlignCenter)
                table.setItem(i, j, item)

    def _collect_config(self) -> Tuple[Optional[DeadlockConfig], Optional[str]]:
        mode = self.combo_mode.currentData()
        num_p = self.spin_processes.value()
        num_r = self.spin_resources.value()

        # Parse Available
        avail_str = self.txt_available.text().replace(",", " ").strip()
        try:
            avail_tokens = [int(x) for x in avail_str.split() if x.strip()]
            if len(avail_tokens) != num_r:
                return None, f"Available vector requires {num_r} integers (found {len(avail_tokens)})."
        except ValueError:
            return None, "Available vector must contain non-negative integers."

        # Parse Allocation Matrix
        alloc: List[List[int]] = []
        for i in range(num_p):
            row: List[int] = []
            for j in range(num_r):
                item = self.table_alloc.item(i, j)
                try:
                    val = int(item.text().strip()) if item and item.text().strip() else 0
                    if val < 0:
                        return None, f"Allocation P{i}[R{j}] cannot be negative."
                    row.append(val)
                except ValueError:
                    return None, f"Allocation P{i}[R{j}] must be a valid integer."
            alloc.append(row)

        # Parse Max / Request Matrix
        max_claim: List[List[int]] = []
        request_matrix: List[List[int]] = []

        for i in range(num_p):
            row: List[int] = []
            for j in range(num_r):
                item = self.table_max.item(i, j)
                try:
                    val = int(item.text().strip()) if item and item.text().strip() else 0
                    if val < 0:
                        return None, f"Matrix cell P{i}[R{j}] cannot be negative."
                    row.append(val)
                except ValueError:
                    return None, f"Matrix cell P{i}[R{j}] must be a valid integer."
            if mode == DeadlockMode.DETECTION:
                request_matrix.append(row)
            else:
                max_claim.append(row)

        # Parse Resource Request parameters if active
        req_p = self.combo_req_proc.currentIndex()
        if req_p < 0 or req_p >= num_p:
            req_p = 0
        req_vec: List[int] = []
        if mode == DeadlockMode.RESOURCE_REQUEST:
            req_str = self.txt_request_vec.text().replace(",", " ").strip()
            try:
                req_tokens = [int(x) for x in req_str.split() if x.strip()]
                if len(req_tokens) != num_r:
                    return None, f"Requested vector requires {num_r} integers (found {len(req_tokens)})."
                req_vec = req_tokens
            except ValueError:
                return None, "Requested vector must contain non-negative integers."

        config = DeadlockConfig(
            mode=mode,
            num_processes=num_p,
            num_resources=num_r,
            available=avail_tokens,
            allocation=alloc,
            max_claim=max_claim if mode != DeadlockMode.DETECTION else alloc,
            request_matrix=request_matrix if mode == DeadlockMode.DETECTION else alloc,
            requesting_process_id=req_p,
            request_vector=req_vec,
        )

        val_err = config.validate()
        if val_err:
            return None, val_err

        return config, None

    def _run_simulation(self) -> None:
        self.lbl_validation_err.hide()
        config, err = self._collect_config()
        if err or not config:
            self.lbl_validation_err.setText(err or "Invalid configuration.")
            self.lbl_validation_err.show()
            return

        # Disable button and show running status
        self.btn_run.setEnabled(False)
        self.btn_run.setText("Analyzing...")
        self.card_state.update_values("Running...", "pending")

        self._active_worker = DeadlockWorker(self.runner, config, self)
        self._active_worker.finished_exec.connect(self._on_simulation_success)
        self._active_worker.failed_exec.connect(self._on_simulation_failed)
        self._active_worker.start()

    def _on_simulation_success(self, result: AnyDeadlockResult) -> None:
        self.btn_run.setEnabled(True)
        self.btn_run.setText("Run Analysis")
        self._last_result = result

        # 1. Update StatCards
        if isinstance(result, DeadlockSafetyResultModel):
            outcome_text = "SAFE" if result.is_safe else "UNSAFE"
            outcome_type = "success" if result.is_safe else "danger"
            seq_text = result.safe_sequence_str if result.is_safe else f"Blocked: {result.blocked_str}"
            self.card_state.update_values(outcome_text, outcome_type)
            self.card_sequence.update_values(seq_text, "success" if result.is_safe else "danger")
            self.card_processes.update_values(f"{result.num_processes} Procs", "neutral")
            self.card_available.update_values(f"[{', '.join(str(x) for x in result.available)}]", "info")

        elif isinstance(result, DeadlockRequestResultModel):
            outcome_text = "GRANTED" if result.granted else "DENIED"
            outcome_type = "success" if result.granted else "danger"
            seq_text = result.safe_sequence_str if result.granted else f"Denied: {result.status_code}"
            self.card_state.update_values(outcome_text, outcome_type)
            self.card_sequence.update_values(seq_text, "success" if result.granted else "danger")
            self.card_processes.update_values(f"P{result.process_id} Requested", "info")
            self.card_available.update_values(f"[{', '.join(str(x) for x in result.available)}]", "neutral")

        elif isinstance(result, DeadlockDetectionResultModel):
            outcome_text = "DEADLOCK" if result.is_deadlocked else "NO DEADLOCK"
            outcome_type = "danger" if result.is_deadlocked else "success"
            seq_text = f"Deadlocked: {result.deadlocked_str}" if result.is_deadlocked else "All Procs Resolvable"
            self.card_state.update_values(outcome_text, outcome_type)
            self.card_sequence.update_values(seq_text, "danger" if result.is_deadlocked else "success")
            self.card_processes.update_values(f"{result.num_processes} Procs", "neutral")
            self.card_available.update_values(f"[{', '.join(str(x) for x in result.available)}]", "info")

        # 2. Update Visual Centerpiece Graph & Sequence Flow Bar
        self.graph_widget.set_result(result)

        # 3. Update Detailed Tables & Diagnostic Reports
        self._populate_summary_table(result)
        self._populate_diagnostics(result)
        self.txt_raw.setPlainText(result.raw_output)

        # Notify dashboard
        if self.on_execution_completed:
            algo_name = self.combo_mode.currentText().split("(")[0].strip()
            self.on_execution_completed(
                f"Deadlock - {algo_name}",
                result.num_processes,
                0.0,
                0.0,
                True,
            )

    def _on_simulation_failed(self, error_msg: str) -> None:
        self.btn_run.setEnabled(True)
        self.btn_run.setText("Run Analysis")
        self.card_state.update_values("Failed", "danger")
        self.lbl_validation_err.setText(error_msg)
        self.lbl_validation_err.show()

    def _populate_summary_table(self, result: AnyDeadlockResult) -> None:
        self.table_summary.setRowCount(result.num_processes)
        for i in range(result.num_processes):
            # Process Item
            p_item = QTableWidgetItem(f"Process P{i}")
            p_item.setTextAlignment(Qt.AlignCenter)
            p_item.setForeground(QColor(ACCENT))
            self.table_summary.setItem(i, 0, p_item)

            # Allocation
            if i < len(result.allocation):
                alloc_str = " ".join(str(x) for x in result.allocation[i])
            else:
                alloc_str = "—"
            a_item = QTableWidgetItem(alloc_str)
            a_item.setTextAlignment(Qt.AlignCenter)
            self.table_summary.setItem(i, 1, a_item)

            # Max or Request
            if hasattr(result, "max_claim") and i < len(result.max_claim):
                max_str = " ".join(str(x) for x in result.max_claim[i])
            elif hasattr(result, "request_matrix") and i < len(result.request_matrix):
                max_str = " ".join(str(x) for x in result.request_matrix[i])
            else:
                max_str = "—"
            m_item = QTableWidgetItem(max_str)
            m_item.setTextAlignment(Qt.AlignCenter)
            self.table_summary.setItem(i, 2, m_item)

            # Need
            if hasattr(result, "need") and i < len(result.need):
                need_str = " ".join(str(x) for x in result.need[i])
            else:
                need_str = "—"
            n_item = QTableWidgetItem(need_str)
            n_item.setTextAlignment(Qt.AlignCenter)
            n_item.setForeground(QColor(ACCENT_EMERALD))
            self.table_summary.setItem(i, 3, n_item)

    def _populate_diagnostics(self, result: AnyDeadlockResult) -> None:
        text_lines: List[str] = []
        text_lines.append("=" * 60)
        text_lines.append(f"  OSCOPE DEADLOCK MANAGEMENT DIAGNOSTIC ANALYSIS")
        text_lines.append("=" * 60)
        text_lines.append("")

        if isinstance(result, DeadlockSafetyResultModel):
            text_lines.append(f"• Algorithm Mode:        Banker's Safety Algorithm (Avoidance)")
            text_lines.append(f"• System State:          {'SAFE' if result.is_safe else 'UNSAFE'}")
            text_lines.append(f"• Diagnostic Message:    {result.message}")
            if result.is_safe:
                text_lines.append(f"• Safe Sequence:         {result.safe_sequence_str}")
                text_lines.append("")
                text_lines.append("Educational Explanation:")
                text_lines.append("  The system is in a SAFE state because an execution order was discovered")
                text_lines.append("  in which each process can obtain its maximum declared resources, finish,")
                text_lines.append("  and return all allocated instances back to the Available work pool.")
            else:
                text_lines.append(f"• Blocked Processes:     {result.blocked_str}")
                text_lines.append("")
                text_lines.append("Educational Explanation:")
                text_lines.append("  An UNSAFE state does NOT necessarily mean an actual deadlock has occurred.")
                text_lines.append("  Instead, it indicates that the OS cannot guarantee completion if all processes")
                text_lines.append("  simultaneously request their maximum declared claims.")

        elif isinstance(result, DeadlockRequestResultModel):
            text_lines.append(f"• Algorithm Mode:        Banker's Resource Request Simulation")
            text_lines.append(f"• Requesting Process:    P{result.process_id}")
            text_lines.append(f"• Requested Vector:      [{', '.join(str(x) for x in result.requested)}]")
            text_lines.append(f"• Decision:              {'GRANTED' if result.granted else 'DENIED'}")
            text_lines.append(f"• Decision Reason:       {result.message}")
            if result.granted:
                text_lines.append(f"• Resulting Safe Seq:    {result.safe_sequence_str}")
            else:
                text_lines.append("  Rollback Action:       Original system state preserved uncorrupted.")

        elif isinstance(result, DeadlockDetectionResultModel):
            text_lines.append(f"• Algorithm Mode:        Deadlock Detection (Recovery / Observation)")
            text_lines.append(f"• Detection Result:      {'DEADLOCK DETECTED' if result.is_deadlocked else 'NO DEADLOCK'}")
            text_lines.append(f"• Diagnostic Message:    {result.message}")
            if result.is_deadlocked:
                text_lines.append(f"• Deadlocked Processes:  {result.deadlocked_str}")
                text_lines.append("")
                text_lines.append("Educational Explanation:")
                text_lines.append("  A circular wait exists among the deadlocked processes. Each process is")
                text_lines.append("  waiting for resources that are currently held by other processes in the cycle.")
            else:
                text_lines.append(f"• Resolvable Processes:  {', '.join(f'P{p}' for p in result.finished_processes)}")
                text_lines.append("  Execution Status:      All processes can acquire pending resources and complete.")

        text_lines.append("")
        text_lines.append("Available Resources at Analysis Time:")
        text_lines.append(f"  Available: [{', '.join(str(x) for x in result.available)}]")

        self.txt_diagnostics.setPlainText("\n".join(text_lines))
