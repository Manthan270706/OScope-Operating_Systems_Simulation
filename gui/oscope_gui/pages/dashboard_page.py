"""Dashboard landing page for OScope Operating Systems Simulation Lab."""

from datetime import datetime
from typing import Callable, Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QScrollArea,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ..backend.runner import BaseBackendRunner
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
    TEXT_MUTED,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
)
from ..widgets.status_badge import StatusBadge


class DashboardPage(QWidget):
    """Main overview landing page with system readiness, experiment modules, and session history."""

    def __init__(
        self,
        runner: BaseBackendRunner,
        navigate_to_page: Callable[[str], None],
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.runner = runner
        self.navigate_to_page = navigate_to_page

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Scroll area for clean responsive layout
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet(f"background-color: {BG_APP}; border: none;")

        content = QWidget()
        content.setStyleSheet(f"background-color: {BG_APP};")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(36, 28, 36, 32)
        content_layout.setSpacing(22)

        # 1. Header Section
        header_layout = QHBoxLayout()
        title_box = QVBoxLayout()
        title_box.setSpacing(3)

        title = QLabel("OScope Simulation Platform")
        title.setStyleSheet("font-size: 24px; font-weight: 800; color: #ffffff; letter-spacing: -0.3px;")

        subtitle = QLabel("Interactive Operating Systems Simulation & Experimentation Laboratory")
        subtitle.setStyleSheet(f"font-size: 13px; color: {TEXT_SECONDARY};")

        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        header_layout.addLayout(title_box)
        header_layout.addStretch()

        # Compact user-facing readiness badge & retry
        self.status_badge = StatusBadge("Checking...", "pending")
        self.btn_retry = QPushButton("Check Status")
        self.btn_retry.setFixedWidth(110)
        self.btn_retry.setStyleSheet(f"font-size: 12px; padding: 5px 10px; background-color: {BG_ELEVATED};")
        self.btn_retry.clicked.connect(self.refresh_backend_status)
        self.btn_retry.hide()

        header_layout.addWidget(self.status_badge)
        header_layout.addWidget(self.btn_retry)
        content_layout.addLayout(header_layout)

        # 2. Primary Experiment Hero Card (CPU Scheduling)
        hero_card = self._build_hero_card()
        content_layout.addWidget(hero_card)

        # 3. Experiment Modules Grid
        modules_header = QHBoxLayout()
        modules_title = QLabel("Experiment Modules")
        modules_title.setStyleSheet("font-size: 16px; font-weight: 700; color: #ffffff;")
        modules_header.addWidget(modules_title)
        modules_header.addStretch()
        content_layout.addLayout(modules_header)

        modules_grid = self._build_modules_grid()
        content_layout.addLayout(modules_grid)

        # 4. Recent Session Executions Section
        history_header = QHBoxLayout()
        history_title = QLabel("Recent Session Executions")
        history_title.setStyleSheet("font-size: 16px; font-weight: 700; color: #ffffff;")
        history_header.addWidget(history_title)
        history_header.addStretch()
        content_layout.addLayout(history_header)

        self.history_table = self._build_history_table()
        content_layout.addWidget(self.history_table)

        self.empty_history_label = QLabel(
            "No simulations executed yet in this session. Head to CPU Scheduling to run your first experiment."
        )
        self.empty_history_label.setStyleSheet(
            f"color: {TEXT_MUTED}; font-size: 12px; padding: 22px; border: 1px dashed {BORDER}; border-radius: 8px; background-color: {BG_SURFACE};"
        )
        self.empty_history_label.setAlignment(Qt.AlignCenter)
        content_layout.addWidget(self.empty_history_label)

        scroll.setWidget(content)
        main_layout.addWidget(scroll)

        # Initial backend check
        self.refresh_backend_status()

    def _build_hero_card(self) -> QFrame:
        card = QFrame()
        card.setObjectName("HeroCard")
        card.setProperty("card", True)
        card.setStyleSheet(
            f"""
            QFrame#HeroCard {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #151d30, stop:1 #0f1523);
                border: 1px solid {BORDER};
                border-left: 4px solid {ACCENT_HOVER};
                border-radius: 8px;
            }}
            QFrame#HeroCard:hover {{
                border-color: {BORDER_LIGHT};
            }}
            """
        )
        layout = QHBoxLayout(card)
        layout.setContentsMargins(22, 18, 22, 18)
        layout.setSpacing(24)

        text_layout = QVBoxLayout()
        text_layout.setSpacing(8)

        title_row = QHBoxLayout()
        title_row.setSpacing(10)
        title = QLabel("CPU Scheduling Simulator")
        title.setStyleSheet("font-size: 18px; font-weight: 700; color: #ffffff;")
        badge = StatusBadge("Available", "success")
        title_row.addWidget(title)
        title_row.addWidget(badge)
        title_row.addStretch()

        desc = QLabel(
            "Simulate and visualize how operating system schedulers allocate CPU execution time among competing processes. "
            "Explore preemption, turnaround times, wait times, and live Gantt chart execution timelines."
        )
        desc.setWordWrap(True)
        desc.setStyleSheet(f"font-size: 13px; color: {TEXT_SECONDARY}; line-height: 1.45;")

        # Tags row for supported algorithms with distinct tasteful accents
        tags_row = QHBoxLayout()
        tags_row.setSpacing(6)
        supported_algos = [
            ("FCFS", ACCENT_HOVER, "rgba(14, 165, 233, 0.12)"),
            ("SJF", ACCENT_EMERALD, "rgba(16, 185, 129, 0.12)"),
            ("SRTF", ACCENT_CYAN, "rgba(6, 182, 212, 0.12)"),
            ("Priority", ACCENT_VIOLET, "rgba(139, 92, 246, 0.12)"),
            ("Round Robin", ACCENT_AMBER, "rgba(245, 158, 11, 0.12)"),
            ("MLFQ", ACCENT_ROSE, "rgba(244, 63, 94, 0.12)"),
            ("Compare All", ACCENT_INDIGO, "rgba(99, 102, 241, 0.12)"),
        ]
        for name, text_col, bg_col in supported_algos:
            tag = QLabel(name)
            tag.setStyleSheet(
                f"background-color: {bg_col}; color: {text_col}; font-size: 11px; font-weight: 600; padding: 3px 8px; border-radius: 4px; border: 1px solid rgba(255, 255, 255, 0.08);"
            )
            tags_row.addWidget(tag)
        tags_row.addStretch()

        text_layout.addLayout(title_row)
        text_layout.addWidget(desc)
        text_layout.addLayout(tags_row)

        # Prominent launch action
        btn_launch = QPushButton("Open CPU Scheduling")
        btn_launch.setProperty("class", "btn-primary")
        btn_launch.setFixedWidth(200)
        btn_launch.setFixedHeight(40)
        btn_launch.setStyleSheet(
            f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {ACCENT}, stop:1 {ACCENT_INDIGO});
                color: #ffffff;
                font-weight: 600;
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
        btn_launch.clicked.connect(lambda: self.navigate_to_page("scheduling"))

        layout.addLayout(text_layout, stretch=1)
        layout.addWidget(btn_launch)

        return card

    def _build_modules_grid(self) -> QGridLayout:
        grid = QGridLayout()
        grid.setSpacing(14)

        modules = [
            (
                "CPU Scheduling",
                "Available",
                "success",
                "Preemptive and non-preemptive algorithms with timeline visualization and performance metrics.",
                True,
                ACCENT_HOVER,
                "scheduling",
            ),
            (
                "Memory Allocation",
                "Available",
                "success",
                "Dynamic memory partitioning and fragmentation analysis with First-Fit, Best-Fit, and Worst-Fit.",
                True,
                ACCENT_EMERALD,
                "memory",
            ),
            (
                "Page Replacement",
                "Available",
                "success",
                "Virtual memory page fault simulation comparing FIFO, LRU, and Belady's Optimal algorithms.",
                True,
                ACCENT_VIOLET,
                "paging",
            ),

            (
                "Deadlock Management",
                "Available",
                "success",
                "Banker's safety verification, resource-request simulation, and deadlock detection with graph flow.",
                True,
                ACCENT_ROSE,
                "deadlock",
            ),
            (
                "Disk Scheduling",
                "Available",
                "success",
                "Secondary storage seek optimization comparing FCFS, SSTF, SCAN, C-SCAN, LOOK, C-LOOK, and LIFO.",
                True,
                ACCENT_AMBER,
                "disk",
            ),
            (
                "Linux / POSIX Experiments",
                "Available",
                "success",
                "Process lifecycle, thread synchronization, producer-consumer, and POSIX IPC channels.",
                True,
                ACCENT_INDIGO,
                "linux",
            ),
            (
                "Host Resource Monitoring",
                "Available",
                "success",
                "Real-time Linux host telemetry from /proc/stat, /proc/meminfo, /proc/loadavg, and statvfs.",
                True,
                ACCENT_CYAN,
                "monitor",
            ),
            (
                "Simulated File System",
                "Available",
                "success",
                "In-memory educational file system: contiguous, linked, indexed block allocations, directory trees, and bitmap.",
                True,
                ACCENT_EMERALD,
                "filesystem",
            ),
            (
                "Virtual Memory & Translation",
                "Available",
                "success",
                "MMU bit decomposition, multi-level page tables, demand paging page faults, and thrashing curves.",
                True,
                ACCENT_CYAN,
                "translation",
            ),
            (
                "Process Lifecycle State Machine",
                "Available",
                "success",
                "Discrete 5-state process lifecycle (New, Ready, Running, Waiting, Terminated) and C++ transition validation.",
                True,
                ACCENT_VIOLET,
                "lifecycle",
            ),
        ]


        for i, (name, status_text, status_state, desc_text, is_active, accent_color, page_key) in enumerate(modules):
            card = QFrame()
            card.setObjectName("ModuleCard")
            card.setProperty("card", True)
            card.setStyleSheet(
                f"""
                QFrame#ModuleCard {{
                    background-color: {BG_SURFACE};
                    border: 1px solid {BORDER};
                    border-top: 3px solid {accent_color};
                    border-radius: 8px;
                }}
                QFrame#ModuleCard:hover {{
                    border-color: {BORDER_LIGHT};
                    background-color: {BG_ELEVATED};
                }}
                """
            )
            c_layout = QVBoxLayout(card)
            c_layout.setContentsMargins(16, 14, 16, 14)
            c_layout.setSpacing(8)

            top_row = QHBoxLayout()
            lbl_name = QLabel(name)
            lbl_name.setStyleSheet("font-size: 14px; font-weight: 700; color: #ffffff;")
            badge = StatusBadge(status_text, status_state)
            top_row.addWidget(lbl_name)
            top_row.addStretch()
            top_row.addWidget(badge)
            c_layout.addLayout(top_row)

            lbl_desc = QLabel(desc_text)
            lbl_desc.setWordWrap(True)
            lbl_desc.setStyleSheet(f"font-size: 12px; color: {TEXT_SECONDARY}; line-height: 1.35;")
            c_layout.addWidget(lbl_desc)

            c_layout.addStretch()

            if is_active:
                btn_action = QPushButton("Launch Experiment →")
                btn_action.setFixedHeight(28)
                btn_action.setStyleSheet(
                    f"background-color: {BG_ELEVATED}; color: {accent_color}; font-size: 12px; font-weight: 600; border: 1px solid {BORDER_LIGHT};"
                )
                btn_action.clicked.connect(lambda _, key=page_key: self.navigate_to_page(key))
                if page_key == "disk":
                    self.btn_launch_disk = btn_action
                elif page_key == "deadlock":
                    self.btn_launch_deadlock = btn_action
                elif page_key == "paging":
                    self.btn_launch_page = btn_action
                elif page_key == "memory":
                    self.btn_launch_mem = btn_action
                elif page_key == "scheduling":
                    self.btn_launch_sched = btn_action
                c_layout.addWidget(btn_action)
            else:
                lbl_planned = QLabel("Planned in upcoming release")
                lbl_planned.setStyleSheet(f"font-size: 11px; color: {TEXT_MUTED}; font-style: italic;")
                c_layout.addWidget(lbl_planned)

            row = i // 3
            col = i % 3
            grid.addWidget(card, row, col)

        return grid

    def _build_history_table(self) -> QTableWidget:
        table = QTableWidget(0, 6)
        table.setHorizontalHeaderLabels([
            "Timestamp",
            "Algorithm",
            "Processes",
            "Avg Waiting",
            "Avg Turnaround",
            "Status",
        ])
        h_header = table.horizontalHeader()
        h_header.setSectionResizeMode(QHeaderView.Stretch)
        h_header.setFixedHeight(34)
        v_header = table.verticalHeader()
        v_header.setVisible(False)
        v_header.setDefaultSectionSize(34)

        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.setMinimumHeight(140)
        table.setMaximumHeight(240)
        table.hide()  # Hidden initially until executions are recorded
        return table

    def record_execution(
        self,
        algorithm: str,
        process_count: int,
        avg_wait: float,
        avg_tat: float,
        success: bool = True,
    ) -> None:
        """Record real session simulation executions in the history table."""
        self.empty_history_label.hide()
        self.history_table.show()

        row = self.history_table.rowCount()
        self.history_table.insertRow(row)

        now = datetime.now().strftime("%H:%M:%S")

        items = [
            QTableWidgetItem(now),
            QTableWidgetItem(algorithm),
            QTableWidgetItem(str(process_count)),
            QTableWidgetItem(f"{avg_wait:.2f}u"),
            QTableWidgetItem(f"{avg_tat:.2f}u"),
            QTableWidgetItem("Completed" if success else "Failed"),
        ]

        for col, it in enumerate(items):
            it.setTextAlignment(Qt.AlignCenter)
            if col == 5:
                it.setForeground(Qt.green if success else Qt.red)
            self.history_table.setItem(row, col, it)

    def refresh_backend_status(self) -> None:
        """Poll the backend runner and update user-facing readiness pill."""
        info = self.runner.get_info()
        if info.is_available:
            self.status_badge.set_state("success", "Ready to run experiments")
            self.btn_retry.hide()
        else:
            self.status_badge.set_state("error", "Experiment engine unavailable")
            self.btn_retry.show()
