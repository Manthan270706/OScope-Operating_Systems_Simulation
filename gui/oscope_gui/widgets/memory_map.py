"""Custom QPainter-based Memory Map visualization widget for dynamic memory partitions."""

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

from ..models.memory import MemoryBlockModel
from ..theme import (
    ACCENT_CYAN,
    ACCENT_EMERALD,
    ACCENT_HOVER,
    BORDER,
    BORDER_LIGHT,
    PROCESS_COLORS,
    TEXT_MUTED,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
)


class MemoryMapWidget(QWidget):
    """Visualizes contiguous memory address space with allocated blocks, free holes, and address ticks."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setMinimumHeight(150)
        self.setSizeIncrement(10, 0)
        self.setMouseTracking(True)

        self._total_memory: int = 1000
        self._blocks: List[MemoryBlockModel] = []
        self._hovered_block: Optional[MemoryBlockModel] = None
        self._block_rects: List[tuple[QRectF, MemoryBlockModel]] = []

    def set_memory_state(self, total_memory: int, blocks: List[MemoryBlockModel]) -> None:
        """Update memory layout data and repaint."""
        self._total_memory = max(1, total_memory)
        self._blocks = blocks or []
        self._block_rects.clear()
        self._hovered_block = None
        self.update()

    def clear(self) -> None:
        self.set_memory_state(1000, [])

    def mouseMoveEvent(self, event) -> None:
        pos = event.position()
        found = None
        for rect, blk in self._block_rects:
            if rect.contains(pos):
                found = blk
                break

        if found:
            self.setCursor(Qt.PointingHandCursor)
        else:
            self.unsetCursor()

        if found != self._hovered_block:
            self._hovered_block = found
            if found:
                pct = (found.size / self._total_memory) * 100.0 if self._total_memory > 0 else 0.0
                if found.is_allocated:
                    pid_text = f"P{found.process_id}" if found.process_id is not None else "N/A"
                    alloc_id_text = str(found.allocation_id) if found.allocation_id is not None else "N/A"
                    tip = (
                        f"<b>Memory Block #{found.block_index} [Allocated]</b><br>"
                        f"Address Range: <code>[{found.start_address} → {found.end_address}]</code><br>"
                        f"Size: <b>{found.size} bytes</b> ({pct:.1f}% of memory pool)<br>"
                        f"Assigned Process: <b>{pid_text}</b><br>"
                        f"Internal Allocation ID: <b>{alloc_id_text}</b>"
                    )
                else:
                    tip = (
                        f"<b>Memory Block #{found.block_index} [Free Space]</b><br>"
                        f"Address Range: <code>[{found.start_address} → {found.end_address}]</code><br>"
                        f"Available Capacity: <b>{found.size} bytes</b> ({pct:.1f}% of pool)<br>"
                        f"<i>Eligible for allocation by fitting strategies.</i>"
                    )
                QToolTip.showText(self.mapToGlobal(event.pos()), tip, self)
            else:
                QToolTip.hideText()
            self.update()

        super().mouseMoveEvent(event)

    def leaveEvent(self, event) -> None:
        self._hovered_block = None
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

        # Outer canvas
        painter.setPen(QPen(QColor(BORDER), 1))
        painter.setBrush(QBrush(QColor("#0e1422")))
        painter.drawRoundedRect(QRectF(1, 1, w - 2, h - 2), 8, 8)

        if not self._blocks:
            painter.setPen(QColor(TEXT_MUTED))
            font = QFont()
            font.setPointSize(11)
            painter.setFont(font)
            painter.drawText(
                QRectF(0, 0, w, h),
                Qt.AlignCenter,
                "Memory Map: Execute an allocation workload to visualize contiguous partitions and free holes.",
            )
            return

        margin_x = 36.0
        usable_w = max(60.0, w - (2 * margin_x))
        bar_y = 28.0
        bar_h = 50.0
        axis_y = bar_y + bar_h

        self._block_rects.clear()

        # Fonts
        title_font = QFont()
        title_font.setPointSize(10)
        title_font.setBold(True)

        sub_font = QFont()
        sub_font.setPointSize(8)
        sub_font.setBold(True)

        address_points = {0, self._total_memory}

        # Draw partitions
        for blk in self._blocks:
            address_points.add(blk.start_address)
            address_points.add(blk.end_address)

            x0 = margin_x + (blk.start_address / self._total_memory) * usable_w
            x1 = margin_x + (blk.end_address / self._total_memory) * usable_w
            seg_w = max(3.0, x1 - x0)

            gap = 1.0 if seg_w > 6 else 0.0
            rect = QRectF(x0 + gap, bar_y, seg_w - (2 * gap), bar_h)
            self._block_rects.append((rect, blk))

            is_hovered = (blk == self._hovered_block)

            if blk.is_allocated:
                # Cyan/Sky gradient for allocated process partitions
                pid_idx = (blk.process_id - 1) % len(PROCESS_COLORS) if blk.process_id is not None and blk.process_id > 0 else 0
                base_color = QColor(PROCESS_COLORS[pid_idx])

                gradient = QLinearGradient(rect.left(), rect.top(), rect.left(), rect.bottom())
                if is_hovered:
                    gradient.setColorAt(0.0, base_color.lighter(135))
                    gradient.setColorAt(1.0, base_color.lighter(110))
                    border_pen = QPen(QColor("#ffffff"), 1.8)
                else:
                    gradient.setColorAt(0.0, base_color.lighter(115))
                    gradient.setColorAt(1.0, base_color.darker(110))
                    border_pen = QPen(base_color.lighter(130), 1)

                painter.setPen(border_pen)
                painter.setBrush(QBrush(gradient))
                painter.drawRoundedRect(rect, 4, 4)

                # Text label
                if seg_w > 28:
                    painter.setPen(QColor("#ffffff"))
                    painter.setFont(title_font)
                    label = f"P{blk.process_id}" if blk.process_id is not None else f"#{blk.allocation_id}"

                    if seg_w > 60:
                        painter.drawText(
                            QRectF(rect.left(), bar_y + 6, rect.width(), bar_h / 2),
                            Qt.AlignCenter,
                            label,
                        )
                        painter.setFont(sub_font)
                        painter.setPen(QColor(255, 255, 255, 210))
                        painter.drawText(
                            QRectF(rect.left(), bar_y + (bar_h / 2) - 1, rect.width(), (bar_h / 2) - 2),
                            Qt.AlignCenter,
                            f"{blk.size} B",
                        )
                    else:
                        painter.drawText(rect, Qt.AlignCenter, label)

            else:
                # Emerald/Mint gradient for free holes
                free_color = QColor("#065f46")
                gradient = QLinearGradient(rect.left(), rect.top(), rect.left(), rect.bottom())
                if is_hovered:
                    gradient.setColorAt(0.0, free_color.lighter(140))
                    gradient.setColorAt(1.0, free_color.lighter(120))
                    border_pen = QPen(QColor(ACCENT_EMERALD), 1.8)
                else:
                    gradient.setColorAt(0.0, free_color.lighter(115))
                    gradient.setColorAt(1.0, free_color.darker(110))
                    border_pen = QPen(QColor("#10b981"), 1)

                painter.setPen(border_pen)
                painter.setBrush(QBrush(gradient))
                painter.drawRoundedRect(rect, 4, 4)

                # Text label
                if seg_w > 28:
                    painter.setPen(QColor("#34d399"))
                    painter.setFont(title_font)
                    if seg_w > 60:
                        painter.drawText(
                            QRectF(rect.left(), bar_y + 6, rect.width(), bar_h / 2),
                            Qt.AlignCenter,
                            "FREE",
                        )
                        painter.setFont(sub_font)
                        painter.setPen(QColor(52, 211, 153, 220))
                        painter.drawText(
                            QRectF(rect.left(), bar_y + (bar_h / 2) - 1, rect.width(), (bar_h / 2) - 2),
                            Qt.AlignCenter,
                            f"{blk.size} B",
                        )
                    else:
                        painter.drawText(rect, Qt.AlignCenter, "FREE")

        # Draw Address Axis and Markers
        painter.setPen(QPen(QColor(BORDER_LIGHT), 1.5))
        painter.drawLine(int(margin_x), int(axis_y + 4), int(margin_x + usable_w), int(axis_y + 4))

        axis_font = QFont()
        axis_font.setPointSize(9)
        axis_font.setBold(True)
        painter.setFont(axis_font)

        sorted_addrs = sorted(address_points)
        last_drawn_x = -999.0

        for addr in sorted_addrs:
            tx = margin_x + (addr / self._total_memory) * usable_w
            if tx - last_drawn_x >= 28 or addr == sorted_addrs[-1] or addr == sorted_addrs[0]:
                painter.setPen(QPen(QColor(BORDER_LIGHT), 1.2))
                painter.drawLine(int(tx), int(axis_y + 4), int(tx), int(axis_y + 9))

                painter.setPen(QColor(TEXT_PRIMARY))
                painter.drawText(
                    QRectF(tx - 25, axis_y + 11, 50, 18),
                    Qt.AlignHCenter | Qt.AlignTop,
                    str(addr),
                )
                last_drawn_x = tx
