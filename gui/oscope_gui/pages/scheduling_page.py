"""CPU Scheduling interactive simulation and results visualization page.

Redesigned with student-friendly guidance, clear input explanations, visible table headers,
vibrant modern aesthetics, and comprehensive performance metrics.
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

from ..backend.executor import SchedulingWorker
from ..backend.runner import BaseBackendRunner
from ..models.scheduling import (
    AlgorithmConfig,
    AlgorithmType,
    ProcessInput,
    SchedulingComparisonResultModel,
    SchedulingResultModel,
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
    DANGER_TEXT,
    TEXT_MUTED,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
)
from ..widgets.gantt_chart import GanttChartWidget
from ..widgets.stat_card import StatCard


class SchedulingPage(QWidget):
    """Interactive CPU Scheduling simulation page with dynamic configuration and real results."""

    def __init__(
        self,
        runner: BaseBackendRunner,
        on_execution_completed: Optional[Callable[[str, int, float, float, bool], None]] = None,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.runner = runner
        self.on_execution_completed = on_execution_completed
        self._active_worker: Optional[SchedulingWorker] = None

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Scroll area for clean responsive layout
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

        # 2. Algorithm Selection & Parameter Card
        algo_card = self._build_algorithm_config_card()
        self.content_layout.addWidget(algo_card)

        # 3. Beginner Guidance Card ("Understanding the Inputs")
        guidance_card = self._build_guidance_card()
        self.content_layout.addWidget(guidance_card)

        # 4. Process Workload Input Table Card
        proc_card = self._build_process_table_card()
        self.content_layout.addWidget(proc_card)

        # 5. Simulation Action Bar (Run / Reset / Status Feedback)
        action_bar = self._build_action_bar()
        self.content_layout.addLayout(action_bar)

        # 6. Inline Validation / Execution Status Banner
        self.status_banner = QLabel()
        self.status_banner.setWordWrap(True)
        self.status_banner.setStyleSheet(
            f"background-color: rgba(14, 165, 233, 0.12); color: {ACCENT_HOVER}; border: 1px solid rgba(14, 165, 233, 0.3); border-radius: 6px; padding: 10px 14px; font-size: 12px; font-weight: 500;"
        )
        self.status_banner.setText("Ready to simulate. Select an algorithm, enter process workload, and click 'Run Simulation'.")
        self.content_layout.addWidget(self.status_banner)

        # 7. Results Section (Metrics, Gantt Chart, Per-Process Table, Comparison)
        results_section = self._build_results_section()
        self.content_layout.addWidget(results_section)

        scroll.setWidget(content)
        main_layout.addWidget(scroll)

        # Initial workload preset
        self.load_preset("Standard 3-Process")

    def _build_header(self) -> QVBoxLayout:
        layout = QVBoxLayout()
        layout.setSpacing(3)

        title = QLabel("CPU Scheduling Simulation")
        title.setStyleSheet("font-size: 22px; font-weight: 800; color: #ffffff; letter-spacing: -0.3px;")

        subtitle = QLabel(
            "Configure workload processes, choose a scheduling algorithm, and observe how the operating system allocates CPU time."
        )
        subtitle.setStyleSheet(f"font-size: 13px; color: {TEXT_SECONDARY};")

        layout.addWidget(title)
        layout.addWidget(subtitle)
        return layout

    def _build_algorithm_config_card(self) -> QFrame:
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
        layout.setSpacing(12)

        # Top row: Algorithm selector & dynamic plain-language explanation
        top_row = QHBoxLayout()
        top_row.setSpacing(14)

        lbl_algo = QLabel("Algorithm:")
        lbl_algo.setStyleSheet("font-weight: 600; font-size: 13px; color: #ffffff;")

        self.algo_combo = QComboBox()
        self.algo_combo.setMinimumWidth(270)
        self.algo_combo.setFixedHeight(34)

        algorithms_display = [
            (AlgorithmType.FCFS, "First-Come, First-Served (FCFS)"),
            (AlgorithmType.SJF, "Shortest Job First (SJF)"),
            (AlgorithmType.SRTF, "Shortest Remaining Time First (SRTF)"),
            (AlgorithmType.PRIORITY, "Priority Scheduling"),
            (AlgorithmType.ROUND_ROBIN, "Round Robin (RR)"),
            (AlgorithmType.MLFQ, "Multilevel Feedback Queue (MLFQ)"),
            (AlgorithmType.COMPARE_ALL, "Compare Algorithms"),
        ]
        for algo_type, display_name in algorithms_display:
            self.algo_combo.addItem(display_name, algo_type)

        self.algo_combo.currentIndexChanged.connect(self._on_algorithm_changed)

        top_row.addWidget(lbl_algo)
        top_row.addWidget(self.algo_combo)

        # Informative policy badge / explanation banner
        self.algo_info_label = QLabel()
        self.algo_info_label.setWordWrap(True)
        self.algo_info_label.setStyleSheet(
            f"background-color: {BG_ELEVATED}; color: {TEXT_PRIMARY}; font-size: 12px; padding: 6px 12px; border-radius: 6px; border-left: 3px solid {ACCENT_HOVER};"
        )
        top_row.addWidget(self.algo_info_label, stretch=1)

        layout.addLayout(top_row)

        # Parameter row: Time Quantum (RR) and MLFQ Quanta
        self.param_row = QHBoxLayout()
        self.param_row.setSpacing(20)

        # RR Quantum input
        self.rr_container = QWidget()
        rr_layout = QHBoxLayout(self.rr_container)
        rr_layout.setContentsMargins(0, 0, 0, 0)
        rr_layout.setSpacing(8)

        lbl_rr = QLabel("Time Quantum:")
        lbl_rr.setStyleSheet("font-weight: 600; color: #ffffff;")
        self.spin_rr = QSpinBox()
        self.spin_rr.setRange(1, 100)
        self.spin_rr.setValue(2)
        self.spin_rr.setFixedWidth(70)
        self.spin_rr.setFixedHeight(28)

        lbl_rr_hint = QLabel("(CPU time slice duration before preemption)")
        lbl_rr_hint.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 11px;")

        rr_layout.addWidget(lbl_rr)
        rr_layout.addWidget(self.spin_rr)
        rr_layout.addWidget(lbl_rr_hint)
        self.param_row.addWidget(self.rr_container)

        # MLFQ Quanta inputs
        self.mlfq_container = QWidget()
        mlfq_layout = QHBoxLayout(self.mlfq_container)
        mlfq_layout.setContentsMargins(0, 0, 0, 0)
        mlfq_layout.setSpacing(8)

        lbl_mlfq = QLabel("MLFQ Time Slices:")
        lbl_mlfq.setStyleSheet("font-weight: 600; color: #ffffff;")

        self.spin_q0 = QSpinBox()
        self.spin_q0.setRange(1, 100)
        self.spin_q0.setValue(2)
        self.spin_q0.setFixedWidth(55)
        self.spin_q0.setFixedHeight(28)

        self.spin_q1 = QSpinBox()
        self.spin_q1.setRange(1, 100)
        self.spin_q1.setValue(4)
        self.spin_q1.setFixedWidth(55)
        self.spin_q1.setFixedHeight(28)

        self.spin_q2 = QSpinBox()
        self.spin_q2.setRange(1, 100)
        self.spin_q2.setValue(8)
        self.spin_q2.setFixedWidth(55)
        self.spin_q2.setFixedHeight(28)

        lbl_mlfq_hint = QLabel("(Q0 highest priority, Q1 medium, Q2 lowest)")
        lbl_mlfq_hint.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 11px;")

        mlfq_layout.addWidget(lbl_mlfq)
        mlfq_layout.addWidget(QLabel("Q0:"))
        mlfq_layout.addWidget(self.spin_q0)
        mlfq_layout.addWidget(QLabel("Q1:"))
        mlfq_layout.addWidget(self.spin_q1)
        mlfq_layout.addWidget(QLabel("Q2:"))
        mlfq_layout.addWidget(self.spin_q2)
        mlfq_layout.addWidget(lbl_mlfq_hint)
        self.param_row.addWidget(self.mlfq_container)

        self.param_row.addStretch()
        layout.addLayout(self.param_row)

        self._update_parameter_visibility()
        return card

    def _build_guidance_card(self) -> QFrame:
        """Beginner guidance section explaining what each process field means with an illustrative example."""
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

        # Title & Toggle
        header_row = QHBoxLayout()
        title = QLabel("Understanding the Inputs")
        title.setStyleSheet("font-weight: 700; font-size: 13px; color: #ffffff;")
        hint = QLabel("Define the processes that will compete for CPU time. Each row represents one process.")
        hint.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 12px;")

        header_row.addWidget(title)
        header_row.addWidget(hint, stretch=1)
        layout.addLayout(header_row)

        # Definitions row with vibrant distinct color indicators
        defs_layout = QHBoxLayout()
        defs_layout.setSpacing(14)

        def_items = [
            ("Process ID (PID)", "Unique integer identifying each process.", ACCENT_CYAN, "rgba(6, 182, 212, 0.12)"),
            ("Arrival Time", "Time when process enters ready queue (>= 0).", ACCENT_EMERALD, "rgba(16, 185, 129, 0.12)"),
            ("CPU Burst Time", "Total execution time required (> 0).", ACCENT_AMBER, "rgba(245, 158, 11, 0.12)"),
            ("Priority", "Lower numeric value = Higher scheduling priority.", ACCENT_VIOLET, "rgba(139, 92, 246, 0.12)"),
        ]

        for term, explanation, color_val, bg_val in def_items:
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
            dot.setStyleSheet(f"background-color: {color_val}; border-radius: 3px;")
            lbl_term = QLabel(term)
            lbl_term.setStyleSheet(f"color: {color_val}; font-size: 11px; font-weight: 700;")
            tag_row.addWidget(dot)
            tag_row.addWidget(lbl_term)
            tag_row.addStretch()

            lbl_exp = QLabel(explanation)
            lbl_exp.setWordWrap(True)
            lbl_exp.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 11px; line-height: 1.3;")

            box.addLayout(tag_row)
            box.addWidget(lbl_exp)
            defs_layout.addWidget(box_frame, stretch=1)

        layout.addLayout(defs_layout)

        # Illustrative Example banner
        example_box = QFrame()
        example_box.setStyleSheet(
            f"background-color: #0e1422; border: 1px solid {BORDER}; border-radius: 6px; padding: 8px 12px;"
        )
        ex_layout = QHBoxLayout(example_box)
        ex_layout.setContentsMargins(8, 4, 8, 4)
        ex_layout.setSpacing(12)

        lbl_ex_title = QLabel("Example Workload:")
        lbl_ex_title.setStyleSheet(f"font-weight: 700; font-size: 11px; color: {ACCENT_HOVER};")

        lbl_ex_content = QLabel(
            "P1 (Arrival: 0, Burst: 5) is ready at time 0 and needs 5 CPU units | "
            "P2 (Arrival: 1, Burst: 3) arrives at time 1 and needs 3 CPU units."
        )
        lbl_ex_content.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 11px;")

        ex_layout.addWidget(lbl_ex_title)
        ex_layout.addWidget(lbl_ex_content, stretch=1)
        layout.addWidget(example_box)

        return card

    def _build_process_table_card(self) -> QFrame:
        card = QFrame()
        card.setObjectName("ProcessCard")
        card.setProperty("card", True)
        card.setStyleSheet(
            f"""
            QFrame#ProcessCard {{
                background-color: {BG_SURFACE};
                border: 1px solid {BORDER};
                border-radius: 8px;
            }}
            """
        )
        layout = QVBoxLayout(card)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(10)

        # Toolbar
        toolbar = QHBoxLayout()
        title = QLabel("Process Workload Configuration")
        title.setStyleSheet("font-weight: 700; font-size: 13px; color: #ffffff;")
        toolbar.addWidget(title)
        toolbar.addStretch()

        btn_add = QPushButton("+ Add Process")
        btn_add.setFixedHeight(30)
        btn_add.setStyleSheet(
            f"background-color: rgba(16, 185, 129, 0.12); color: {ACCENT_EMERALD}; border: 1px solid rgba(16, 185, 129, 0.3); padding: 4px 12px; font-size: 12px; font-weight: 600; border-radius: 5px;"
        )
        btn_add.clicked.connect(self.add_process_row)
        toolbar.addWidget(btn_add)

        btn_remove = QPushButton("- Remove Selected")
        btn_remove.setFixedHeight(30)
        btn_remove.setStyleSheet(
            f"background-color: rgba(244, 63, 94, 0.12); color: {ACCENT_ROSE}; border: 1px solid rgba(244, 63, 94, 0.3); padding: 4px 12px; font-size: 12px; font-weight: 600; border-radius: 5px;"
        )
        btn_remove.clicked.connect(self.remove_selected_row)
        toolbar.addWidget(btn_remove)

        self.preset_combo = QComboBox()
        self.preset_combo.setFixedHeight(30)
        self.preset_combo.addItem("Presets: Standard 3-Process")
        self.preset_combo.addItem("Presets: Convoy Effect (FCFS)")
        self.preset_combo.addItem("Presets: Preemptive SJF / SRTF Split")
        self.preset_combo.addItem("Presets: Priority Differentiation")
        self.preset_combo.currentIndexChanged.connect(self._on_preset_selected)
        toolbar.addWidget(self.preset_combo)

        btn_clear = QPushButton("Clear All")
        btn_clear.setFixedHeight(30)
        btn_clear.setStyleSheet(
            f"background-color: {BG_ELEVATED}; color: {TEXT_SECONDARY}; padding: 4px 12px; font-size: 12px; border-radius: 5px;"
        )
        btn_clear.clicked.connect(self.clear_all_rows)
        toolbar.addWidget(btn_clear)

        layout.addLayout(toolbar)

        # Process Input Table
        self.proc_table = QTableWidget(0, 4)
        self.proc_table.setHorizontalHeaderLabels([
            "Process ID (PID)",
            "Arrival Time (>= 0)",
            "CPU Burst Time (> 0)",
            "Priority (Lower = Higher)",
        ])

        h_header = self.proc_table.horizontalHeader()
        h_header.setSectionResizeMode(0, QHeaderView.Fixed)
        self.proc_table.setColumnWidth(0, 140)
        h_header.setSectionResizeMode(1, QHeaderView.Fixed)
        self.proc_table.setColumnWidth(1, 170)
        h_header.setSectionResizeMode(2, QHeaderView.Fixed)
        self.proc_table.setColumnWidth(2, 170)
        h_header.setSectionResizeMode(3, QHeaderView.Stretch)

        h_header.setFixedHeight(34)
        h_header.setDefaultAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        v_header = self.proc_table.verticalHeader()
        v_header.setVisible(False)
        v_header.setDefaultSectionSize(36)

        self.proc_table.setMinimumHeight(150)
        self.proc_table.setMaximumHeight(220)
        self.proc_table.setStyleSheet(
            f"""
            QTableWidget {{
                background-color: {BG_INPUT};
                border: 1px solid {BORDER};
                border-radius: 6px;
            }}
            """
        )
        layout.addWidget(self.proc_table)

        return card

    def _build_action_bar(self) -> QHBoxLayout:
        bar = QHBoxLayout()
        bar.setSpacing(12)

        self.btn_run = QPushButton("Run Simulation")
        self.btn_run.setProperty("class", "btn-primary")
        self.btn_run.setFixedHeight(40)
        self.btn_run.setFixedWidth(180)
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
        title = QLabel("Simulation Results & Analysis")
        title.setStyleSheet("font-size: 17px; font-weight: 800; color: #ffffff;")
        res_header.addWidget(title)
        res_header.addStretch()
        layout.addLayout(res_header)

        # Metric summary cards row with vibrant accent highlights and educational tooltips
        self.metrics_cards_layout = QHBoxLayout()
        self.metrics_cards_layout.setSpacing(12)

        self.card_avg_wait = StatCard(
            "Average Waiting Time",
            "--",
            "time units",
            tooltip="Total time processes spent waiting in the ready queue before completing execution.",
            accent_color=ACCENT_HOVER,
        )
        self.card_avg_tat = StatCard(
            "Average Turnaround Time",
            "--",
            "time units",
            tooltip="Total elapsed time from process arrival to final completion (Turnaround = Completion - Arrival).",
            accent_color=ACCENT_VIOLET,
        )
        self.card_avg_resp = StatCard(
            "Average Response Time",
            "--",
            "time units",
            tooltip="Time elapsed from arrival until the process first receives CPU execution time.",
            accent_color=ACCENT_EMERALD,
        )
        self.card_duration = StatCard(
            "Total Simulation Interval",
            "--",
            "time units",
            tooltip="Total time span required to execute the complete workload from start to finish.",
            accent_color=ACCENT_AMBER,
        )

        self.metrics_cards_layout.addWidget(self.card_avg_wait)
        self.metrics_cards_layout.addWidget(self.card_avg_tat)
        self.metrics_cards_layout.addWidget(self.card_avg_resp)
        self.metrics_cards_layout.addWidget(self.card_duration)
        layout.addLayout(self.metrics_cards_layout)

        # Gantt Chart Card
        self.gantt_box = QFrame()
        self.gantt_box.setObjectName("GanttCard")
        self.gantt_box.setProperty("card", True)
        self.gantt_box.setStyleSheet(
            f"""
            QFrame#GanttCard {{
                background-color: {BG_SURFACE};
                border: 1px solid {BORDER};
                border-radius: 8px;
            }}
            """
        )
        gantt_layout = QVBoxLayout(self.gantt_box)
        gantt_layout.setContentsMargins(18, 14, 18, 16)
        gantt_layout.setSpacing(10)

        g_header = QHBoxLayout()
        g_title = QLabel("CPU Execution Timeline (Gantt Chart)")
        g_title.setStyleSheet("font-weight: 700; font-size: 13px; color: #ffffff;")
        g_hint = QLabel("A timeline showing which process holds the CPU during each interval.")
        g_hint.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 11px;")

        g_header.addWidget(g_title)
        g_header.addWidget(g_hint)
        g_header.addStretch()

        self.gantt_chart = GanttChartWidget()

        # Educational caption
        lbl_gantt_caption = QLabel(
            "Gantt Chart: Visual timeline of CPU allocation over time. Hover over segments to inspect execution slices and idle intervals."
        )
        lbl_gantt_caption.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 11px; padding-top: 2px;")

        gantt_layout.addLayout(g_header)
        gantt_layout.addWidget(self.gantt_chart)
        gantt_layout.addWidget(lbl_gantt_caption)
        layout.addWidget(self.gantt_box)

        # Tabbed Results: Per-Process Metrics Table, Comparison Table, Raw Terminal Output
        self.tabs = QTabWidget()

        # Tab 1: Per-process metrics table
        self.tab_metrics = QWidget()
        t1_layout = QVBoxLayout(self.tab_metrics)
        t1_layout.setContentsMargins(10, 10, 10, 10)
        t1_layout.setSpacing(8)

        self.res_table = QTableWidget(0, 7)
        self.res_table.setHorizontalHeaderLabels([
            "Process ID (PID)",
            "Arrival Time",
            "CPU Burst Time",
            "Completion Time",
            "Turnaround Time",
            "Waiting Time",
            "Response Time",
        ])
        self.res_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.res_table.horizontalHeader().setFixedHeight(34)
        self.res_table.verticalHeader().setVisible(False)
        self.res_table.verticalHeader().setDefaultSectionSize(34)
        self.res_table.setEditTriggers(QTableWidget.NoEditTriggers)
        t1_layout.addWidget(self.res_table)

        lbl_formula = QLabel(
            "Metric Formulas: Turnaround Time = Completion − Arrival | Waiting Time = Turnaround − Burst | Response Time = First Run − Arrival"
        )
        lbl_formula.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 11px; padding: 2px 4px;")
        t1_layout.addWidget(lbl_formula)

        self.tabs.addTab(self.tab_metrics, "Per-Process Metrics")

        # Tab 2: Comparison table (for Compare Algorithms)
        self.tab_comparison = QWidget()
        t2_layout = QVBoxLayout(self.tab_comparison)
        t2_layout.setContentsMargins(10, 10, 10, 10)
        t2_layout.setSpacing(8)

        self.comp_table = QTableWidget(0, 4)
        self.comp_table.setHorizontalHeaderLabels([
            "Algorithm",
            "Avg Waiting Time",
            "Avg Turnaround Time",
            "Avg Response Time",
        ])
        self.comp_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.comp_table.horizontalHeader().setFixedHeight(34)
        self.comp_table.verticalHeader().setVisible(False)
        self.comp_table.verticalHeader().setDefaultSectionSize(34)
        self.comp_table.setEditTriggers(QTableWidget.NoEditTriggers)
        t2_layout.addWidget(self.comp_table)

        lbl_comp_hint = QLabel("Benchmark comparison evaluating all scheduling algorithms side-by-side using the identical workload.")
        lbl_comp_hint.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 11px; padding: 2px 4px;")
        t2_layout.addWidget(lbl_comp_hint)

        self.tabs.addTab(self.tab_comparison, "Multi-Algorithm Comparison")

        # Tab 3: Raw Output
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
        self._update_parameter_visibility()
        self._update_table_priority_column()

    def _update_parameter_visibility(self) -> None:
        algo_data = self.algo_combo.currentData()
        if not algo_data:
            return
        algo = AlgorithmType(algo_data) if isinstance(algo_data, str) else algo_data

        self.rr_container.setVisible(algo.requires_quantum)
        self.mlfq_container.setVisible(algo.requires_mlfq_quanta)

        if algo == AlgorithmType.FCFS:
            desc = "First-Come, First-Served: Non-preemptive. Processes execute in the exact order of their arrival."
        elif algo == AlgorithmType.SJF:
            desc = "Shortest Job First: Non-preemptive. Selects the ready process with the shortest CPU burst time."
        elif algo == AlgorithmType.SRTF:
            desc = "Shortest Remaining Time First: Preemptive SJF. Selects the process with the least remaining CPU burst."
        elif algo == AlgorithmType.PRIORITY:
            desc = "Priority Scheduling: Non-preemptive. Selects process with highest priority (lower numeric value = higher priority)."
        elif algo == AlgorithmType.ROUND_ROBIN:
            desc = "Round Robin: Preemptive. Gives each ready process a fixed time slice (quantum) in circular order."
        elif algo == AlgorithmType.MLFQ:
            desc = "Multilevel Feedback Queue: Preemptive. 3 priority queues (Q0, Q1, Q2) with demotion on quantum expiration."
        else:
            desc = "Compare Algorithms: Evaluates all scheduling algorithms side-by-side using the identical process workload."

        self.algo_info_label.setText(desc)

    def _update_table_priority_column(self) -> None:
        """Update header and styling of priority column based on whether selected algorithm uses it."""
        algo_data = self.algo_combo.currentData()
        if not algo_data:
            return
        algo = AlgorithmType(algo_data) if isinstance(algo_data, str) else algo_data

        header_item = self.proc_table.horizontalHeaderItem(3)
        if not header_item:
            return

        if algo.requires_priority:
            header_item.setText("Priority (Lower = Higher)")
            for r in range(self.proc_table.rowCount()):
                item = self.proc_table.item(r, 3)
                if item:
                    item.setFlags(item.flags() | Qt.ItemIsEditable)
                    if item.text().endswith("(Ignored)"):
                        clean_val = item.text().replace("(Ignored)", "").strip()
                        item.setText(clean_val or "0")
                    item.setForeground(Qt.white)
        else:
            header_item.setText("Priority (Ignored)")
            for r in range(self.proc_table.rowCount()):
                item = self.proc_table.item(r, 3)
                if item:
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                    val = item.text().replace("(Ignored)", "").strip() or "0"
                    item.setText(f"{val} (Ignored)")
                    item.setForeground(QColor(TEXT_MUTED))

    def add_process_row(
        self,
        pid: Optional[int] = None,
        arrival: int = 0,
        burst: int = 4,
        priority: int = 1,
    ) -> None:
        """Add an editable process row with sensible initial bounds."""
        row = self.proc_table.rowCount()
        self.proc_table.insertRow(row)

        if pid is None:
            max_pid = 0
            for r in range(row):
                item = self.proc_table.item(r, 0)
                if item and item.text().isdigit():
                    max_pid = max(max_pid, int(item.text()))
            pid = max_pid + 1

        item_pid = QTableWidgetItem(str(pid))
        item_pid.setTextAlignment(Qt.AlignCenter)

        item_arr = QTableWidgetItem(str(arrival))
        item_arr.setTextAlignment(Qt.AlignCenter)

        item_burst = QTableWidgetItem(str(burst))
        item_burst.setTextAlignment(Qt.AlignCenter)

        item_prio = QTableWidgetItem(str(priority))
        item_prio.setTextAlignment(Qt.AlignCenter)

        self.proc_table.setItem(row, 0, item_pid)
        self.proc_table.setItem(row, 1, item_arr)
        self.proc_table.setItem(row, 2, item_burst)
        self.proc_table.setItem(row, 3, item_prio)

        self._update_table_priority_column()

    def remove_selected_row(self) -> None:
        selected_rows = sorted(
            list({idx.row() for idx in self.proc_table.selectedIndexes()}),
            reverse=True,
        )
        if not selected_rows and self.proc_table.rowCount() > 0:
            selected_rows = [self.proc_table.rowCount() - 1]

        for r in selected_rows:
            self.proc_table.removeRow(r)

    def clear_all_rows(self) -> None:
        self.proc_table.setRowCount(0)

    def _on_preset_selected(self, index: int) -> None:
        text = self.preset_combo.currentText()
        if "Standard 3-Process" in text:
            self.load_preset("Standard 3-Process")
        elif "Convoy Effect" in text:
            self.load_preset("Convoy Effect")
        elif "Preemptive" in text:
            self.load_preset("Preemptive SJF / SRTF Split")
        elif "Priority" in text:
            self.load_preset("Priority Differentiation")

    def load_preset(self, name: str) -> None:
        self.clear_all_rows()
        if name == "Standard 3-Process":
            self.add_process_row(pid=1, arrival=0, burst=5, priority=2)
            self.add_process_row(pid=2, arrival=1, burst=3, priority=1)
            self.add_process_row(pid=3, arrival=2, burst=8, priority=3)
        elif name == "Convoy Effect":
            self.add_process_row(pid=1, arrival=0, burst=24, priority=0)
            self.add_process_row(pid=2, arrival=0, burst=3, priority=0)
            self.add_process_row(pid=3, arrival=0, burst=3, priority=0)
        elif name == "Preemptive SJF / SRTF Split":
            self.add_process_row(pid=1, arrival=0, burst=8, priority=0)
            self.add_process_row(pid=2, arrival=1, burst=4, priority=0)
            self.add_process_row(pid=3, arrival=2, burst=9, priority=0)
            self.add_process_row(pid=4, arrival=3, burst=5, priority=0)
        elif name == "Priority Differentiation":
            self.add_process_row(pid=1, arrival=0, burst=4, priority=3)
            self.add_process_row(pid=2, arrival=1, burst=5, priority=1)
            self.add_process_row(pid=3, arrival=2, burst=2, priority=4)
            self.add_process_row(pid=4, arrival=3, burst=3, priority=2)

    def collect_inputs(self) -> tuple[Optional[AlgorithmConfig], Optional[List[ProcessInput]], Optional[str]]:
        """Validate and collect user inputs from table and form with student-friendly error messages."""
        algo_data = self.algo_combo.currentData()
        algo = AlgorithmType(algo_data) if isinstance(algo_data, str) else algo_data
        config = AlgorithmConfig(
            algorithm=algo,
            rr_quantum=self.spin_rr.value(),
            mlfq_q0=self.spin_q0.value(),
            mlfq_q1=self.spin_q1.value(),
            mlfq_q2=self.spin_q2.value(),
        )

        cfg_err = config.validate()
        if cfg_err:
            return None, None, cfg_err

        row_count = self.proc_table.rowCount()
        if row_count == 0:
            return None, None, "No processes entered. Click '+ Add Process' or choose a preset workload."

        processes: List[ProcessInput] = []
        seen_pids = set()

        for r in range(row_count):
            # PID
            item_pid = self.proc_table.item(r, 0)
            if not item_pid or not item_pid.text().strip():
                return None, None, f"Row {r + 1}: Process ID (PID) cannot be empty."
            try:
                pid = int(item_pid.text().strip())
            except ValueError:
                return None, None, f"Row {r + 1}: Process ID (PID) must be an integer, got '{item_pid.text()}'."
            if pid in seen_pids:
                return None, None, f"Duplicate PID {pid} detected on row {r + 1}. Process IDs (PIDs) must be unique."
            seen_pids.add(pid)

            # Arrival Time
            item_arr = self.proc_table.item(r, 1)
            if not item_arr or not item_arr.text().strip():
                return None, None, f"Row {r + 1} (PID {pid}): Arrival time cannot be empty."
            try:
                arrival = int(item_arr.text().strip())
            except ValueError:
                return None, None, f"Row {r + 1} (PID {pid}): Arrival time must be an integer."
            if arrival < 0:
                return None, None, f"Row {r + 1} (PID {pid}): Arrival time must be non-negative (>= 0)."

            # CPU Burst Time
            item_burst = self.proc_table.item(r, 2)
            if not item_burst or not item_burst.text().strip():
                return None, None, f"Row {r + 1} (PID {pid}): CPU Burst time cannot be empty."
            try:
                burst = int(item_burst.text().strip())
            except ValueError:
                return None, None, f"Row {r + 1} (PID {pid}): CPU Burst time must be an integer."
            if burst <= 0:
                return None, None, f"Row {r + 1} (PID {pid}): CPU Burst time must be positive (> 0)."

            # Priority
            item_prio = self.proc_table.item(r, 3)
            prio_text = item_prio.text().replace("(Ignored)", "").strip() if item_prio else "0"
            try:
                priority = int(prio_text)
            except ValueError:
                priority = 0

            processes.append(ProcessInput(pid=pid, arrival_time=arrival, burst_time=burst, priority=priority))

        return config, processes, None

    def run_simulation(self) -> None:
        """Trigger backend execution with inline validation feedback."""
        config, processes, err = self.collect_inputs()
        if err:
            self.status_banner.setStyleSheet(
                f"background-color: {DANGER_BG}; color: {DANGER_TEXT}; border: 1px solid {DANGER}; border-radius: 6px; padding: 10px 14px; font-weight: 500;"
            )
            self.status_banner.setText(f"Input validation error: {err}")
            return

        # Disable Run button during active execution to prevent double submission
        self.btn_run.setEnabled(False)
        self.status_banner.setStyleSheet(
            f"background-color: rgba(14, 165, 233, 0.15); color: {ACCENT_HOVER}; border: 1px solid rgba(14, 165, 233, 0.35); border-radius: 6px; padding: 10px 14px; font-weight: 500;"
        )
        self.status_banner.setText(f"Running {config.algorithm.value} simulation via C++ backend...")

        self._active_worker = SchedulingWorker(self.runner, config, processes)
        self._active_worker.signals.completed.connect(self._on_simulation_success)
        self._active_worker.signals.failed.connect(self._on_simulation_failed)
        self._active_worker.start()

    def _on_simulation_success(self, result: object) -> None:
        self.btn_run.setEnabled(True)
        self.status_banner.setStyleSheet(
            f"background-color: {SUCCESS_BG}; color: {SUCCESS_TEXT}; border: 1px solid {SUCCESS}; border-radius: 6px; padding: 10px 14px; font-weight: 500;"
        )

        algo_data = self.algo_combo.currentData()
        algo = AlgorithmType(algo_data) if isinstance(algo_data, str) else algo_data

        if isinstance(result, SchedulingComparisonResultModel):
            self.status_banner.setText("Comparison simulation completed successfully across all algorithms.")
            self._display_comparison_results(result)
            if self.on_execution_completed:
                self.on_execution_completed("Compare Algorithms", self.proc_table.rowCount(), 0.0, 0.0, True)
        elif isinstance(result, SchedulingResultModel):
            self.status_banner.setText(f"{result.algorithm_name} simulation completed successfully.")
            self._display_single_algorithm_results(result)
            if self.on_execution_completed:
                self.on_execution_completed(
                    result.algorithm_name,
                    result.total_processes,
                    result.averages.average_waiting_time,
                    result.averages.average_turnaround_time,
                    True,
                )

    def _on_simulation_failed(self, error_message: str) -> None:
        self.btn_run.setEnabled(True)
        self.status_banner.setStyleSheet(
            f"background-color: {DANGER_BG}; color: {DANGER_TEXT}; border: 1px solid {DANGER}; border-radius: 6px; padding: 10px 14px; font-weight: 500;"
        )
        self.status_banner.setText(f"Execution failed: {error_message}")
        self.raw_text.setPlainText(error_message)

    def _display_single_algorithm_results(self, result: SchedulingResultModel) -> None:
        # Update Stat Cards with clear formatting
        self.card_avg_wait.set_value(f"{result.averages.average_waiting_time:.2f}", "time units")
        self.card_avg_tat.set_value(f"{result.averages.average_turnaround_time:.2f}", "time units")
        self.card_avg_resp.set_value(f"{result.averages.average_response_time:.2f}", "time units")
        self.card_duration.set_value(f"{result.total_duration}", "time units")

        # Update Gantt Chart timeline
        self.gantt_chart.set_timeline(result.timeline)

        # Update per-process results table
        self.res_table.setRowCount(0)
        for p in result.process_results:
            row = self.res_table.rowCount()
            self.res_table.insertRow(row)

            items = [
                QTableWidgetItem(f"P{p.pid}"),
                QTableWidgetItem(str(p.arrival_time)),
                QTableWidgetItem(str(p.burst_time)),
                QTableWidgetItem(str(p.completion_time)),
                QTableWidgetItem(str(p.turnaround_time)),
                QTableWidgetItem(str(p.waiting_time)),
                QTableWidgetItem(str(p.response_time)),
            ]
            for col, item in enumerate(items):
                item.setTextAlignment(Qt.AlignCenter)
                self.res_table.setItem(row, col, item)

        self.raw_text.setPlainText(result.raw_output)
        self.tabs.setCurrentIndex(0)

    def _display_comparison_results(self, result: SchedulingComparisonResultModel) -> None:
        self.comp_table.setRowCount(0)
        for entry in result.entries:
            row = self.comp_table.rowCount()
            self.comp_table.insertRow(row)

            items = [
                QTableWidgetItem(entry.algorithm),
                QTableWidgetItem(f"{entry.avg_waiting_time:.2f}"),
                QTableWidgetItem(f"{entry.avg_turnaround_time:.2f}"),
                QTableWidgetItem(f"{entry.avg_response_time:.2f}"),
            ]
            for col, item in enumerate(items):
                if col > 0:
                    item.setTextAlignment(Qt.AlignCenter)
                self.comp_table.setItem(row, col, item)

        self.raw_text.setPlainText(result.raw_output)
        self.tabs.setCurrentIndex(1)

    def reset_results(self) -> None:
        """Reset metric cards, clear timeline, and wipe results tables."""
        self.card_avg_wait.set_value("--", "time units")
        self.card_avg_tat.set_value("--", "time units")
        self.card_avg_resp.set_value("--", "time units")
        self.card_duration.set_value("--", "time units")

        self.gantt_chart.clear()
        self.res_table.setRowCount(0)
        self.comp_table.setRowCount(0)
        self.raw_text.clear()

        self.status_banner.setStyleSheet(
            f"background-color: rgba(14, 165, 233, 0.12); color: {ACCENT_HOVER}; border: 1px solid rgba(14, 165, 233, 0.3); border-radius: 6px; padding: 10px 14px; font-weight: 500;"
        )
        self.status_banner.setText("Results reset. Select an algorithm and click 'Run Simulation'.")
