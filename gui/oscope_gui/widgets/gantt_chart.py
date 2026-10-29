"""Custom QPainter-based Gantt chart widget for CPU scheduling timeline.

Features vibrant process color tokens, diagonal hatch for idle intervals,
interactive hover highlights, precision time ticks, and educational tooltips.
"""

from typing import List, Optional

from PySide6.QtCore import QPoint, QRectF, Qt
from PySide6.QtGui import (
    QBrush,
    QColor,
    QFont,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
)
from PySide6.QtWidgets import QToolTip, QWidget

from ..models.scheduling import ExecutionSegmentModel
from ..theme import (
    BG_SURFACE,
    BORDER,
    BORDER_LIGHT,
    IDLE_BORDER_COLOR,
    IDLE_COLOR,
    IDLE_TEXT_COLOR,
    PROCESS_COLORS,
    TEXT_MUTED,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
)


class GanttChartWidget(QWidget):
    """Visualizes scheduling execution timeline segments with rich process blocks and interactive inspection."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setMinimumHeight(140)
        self.setSizeIncrement(10, 0)
        self.setMouseTracking(True)

        self._timeline: List[ExecutionSegmentModel] = []
        self._hovered_segment: Optional[ExecutionSegmentModel] = None
        self._segment_rects: List[tuple[QRectF, ExecutionSegmentModel]] = []

    def set_timeline(self, timeline: List[ExecutionSegmentModel]) -> None:
        """Update timeline data and trigger repaint."""
        self._timeline = timeline or []
        self._segment_rects.clear()
        self._hovered_segment = None
        self.update()

    def clear(self) -> None:
        self.set_timeline([])

    def mouseMoveEvent(self, event) -> None:
        pos = event.position()
        found = None
        for rect, seg in self._segment_rects:
            if rect.contains(pos):
                found = seg
                break

        if found:
            self.setCursor(Qt.PointingHandCursor)
        else:
            self.unsetCursor()

        if found != self._hovered_segment:
            self._hovered_segment = found
            if found:
                if found.is_idle:
                    tip = (
                        f"<b>CPU Idle State</b><br>"
                        f"Interval: <code>[{found.start_time} → {found.end_time}]</code><br>"
                        f"Idle Duration: <b>{found.duration} time units</b><br>"
                        f"<i>No ready processes were eligible for CPU time.</i>"
                    )
                else:
                    tip = (
                        f"<b>Process P{found.pid}</b><br>"
                        f"Execution Slice: <code>[{found.start_time} → {found.end_time}]</code><br>"
                        f"Allotted CPU Time: <b>{found.duration} unit(s)</b>"
                    )
                QToolTip.showText(self.mapToGlobal(event.pos()), tip, self)
            else:
                QToolTip.hideText()
            self.update()

        super().mouseMoveEvent(event)

    def leaveEvent(self, event) -> None:
        self._hovered_segment = None
        self.unsetCursor()
        QToolTip.hideText()
        self.update()
        super().leaveEvent(event)

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.TextAntialiasing, True)

        w = float(self.width())
        h = float(self.height())

        # Clean background surface
        painter.setPen(QPen(QColor(BORDER), 1))
        painter.setBrush(QBrush(QColor("#0e1422")))
        painter.drawRoundedRect(QRectF(1, 1, w - 2, h - 2), 8, 8)

        if not self._timeline:
            painter.setPen(QColor(TEXT_MUTED))
            font = QFont()
            font.setPointSize(11)
            painter.setFont(font)
            painter.drawText(
                QRectF(0, 0, w, h),
                Qt.AlignCenter,
                "CPU Timeline (Gantt Chart): Run a simulation to visualize real process execution intervals.",
            )
            return

        first_start = self._timeline[0].start_time
        final_end = self._timeline[-1].end_time
        span = max(1, final_end - first_start)

        margin_x = 36.0
        usable_w = max(60.0, w - (2 * margin_x))
        block_y = 24.0
        block_h = 44.0
        axis_y = block_y + block_h

        self._segment_rects.clear()

        # Collect time marks
        time_points = {first_start}
        for seg in self._timeline:
            time_points.add(seg.end_time)

        # Draw subtle vertical guide grid lines
        sorted_times = sorted(time_points)
        painter.setPen(QPen(QColor(BORDER), 1, Qt.DashLine))
        for t in sorted_times:
            tx = margin_x + ((t - first_start) / span) * usable_w
            painter.drawLine(int(tx), int(block_y - 4), int(tx), int(axis_y + 4))

        # Fonts
        title_font = QFont()
        title_font.setPointSize(10)
        title_font.setBold(True)

        sub_font = QFont()
        sub_font.setPointSize(8)
        sub_font.setBold(True)

        # Render Segments
        for seg in self._timeline:
            x0 = margin_x + ((seg.start_time - first_start) / span) * usable_w
            x1 = margin_x + ((seg.end_time - first_start) / span) * usable_w
            seg_w = max(4.0, x1 - x0)

            # Apply slight inner margin for clear segment boundaries
            gap = 1.0 if seg_w > 8 else 0.0
            rect = QRectF(x0 + gap, block_y, seg_w - (2 * gap), block_h)
            self._segment_rects.append((rect, seg))

            is_hovered = (seg == self._hovered_segment)

            if seg.is_idle:
                # Diagonal hatch pattern for idle interval
                painter.setPen(QPen(QColor(BORDER_LIGHT), 1))
                painter.setBrush(QBrush(QColor(IDLE_COLOR)))
                painter.drawRoundedRect(rect, 4, 4)

                # Draw diagonal hatch lines inside
                painter.save()
                clip_path = QPainterPath()
                clip_path.addRoundedRect(rect, 4, 4)
                painter.setClipPath(clip_path)

                hatch_pen = QPen(QColor("#334155"), 1.2)
                painter.setPen(hatch_pen)
                step = 8
                x_start = int(rect.left()) - int(block_h)
                x_end = int(rect.right()) + int(block_h)
                for hx in range(x_start, x_end, step):
                    painter.drawLine(hx, int(rect.top()), hx + int(block_h), int(rect.bottom()))
                painter.restore()

                text_color = QColor(IDLE_TEXT_COLOR)
                label = "IDLE"
            else:
                idx = (seg.pid - 1) % len(PROCESS_COLORS) if seg.pid is not None else 0
                base_color = QColor(PROCESS_COLORS[idx])

                # Subtle vertical gradient for premium finish
                gradient = QLinearGradient(rect.left(), rect.top(), rect.left(), rect.bottom())
                if is_hovered:
                    gradient.setColorAt(0.0, base_color.lighter(135))
                    gradient.setColorAt(1.0, base_color.lighter(110))
                    border_pen = QPen(QColor("#ffffff"), 1.8)
                else:
                    gradient.setColorAt(0.0, base_color.lighter(115))
                    gradient.setColorAt(1.0, base_color.darker(108))
                    border_pen = QPen(base_color.lighter(130), 1)

                painter.setPen(border_pen)
                painter.setBrush(QBrush(gradient))
                painter.drawRoundedRect(rect, 5, 5)

                text_color = QColor("#ffffff")
                label = f"P{seg.pid}"

            # Draw text inside block if space allows
            if seg_w > 26:
                painter.setPen(text_color)
                painter.setFont(title_font)

                if seg_w > 56:
                    painter.drawText(
                        QRectF(rect.left(), block_y + 4, rect.width(), block_h / 2),
                        Qt.AlignCenter,
                        label,
                    )
                    painter.setFont(sub_font)
                    painter.setPen(text_color if seg.is_idle else QColor(255, 255, 255, 210))
                    painter.drawText(
                        QRectF(rect.left(), block_y + (block_h / 2) - 1, rect.width(), (block_h / 2) - 2),
                        Qt.AlignCenter,
                        f"{seg.duration}u",
                    )
                else:
                    painter.drawText(rect, Qt.AlignCenter, label)

        # Draw Axis and Time Markers
        painter.setPen(QPen(QColor(BORDER_LIGHT), 1.5))
        painter.drawLine(int(margin_x), int(axis_y + 4), int(margin_x + usable_w), int(axis_y + 4))

        axis_font = QFont()
        axis_font.setPointSize(9)
        axis_font.setBold(True)
        painter.setFont(axis_font)

        last_drawn_x = -999.0

        for t in sorted_times:
            tx = margin_x + ((t - first_start) / span) * usable_w
            if tx - last_drawn_x >= 24 or t == sorted_times[-1] or t == sorted_times[0]:
                painter.setPen(QPen(QColor(BORDER_LIGHT), 1.2))
                painter.drawLine(int(tx), int(axis_y + 4), int(tx), int(axis_y + 9))

                painter.setPen(QColor(TEXT_PRIMARY))
                painter.drawText(
                    QRectF(tx - 20, axis_y + 11, 40, 18),
                    Qt.AlignHCenter | Qt.AlignTop,
                    str(t),
                )
                last_drawn_x = tx
