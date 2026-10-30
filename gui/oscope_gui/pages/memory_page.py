"""Memory Allocation interactive simulation and visualization page.

Supports First Fit, Best Fit, Worst Fit, and Multi-Strategy Comparison using real C++ backend execution.
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

from ..backend.executor import MemoryWorker
from ..backend.runner import BaseBackendRunner
from ..models.memory import (
    MemoryComparisonResultModel,
    MemoryConfig,
    MemoryOperationInput,
    MemoryOperationType,
    MemorySimulationResultModel,
    MemoryStrategy,
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
from ..widgets.memory_map import MemoryMapWidget
from ..widgets.stat_card import StatCard


class MemoryAllocationPage(QWidget):
    """Interactive Memory Allocation simulation page with dynamic configuration and real results."""

    def __init__(
        self,
        runner: BaseBackendRunner,
        on_execution_completed: Optional[Callable[[str, int, float, float, bool], None]] = None,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.runner = runner
        self.on_execution_completed = on_execution_completed
        self._active_worker: Optional[MemoryWorker] = None

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Scroll area for responsive scaling
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

        # 2. Strategy Selection & Memory Pool Card
        strategy_card = self._build_strategy_card()
        self.content_layout.addWidget(strategy_card)

        # 3. Beginner Guidance Card ("Understanding Memory Allocation")
        guidance_card = self._build_guidance_card()
        self.content_layout.addWidget(guidance_card)

        # 4. Workload Configuration Card (Operations Table & Controls)
        workload_card = self._build_workload_card()
        self.content_layout.addWidget(workload_card)

        # 5. Action Bar (Run / Reset)
        action_bar = self._build_action_bar()
        self.content_layout.addLayout(action_bar)

        # 6. Status Feedback Banner
        self.status_banner = QLabel()
        self.status_banner.setWordWrap(True)
        self.status_banner.setStyleSheet(
            f"background-color: rgba(14, 165, 233, 0.12); color: {ACCENT_HOVER}; border: 1px solid rgba(14, 165, 233, 0.3); border-radius: 6px; padding: 10px 14px; font-size: 12px; font-weight: 500;"
        )
        self.status_banner.setText("Ready to simulate. Select an allocation strategy, define memory operations, and click 'Run Simulation'.")
        self.content_layout.addWidget(self.status_banner)

        # 7. Results Section (Metrics, Memory Map, Blocks Table, Operations Log, Comparison Table)
        results_section = self._build_results_section()
        self.content_layout.addWidget(results_section)

        scroll.setWidget(content)
        main_layout.addWidget(scroll)

        # Initial preset
        self.load_preset("Standard Partitioning")

    def _build_header(self) -> QVBoxLayout:
        layout = QVBoxLayout()
        layout.setSpacing(3)

        title = QLabel("Memory Allocation Simulator")
        title.setStyleSheet("font-size: 22px; font-weight: 800; color: #ffffff; letter-spacing: -0.3px;")

        subtitle = QLabel("Explore how operating systems assign memory to processes and manage available space.")
        subtitle.setStyleSheet(f"font-size: 13px; color: {TEXT_SECONDARY};")

        layout.addWidget(title)
        layout.addWidget(subtitle)
        return layout

    def _build_strategy_card(self) -> QFrame:
        card = QFrame()
        card.setObjectName("StrategyCard")
        card.setProperty("card", True)
        card.setStyleSheet(
            f"""
            QFrame#StrategyCard {{
                background-color: {BG_SURFACE};
                border: 1px solid {BORDER};
                border-radius: 8px;
            }}
            """
        )
        layout = QVBoxLayout(card)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(12)

        # Strategy selector row
        top_row = QHBoxLayout()
        top_row.setSpacing(14)

        lbl_strat = QLabel("Allocation Strategy:")
        lbl_strat.setStyleSheet("font-weight: 600; font-size: 13px; color: #ffffff;")

        self.strategy_combo = QComboBox()
        self.strategy_combo.setMinimumWidth(240)
        self.strategy_combo.setFixedHeight(34)

        strategies_display = [
            (MemoryStrategy.FIRST_FIT, "First Fit"),
            (MemoryStrategy.BEST_FIT, "Best Fit"),
            (MemoryStrategy.WORST_FIT, "Worst Fit"),
            (MemoryStrategy.COMPARE_ALL, "Compare All Strategies"),
        ]
        for strat_enum, display_name in strategies_display:
            self.strategy_combo.addItem(display_name, strat_enum)

        self.strategy_combo.currentIndexChanged.connect(self._on_strategy_changed)

        top_row.addWidget(lbl_strat)
        top_row.addWidget(self.strategy_combo)

        # Strategy explanation banner
        self.strategy_info_label = QLabel()
        self.strategy_info_label.setWordWrap(True)
        self.strategy_info_label.setStyleSheet(
            f"background-color: {BG_ELEVATED}; color: {TEXT_PRIMARY}; font-size: 12px; padding: 6px 12px; border-radius: 6px; border-left: 3px solid {ACCENT_HOVER};"
        )
        top_row.addWidget(self.strategy_info_label, stretch=1)

        layout.addLayout(top_row)

        # Total Memory Pool Configuration Row
        mem_row = QHBoxLayout()
        mem_row.setSpacing(10)

        lbl_total = QLabel("Total Memory Pool:")
        lbl_total.setStyleSheet("font-weight: 600; color: #ffffff;")

        self.spin_total_memory = QSpinBox()
        self.spin_total_memory.setRange(64, 10000000)
        self.spin_total_memory.setValue(1000)
        self.spin_total_memory.setFixedWidth(110)
        self.spin_total_memory.setFixedHeight(28)

        lbl_units = QLabel("bytes")
        lbl_units.setStyleSheet(f"color: {TEXT_SECONDARY}; font-weight: 500;")

        lbl_pool_hint = QLabel("(Contiguous physical memory capacity managed by allocator)")
        lbl_pool_hint.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 11px;")

        mem_row.addWidget(lbl_total)
        mem_row.addWidget(self.spin_total_memory)
        mem_row.addWidget(lbl_units)
        mem_row.addWidget(lbl_pool_hint)
        mem_row.addStretch()

        layout.addLayout(mem_row)

        self._update_strategy_description()
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

        header_row = QHBoxLayout()
        title = QLabel("Understanding Memory Allocation")
        title.setStyleSheet("font-weight: 700; font-size: 13px; color: #ffffff;")
        hint = QLabel("Dynamic memory partition concepts implemented by the OScope memory manager.")
        hint.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 12px;")

        header_row.addWidget(title)
        header_row.addWidget(hint, stretch=1)
        layout.addLayout(header_row)

        # 4 concept cards
        defs_layout = QHBoxLayout()
        defs_layout.setSpacing(14)

        def_items = [
            ("Memory Pool", "Total contiguous byte capacity available to allocator.", ACCENT_CYAN),
            ("Logical Request ID", "Unique positive ID tracking each allocation request.", ACCENT_EMERALD),
            ("Block vs Process", "Block capacity is total partition size; process size is requested bytes.", ACCENT_AMBER),
            ("Free Coalescing", "When memory is freed, adjacent free blocks merge into one larger hole.", ACCENT_VIOLET),
        ]

        for term, explanation, color_val in def_items:
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

        # Example workload banner
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
            "Alloc #1 (200 B, PID 1)  →  Alloc #2 (300 B, PID 2)  →  Dealloc #1 (Frees 200 B at address 0)  →  Alloc #3 (150 B)"
        )
        lbl_ex_content.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 11px;")

        ex_layout.addWidget(lbl_ex_title)
        ex_layout.addWidget(lbl_ex_content, stretch=1)
        layout.addWidget(example_box)

        return card

    def _build_workload_card(self) -> QFrame:
        card = QFrame()
        card.setObjectName("WorkloadCard")
        card.setProperty("card", True)
        card.setStyleSheet(
            f"""
            QFrame#WorkloadCard {{
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
        title = QLabel("Memory Workload Operations")
        title.setStyleSheet("font-weight: 700; font-size: 13px; color: #ffffff;")
        toolbar.addWidget(title)
        toolbar.addStretch()

        btn_add_alloc = QPushButton("+ Add Allocate")
        btn_add_alloc.setFixedHeight(30)
        btn_add_alloc.setStyleSheet(
            f"background-color: rgba(16, 185, 129, 0.12); color: {ACCENT_EMERALD}; border: 1px solid rgba(16, 185, 129, 0.3); padding: 4px 12px; font-size: 12px; font-weight: 600; border-radius: 5px;"
        )
        btn_add_alloc.clicked.connect(lambda: self.add_operation_row(MemoryOperationType.ALLOCATE))
        toolbar.addWidget(btn_add_alloc)

        btn_add_dealloc = QPushButton("+ Add Deallocate")
        btn_add_dealloc.setFixedHeight(30)
        btn_add_dealloc.setStyleSheet(
            f"background-color: rgba(245, 158, 11, 0.12); color: {ACCENT_AMBER}; border: 1px solid rgba(245, 158, 11, 0.3); padding: 4px 12px; font-size: 12px; font-weight: 600; border-radius: 5px;"
        )
        btn_add_dealloc.clicked.connect(lambda: self.add_operation_row(MemoryOperationType.DEALLOCATE))
        toolbar.addWidget(btn_add_dealloc)

        btn_remove = QPushButton("- Remove Selected")
        btn_remove.setFixedHeight(30)
        btn_remove.setStyleSheet(
            f"background-color: rgba(244, 63, 94, 0.12); color: {ACCENT_ROSE}; border: 1px solid rgba(244, 63, 94, 0.3); padding: 4px 12px; font-size: 12px; font-weight: 600; border-radius: 5px;"
        )
        btn_remove.clicked.connect(self.remove_selected_row)
        toolbar.addWidget(btn_remove)

        self.preset_combo = QComboBox()
        self.preset_combo.setFixedHeight(30)
        self.preset_combo.addItem("Presets: Standard Partitioning")
        self.preset_combo.addItem("Presets: Fragmentation & Coalescing")
        self.preset_combo.addItem("Presets: Strategy Differentiation")
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

        # Operations Table
        self.op_table = QTableWidget(0, 5)
        self.op_table.setHorizontalHeaderLabels([
            "Step",
            "Operation Type",
            "Logical Request ID",
            "Size (Bytes)",
            "Process ID (Optional)",
        ])

        h_header = self.op_table.horizontalHeader()
        h_header.setSectionResizeMode(0, QHeaderView.Fixed)
        self.op_table.setColumnWidth(0, 65)
        h_header.setSectionResizeMode(1, QHeaderView.Fixed)
        self.op_table.setColumnWidth(1, 140)
        h_header.setSectionResizeMode(2, QHeaderView.Fixed)
        self.op_table.setColumnWidth(2, 160)
        h_header.setSectionResizeMode(3, QHeaderView.Fixed)
        self.op_table.setColumnWidth(3, 160)
        h_header.setSectionResizeMode(4, QHeaderView.Stretch)

        h_header.setFixedHeight(34)
        h_header.setDefaultAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        v_header = self.op_table.verticalHeader()
        v_header.setVisible(False)
        v_header.setDefaultSectionSize(36)

        self.op_table.setMinimumHeight(160)
        self.op_table.setMaximumHeight(230)
        self.op_table.setStyleSheet(
            f"""
            QTableWidget {{
                background-color: {BG_INPUT};
                border: 1px solid {BORDER};
                border-radius: 6px;
            }}
            """
        )
        layout.addWidget(self.op_table)

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
        title = QLabel("Memory Simulation Results & Layout")
        title.setStyleSheet("font-size: 17px; font-weight: 800; color: #ffffff;")
        res_header.addWidget(title)
        res_header.addStretch()
        layout.addLayout(res_header)

        # 4 Metric StatCards
        self.metrics_cards_layout = QHBoxLayout()
        self.metrics_cards_layout.setSpacing(12)

        self.card_allocated = StatCard(
            "Allocated Memory",
            "--",
            "bytes",
            tooltip="Total memory space currently assigned to active processes.",
            accent_color=ACCENT_HOVER,
        )
        self.card_free = StatCard(
            "Free Memory",
            "--",
            "bytes",
            tooltip="Total unused memory available across all free partition blocks.",
            accent_color=ACCENT_EMERALD,
        )
        self.card_largest = StatCard(
            "Largest Free Block",
            "--",
            "bytes",
            tooltip="Maximum contiguous partition available for future allocation requests.",
            accent_color=ACCENT_AMBER,
        )
        self.card_ext_frag = StatCard(
            "External Fragmentation",
            "--",
            "ratio",
            tooltip="Proportion of free memory that cannot satisfy an allocation due to discontiguous fragmentation.",
            accent_color=ACCENT_ROSE,
        )

        self.metrics_cards_layout.addWidget(self.card_allocated)
        self.metrics_cards_layout.addWidget(self.card_free)
        self.metrics_cards_layout.addWidget(self.card_largest)
        self.metrics_cards_layout.addWidget(self.card_ext_frag)
        layout.addLayout(self.metrics_cards_layout)

        # Memory Map Card
        self.map_box = QFrame()
        self.map_box.setObjectName("MemoryMapCard")
        self.map_box.setProperty("card", True)
        self.map_box.setStyleSheet(
            f"""
            QFrame#MemoryMapCard {{
                background-color: {BG_SURFACE};
                border: 1px solid {BORDER};
                border-radius: 8px;
            }}
            """
        )
        map_layout = QVBoxLayout(self.map_box)
        map_layout.setContentsMargins(18, 14, 18, 16)
        map_layout.setSpacing(10)

        m_header = QHBoxLayout()
        m_title = QLabel("Contiguous Memory Pool Layout")
        m_title.setStyleSheet("font-weight: 700; font-size: 13px; color: #ffffff;")
        m_hint = QLabel("A visual map representing allocated partitions (Cyan) and free blocks (Emerald).")
        m_hint.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 11px;")

        m_header.addWidget(m_title)
        m_header.addWidget(m_hint)
        m_header.addStretch()

        self.memory_map = MemoryMapWidget()

        lbl_map_caption = QLabel(
            "Memory Map: Represents physical address space [0 → Total]. Hover over blocks to inspect start address, capacity, and assigned PID."
        )
        lbl_map_caption.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 11px; padding-top: 2px;")

        map_layout.addLayout(m_header)
        map_layout.addWidget(self.memory_map)
        map_layout.addWidget(lbl_map_caption)
        layout.addWidget(self.map_box)

        # Tabbed Results: Blocks Table, Operation Log, Comparison Table, Raw Terminal
        self.tabs = QTabWidget()

        # Tab 1: Memory Block Layout Table
        self.tab_blocks = QWidget()
        t1_layout = QVBoxLayout(self.tab_blocks)
        t1_layout.setContentsMargins(10, 10, 10, 10)
        t1_layout.setSpacing(8)

        self.blocks_table = QTableWidget(0, 6)
        self.blocks_table.setHorizontalHeaderLabels([
            "Block #",
            "Start Address",
            "Size (Bytes)",
            "Status",
            "Allocation ID",
            "Process ID",
        ])
        self.blocks_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.blocks_table.horizontalHeader().setFixedHeight(34)
        self.blocks_table.verticalHeader().setVisible(False)
        self.blocks_table.verticalHeader().setDefaultSectionSize(34)
        self.blocks_table.setEditTriggers(QTableWidget.NoEditTriggers)
        t1_layout.addWidget(self.blocks_table)

        lbl_block_note = QLabel(
            "Block Table: Verified contiguous memory layout after execution. Adjacent free blocks are automatically coalesced."
        )
        lbl_block_note.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 11px; padding: 2px 4px;")
        t1_layout.addWidget(lbl_block_note)

        self.tabs.addTab(self.tab_blocks, "Memory Block Layout")

        # Tab 2: Operation Log
        self.tab_ops = QWidget()
        t2_layout = QVBoxLayout(self.tab_ops)
        t2_layout.setContentsMargins(10, 10, 10, 10)
        t2_layout.setSpacing(8)

        self.ops_table = QTableWidget(0, 5)
        self.ops_table.setHorizontalHeaderLabels([
            "Step",
            "Type",
            "Request ID",
            "Result",
            "Details / Error Message",
        ])
        self.ops_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        self.ops_table.setColumnWidth(0, 60)
        self.ops_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Fixed)
        self.ops_table.setColumnWidth(1, 110)
        self.ops_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Fixed)
        self.ops_table.setColumnWidth(2, 110)
        self.ops_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Fixed)
        self.ops_table.setColumnWidth(3, 110)
        self.ops_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)

        self.ops_table.horizontalHeader().setFixedHeight(34)
        self.ops_table.verticalHeader().setVisible(False)
        self.ops_table.verticalHeader().setDefaultSectionSize(34)
        self.ops_table.setEditTriggers(QTableWidget.NoEditTriggers)
        t2_layout.addWidget(self.ops_table)

        self.tabs.addTab(self.tab_ops, "Operation Execution Log")

        # Tab 3: Comparison Table (for Compare All)
        self.tab_comparison = QWidget()
        t3_layout = QVBoxLayout(self.tab_comparison)
        t3_layout.setContentsMargins(10, 10, 10, 10)
        t3_layout.setSpacing(8)

        self.comp_table = QTableWidget(0, 8)
        self.comp_table.setHorizontalHeaderLabels([
            "Strategy",
            "Attempts",
            "Success",
            "Failures",
            "Success Rate",
            "Allocated (B)",
            "Free (B)",
            "Ext Frag",
        ])
        self.comp_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.comp_table.horizontalHeader().setFixedHeight(34)
        self.comp_table.verticalHeader().setVisible(False)
        self.comp_table.verticalHeader().setDefaultSectionSize(34)
        self.comp_table.setEditTriggers(QTableWidget.NoEditTriggers)
        t3_layout.addWidget(self.comp_table)

        lbl_comp_note = QLabel("Strategy Comparison: Side-by-side benchmark of First Fit, Best Fit, and Worst Fit using the identical workload.")
        lbl_comp_note.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 11px; padding: 2px 4px;")
        t3_layout.addWidget(lbl_comp_note)

        self.tabs.addTab(self.tab_comparison, "Multi-Strategy Comparison")

        # Tab 4: Raw Terminal Output
        self.tab_raw = QWidget()
        t4_layout = QVBoxLayout(self.tab_raw)
        t4_layout.setContentsMargins(10, 10, 10, 10)
        self.raw_text = QTextEdit()
        self.raw_text.setReadOnly(True)
        t4_layout.addWidget(self.raw_text)
        self.tabs.addTab(self.tab_raw, "Raw Terminal Output")

        layout.addWidget(self.tabs)
        return widget

    def _on_strategy_changed(self, index: int) -> None:
        self._update_strategy_description()

    def _update_strategy_description(self) -> None:
        strat_data = self.strategy_combo.currentData()
        if not strat_data:
            return
        strat = MemoryStrategy(strat_data) if isinstance(strat_data, str) else strat_data
        self.strategy_info_label.setText(strat.description)

    def add_operation_row(
        self,
        op_type: MemoryOperationType = MemoryOperationType.ALLOCATE,
        request_id: Optional[int] = None,
        size: int = 150,
        process_id: Optional[int] = None,
    ) -> None:
        """Add an operation row to the workload table."""
        row = self.op_table.rowCount()
        self.op_table.insertRow(row)

        if request_id is None:
            max_id = 0
            for r in range(row):
                it = self.op_table.item(r, 2)
                if it and it.text().isdigit():
                    max_id = max(max_id, int(it.text()))
            request_id = max_id + 1

        if process_id is None and op_type == MemoryOperationType.ALLOCATE:
            process_id = request_id

        # Col 0: Step
        item_step = QTableWidgetItem(str(row + 1))
        item_step.setTextAlignment(Qt.AlignCenter)
        item_step.setFlags(item_step.flags() & ~Qt.ItemIsEditable)

        # Col 1: Type (Allocate / Deallocate)
        item_type = QTableWidgetItem(op_type.value)
        item_type.setTextAlignment(Qt.AlignCenter)
        item_type.setFlags(item_type.flags() & ~Qt.ItemIsEditable)
        if op_type == MemoryOperationType.ALLOCATE:
            item_type.setForeground(QColor(ACCENT_EMERALD))
        else:
            item_type.setForeground(QColor(ACCENT_AMBER))

        # Col 2: Request ID
        item_req = QTableWidgetItem(str(request_id))
        item_req.setTextAlignment(Qt.AlignCenter)

        # Col 3: Size
        if op_type == MemoryOperationType.ALLOCATE:
            item_size = QTableWidgetItem(str(size))
        else:
            item_size = QTableWidgetItem("N/A")
            item_size.setFlags(item_size.flags() & ~Qt.ItemIsEditable)
            item_size.setForeground(QColor(TEXT_MUTED))
        item_size.setTextAlignment(Qt.AlignCenter)

        # Col 4: Process ID
        if op_type == MemoryOperationType.ALLOCATE:
            item_pid = QTableWidgetItem(str(process_id) if process_id is not None else "-1")
        else:
            item_pid = QTableWidgetItem("N/A")
            item_pid.setFlags(item_pid.flags() & ~Qt.ItemIsEditable)
            item_pid.setForeground(QColor(TEXT_MUTED))
        item_pid.setTextAlignment(Qt.AlignCenter)

        self.op_table.setItem(row, 0, item_step)
        self.op_table.setItem(row, 1, item_type)
        self.op_table.setItem(row, 2, item_req)
        self.op_table.setItem(row, 3, item_size)
        self.op_table.setItem(row, 4, item_pid)

    def remove_selected_row(self) -> None:
        selected_rows = sorted(
            list({idx.row() for idx in self.op_table.selectedIndexes()}),
            reverse=True,
        )
        if not selected_rows and self.op_table.rowCount() > 0:
            selected_rows = [self.op_table.rowCount() - 1]

        for r in selected_rows:
            self.op_table.removeRow(r)

        # Update step numbers
        for r in range(self.op_table.rowCount()):
            it = self.op_table.item(r, 0)
            if it:
                it.setText(str(r + 1))

    def clear_all_rows(self) -> None:
        self.op_table.setRowCount(0)

    def _on_preset_selected(self, index: int) -> None:
        text = self.preset_combo.currentText()
        if "Standard Partitioning" in text:
            self.load_preset("Standard Partitioning")
        elif "Fragmentation & Coalescing" in text:
            self.load_preset("Fragmentation & Coalescing")
        elif "Strategy Differentiation" in text:
            self.load_preset("Strategy Differentiation")

    def load_preset(self, name: str) -> None:
        self.clear_all_rows()
        if name == "Standard Partitioning":
            self.spin_total_memory.setValue(1000)
            self.add_operation_row(MemoryOperationType.ALLOCATE, 1, 200, 1)
            self.add_operation_row(MemoryOperationType.ALLOCATE, 2, 300, 2)
            self.add_operation_row(MemoryOperationType.DEALLOCATE, 1)
            self.add_operation_row(MemoryOperationType.ALLOCATE, 3, 150, 3)
        elif name == "Fragmentation & Coalescing":
            self.spin_total_memory.setValue(1200)
            self.add_operation_row(MemoryOperationType.ALLOCATE, 1, 300, 1)
            self.add_operation_row(MemoryOperationType.ALLOCATE, 2, 200, 2)
            self.add_operation_row(MemoryOperationType.ALLOCATE, 3, 400, 3)
            self.add_operation_row(MemoryOperationType.DEALLOCATE, 1)
            self.add_operation_row(MemoryOperationType.DEALLOCATE, 2)  # Coalesces with 1!
            self.add_operation_row(MemoryOperationType.ALLOCATE, 4, 450, 4)
        elif name == "Strategy Differentiation":
            self.spin_total_memory.setValue(1000)
            self.add_operation_row(MemoryOperationType.ALLOCATE, 1, 300, 1)
            self.add_operation_row(MemoryOperationType.ALLOCATE, 2, 200, 2)
            self.add_operation_row(MemoryOperationType.ALLOCATE, 3, 300, 3)
            self.add_operation_row(MemoryOperationType.DEALLOCATE, 1)
            self.add_operation_row(MemoryOperationType.DEALLOCATE, 3)
            # Two holes: 300 B at 0, 300 B at 500, 200 B free at 800
            self.add_operation_row(MemoryOperationType.ALLOCATE, 4, 250, 4)

    def collect_inputs(self) -> tuple[Optional[MemoryConfig], Optional[List[MemoryOperationInput]], Optional[str]]:
        """Validate and collect user inputs from table with student-friendly error messages."""
        strat_data = self.strategy_combo.currentData()
        strat = MemoryStrategy(strat_data) if isinstance(strat_data, str) else strat_data

        config = MemoryConfig(
            strategy=strat,
            total_memory=self.spin_total_memory.value(),
        )

        cfg_err = config.validate()
        if cfg_err:
            return None, None, cfg_err

        row_count = self.op_table.rowCount()
        if row_count == 0:
            return None, None, "No memory operations entered. Click '+ Add Allocate' or select a preset workload."

        operations: List[MemoryOperationInput] = []

        for r in range(row_count):
            # Op Type
            item_type = self.op_table.item(r, 1)
            type_str = item_type.text().strip() if item_type else "Allocate"
            op_type = MemoryOperationType.ALLOCATE if type_str == "Allocate" else MemoryOperationType.DEALLOCATE

            # Request ID
            item_req = self.op_table.item(r, 2)
            if not item_req or not item_req.text().strip():
                return None, None, f"Row {r + 1}: Logical Request ID cannot be empty."
            try:
                req_id = int(item_req.text().strip())
            except ValueError:
                return None, None, f"Row {r + 1}: Logical Request ID must be an integer, got '{item_req.text()}'."
            if req_id <= 0:
                return None, None, f"Row {r + 1}: Logical Request ID must be positive (> 0), got {req_id}."

            # Size
            size = 0
            if op_type == MemoryOperationType.ALLOCATE:
                item_size = self.op_table.item(r, 3)
                if not item_size or not item_size.text().strip():
                    return None, None, f"Row {r + 1} (Request ID {req_id}): Allocation size cannot be empty."
                try:
                    size = int(item_size.text().strip())
                except ValueError:
                    return None, None, f"Row {r + 1} (Request ID {req_id}): Size must be an integer, got '{item_size.text()}'."
                if size <= 0:
                    return None, None, f"Row {r + 1} (Request ID {req_id}): Allocation size must be positive (> 0), got {size}."

            # Process ID
            pid = None
            if op_type == MemoryOperationType.ALLOCATE:
                item_pid = self.op_table.item(r, 4)
                if item_pid and item_pid.text().strip() and item_pid.text().strip() != "N/A":
                    try:
                        val = int(item_pid.text().strip())
                        if val >= 0:
                            pid = val
                    except ValueError:
                        pass

            operations.append(MemoryOperationInput(op_type=op_type, request_id=req_id, size=size, process_id=pid))

        return config, operations, None

    def run_simulation(self) -> None:
        """Trigger backend execution with inline validation feedback."""
        config, operations, err = self.collect_inputs()
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
        self.status_banner.setText(f"Running {config.strategy.value} simulation via C++ memory manager...")

        self._active_worker = MemoryWorker(self.runner, config, operations)
        self._active_worker.signals.completed.connect(self._on_simulation_success)
        self._active_worker.signals.failed.connect(self._on_simulation_failed)
        self._active_worker.start()

    def _on_simulation_success(self, result: object) -> None:
        self.btn_run.setEnabled(True)
        self.status_banner.setStyleSheet(
            f"background-color: {SUCCESS_BG}; color: {SUCCESS_TEXT}; border: 1px solid {SUCCESS}; border-radius: 6px; padding: 10px 14px; font-weight: 500;"
        )

        if isinstance(result, MemoryComparisonResultModel):
            self.status_banner.setText("Memory strategy comparison completed successfully across First Fit, Best Fit, and Worst Fit.")
            self._display_comparison_results(result)
            if self.on_execution_completed:
                self.on_execution_completed("Memory Strategy Comparison", len(result.entries), 0.0, 0.0, True)
        elif isinstance(result, MemorySimulationResultModel):
            self.status_banner.setText(f"{result.strategy_name} simulation completed successfully. Final memory layout verified.")
            self._display_single_result(result)
            if self.on_execution_completed:
                self.on_execution_completed(
                    f"{result.strategy_name} Memory",
                    len(result.blocks),
                    float(result.metrics.allocated_memory),
                    float(result.metrics.free_memory),
                    True,
                )

    def _on_simulation_failed(self, error_message: str) -> None:
        self.btn_run.setEnabled(True)
        self.status_banner.setStyleSheet(
            f"background-color: {DANGER_BG}; color: {DANGER_TEXT}; border: 1px solid {DANGER}; border-radius: 6px; padding: 10px 14px; font-weight: 500;"
        )
        self.status_banner.setText(f"Execution failed: {error_message}")
        self.raw_text.setPlainText(error_message)

    def _display_single_result(self, result: MemorySimulationResultModel) -> None:
        # Update StatCards
        m = result.metrics
        self.card_allocated.set_value(f"{m.allocated_memory} B", f"{m.utilization_percentage:.1f}% of pool")
        self.card_free.set_value(f"{m.free_memory} B", f"{(100.0 - m.utilization_percentage):.1f}% available")
        self.card_largest.set_value(f"{m.largest_free_block} B", "largest contiguous")
        self.card_ext_frag.set_value(f"{(m.external_fragmentation * 100.0):.1f}%", f"ratio: {m.external_fragmentation:.2f}")

        # Update Memory Map
        self.memory_map.set_memory_state(result.total_memory, result.blocks)

        # Update Blocks Table
        self.blocks_table.setRowCount(0)
        for blk in result.blocks:
            row = self.blocks_table.rowCount()
            self.blocks_table.insertRow(row)

            items = [
                QTableWidgetItem(str(blk.block_index)),
                QTableWidgetItem(f"{blk.start_address} → {blk.end_address}"),
                QTableWidgetItem(f"{blk.size} B"),
                QTableWidgetItem("Allocated" if blk.is_allocated else "Free"),
                QTableWidgetItem(str(blk.allocation_id) if blk.allocation_id is not None else "-"),
                QTableWidgetItem(f"P{blk.process_id}" if blk.process_id is not None else "-"),
            ]
            for col, it in enumerate(items):
                it.setTextAlignment(Qt.AlignCenter)
                if col == 3:
                    it.setForeground(QColor(ACCENT_HOVER if blk.is_allocated else ACCENT_EMERALD))
                self.blocks_table.setItem(row, col, it)

        # Update Operations Log Table
        self.ops_table.setRowCount(0)
        for op in result.operations:
            row = self.ops_table.rowCount()
            self.ops_table.insertRow(row)

            items = [
                QTableWidgetItem(str(op.op_number)),
                QTableWidgetItem(op.op_type),
                QTableWidgetItem(str(op.request_id)),
                QTableWidgetItem("Success" if op.success else "Failed"),
                QTableWidgetItem(op.message),
            ]
            for col, it in enumerate(items):
                if col < 4:
                    it.setTextAlignment(Qt.AlignCenter)
                if col == 3:
                    it.setForeground(QColor(SUCCESS_TEXT if op.success else DANGER_TEXT))
                self.ops_table.setItem(row, col, it)

        self.raw_text.setPlainText(result.raw_output)
        self.tabs.setCurrentIndex(0)

    def _display_comparison_results(self, result: MemoryComparisonResultModel) -> None:
        self.comp_table.setRowCount(0)
        for entry in result.entries:
            row = self.comp_table.rowCount()
            self.comp_table.insertRow(row)

            items = [
                QTableWidgetItem(entry.strategy_name),
                QTableWidgetItem(str(entry.attempts)),
                QTableWidgetItem(str(entry.success)),
                QTableWidgetItem(str(entry.failures)),
                QTableWidgetItem(f"{(entry.success_rate * 100.0):.1f}%"),
                QTableWidgetItem(f"{entry.allocated_bytes} B"),
                QTableWidgetItem(f"{entry.free_bytes} B"),
                QTableWidgetItem(f"{(entry.external_fragmentation * 100.0):.1f}%"),
            ]
            for col, it in enumerate(items):
                if col > 0:
                    it.setTextAlignment(Qt.AlignCenter)
                self.comp_table.setItem(row, col, it)

        self.raw_text.setPlainText(result.raw_output)
        self.tabs.setCurrentIndex(2)

    def display_results(self, result: MemorySimulationResultModel) -> None:
        """Display single simulation result (used by worker or test runners)."""
        self._on_simulation_success(result)

    def display_comparison(self, result: MemoryComparisonResultModel) -> None:
        """Display multi-strategy comparison result."""
        self._on_simulation_success(result)

    def show_error(self, error_message: str) -> None:
        """Display error banner and message."""
        self._on_simulation_failed(error_message)

    def reset_results(self) -> None:
        """Reset metric cards, clear memory map, and wipe result tables."""
        self.card_allocated.set_value("--", "bytes")
        self.card_free.set_value("--", "bytes")
        self.card_largest.set_value("--", "bytes")
        self.card_ext_frag.set_value("--", "ratio")

        self.memory_map.clear()
        self.blocks_table.setRowCount(0)
        self.ops_table.setRowCount(0)
        self.comp_table.setRowCount(0)
        self.raw_text.clear()

        self.status_banner.setStyleSheet(
            f"background-color: rgba(14, 165, 233, 0.12); color: {ACCENT_HOVER}; border: 1px solid rgba(14, 165, 233, 0.3); border-radius: 6px; padding: 10px 14px; font-size: 12px; font-weight: 500;"
        )
        self.status_banner.setText("Memory layout and results cleared. Select an allocation strategy and click 'Run Simulation'.")

