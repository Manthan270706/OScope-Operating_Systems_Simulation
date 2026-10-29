"""Visualizations and widgets for Host Resource Monitoring."""

from typing import List, Optional

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import (
    QBrush,
    QColor,
    QFont,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
)
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QProgressBar,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ..models.host_monitor import (
    HostCpuModel,
    HostDiskIoModel,
    HostMemoryModel,
    HostMonitoringSnapshotModel,
    HostProcessModel,
    HostSystemModel,
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
    BG_SURFACE,
    BORDER,
    BORDER_LIGHT,
    FONT_FAMILY,
    SUCCESS,
    TEXT_MUTED,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
)


class HostMetricCard(QFrame):
    """Elevated card with live percentage bar and metric detail breakdown."""

    def __init__(
        self,
        title: str,
        accent_color: str = ACCENT,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.accent_color = accent_color
        self.setProperty("card", True)
        self.setStyleSheet(
            f"""
            QFrame {{
                background-color: {BG_SURFACE};
                border: 1px solid {BORDER};
                border-top: 3px solid {accent_color};
                border-radius: 8px;
            }}
            """
        )
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.setMinimumHeight(130)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(6)

        # Header Row
        h_row = QHBoxLayout()
        self.lbl_title = QLabel(title)
        self.lbl_title.setStyleSheet(f"font-size: 11px; font-weight: 700; color: {TEXT_MUTED}; letter-spacing: 0.5px;")
        h_row.addWidget(self.lbl_title)
        h_row.addStretch()

        self.lbl_badge = QLabel("Active")
        self.lbl_badge.setStyleSheet(
            f"font-size: 10px; font-weight: 700; color: {SUCCESS}; background-color: rgba(16, 185, 129, 0.15); "
            f"padding: 2px 6px; border-radius: 4px; border: 1px solid rgba(16, 185, 129, 0.3);"
        )
        h_row.addWidget(self.lbl_badge)
        layout.addLayout(h_row)

        # Big Value
        self.lbl_value = QLabel("—")
        self.lbl_value.setStyleSheet("font-size: 22px; font-weight: 800; color: #ffffff;")
        layout.addWidget(self.lbl_value)

        # Progress / Utilization Bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(6)
        self._set_bar_color(accent_color)
        layout.addWidget(self.progress_bar)

        # Subtitle breakdown
        self.lbl_detail = QLabel("Awaiting telemetry sample...")
        self.lbl_detail.setStyleSheet(f"font-size: 11px; color: {TEXT_SECONDARY};")
        self.lbl_detail.setWordWrap(True)
        layout.addWidget(self.lbl_detail)

    def _set_bar_color(self, color_hex: str) -> None:
        self.progress_bar.setStyleSheet(
            f"""
            QProgressBar {{
                background-color: {BG_CANVAS};
                border: 1px solid {BORDER};
                border-radius: 3px;
            }}
            QProgressBar::chunk {{
                background-color: {color_hex};
                border-radius: 3px;
            }}
            """
        )

    def update_metric(self, value_text: str, percentage: float, detail_text: str, is_active: bool = True) -> None:
        self.lbl_value.setText(value_text)
        pct = max(0.0, min(100.0, percentage))
        self.progress_bar.setValue(int(pct))
        self.lbl_detail.setText(detail_text)

        if not is_active:
            self.lbl_badge.setText("Stale / Paused")
            self.lbl_badge.setStyleSheet(
                f"font-size: 10px; font-weight: 700; color: {TEXT_MUTED}; background-color: {BG_ELEVATED}; "
                f"padding: 2px 6px; border-radius: 4px; border: 1px solid {BORDER};"
            )
            self._set_bar_color(BORDER_LIGHT)
            return

        self.lbl_badge.setText("Live")
        self.lbl_badge.setStyleSheet(
            f"font-size: 10px; font-weight: 700; color: {SUCCESS}; background-color: rgba(16, 185, 129, 0.15); "
            f"padding: 2px 6px; border-radius: 4px; border: 1px solid rgba(16, 185, 129, 0.3);"
        )

        # Dynamically color bar according to load threshold
        if pct > 85.0:
            self._set_bar_color(ACCENT_ROSE)
        elif pct > 65.0:
            self._set_bar_color(ACCENT_AMBER)
        else:
            self._set_bar_color(self.accent_color)


class HostMetricHistoryPlotWidget(QWidget):
    """Smooth anti-aliased time-series chart of historical host CPU and Memory telemetry."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setMinimumHeight(240)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.MinimumExpanding)
        self.setStyleSheet(f"background-color: {BG_CANVAS}; border: 1px solid {BORDER}; border-radius: 8px;")

        self.cpu_history: List[float] = []
        self.mem_history: List[float] = []
        self.timestamps: List[str] = []
        self.max_samples = 40

    def add_sample(self, cpu_pct: float, mem_pct: float, timestamp: str = "") -> None:
        self.cpu_history.append(max(0.0, min(100.0, cpu_pct)))
        self.mem_history.append(max(0.0, min(100.0, mem_pct)))
        self.timestamps.append(timestamp)

        if len(self.cpu_history) > self.max_samples:
            self.cpu_history.pop(0)
            self.mem_history.pop(0)
            self.timestamps.pop(0)

        self.update()

    def clear(self) -> None:
        self.cpu_history.clear()
        self.mem_history.clear()
        self.timestamps.clear()
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()

        # Canvas Background
        painter.fillRect(0, 0, w, h, QColor(BG_CANVAS))

        # Margin definition
        m_left = 48
        m_right = 24
        m_top = 34
        m_bottom = 28

        chart_w = max(10, w - m_left - m_right)
        chart_h = max(10, h - m_top - m_bottom)

        # Draw Grid Lines & Y-axis labels
        grid_pen = QPen(QColor(BORDER), 1, Qt.DashLine)
        painter.setPen(grid_pen)
        painter.setFont(QFont(FONT_FAMILY, 9))

        for pct in (0, 25, 50, 75, 100):
            y = m_top + chart_h - (pct / 100.0) * chart_h
            painter.drawLine(m_left, int(y), m_left + chart_w, int(y))

            # Y text
            painter.setPen(QColor(TEXT_MUTED))
            painter.drawText(8, int(y) + 4, f"{pct}%")
            painter.setPen(grid_pen)

        # Legend Header
        painter.setPen(Qt.NoPen)
        # CPU Legend Pill
        painter.setPen(QPen(QColor(ACCENT_CYAN), 2))
        painter.drawLine(m_left, 18, m_left + 18, 18)
        painter.drawText(m_left + 24, 22, "CPU Utilization (%)")

        # Memory Legend Pill
        painter.setPen(QPen(QColor(ACCENT_EMERALD), 2))
        painter.drawLine(m_left + 160, 18, m_left + 178, 18)
        painter.drawText(m_left + 184, 22, "Memory Utilization (%)")

        # Draw Samples if available
        n_samples = len(self.cpu_history)
        if n_samples < 2:
            painter.setPen(QColor(TEXT_MUTED))
            painter.setFont(QFont(FONT_FAMILY, 11))
            painter.drawText(QRectF(m_left, m_top, chart_w, chart_h), Qt.AlignCenter, "Collecting host telemetry samples...")
            return

        step_x = chart_w / max(1, self.max_samples - 1)

        # 1. Plot Memory Path (Background Area)
        mem_path = QPainterPath()
        start_x = m_left + (self.max_samples - n_samples) * step_x
        start_y = m_top + chart_h - (self.mem_history[0] / 100.0) * chart_h
        mem_path.moveTo(start_x, start_y)

        for i in range(1, n_samples):
            x = start_x + i * step_x
            y = m_top + chart_h - (self.mem_history[i] / 100.0) * chart_h
            mem_path.lineTo(x, y)

        # Gradient fill for memory
        mem_fill = QPainterPath(mem_path)
        last_x = start_x + (n_samples - 1) * step_x
        mem_fill.lineTo(last_x, m_top + chart_h)
        mem_fill.lineTo(start_x, m_top + chart_h)
        mem_fill.closeSubpath()

        mem_grad = QLinearGradient(0, m_top, 0, m_top + chart_h)
        mem_grad.setColorAt(0, QColor(16, 185, 129, 60))
        mem_grad.setColorAt(1, QColor(16, 185, 129, 5))
        painter.fillPath(mem_fill, QBrush(mem_grad))

        painter.setPen(QPen(QColor(ACCENT_EMERALD), 2))
        painter.drawPath(mem_path)

        # 2. Plot CPU Path
        cpu_path = QPainterPath()
        start_y_cpu = m_top + chart_h - (self.cpu_history[0] / 100.0) * chart_h
        cpu_path.moveTo(start_x, start_y_cpu)

        for i in range(1, n_samples):
            x = start_x + i * step_x
            y = m_top + chart_h - (self.cpu_history[i] / 100.0) * chart_h
            cpu_path.lineTo(x, y)

        cpu_fill = QPainterPath(cpu_path)
        cpu_fill.lineTo(last_x, m_top + chart_h)
        cpu_fill.lineTo(start_x, m_top + chart_h)
        cpu_fill.closeSubpath()

        cpu_grad = QLinearGradient(0, m_top, 0, m_top + chart_h)
        cpu_grad.setColorAt(0, QColor(56, 189, 248, 70))
        cpu_grad.setColorAt(1, QColor(56, 189, 248, 5))
        painter.fillPath(cpu_fill, QBrush(cpu_grad))

        painter.setPen(QPen(QColor(ACCENT_CYAN), 2.2))
        painter.drawPath(cpu_path)

        # Draw point markers on latest sample
        painter.setBrush(QColor(ACCENT_CYAN))
        painter.drawEllipse(QPointF(last_x, m_top + chart_h - (self.cpu_history[-1] / 100.0) * chart_h), 4, 4)

        painter.setBrush(QColor(ACCENT_EMERALD))
        painter.drawEllipse(QPointF(last_x, m_top + chart_h - (self.mem_history[-1] / 100.0) * chart_h), 4, 4)


class HostProcessTableWidget(QTableWidget):
    """Table presenting self-process observation from /proc/[pid]/stat."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setColumnCount(7)
        self.setHorizontalHeaderLabels([
            "PID",
            "Executable (Comm)",
            "Kernel State",
            "PPID",
            "Resident RAM (RSS)",
            "Virtual Memory (VM)",
            "CPU User/Sys Ticks",
        ])
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.verticalHeader().setVisible(False)
        self.setEditTriggers(QTableWidget.NoEditTriggers)
        self.setSelectionBehavior(QTableWidget.SelectRows)
        self.setStyleSheet(
            f"""
            QTableWidget {{
                background-color: {BG_SURFACE};
                border: 1px solid {BORDER};
                border-radius: 6px;
                gridline-color: {BORDER};
                color: {TEXT_PRIMARY};
                font-size: 12px;
            }}
            QHeaderView::section {{
                background-color: {BG_ELEVATED};
                color: {TEXT_SECONDARY};
                font-weight: 700;
                font-size: 11px;
                padding: 6px;
                border: 1px solid {BORDER};
            }}
            """
        )

    def update_process(self, proc: Optional[HostProcessModel]) -> None:
        self.setRowCount(0)
        if not proc or not proc.valid:
            return

        self.insertRow(0)

        # PID
        item_pid = QTableWidgetItem(str(proc.pid))
        item_pid.setTextAlignment(Qt.AlignCenter)
        self.setItem(0, 0, item_pid)

        # Comm
        item_comm = QTableWidgetItem(proc.comm or "oscope")
        self.setItem(0, 1, item_comm)

        # State
        item_state = QTableWidgetItem(proc.state_description)
        item_state.setTextAlignment(Qt.AlignCenter)
        if proc.state == "R":
            item_state.setForeground(QColor(SUCCESS))
        elif proc.state == "Z":
            item_state.setForeground(QColor(ACCENT_ROSE))
        else:
            item_state.setForeground(QColor(ACCENT_CYAN))
        self.setItem(0, 2, item_state)

        # PPID
        item_ppid = QTableWidgetItem(str(proc.ppid))
        item_ppid.setTextAlignment(Qt.AlignCenter)
        self.setItem(0, 3, item_ppid)

        # RSS
        rss_str = f"{proc.rss_kb:,} kB ({proc.rss_kb / 1024.0:.2f} MB)" if proc.rss_kb else "—"
        self.setItem(0, 4, QTableWidgetItem(rss_str))

        # VM
        vm_kb = proc.vm_size_bytes // 1024
        vm_str = f"{vm_kb:,} kB ({vm_kb / 1024.0:.2f} MB)" if vm_kb else "—"
        self.setItem(0, 5, QTableWidgetItem(vm_str))

        # Ticks
        ticks_str = f"U: {proc.utime_ticks} | S: {proc.stime_ticks}"
        self.setItem(0, 6, QTableWidgetItem(ticks_str))


class HostDiskTableWidget(QTableWidget):
    """Table presenting host block device I/O from /proc/diskstats."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setColumnCount(5)
        self.setHorizontalHeaderLabels([
            "Device Name",
            "Reads Completed",
            "Sectors Read",
            "Writes Completed",
            "Sectors Written",
        ])
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.verticalHeader().setVisible(False)
        self.setEditTriggers(QTableWidget.NoEditTriggers)
        self.setSelectionBehavior(QTableWidget.SelectRows)
        self.setStyleSheet(
            f"""
            QTableWidget {{
                background-color: {BG_SURFACE};
                border: 1px solid {BORDER};
                border-radius: 6px;
                gridline-color: {BORDER};
                color: {TEXT_PRIMARY};
                font-size: 12px;
            }}
            QHeaderView::section {{
                background-color: {BG_ELEVATED};
                color: {TEXT_SECONDARY};
                font-weight: 700;
                font-size: 11px;
                padding: 6px;
                border: 1px solid {BORDER};
            }}
            """
        )

    def update_disks(self, disks: List[HostDiskIoModel]) -> None:
        self.setRowCount(0)
        for i, d in enumerate(disks):
            self.insertRow(i)

            item_dev = QTableWidgetItem(d.device_name)
            item_dev.setFont(QFont(FONT_FAMILY, 11, QFont.Bold))
            item_dev.setForeground(QColor(ACCENT_AMBER))
            self.setItem(i, 0, item_dev)

            self.setItem(i, 1, QTableWidgetItem(f"{d.reads_completed:,}"))
            self.setItem(i, 2, QTableWidgetItem(f"{d.sectors_read:,}"))
            self.setItem(i, 3, QTableWidgetItem(f"{d.writes_completed:,}"))
            self.setItem(i, 4, QTableWidgetItem(f"{d.sectors_written:,}"))
