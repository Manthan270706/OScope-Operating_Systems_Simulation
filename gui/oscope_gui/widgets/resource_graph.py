"""Interactive Resource Allocation Graph & Sequence Flow Widget for OScope Deadlock Management."""

from typing import Dict, List, Optional, Tuple, Union

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
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QSizePolicy,
    QToolTip,
    QVBoxLayout,
    QWidget,
)

from ..models.deadlock import (
    DeadlockDetectionResultModel,
    DeadlockRequestResultModel,
    DeadlockSafetyResultModel,
)
from ..theme import (
    ACCENT,
    ACCENT_AMBER,
    ACCENT_EMERALD,
    ACCENT_ROSE,
    ACCENT_VIOLET,
    BG_CANVAS,
    BG_ELEVATED,
    BG_SURFACE,
    BORDER,
    FONT_FAMILY,
    TEXT_MUTED,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
)

AnyDeadlockResult = Union[
    DeadlockSafetyResultModel,
    DeadlockRequestResultModel,
    DeadlockDetectionResultModel,
]


class SequenceFlowBar(QFrame):
    """Horizontal banner presenting the step-by-step safe execution sequence or deadlock alert."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("SequenceFlowBar")
        self.setStyleSheet(
            f"""
            QFrame#SequenceFlowBar {{
                background-color: {BG_SURFACE};
                border: 1px solid {BORDER};
                border-radius: 8px;
                padding: 4px;
            }}
            """
        )
        bar_layout = QHBoxLayout(self)
        bar_layout.setContentsMargins(12, 10, 12, 10)
        bar_layout.setSpacing(8)

        self.lbl_title = QLabel("Execution Order:")
        self.lbl_title.setStyleSheet(f"font-size: 11px; font-weight: 700; color: {TEXT_MUTED}; letter-spacing: 0.5px;")
        bar_layout.addWidget(self.lbl_title)

        self.flow_container = QHBoxLayout()
        self.flow_container.setSpacing(6)
        bar_layout.addLayout(self.flow_container)
        bar_layout.addStretch()

        self._show_empty()

    def _show_empty(self) -> None:
        self._clear_flow()
        lbl = QLabel("Run Banker's Safety or Deadlock Detection to inspect execution flow.")
        lbl.setStyleSheet(f"font-size: 12px; color: {TEXT_MUTED}; font-style: italic;")
        self.flow_container.addWidget(lbl)

    def _clear_flow(self) -> None:
        while self.flow_container.count() > 0:
            item = self.flow_container.takeAt(0)
            widget = item.widget()
            if widget:
                widget.hide()
                widget.setParent(None)
                widget.deleteLater()

    def update_result(self, result: Optional[AnyDeadlockResult]) -> None:
        self._clear_flow()
        if not result:
            self._show_empty()
            return

        if isinstance(result, DeadlockSafetyResultModel):
            if result.is_safe and result.safe_sequence:
                self.lbl_title.setText("SAFE SEQUENCE:")
                self.lbl_title.setStyleSheet(f"font-size: 11px; font-weight: 700; color: {ACCENT_EMERALD};")
                for idx, pid in enumerate(result.safe_sequence):
                    pill = QLabel(f"Step {idx + 1}: P{pid}")
                    pill.setStyleSheet(
                        f"""
                        background-color: rgba(16, 185, 129, 0.15);
                        color: {ACCENT_EMERALD};
                        border: 1px solid rgba(16, 185, 129, 0.4);
                        border-radius: 5px;
                        font-weight: 700;
                        font-size: 11px;
                        padding: 4px 8px;
                        """
                    )
                    self.flow_container.addWidget(pill)
                    if idx + 1 < len(result.safe_sequence):
                        arrow = QLabel("➔")
                        arrow.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 12px;")
                        self.flow_container.addWidget(arrow)
            else:
                self.lbl_title.setText("UNSAFE STATE:")
                self.lbl_title.setStyleSheet(f"font-size: 11px; font-weight: 700; color: {ACCENT_ROSE};")
                alert = QLabel(f"No safe sequence found. Blocked processes: {result.blocked_str}")
                alert.setStyleSheet(
                    f"""
                    background-color: rgba(244, 63, 94, 0.15);
                    color: {ACCENT_ROSE};
                    border: 1px solid rgba(244, 63, 94, 0.4);
                    border-radius: 5px;
                    font-weight: 600;
                    font-size: 11px;
                    padding: 4px 10px;
                    """
                )
                self.flow_container.addWidget(alert)

        elif isinstance(result, DeadlockRequestResultModel):
            if result.granted and result.safe_sequence:
                self.lbl_title.setText("REQUEST GRANTED:")
                self.lbl_title.setStyleSheet(f"font-size: 11px; font-weight: 700; color: {ACCENT_EMERALD};")
                for idx, pid in enumerate(result.safe_sequence):
                    pill = QLabel(f"Step {idx + 1}: P{pid}")
                    pill.setStyleSheet(
                        f"""
                        background-color: rgba(16, 185, 129, 0.15);
                        color: {ACCENT_EMERALD};
                        border: 1px solid rgba(16, 185, 129, 0.4);
                        border-radius: 5px;
                        font-weight: 700;
                        font-size: 11px;
                        padding: 4px 8px;
                        """
                    )
                    self.flow_container.addWidget(pill)
                    if idx + 1 < len(result.safe_sequence):
                        arrow = QLabel("➔")
                        arrow.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 12px;")
                        self.flow_container.addWidget(arrow)
            else:
                self.lbl_title.setText("REQUEST DENIED:")
                self.lbl_title.setStyleSheet(f"font-size: 11px; font-weight: 700; color: {ACCENT_ROSE};")
                alert = QLabel(f"Request denied: {result.message}")
                alert.setStyleSheet(
                    f"""
                    background-color: rgba(244, 63, 94, 0.15);
                    color: {ACCENT_ROSE};
                    border: 1px solid rgba(244, 63, 94, 0.4);
                    border-radius: 5px;
                    font-weight: 600;
                    font-size: 11px;
                    padding: 4px 10px;
                    """
                )
                self.flow_container.addWidget(alert)

        elif isinstance(result, DeadlockDetectionResultModel):
            if result.is_deadlocked:
                self.lbl_title.setText("DEADLOCK DETECTED:")
                self.lbl_title.setStyleSheet(f"font-size: 11px; font-weight: 700; color: {ACCENT_ROSE};")
                alert = QLabel(f"Deadlocked processes: {result.deadlocked_str}")
                alert.setStyleSheet(
                    f"""
                    background-color: rgba(244, 63, 94, 0.15);
                    color: {ACCENT_ROSE};
                    border: 1px solid rgba(244, 63, 94, 0.4);
                    border-radius: 5px;
                    font-weight: 700;
                    font-size: 11px;
                    padding: 4px 10px;
                    """
                )
                self.flow_container.addWidget(alert)
            else:
                self.lbl_title.setText("NO DEADLOCK:")
                self.lbl_title.setStyleSheet(f"font-size: 11px; font-weight: 700; color: {ACCENT_EMERALD};")
                alert = QLabel("All active processes can acquire pending resources and complete safely.")
                alert.setStyleSheet(
                    f"""
                    background-color: rgba(16, 185, 129, 0.15);
                    color: {ACCENT_EMERALD};
                    border: 1px solid rgba(16, 185, 129, 0.4);
                    border-radius: 5px;
                    font-weight: 600;
                    font-size: 11px;
                    padding: 4px 10px;
                    """
                )
                self.flow_container.addWidget(alert)


class GraphCanvas(QWidget):
    """Custom QPainter canvas rendering Process nodes, Resource nodes, Allocation and Request edges."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setMouseTracking(True)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.MinimumExpanding)
        self.setMinimumHeight(420)

        self.result: Optional[AnyDeadlockResult] = None
        self.hovered_node: Optional[Tuple[str, int]] = None  # ("P", index) or ("R", index)
        self.node_rects: Dict[Tuple[str, int], QRectF] = {}

    def set_result(self, result: Optional[AnyDeadlockResult]) -> None:
        self.result = result
        self.hovered_node = None
        if self.result:
            count = max(self.result.num_processes, self.result.num_resources, 3)
            self.setMinimumHeight(max(400, count * 75 + 60))
        else:
            self.setMinimumHeight(350)
        self.update()

    def mouseMoveEvent(self, event) -> None:
        pos = event.position()
        found: Optional[Tuple[str, int]] = None
        tooltip_text = ""

        for key, rect in self.node_rects.items():
            if rect.contains(pos):
                found = key
                tag, idx = key
                if self.result:
                    if tag == "P":
                        alloc_str = ", ".join(str(x) for x in self.result.allocation[idx])
                        if hasattr(self.result, "need"):
                            demand_str = f"Need: [{', '.join(str(x) for x in self.result.need[idx])}]"
                        elif hasattr(self.result, "request_matrix"):
                            demand_str = f"Pending Request: [{', '.join(str(x) for x in self.result.request_matrix[idx])}]"
                        else:
                            demand_str = ""
                        tooltip_text = f"Process P{idx}\nAllocated: [{alloc_str}]\n{demand_str}"
                    elif tag == "R":
                        avail_count = self.result.available[idx]
                        allocated_total = sum(self.result.allocation[p][idx] for p in range(self.result.num_processes))
                        tooltip_text = f"Resource R{idx}\nAvailable: {avail_count}\nAllocated: {allocated_total}\nTotal Units: {avail_count + allocated_total}"
                break

        if found != self.hovered_node:
            self.hovered_node = found
            self.update()

        if tooltip_text:
            QToolTip.showText(event.globalPosition().toPoint(), tooltip_text, self)
        else:
            QToolTip.hideText()

        super().mouseMoveEvent(event)

    def leaveEvent(self, event) -> None:
        self.hovered_node = None
        self.update()
        super().leaveEvent(event)

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Background
        painter.fillRect(self.rect(), QColor(BG_CANVAS))

        if not self.result or self.result.num_processes == 0 or self.result.num_resources == 0:
            self._paint_empty_state(painter)
            return

        w = self.width()
        h = self.height()
        num_p = self.result.num_processes
        num_r = self.result.num_resources

        self.node_rects.clear()

        # Responsive geometry setup
        node_w = max(110, min(170, int((w - 120) * 0.28)))
        left_x = 36
        right_x = max(left_x + node_w + 60, w - node_w - 36)
        node_h = 56

        p_spacing = (h - 60) / max(1, num_p)
        r_spacing = (h - 60) / max(1, num_r)

        p_centers: Dict[int, QPointF] = {}
        r_centers: Dict[int, QPointF] = {}

        # 1. Calculate and store node positions
        for i in range(num_p):
            top_y = 30 + i * p_spacing + (p_spacing - node_h) / 2
            rect = QRectF(left_x, top_y, node_w, node_h)
            self.node_rects[("P", i)] = rect
            p_centers[i] = QPointF(left_x + node_w, top_y + node_h / 2)

        for j in range(num_r):
            top_y = 30 + j * r_spacing + (r_spacing - node_h) / 2
            rect = QRectF(right_x, top_y, node_w, node_h)
            self.node_rects[("R", j)] = rect
            r_centers[j] = QPointF(right_x, top_y + node_h / 2)

        # 2. Draw Edges
        self._paint_edges(painter, p_centers, r_centers)

        # 3. Draw Process Nodes
        self._paint_process_nodes(painter, num_p)

        # 4. Draw Resource Nodes
        self._paint_resource_nodes(painter, num_r)

    def _paint_empty_state(self, painter: QPainter) -> None:
        painter.setPen(QColor(TEXT_MUTED))
        painter.setFont(QFont(FONT_FAMILY, 12))
        painter.drawText(
            self.rect(),
            Qt.AlignCenter,
            "No deadlock analysis executed yet.\nConfigure processes and resources above and click 'Run Analysis'.",
        )

    def _paint_edges(
        self,
        painter: QPainter,
        p_centers: Dict[int, QPointF],
        r_centers: Dict[int, QPointF],
    ) -> None:
        if not self.result:
            return

        num_p = self.result.num_processes
        num_r = self.result.num_resources

        # Edges:
        # 1. Allocation: R -> P (solid cyan line with badge)
        # 2. Demand/Need/Request: P -> R (dashed amber line with badge)
        for i in range(num_p):
            for j in range(num_r):
                alloc_val = 0
                if i < len(self.result.allocation) and j < len(self.result.allocation[i]):
                    alloc_val = self.result.allocation[i][j]

                demand_val = 0
                if hasattr(self.result, "need") and i < len(self.result.need) and j < len(self.result.need[i]):
                    demand_val = self.result.need[i][j]
                elif hasattr(self.result, "request_matrix") and i < len(self.result.request_matrix) and j < len(self.result.request_matrix[i]):
                    demand_val = self.result.request_matrix[i][j]

                p_pt = p_centers[i]
                r_pt = r_centers[j]

                is_p_hovered = self.hovered_node == ("P", i)
                is_r_hovered = self.hovered_node == ("R", j)
                is_connected = is_p_hovered or is_r_hovered
                has_hover = self.hovered_node is not None

                # Allocation Edge: Rj -> Pi (resources held by Pi)
                if alloc_val > 0:
                    alpha = 255 if is_connected else (60 if has_hover else 160)
                    pen = QPen(QColor(56, 189, 248, alpha), 1.8 if is_connected else 1.2, Qt.SolidLine)
                    painter.setPen(pen)

                    # Curve path from R to P
                    path = QPainterPath()
                    ctrl_dx = (r_pt.x() - p_pt.x()) * 0.4
                    path.moveTo(r_pt.x(), r_pt.y() - 6)
                    path.cubicTo(
                        r_pt.x() - ctrl_dx,
                        r_pt.y() - 6,
                        p_pt.x() + ctrl_dx,
                        p_pt.y() - 6,
                        p_pt.x(),
                        p_pt.y() - 6,
                    )
                    painter.drawPath(path)

                    # Badge at 30% towards P
                    mid_x = r_pt.x() * 0.35 + p_pt.x() * 0.65
                    mid_y = (r_pt.y() - 6) * 0.35 + (p_pt.y() - 6) * 0.65
                    self._draw_edge_badge(painter, mid_x, mid_y, f"{alloc_val}", QColor(56, 189, 248), alpha)

                # Need/Request Edge: Pi -> Rj (resources requested by Pi)
                if demand_val > 0:
                    alpha = 255 if is_connected else (60 if has_hover else 140)
                    edge_color = QColor(245, 158, 11)  # Amber
                    if isinstance(self.result, DeadlockDetectionResultModel) and self.result.is_deadlocked:
                        if i in self.result.deadlocked_processes:
                            edge_color = QColor(244, 63, 94)  # Rose for deadlocked request!

                    pen = QPen(QColor(edge_color.red(), edge_color.green(), edge_color.blue(), alpha), 1.8 if is_connected else 1.1, Qt.DashLine)
                    painter.setPen(pen)

                    path = QPainterPath()
                    ctrl_dx = (r_pt.x() - p_pt.x()) * 0.4
                    path.moveTo(p_pt.x(), p_pt.y() + 6)
                    path.cubicTo(
                        p_pt.x() + ctrl_dx,
                        p_pt.y() + 6,
                        r_pt.x() - ctrl_dx,
                        r_pt.y() + 6,
                        r_pt.x(),
                        r_pt.y() + 6,
                    )
                    painter.drawPath(path)

                    # Badge at 65% towards R
                    mid_x = p_pt.x() * 0.35 + r_pt.x() * 0.65
                    mid_y = (p_pt.y() + 6) * 0.35 + (r_pt.y() + 6) * 0.65
                    self._draw_edge_badge(painter, mid_x, mid_y, f"{demand_val}", edge_color, alpha)

    def _draw_edge_badge(
        self,
        painter: QPainter,
        x: float,
        y: float,
        text: str,
        color: QColor,
        alpha: int,
    ) -> None:
        badge_w = 20
        badge_h = 16
        rect = QRectF(x - badge_w / 2, y - badge_h / 2, badge_w, badge_h)

        bg_col = QColor(BG_SURFACE)
        bg_col.setAlpha(alpha)
        border_col = QColor(color)
        border_col.setAlpha(alpha)

        painter.setBrush(QBrush(bg_col))
        painter.setPen(QPen(border_col, 1))
        painter.drawRoundedRect(rect, 4, 4)

        text_col = QColor(color)
        text_col.setAlpha(alpha)
        painter.setPen(text_col)
        painter.setFont(QFont(FONT_FAMILY, 9, QFont.Bold))
        painter.drawText(rect, Qt.AlignCenter, text)

    def _paint_process_nodes(self, painter: QPainter, num_p: int) -> None:
        for i in range(num_p):
            rect = self.node_rects[("P", i)]
            is_hovered = self.hovered_node == ("P", i)

            # Determine status
            is_deadlocked = False
            is_safe = False

            if isinstance(self.result, DeadlockSafetyResultModel):
                if self.result.is_safe and i in self.result.safe_sequence:
                    is_safe = True
                elif not self.result.is_safe and i in self.result.blocked_processes:
                    is_deadlocked = True
            elif isinstance(self.result, DeadlockRequestResultModel):
                if self.result.granted and i in self.result.safe_sequence:
                    is_safe = True
            elif isinstance(self.result, DeadlockDetectionResultModel):
                if self.result.is_deadlocked and i in self.result.deadlocked_processes:
                    is_deadlocked = True
                elif not self.result.is_deadlocked or i in self.result.finished_processes:
                    is_safe = True

            # Card background and border
            if is_deadlocked:
                border_color = QColor(ACCENT_ROSE)
                badge_bg = QColor(244, 63, 94, 30)
                status_text = "BLOCKED"
                status_color = QColor(ACCENT_ROSE)
            elif is_safe:
                border_color = QColor(ACCENT_EMERALD)
                badge_bg = QColor(16, 185, 129, 30)
                status_text = "SAFE"
                status_color = QColor(ACCENT_EMERALD)
            else:
                border_color = QColor(ACCENT)
                badge_bg = QColor(56, 189, 248, 30)
                status_text = "ACTIVE"
                status_color = QColor(ACCENT)

            if is_hovered:
                card_bg = QColor(BG_ELEVATED)
                pen = QPen(border_color, 2)
            else:
                card_bg = QColor(BG_SURFACE)
                pen = QPen(border_color if (is_deadlocked or is_safe) else QColor(BORDER), 1.2)

            painter.setBrush(QBrush(card_bg))
            painter.setPen(pen)
            painter.drawRoundedRect(rect, 8, 8)

            # Process Name Emblem
            emblem_rect = QRectF(rect.x() + 10, rect.y() + 10, 36, 36)
            painter.setBrush(QBrush(badge_bg))
            painter.setPen(QPen(border_color, 1))
            painter.drawRoundedRect(emblem_rect, 6, 6)

            painter.setPen(QColor(TEXT_PRIMARY))
            painter.setFont(QFont(FONT_FAMILY, 12, QFont.Bold))
            painter.drawText(emblem_rect, Qt.AlignCenter, f"P{i}")

            # Process Details & Status Badge
            text_x = rect.x() + 54
            text_w = max(45, int(rect.width() - 58))
            painter.setPen(status_color)
            painter.setFont(QFont(FONT_FAMILY, 9, QFont.Bold))
            painter.drawText(QRectF(text_x, rect.y() + 10, text_w, 16), Qt.AlignLeft | Qt.AlignVCenter, status_text)

            # Sub-text with allocation snapshot
            alloc_brief = ",".join(str(x) for x in self.result.allocation[i]) if i < len(self.result.allocation) else "—"
            painter.setPen(QColor(TEXT_SECONDARY))
            painter.setFont(QFont(FONT_FAMILY, 9))
            painter.drawText(
                QRectF(text_x, rect.y() + 28, text_w, 16),
                Qt.AlignLeft | Qt.AlignVCenter,
                f"Alloc: [{alloc_brief}]",
            )

    def _paint_resource_nodes(self, painter: QPainter, num_r: int) -> None:
        for j in range(num_r):
            rect = self.node_rects[("R", j)]
            is_hovered = self.hovered_node == ("R", j)

            border_color = QColor(ACCENT_AMBER)
            if is_hovered:
                card_bg = QColor(BG_ELEVATED)
                pen = QPen(border_color, 2)
            else:
                card_bg = QColor(BG_SURFACE)
                pen = QPen(QColor(BORDER), 1.2)

            painter.setBrush(QBrush(card_bg))
            painter.setPen(pen)
            painter.drawRoundedRect(rect, 8, 8)

            # Resource Emblem
            emblem_rect = QRectF(rect.x() + 10, rect.y() + 10, 36, 36)
            painter.setBrush(QBrush(QColor(245, 158, 11, 30)))
            painter.setPen(QPen(border_color, 1))
            painter.drawRoundedRect(emblem_rect, 6, 6)

            res_label = chr(65 + j) if j < 26 else f"R{j}"
            painter.setPen(QColor(TEXT_PRIMARY))
            painter.setFont(QFont(FONT_FAMILY, 12, QFont.Bold))
            painter.drawText(emblem_rect, Qt.AlignCenter, res_label)

            # Resource Details
            text_x = rect.x() + 54
            text_w = max(45, int(rect.width() - 58))
            avail_val = self.result.available[j] if j < len(self.result.available) else 0

            painter.setPen(QColor(ACCENT_AMBER))
            painter.setFont(QFont(FONT_FAMILY, 10, QFont.Bold))
            painter.drawText(
                QRectF(text_x, rect.y() + 10, text_w, 16),
                Qt.AlignLeft | Qt.AlignVCenter,
                f"Avail: {avail_val}",
            )

            allocated_total = sum(self.result.allocation[p][j] for p in range(self.result.num_processes))
            painter.setPen(QColor(TEXT_SECONDARY))
            painter.setFont(QFont(FONT_FAMILY, 9))
            painter.drawText(
                QRectF(text_x, rect.y() + 28, text_w, 16),
                Qt.AlignLeft | Qt.AlignVCenter,
                f"Held: {allocated_total} (Total {avail_val + allocated_total})",
            )


class ResourceGraphWidget(QWidget):
    """Complete visual component including the Safe Sequence Flow Bar, Resource Allocation Canvas, and Legend."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        # 1. Top sequence flow / deadlock alert bar
        self.flow_bar = SequenceFlowBar(self)
        layout.addWidget(self.flow_bar)

        # 2. Interactive visual canvas
        self.canvas = GraphCanvas(self)
        layout.addWidget(self.canvas)

        # 3. Legend Bar
        legend_frame = QFrame()
        legend_frame.setObjectName("GraphLegendFrame")
        legend_frame.setStyleSheet(
            f"""
            QFrame#GraphLegendFrame {{
                background-color: {BG_SURFACE};
                border: 1px solid {BORDER};
                border-radius: 6px;
                padding: 4px;
            }}
            """
        )
        l_layout = QGridLayout(legend_frame)
        l_layout.setContentsMargins(12, 6, 12, 6)
        l_layout.setHorizontalSpacing(20)
        l_layout.setVerticalSpacing(6)

        legend_items = [
            ("Process Node (P)", ACCENT, "rectangle"),
            ("Resource Node (R)", ACCENT_AMBER, "rectangle"),
            ("Allocated (Held)", ACCENT, "solid"),
            ("Need / Pending Request", ACCENT_AMBER, "dashed"),
            ("Safe / Finished", ACCENT_EMERALD, "badge"),
            ("Deadlocked / Blocked", ACCENT_ROSE, "badge"),
        ]

        for idx, (text, col, style) in enumerate(legend_items):
            item_box = QHBoxLayout()
            item_box.setSpacing(6)
            icon = QLabel()
            icon.setFixedSize(14, 10)
            if style == "solid":
                icon.setStyleSheet(f"background-color: {col}; border-radius: 2px;")
            elif style == "dashed":
                icon.setStyleSheet(f"border-top: 2px dashed {col}; margin-top: 4px;")
            else:
                icon.setStyleSheet(f"background-color: {col}; border-radius: 3px;")
            lbl = QLabel(text)
            lbl.setStyleSheet(f"font-size: 11px; color: {TEXT_SECONDARY};")
            item_box.addWidget(icon)
            item_box.addWidget(lbl)
            
            row = idx // 3
            col_idx = idx % 3
            l_layout.addLayout(item_box, row, col_idx)

        layout.addWidget(legend_frame)

    def set_result(self, result: Optional[AnyDeadlockResult]) -> None:
        """Update both the sequence flow bar and visual canvas."""
        self.flow_bar.update_result(result)
        self.canvas.set_result(result)
