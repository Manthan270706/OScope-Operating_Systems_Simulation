"""Interactive visual widgets for Process Lifecycle State Machine simulation."""

import math
from typing import Dict, List, Optional, Tuple

from PySide6.QtCore import QPointF, QRectF, Qt, Signal
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
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ..models.process_lifecycle import (
    ProcessInstanceModel,
    ProcessLifecycleState,
    ProcessTransitionModel,
)
from ..theme import (
    ACCENT,
    ACCENT_AMBER,
    ACCENT_CYAN,
    ACCENT_EMERALD,
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
    DANGER_BG,
    DANGER_TEXT,
    SUCCESS,
    SUCCESS_BG,
    SUCCESS_TEXT,
    TEXT_MUTED,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    WARNING,
    WARNING_BG,
    WARNING_TEXT,
)


class ProcessStateDiagramWidget(QWidget):
    """Custom QPainter rendering the authoritative 5-state process lifecycle diagram with live active state glow."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setMinimumHeight(280)
        self._current_state: Optional[str] = None
        self._last_transition: Optional[ProcessTransitionModel] = None

    @property
    def active_state(self) -> Optional[str]:
        return self._current_state

    @property
    def _active_state(self) -> Optional[str]:
        return self._current_state

    def set_active_state(
        self,
        state: Optional[object],
        transition: Optional[ProcessTransitionModel] = None,
        last_transition: Optional[ProcessTransitionModel] = None,
    ) -> None:
        if state is None:
            self._current_state = None
        elif hasattr(state, "value"):
            self._current_state = str(state.value)
        else:
            self._current_state = str(state)

        self._last_transition = transition if transition is not None else last_transition
        self.update()

    def clear(self) -> None:
        self._current_state = None
        self._last_transition = None
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()

        # Canvas background
        painter.fillRect(0, 0, w, h, QColor(BG_CARD))
        painter.setPen(QPen(QColor(BORDER), 1))
        painter.drawRoundedRect(0, 0, w - 1, h - 1, 8, 8)

        # Title
        painter.setFont(QFont("Segoe UI", 11, QFont.Bold))
        painter.setPen(QColor(TEXT_PRIMARY))
        painter.drawText(20, 26, "Process Lifecycle State Machine (5-State Model)")

        # State node geometry definitions
        # Centers for: New, Ready, Running, Waiting, Terminated
        # Layout:
        #  [New] ---> [Ready] <=====> [Running] ---> [Terminated]
        #               ^                 |
        #               |--- [Waiting] <--|
        cy = h * 0.45
        node_radius_x = 48
        node_radius_y = 26

        pos_new = QPointF(w * 0.12, cy)
        pos_ready = QPointF(w * 0.35, cy)
        pos_running = QPointF(w * 0.65, cy)
        pos_term = QPointF(w * 0.88, cy)
        pos_waiting = QPointF(w * 0.50, h * 0.78)

        nodes = {
            "New": pos_new,
            "Ready": pos_ready,
            "Running": pos_running,
            "Waiting": pos_waiting,
            "Terminated": pos_term,
        }

        # Draw transitions (arrows)
        # 1. New -> Ready (Admitted)
        self._draw_arrow(painter, pos_new, pos_ready, "Admitted", offset_y=0, is_active=self._is_recent("New", "Ready"))

        # 2. Ready -> Running (Scheduler Dispatch)
        self._draw_arrow(painter, pos_ready, pos_running, "Dispatch", offset_y=-16, is_active=self._is_recent("Ready", "Running"))

        # 3. Running -> Ready (Interrupt / Time slice expired)
        self._draw_arrow(painter, pos_running, pos_ready, "Interrupt", offset_y=16, is_active=self._is_recent("Running", "Ready"))

        # 4. Running -> Waiting (I/O or Event wait)
        self._draw_curved_arrow(painter, pos_running, pos_waiting, "I/O Wait", curve_down=True, is_active=self._is_recent("Running", "Waiting"))

        # 5. Waiting -> Ready (I/O or Event completion)
        self._draw_curved_arrow(painter, pos_waiting, pos_ready, "I/O Done", curve_down=True, is_active=self._is_recent("Waiting", "Ready"))

        # 6. Running -> Terminated (Exit)
        self._draw_arrow(painter, pos_running, pos_term, "Exit", offset_y=0, is_active=self._is_recent("Running", "Terminated"))

        # Draw state nodes
        for name, pos in nodes.items():
            is_active = (name.lower() == self._current_state.lower())
            self._draw_node(painter, pos, name, node_radius_x, node_radius_y, is_active)

    def _is_recent(self, from_s: str, to_s: str) -> bool:
        if not self._last_transition or not self._last_transition.success:
            return False
        return (
            self._last_transition.from_state.lower() == from_s.lower()
            and self._last_transition.to_state.lower() == to_s.lower()
        )

    def _draw_node(self, painter: QPainter, pos: QPointF, name: str, rx: float, ry: float, is_active: bool) -> None:
        rect = QRectF(pos.x() - rx, pos.y() - ry, rx * 2, ry * 2)

        # Glow / halo if active
        if is_active:
            glow_rect = QRectF(pos.x() - rx - 6, pos.y() - ry - 6, (rx + 6) * 2, (ry + 6) * 2)
            painter.setBrush(QColor(0, 229, 255, 30))
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(glow_rect, 14, 14)

            # Node fill
            grad = QLinearGradient(rect.topLeft(), rect.bottomRight())
            grad.setColorAt(0.0, QColor("#0369a1"))
            grad.setColorAt(1.0, QColor("#0284c7"))
            painter.setBrush(QBrush(grad))
            painter.setPen(QPen(QColor(ACCENT_CYAN), 2.5))
        else:
            painter.setBrush(QColor(BG_DARK))
            painter.setPen(QPen(QColor(BORDER_LIGHT), 1.5))

        painter.drawRoundedRect(rect, 10, 10)

        # Text
        painter.setFont(QFont("Segoe UI", 10, QFont.Bold if is_active else QFont.Normal))
        painter.setPen(QColor("#ffffff" if is_active else TEXT_SECONDARY))
        painter.drawText(rect, Qt.AlignCenter, name)

    def _draw_arrow(
        self,
        painter: QPainter,
        start: QPointF,
        end: QPointF,
        label: str,
        offset_y: float = 0,
        is_active: bool = False,
    ) -> None:
        p1 = QPointF(start.x() + 50, start.y() + offset_y)
        p2 = QPointF(end.x() - 50, end.y() + offset_y)

        pen = QPen(QColor(ACCENT_EMERALD if is_active else TEXT_MUTED), 2 if is_active else 1.2)
        if is_active:
            pen.setStyle(Qt.SolidLine)
        painter.setPen(pen)
        painter.drawLine(p1, p2)

        # Arrowhead
        dx = p2.x() - p1.x()
        dy = p2.y() - p1.y()
        angle = math.atan2(dy, dx)
        arrow_size = 7
        arrow_p1 = QPointF(
            p2.x() - arrow_size * math.cos(angle - math.pi / 6),
            p2.y() - arrow_size * math.sin(angle - math.pi / 6),
        )
        arrow_p2 = QPointF(
            p2.x() - arrow_size * math.cos(angle + math.pi / 6),
            p2.y() - arrow_size * math.sin(angle + math.pi / 6),
        )
        arrow_head = QPainterPath()
        arrow_head.moveTo(p2)
        arrow_head.lineTo(arrow_p1)
        arrow_head.lineTo(arrow_p2)
        arrow_head.closeSubpath()
        painter.setBrush(QColor(ACCENT_EMERALD if is_active else TEXT_MUTED))
        painter.drawPath(arrow_head)

        # Label
        mid_x = (p1.x() + p2.x()) / 2
        mid_y = (p1.y() + p2.y()) / 2 + (offset_y * 0.6) - 10
        painter.setFont(QFont("Segoe UI", 8, QFont.Bold if is_active else QFont.Normal))
        painter.setPen(QColor(SUCCESS_TEXT if is_active else TEXT_MUTED))
        painter.drawText(int(mid_x - 50), int(mid_y), 100, 16, Qt.AlignCenter, label)

    def _draw_curved_arrow(
        self,
        painter: QPainter,
        start: QPointF,
        end: QPointF,
        label: str,
        curve_down: bool = True,
        is_active: bool = False,
    ) -> None:
        path = QPainterPath()
        p1 = QPointF(start.x(), start.y() + 26)
        p2 = QPointF(end.x(), end.y() + 26)
        ctrl = QPointF((p1.x() + p2.x()) / 2, p1.y() + (35 if curve_down else -35))

        path.moveTo(p1)
        path.quadTo(ctrl, p2)

        pen = QPen(QColor(ACCENT_EMERALD if is_active else TEXT_MUTED), 2 if is_active else 1.2)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawPath(path)

        # Label
        painter.setFont(QFont("Segoe UI", 8, QFont.Bold if is_active else QFont.Normal))
        painter.setPen(QColor(SUCCESS_TEXT if is_active else TEXT_MUTED))
        painter.drawText(int(ctrl.x() - 40), int(ctrl.y() + 4), 80, 16, Qt.AlignCenter, label)


class ProcessTableWidget(QFrame):
    """Displays the process table with current state, metadata, and selection triggers."""

    process_selected = Signal(int)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("processTableCard")
        self.setStyleSheet(
            f"""
            QFrame#processTableCard {{
                background-color: {BG_CARD};
                border: 1px solid {BORDER};
                border-radius: 8px;
                padding: 10px;
            }}
            """
        )
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)

        title = QLabel("Process Control Block (PCB) Table")
        title.setStyleSheet(f"font-size: 12px; font-weight: bold; color: {TEXT_PRIMARY};")
        layout.addWidget(title)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["PID", "Arrival Time", "Burst Time", "Priority", "Current Lifecycle State"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setStyleSheet(
            f"""
            QTableWidget {{
                background-color: {BG_DARK};
                border: 1px solid {BORDER};
                border-radius: 6px;
                color: {TEXT_PRIMARY};
                gridline-color: {BORDER};
                font-family: monospace;
            }}
            QHeaderView::section {{
                background-color: {BG_ELEVATED};
                color: {TEXT_SECONDARY};
                font-size: 11px;
                font-weight: bold;
                padding: 4px;
                border: none;
                border-bottom: 1px solid {BORDER};
            }}
            """
        )
        self.table.itemSelectionChanged.connect(self._on_selection_changed)
        layout.addWidget(self.table)

    def populate(self, processes: List[ProcessInstanceModel], selected_pid: Optional[int] = None) -> None:
        self.table.blockSignals(True)
        self.table.setRowCount(len(processes))

        select_row = -1
        for row, p in enumerate(processes):
            pid_item = QTableWidgetItem(f"PID {p.pid}")
            pid_item.setTextAlignment(Qt.AlignCenter)
            pid_item.setData(Qt.UserRole, p.pid)

            arr_item = QTableWidgetItem(str(p.arrival_time))
            arr_item.setTextAlignment(Qt.AlignCenter)

            burst_item = QTableWidgetItem(f"{p.burst_time} units")
            burst_item.setTextAlignment(Qt.AlignCenter)

            prio_item = QTableWidgetItem(str(p.priority))
            prio_item.setTextAlignment(Qt.AlignCenter)

            state_item = QTableWidgetItem(p.state)
            state_item.setTextAlignment(Qt.AlignCenter)

            # State-specific badge coloring
            if p.state == "Running":
                state_item.setForeground(QColor(ACCENT_CYAN))
            elif p.state == "Ready":
                state_item.setForeground(QColor(ACCENT_EMERALD))
            elif p.state == "Waiting":
                state_item.setForeground(QColor(WARNING_TEXT))
            elif p.state == "Terminated":
                state_item.setForeground(QColor(TEXT_MUTED))
            else:
                state_item.setForeground(QColor(ACCENT_VIOLET))

            self.table.setItem(row, 0, pid_item)
            self.table.setItem(row, 1, arr_item)
            self.table.setItem(row, 2, burst_item)
            self.table.setItem(row, 3, prio_item)
            self.table.setItem(row, 4, state_item)

            if selected_pid is not None and p.pid == selected_pid:
                select_row = row

        self.table.blockSignals(False)
        if select_row >= 0:
            self.table.selectRow(select_row)

    def rowCount(self) -> int:
        return self.table.rowCount()

    def item(self, row: int, col: int) -> Optional[QTableWidgetItem]:
        return self.table.item(row, col)

    def clear(self) -> None:
        self.table.setRowCount(0)

    def _on_selection_changed(self) -> None:
        selected_rows = self.table.selectionModel().selectedRows()
        if selected_rows:
            row = selected_rows[0].row()
            pid_item = self.table.item(row, 0)
            if pid_item:
                pid = pid_item.data(Qt.UserRole)
                if pid is not None:
                    self.process_selected.emit(int(pid))


class ProcessTransitionHistoryWidget(QFrame):
    """Step-by-step transition history showing validation outcomes and reason explanations."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("transitionHistoryCard")
        self.setStyleSheet(
            f"""
            QFrame#transitionHistoryCard {{
                background-color: {BG_CARD};
                border: 1px solid {BORDER};
                border-radius: 8px;
                padding: 10px;
            }}
            """
        )
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)

        title = QLabel("Lifecycle State Transition Trace (Authoritative C++ Result)")
        title.setStyleSheet(f"font-size: 12px; font-weight: bold; color: {TEXT_PRIMARY};")
        layout.addWidget(title)

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "Step", "PID", "Transition Request", "Outcome", "Resulting State", "C++ Validation Details"
        ])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setStyleSheet(
            f"""
            QTableWidget {{
                background-color: {BG_DARK};
                border: 1px solid {BORDER};
                border-radius: 6px;
                color: {TEXT_PRIMARY};
                gridline-color: {BORDER};
                font-family: monospace;
            }}
            QHeaderView::section {{
                background-color: {BG_ELEVATED};
                color: {TEXT_SECONDARY};
                font-size: 11px;
                font-weight: bold;
                padding: 4px;
                border: none;
                border-bottom: 1px solid {BORDER};
            }}
            """
        )
        layout.addWidget(self.table)

    def populate(self, transitions: List[ProcessTransitionModel]) -> None:
        self.table.setRowCount(len(transitions))
        for row, tr in enumerate(transitions):
            step_item = QTableWidgetItem(f"#{row + 1}")
            step_item.setTextAlignment(Qt.AlignCenter)

            pid_item = QTableWidgetItem(f"PID {tr.pid}")
            pid_item.setTextAlignment(Qt.AlignCenter)

            req_item = QTableWidgetItem(f"{tr.from_state} ➔ {tr.requested_state}")
            req_item.setTextAlignment(Qt.AlignCenter)

            status_item = QTableWidgetItem("SUCCESS" if tr.success else "REJECTED")
            status_item.setTextAlignment(Qt.AlignCenter)
            status_item.setForeground(QColor(SUCCESS_TEXT if tr.success else DANGER_TEXT))

            to_item = QTableWidgetItem(tr.to_state)
            to_item.setTextAlignment(Qt.AlignCenter)

            msg_item = QTableWidgetItem(tr.message)

            self.table.setItem(row, 0, step_item)
            self.table.setItem(row, 1, pid_item)
            self.table.setItem(row, 2, req_item)
            self.table.setItem(row, 3, status_item)
            self.table.setItem(row, 4, to_item)
            self.table.setItem(row, 5, msg_item)

    def rowCount(self) -> int:
        return self.table.rowCount()

    def item(self, row: int, col: int) -> Optional[QTableWidgetItem]:
        return self.table.item(row, col)

    def clear(self) -> None:
        self.table.setRowCount(0)
