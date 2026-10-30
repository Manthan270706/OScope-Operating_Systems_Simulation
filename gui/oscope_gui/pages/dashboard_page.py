"""Dashboard landing page for OScope Operating Systems Simulation Lab."""

from datetime import datetime
from typing import Callable, Optional

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QBrush, QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ..backend.runner import BaseBackendRunner
from ..icons import render_svg_icon, render_svg_pixmap
from ..theme import (
    ACCENT,
    ACCENT_HOVER,
    ACCENT_LIGHT,
    ACCENT_LIGHT_HOVER,
    BG_APP,
    BG_DARK,
    BG_ELEVATED,
    BG_SURFACE,
    BORDER,
    BORDER_LIGHT,
    TEXT_MUTED,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
)
from ..widgets.status_badge import StatusBadge


class MiniGanttPreviewWidget(QWidget):
    """Clean miniature preview Gantt chart for the hero CPU Scheduling card."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setFixedSize(220, 110)

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = float(self.width())
        h = float(self.height())

        # Card container with subtle border
        painter.setPen(QPen(QColor(BORDER), 1))
        painter.setBrush(QBrush(QColor("#FFFFFF")))
        painter.drawRoundedRect(QRectF(1, 1, w - 2, h - 2), 6, 6)

        margin_left = 32.0
        margin_right = 14.0
        margin_top = 10.0
        margin_bottom = 22.0

        chart_w = w - margin_left - margin_right
        chart_h = h - margin_top - margin_bottom

        # Process rows: P1, P2, P3, P4
        labels = ["P1", "P2", "P3", "P4"]
        n_rows = len(labels)
        row_h = chart_h / n_rows

        font = QFont("Segoe UI", 7, QFont.Bold)
        painter.setFont(font)

        # Draw row labels and subtle horizontal guide lines
        for i, lbl in enumerate(labels):
            y = margin_top + i * row_h
            painter.setPen(QColor(TEXT_MUTED))
            painter.drawText(QRectF(4, y, margin_left - 8, row_h), Qt.AlignRight | Qt.AlignVCenter, lbl)

            # Subtle horizontal rule
            painter.setPen(QPen(QColor("#F1F5F9"), 1))
            painter.drawLine(int(margin_left), int(y + row_h), int(w - margin_right), int(y + row_h))

        # Sample preview execution slices (start, end, row, color)
        slices = [
            (0, 12, 0, "#3B82F6"),
            (12, 22, 1, "#60A5FA"),
            (22, 38, 2, "#2563EB"),
            (38, 52, 3, "#93C5FD"),
        ]
        total_time = 54.0

        for start, end, row_idx, col_hex in slices:
            x0 = margin_left + (start / total_time) * chart_w
            x1 = margin_left + (end / total_time) * chart_w
            y0 = margin_top + row_idx * row_h + 3.0
            bh = row_h - 6.0

            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(QColor(col_hex)))
            painter.drawRoundedRect(QRectF(x0, y0, max(4.0, x1 - x0), bh), 3, 3)

        # Bottom time axis ticks: 0, 10, 20, 30, 40, 50
        axis_font = QFont("Segoe UI", 6)
        painter.setFont(axis_font)
        painter.setPen(QColor(TEXT_MUTED))
        for t in [0, 10, 20, 30, 40, 50]:
            tx = margin_left + (t / total_time) * chart_w
            painter.drawLine(int(tx), int(h - margin_bottom + 1), int(tx), int(h - margin_bottom + 4))
            painter.drawText(QRectF(tx - 10, h - margin_bottom + 5, 20, 12), Qt.AlignCenter, str(t))


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
        title.setStyleSheet(f"font-size: 22px; font-weight: 800; color: {TEXT_PRIMARY}; letter-spacing: -0.3px;")

        subtitle = QLabel("Interactive Operating Systems Simulation & Experimentation Laboratory")
        subtitle.setStyleSheet(f"font-size: 13px; color: {TEXT_SECONDARY};")

        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        header_layout.addLayout(title_box)
        header_layout.addStretch()

        # Engine status pill & actions
        self.status_badge = StatusBadge("Engine status: Available", "success")
        self.btn_retry = QPushButton("Check Status")
        self.btn_retry.setFixedHeight(30)
        self.btn_retry.setStyleSheet(
            f"""
            QPushButton {{
                font-size: 12px;
                padding: 4px 12px;
                background-color: {BG_SURFACE};
                color: {TEXT_PRIMARY};
                border: 1px solid {BORDER_LIGHT};
                border-radius: 6px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: {BG_DARK};
                border-color: {TEXT_MUTED};
            }}
            """
        )
        self.btn_retry.clicked.connect(self.refresh_backend_status)

        header_layout.addWidget(self.status_badge)
        header_layout.addWidget(self.btn_retry)
        content_layout.addLayout(header_layout)

        # 2. Primary Experiment Hero Card (CPU Scheduling)
        hero_card = self._build_hero_card()
        content_layout.addWidget(hero_card)

        # 3. Experiment Modules Grid
        modules_header = QHBoxLayout()
        modules_title = QLabel("Experiment Modules")
        modules_title.setStyleSheet(f"font-size: 16px; font-weight: 700; color: {TEXT_PRIMARY};")
        modules_header.addWidget(modules_title)
        modules_header.addStretch()
        content_layout.addLayout(modules_header)

        modules_grid = self._build_modules_grid()
        content_layout.addLayout(modules_grid)

        # 4. Recent Session Executions Section
        history_header = QHBoxLayout()
        history_title = QLabel("Recent Session Executions")
        history_title.setStyleSheet(f"font-size: 16px; font-weight: 700; color: {TEXT_PRIMARY};")
        history_header.addWidget(history_title)
        history_header.addStretch()
        content_layout.addLayout(history_header)

        self.history_table = self._build_history_table()
        content_layout.addWidget(self.history_table)

        # Clean empty state box matching reference design
        self.empty_history_container = QFrame()
        self.empty_history_container.setStyleSheet(
            f"""
            QFrame {{
                background-color: {BG_SURFACE};
                border: 1px solid {BORDER};
                border-radius: 8px;
                padding: 16px;
            }}
            """
        )
        empty_layout = QHBoxLayout(self.empty_history_container)
        empty_layout.setContentsMargins(20, 16, 20, 16)
        empty_layout.setSpacing(14)

        icon_doc = QLabel()
        icon_doc.setPixmap(render_svg_pixmap("paging", "#94A3B8", 28))
        icon_doc.setFixedSize(36, 36)
        icon_doc.setAlignment(Qt.AlignCenter)

        empty_text_layout = QVBoxLayout()
        empty_text_layout.setSpacing(2)

        lbl_empty_title = QLabel("No simulations executed yet")
        lbl_empty_title.setStyleSheet(f"font-size: 13px; font-weight: 600; color: {TEXT_PRIMARY};")

        lbl_empty_sub = QLabel("Run an experiment from the modules above to see your recent sessions here.")
        lbl_empty_sub.setStyleSheet(f"font-size: 12px; color: {TEXT_SECONDARY};")

        empty_text_layout.addWidget(lbl_empty_title)
        empty_text_layout.addWidget(lbl_empty_sub)

        empty_layout.addStretch()
        empty_layout.addWidget(icon_doc)
        empty_layout.addLayout(empty_text_layout)
        empty_layout.addStretch()

        content_layout.addWidget(self.empty_history_container)

        # Legacy alias so existing tests pass cleanly
        self.empty_history_label = self.empty_history_container

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
                background-color: {BG_SURFACE};
                border: 1px solid {BORDER};
                border-radius: 8px;
            }}
            QFrame#HeroCard:hover {{
                border-color: {BORDER_LIGHT};
            }}
            """
        )
        layout = QHBoxLayout(card)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(20)

        # Icon Container: 44x44, background #EAF2FF, rounded 8px
        icon_box = QLabel()
        icon_box.setFixedSize(44, 44)
        icon_box.setAlignment(Qt.AlignCenter)
        icon_box.setStyleSheet(f"background-color: {ACCENT_LIGHT}; border-radius: 8px;")
        icon_box.setPixmap(render_svg_pixmap("cpu", ACCENT, 24))
        layout.addWidget(icon_box, alignment=Qt.AlignTop)

        text_layout = QVBoxLayout()
        text_layout.setSpacing(8)

        title_row = QHBoxLayout()
        title_row.setSpacing(10)
        title = QLabel("CPU Scheduling Simulator")
        title.setStyleSheet(f"font-size: 17px; font-weight: 700; color: {TEXT_PRIMARY};")
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

        # Tags row with restrained, uniform light-blue badges matching reference design
        tags_row = QHBoxLayout()
        tags_row.setSpacing(8)
        supported_algos = ["FCFS", "SJF", "SRTF", "Priority", "Round Robin", "MLFQ"]
        for name in supported_algos:
            tag = QLabel(name)
            tag.setStyleSheet(
                f"""
                background-color: {ACCENT_LIGHT};
                color: {ACCENT};
                font-size: 11px;
                font-weight: 600;
                padding: 4px 10px;
                border-radius: 6px;
                border: 1px solid #DBEAFE;
                """
            )
            tags_row.addWidget(tag)
        tags_row.addStretch()

        text_layout.addLayout(title_row)
        text_layout.addWidget(desc)
        text_layout.addLayout(tags_row)
        layout.addLayout(text_layout, stretch=1)

        # Mini Gantt Preview Widget
        mini_gantt = MiniGanttPreviewWidget()
        layout.addWidget(mini_gantt)

        # Prominent primary blue launch button
        btn_launch = QPushButton("Open CPU Scheduling →")
        btn_launch.setProperty("class", "btn-primary")
        btn_launch.setFixedWidth(190)
        btn_launch.setFixedHeight(40)
        btn_launch.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {ACCENT};
                color: #172033;
                font-weight: 600;
                font-size: 13px;
                border-radius: 6px;
                border: 1px solid {ACCENT};
            }}
            QPushButton:hover {{
                background-color: {ACCENT_HOVER};
                border-color: {ACCENT_HOVER};
            }}
            """
        )
        btn_launch.clicked.connect(lambda: self.navigate_to_page("scheduling"))
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
                "cpu",
                "scheduling",
            ),
            (
                "Memory Allocation",
                "Available",
                "success",
                "Dynamic memory partitioning and fragmentation analysis with First-Fit, Best-Fit, and Worst-Fit.",
                True,
                "memory",
                "memory",
            ),
            (
                "Page Replacement",
                "Available",
                "success",
                "Virtual memory page fault simulation comparing FIFO, LRU, and Belady's Optimal algorithms.",
                True,
                "paging",
                "paging",
            ),
            (
                "Deadlock Management",
                "Available",
                "success",
                "Banker's safety verification, resource-request simulation, and deadlock detection with graph flow.",
                True,
                "deadlock",
                "deadlock",
            ),
            (
                "Disk Scheduling",
                "Available",
                "success",
                "Seek optimization comparing FCFS, SSTF, SCAN, C-SCAN, LOOK, C-LOOK, and LIFO.",
                True,
                "disk",
                "disk",
            ),
            (
                "Linux / POSIX Experiments",
                "Available",
                "success",
                "Process lifecycle, thread synchronization, producer-consumer, and POSIX IPC channels.",
                True,
                "linux",
                "linux",
            ),
            (
                "Host Resource Monitoring",
                "Available",
                "success",
                "Real-time Linux host telemetry from /proc and /sys (CPU, memory, disk, process stats).",
                True,
                "monitor",
                "monitor",
            ),
            (
                "Simulated File System",
                "Available",
                "success",
                "In-memory educational file system: contiguous, linked, indexed block allocations, directory trees.",
                True,
                "filesystem",
                "filesystem",
            ),
            (
                "Virtual Memory & Translation",
                "Available",
                "success",
                "MMU bit decomposition, multi-level page tables, demand paging page faults, and thrashing curves.",
                True,
                "translation",
                "translation",
            ),
            (
                "Process Lifecycle State Machine",
                "Available",
                "success",
                "Visualize process states (New, Ready, Running, Waiting, Terminated) with state transitions.",
                True,
                "lifecycle",
                "lifecycle",
            ),
        ]

        for i, (name, status_text, status_state, desc_text, is_active, icon_name, page_key) in enumerate(modules):
            card = QFrame()
            card.setObjectName("ModuleCard")
            card.setProperty("card", True)
            card.setStyleSheet(
                f"""
                QFrame#ModuleCard {{
                    background-color: {BG_SURFACE};
                    border: 1px solid {BORDER};
                    border-radius: 8px;
                }}
                QFrame#ModuleCard:hover {{
                    border-color: {BORDER_LIGHT};
                }}
                """
            )
            c_layout = QVBoxLayout(card)
            c_layout.setContentsMargins(16, 16, 16, 16)
            c_layout.setSpacing(10)

            # Top row: Icon container + Title + Status badge
            top_row = QHBoxLayout()
            top_row.setSpacing(10)

            icon_box = QLabel()
            icon_box.setFixedSize(38, 38)
            icon_box.setAlignment(Qt.AlignCenter)
            icon_box.setStyleSheet(f"background-color: {ACCENT_LIGHT}; border-radius: 8px;")
            icon_box.setPixmap(render_svg_pixmap(icon_name, ACCENT, 20))
            top_row.addWidget(icon_box)

            lbl_name = QLabel(name)
            lbl_name.setStyleSheet(f"font-size: 14px; font-weight: 700; color: {TEXT_PRIMARY};")
            top_row.addWidget(lbl_name)
            top_row.addStretch()

            badge = StatusBadge(status_text, status_state)
            top_row.addWidget(badge)
            c_layout.addLayout(top_row)

            lbl_desc = QLabel(desc_text)
            lbl_desc.setWordWrap(True)
            lbl_desc.setStyleSheet(f"font-size: 12px; color: {TEXT_SECONDARY}; line-height: 1.4;")
            c_layout.addWidget(lbl_desc)

            c_layout.addStretch()

            if is_active:
                btn_action = QPushButton("Launch Experiment →")
                btn_action.setFixedHeight(32)
                btn_action.setStyleSheet(
                    f"""
                    QPushButton {{
                        background-color: {ACCENT_LIGHT};
                        color: {ACCENT};
                        font-size: 12px;
                        font-weight: 600;
                        border: 1px solid #DBEAFE;
                        border-radius: 6px;
                    }}
                    QPushButton:hover {{
                        background-color: {ACCENT_LIGHT_HOVER};
                        border-color: #BFDBFE;
                    }}
                    """
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
        self.empty_history_container.hide()
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
                it.setForeground(QColor("#16A34A") if success else QColor("#DC2626"))
            self.history_table.setItem(row, col, it)

    def refresh_backend_status(self) -> None:
        """Poll the backend runner and update user-facing readiness pill."""
        info = self.runner.get_info()
        if info.is_available:
            self.status_badge.set_state("success", "Engine status: Available")
            self.btn_retry.show()
        else:
            self.status_badge.set_state("error", "Engine status: Unavailable")
            self.btn_retry.show()
