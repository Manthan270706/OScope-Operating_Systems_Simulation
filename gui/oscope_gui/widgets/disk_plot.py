"""Interactive Disk Head Movement Trajectory Plot & Sequence Widget for OScope Disk Scheduling."""

from typing import Any, Dict, List, Optional, Tuple, Union

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
    QSizePolicy,
    QToolTip,
    QVBoxLayout,
    QWidget,
)

from ..models.disk import (
    DiskComparisonResultModel,
    DiskSchedulingResultModel,
    DiskStepModel,
)
from ..theme import (
    ACCENT,
    ACCENT_AMBER,
    ACCENT_CYAN,
    ACCENT_EMERALD,
    ACCENT_INDIGO,
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


class DiskSequenceFlowBar(QFrame):
    """Horizontal banner presenting the step-by-step serviced sequence and total seek movement."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("DiskSequenceFlowBar")
        self.setStyleSheet(
            f"""
            QFrame#DiskSequenceFlowBar {{
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

        self.lbl_title = QLabel("Service Order:")
        self.lbl_title.setStyleSheet(f"font-size: 11px; font-weight: 700; color: {TEXT_MUTED}; letter-spacing: 0.5px;")
        bar_layout.addWidget(self.lbl_title)

        self.flow_container = QHBoxLayout()
        self.flow_container.setSpacing(6)
        bar_layout.addLayout(self.flow_container)
        bar_layout.addStretch()

        self._show_empty()

    def _show_empty(self) -> None:
        self._clear_flow()
        lbl = QLabel("Run a disk simulation to inspect head traversal order.")
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

    def count(self) -> int:
        """Return number of items in the flow container."""
        return self.flow_container.count()

    def update_result(self, result: Optional[DiskSchedulingResultModel]) -> None:
        self._clear_flow()
        if not result or not result.head_path:
            self._show_empty()
            return

        self.lbl_title.setText(f"{result.algorithm_name.upper()} ORDER:")
        self.lbl_title.setStyleSheet(f"font-size: 11px; font-weight: 700; color: {ACCENT_EMERALD};")

        # Initial head badge
        init_pill = QLabel(f"Head: {result.initial_head_position}")
        init_pill.setStyleSheet(
            f"""
            background-color: rgba(245, 158, 11, 0.15);
            color: {ACCENT_AMBER};
            border: 1px solid rgba(245, 158, 11, 0.4);
            border-radius: 5px;
            font-weight: 700;
            font-size: 11px;
            padding: 3px 8px;
            """
        )
        self.flow_container.addWidget(init_pill)

        # Serviced items (cap visible pills to 12 with a summary count if longer)
        display_items = result.serviced_requests
        max_visible = 12
        show_items = display_items[:max_visible]

        for idx, cyl in enumerate(show_items):
            arrow = QLabel("->")
            arrow.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 10px; font-weight: 700;")
            self.flow_container.addWidget(arrow)

            pill = QLabel(f"#{idx + 1}: Cyl {cyl}")
            pill.setStyleSheet(
                f"""
                background-color: rgba(56, 189, 248, 0.12);
                color: {ACCENT};
                border: 1px solid rgba(56, 189, 248, 0.35);
                border-radius: 5px;
                font-weight: 700;
                font-size: 11px;
                padding: 3px 8px;
                """
            )
            self.flow_container.addWidget(pill)

        if len(display_items) > max_visible:
            arrow = QLabel("->")
            arrow.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 10px; font-weight: 700;")
            self.flow_container.addWidget(arrow)

            rem = len(display_items) - max_visible
            more_pill = QLabel(f"+{rem} more requests...")
            more_pill.setStyleSheet(
                f"""
                background-color: {BG_ELEVATED};
                color: {TEXT_SECONDARY};
                border: 1px solid {BORDER};
                border-radius: 5px;
                font-weight: 600;
                font-size: 11px;
                padding: 3px 8px;
                """
            )
            self.flow_container.addWidget(more_pill)


class DiskHeadPlotCanvas(QWidget):
    """Custom QPainter canvas plotting cylinder position (X-axis) vs. step progression (Y-axis)."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setMouseTracking(True)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.MinimumExpanding)
        self.setMinimumHeight(380)

        self.result: Optional[DiskSchedulingResultModel] = None
        self.min_cyl: int = 0
        self.max_cyl: int = 199
        self.hovered_point: Optional[int] = None  # index in head_path
        self.point_coords: List[Tuple[float, float, int]] = []  # (x, y, cyl)

    @property
    def nodes(self) -> List[Any]:
        if self.result and self.result.head_path:
            return self.result.head_path
        return self.point_coords

    def set_data(
        self,
        result: Optional[DiskSchedulingResultModel],
        min_cyl: int = 0,
        max_cyl: int = 199,
    ) -> None:
        self.result = result
        self.min_cyl = min_cyl
        self.max_cyl = max(min_cyl + 1, max_cyl)
        self.hovered_point = None

        if self.result and self.result.head_path:
            n_points = len(self.result.head_path)
            # Dynamic height based on number of points
            self.setMinimumHeight(max(380, min(800, n_points * 36 + 100)))
        else:
            self.setMinimumHeight(340)

        self.update()

    def mouseMoveEvent(self, event) -> None:
        pos = event.position()
        found: Optional[int] = None

        for idx, (px, py, cyl) in enumerate(self.point_coords):
            dx = pos.x() - px
            dy = pos.y() - py
            if (dx * dx + dy * dy) <= 144:  # 12px hit radius
                found = idx
                break

        if found != self.hovered_point:
            self.hovered_point = found
            if found is not None and self.result:
                cyl = self.point_coords[found][2]
                if found == 0:
                    text = f"Initial Head: Cylinder {cyl}"
                else:
                    step_idx = found - 1
                    if step_idx < len(self.result.steps):
                        step = self.result.steps[step_idx]
                        text = (
                            f"Step {found}: Cylinder {cyl}\n"
                            f"Seek: {step.movement} cyl (Cumulative: {step.cumulative_movement} cyl)\n"
                            f"Type: {step.step_type_label}\n"
                            f"{step.action_description}"
                        )
                    else:
                        text = f"Step {found}: Cylinder {cyl}"
                QToolTip.showText(event.globalPosition().toPoint(), text, self)
            self.update()

    def leaveEvent(self, event) -> None:
        self.hovered_point = None
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()

        # Canvas background with rounded corners
        bg_rect = QRectF(0, 0, w, h)
        painter.fillRect(bg_rect, QColor(BG_CANVAS))

        if not self.result or not self.result.head_path:
            self._paint_empty_state(painter)
            return

        path = self.result.head_path
        n = len(path)
        if n < 1:
            self._paint_empty_state(painter)
            return

        # Margins: Left=70px (for step labels), Right=50px, Top=50px, Bottom=45px (for cylinder scale)
        left_m = 70.0
        right_m = 50.0
        top_m = 50.0
        bottom_m = 45.0

        plot_w = max(100.0, w - left_m - right_m)
        plot_h = max(100.0, h - top_m - bottom_m)

        cyl_range = max(1, self.max_cyl - self.min_cyl)

        def to_x(cyl: int) -> float:
            ratio = (cyl - self.min_cyl) / cyl_range
            return left_m + ratio * plot_w

        def to_y(step_idx: int) -> float:
            if n <= 1:
                return top_m + plot_h / 2.0
            return top_m + (step_idx / (n - 1)) * plot_h

        # 1. Grid lines and Cylinder Axis
        self._paint_axes(painter, left_m, plot_w, top_m, plot_h, to_x)

        # 2. Compute point coordinates
        self.point_coords = [(to_x(cyl), to_y(i), cyl) for i, cyl in enumerate(path)]

        # 3. Draw head movement trajectories (Lines/Arcs)
        self._paint_trajectories(painter)

        # 4. Draw node pins & step badges
        self._paint_nodes(painter)

    def _paint_empty_state(self, painter: QPainter) -> None:
        painter.setPen(QColor(TEXT_MUTED))
        painter.setFont(QFont(FONT_FAMILY, 12))
        painter.drawText(
            self.rect(),
            Qt.AlignCenter,
            "No disk simulation executed yet.\nConfigure cylinder requests above and click 'Run Simulation'.",
        )

    def _paint_axes(
        self,
        painter: QPainter,
        left_m: float,
        plot_w: float,
        top_m: float,
        plot_h: float,
        to_x,
    ) -> None:
        h = self.height()

        # Vertical grid columns for cylinder graduation marks
        grid_pen = QPen(QColor(BORDER), 1, Qt.DotLine)
        painter.setPen(grid_pen)

        # Draw 5 to 9 nice tick marks across cylinder range
        ticks = [self.min_cyl]
        span = self.max_cyl - self.min_cyl
        step_val = max(10, (span // 6 // 10) * 10 or 25)
        curr = ((self.min_cyl + step_val) // step_val) * step_val
        while curr < self.max_cyl:
            ticks.append(curr)
            curr += step_val
        if self.max_cyl not in ticks:
            ticks.append(self.max_cyl)

        painter.setFont(QFont(FONT_FAMILY, 9))
        for t in ticks:
            tx = to_x(t)
            painter.setPen(QPen(QColor(255, 255, 255, 18), 1, Qt.DotLine))
            painter.drawLine(QPointF(tx, top_m - 10), QPointF(tx, top_m + plot_h + 8))

            # Bottom cylinder label
            painter.setPen(QColor(TEXT_SECONDARY))
            is_boundary = t in (self.min_cyl, self.max_cyl)
            if is_boundary:
                painter.setFont(QFont(FONT_FAMILY, 9, QFont.Bold))
                painter.setPen(QColor(ACCENT_VIOLET))
            else:
                painter.setFont(QFont(FONT_FAMILY, 9))
                painter.setPen(QColor(TEXT_MUTED))

            painter.drawText(
                QRectF(tx - 30, top_m + plot_h + 12, 60, 20),
                Qt.AlignCenter,
                str(t),
            )

        # Axis title at top
        painter.setFont(QFont(FONT_FAMILY, 10, QFont.Bold))
        painter.setPen(QColor(TEXT_PRIMARY))
        painter.drawText(
            QRectF(left_m, 12, plot_w, 22),
            Qt.AlignCenter,
            f"Disk Cylinders Range: [{self.min_cyl} ... {self.max_cyl}]",
        )

        # Step axis line
        painter.setPen(QPen(QColor(BORDER), 1, Qt.SolidLine))
        painter.drawLine(QPointF(left_m - 10, top_m), QPointF(left_m - 10, top_m + plot_h))

    def _paint_trajectories(self, painter: QPainter) -> None:
        if not self.result:
            return

        for i in range(1, len(self.point_coords)):
            p1_x, p1_y, c1 = self.point_coords[i - 1]
            p2_x, p2_y, c2 = self.point_coords[i]

            step_idx = i - 1
            step = self.result.steps[step_idx] if step_idx < len(self.result.steps) else None
            is_wrap = step.is_wraparound if step else False
            is_boundary = step.is_boundary if step else False

            if is_wrap:
                # Wraparound seek: Curved dashed arc in warm amber/rose
                pen = QPen(QColor(ACCENT_AMBER), 2.0, Qt.DashLine)
                painter.setPen(pen)
                path = QPainterPath()
                path.moveTo(p1_x, p1_y)
                # Curve inward
                ctrl_y = (p1_y + p2_y) / 2.0
                ctrl_x = (p1_x + p2_x) / 2.0
                path.quadTo(ctrl_x, ctrl_y, p2_x, p2_y)
                painter.drawPath(path)

                # Distance badge along the curve
                mid_x = (p1_x + p2_x) / 2.0
                mid_y = (p1_y + p2_y) / 2.0
                self._draw_step_badge(painter, mid_x, mid_y, f"Jump: {abs(c2 - c1)} cyl", QColor(ACCENT_AMBER))
            else:
                # Normal seek line: Solid gradient line
                line_color = QColor(ACCENT_VIOLET) if is_boundary else QColor(ACCENT)
                pen = QPen(line_color, 2.2, Qt.SolidLine)
                painter.setPen(pen)
                painter.drawLine(QPointF(p1_x, p1_y), QPointF(p2_x, p2_y))

                # Step seek distance badge
                mid_x = (p1_x + p2_x) / 2.0
                mid_y = (p1_y + p2_y) / 2.0
                badge_color = QColor(ACCENT_VIOLET) if is_boundary else QColor(ACCENT_CYAN)
                self._draw_step_badge(painter, mid_x, mid_y, f"{abs(c2 - c1)}", badge_color)

    def _draw_step_badge(self, painter: QPainter, x: float, y: float, text: str, color: QColor) -> None:
        painter.setFont(QFont(FONT_FAMILY, 8, QFont.Bold))
        metrics = painter.fontMetrics()
        tw = metrics.horizontalAdvance(text) + 8
        th = 16.0

        badge_rect = QRectF(x - tw / 2.0, y - th / 2.0, tw, th)
        painter.setBrush(QBrush(QColor(15, 23, 42, 230)))
        painter.setPen(QPen(color, 1))
        painter.drawRoundedRect(badge_rect, 4, 4)

        painter.setPen(color)
        painter.drawText(badge_rect, Qt.AlignCenter, text)

    def _paint_nodes(self, painter: QPainter) -> None:
        if not self.result:
            return

        for idx, (px, py, cyl) in enumerate(self.point_coords):
            is_hovered = (idx == self.hovered_point)
            radius = 7.0 if not is_hovered else 9.5

            # Step label on left margin
            painter.setFont(QFont(FONT_FAMILY, 9, QFont.Bold if is_hovered else QFont.Normal))
            painter.setPen(QColor(TEXT_PRIMARY if is_hovered else TEXT_MUTED))
            step_lbl = f"Start" if idx == 0 else f"Step {idx}"
            painter.drawText(
                QRectF(6, py - 10, 52, 20),
                Qt.AlignRight | Qt.AlignVCenter,
                step_lbl,
            )

            # Horizontal dotted guide from step label to node
            painter.setPen(QPen(QColor(255, 255, 255, 12), 1, Qt.DotLine))
            painter.drawLine(QPointF(58, py), QPointF(px - radius - 2, py))

            # Determine node styling
            if idx == 0:
                # Initial Head: Diamond node in amber
                painter.setBrush(QBrush(QColor(ACCENT_AMBER)))
                painter.setPen(QPen(QColor("#ffffff"), 2.0 if is_hovered else 1.5))
                diamond = QPainterPath()
                d_r = radius * 1.2
                diamond.moveTo(px, py - d_r)
                diamond.lineTo(px + d_r, py)
                diamond.lineTo(px, py + d_r)
                diamond.lineTo(px - d_r, py)
                diamond.closeSubpath()
                painter.drawPath(diamond)

                # Label badge next to initial node
                self._draw_node_tag(painter, px, py - 16, f"Head: {cyl}", QColor(ACCENT_AMBER))
            else:
                step_idx = idx - 1
                step = self.result.steps[step_idx] if step_idx < len(self.result.steps) else None
                is_boundary = step.is_boundary if step else False
                is_wrap = step.is_wraparound if step else False

                if is_wrap:
                    # Wraparound node
                    painter.setBrush(QBrush(QColor(ACCENT_AMBER)))
                    painter.setPen(QPen(QColor("#ffffff"), 1.8 if is_hovered else 1.2))
                    painter.drawEllipse(QPointF(px, py), radius, radius)
                    self._draw_node_tag(painter, px, py - 14, f"Wrap: {cyl}", QColor(ACCENT_AMBER))
                elif is_boundary:
                    # Boundary node (Square)
                    painter.setBrush(QBrush(QColor(ACCENT_VIOLET)))
                    painter.setPen(QPen(QColor("#ffffff"), 1.8 if is_hovered else 1.2))
                    sq_r = radius
                    painter.drawRoundedRect(QRectF(px - sq_r, py - sq_r, sq_r * 2, sq_r * 2), 2, 2)
                    self._draw_node_tag(painter, px, py - 14, f"Boundary: {cyl}", QColor(ACCENT_VIOLET))
                else:
                    # Serviced Request Node: Circle in cyan/emerald
                    painter.setBrush(QBrush(QColor(ACCENT_EMERALD if is_hovered else ACCENT)))
                    painter.setPen(QPen(QColor("#ffffff"), 1.8 if is_hovered else 1.2))
                    painter.drawEllipse(QPointF(px, py), radius, radius)
                    self._draw_node_tag(painter, px, py - 14, f"Cyl {cyl}", QColor(ACCENT_CYAN))

    def _draw_node_tag(self, painter: QPainter, x: float, y: float, text: str, color: QColor) -> None:
        painter.setFont(QFont(FONT_FAMILY, 8, QFont.Bold))
        metrics = painter.fontMetrics()
        tw = metrics.horizontalAdvance(text) + 8
        th = 14.0

        tag_rect = QRectF(x - tw / 2.0, y - th, tw, th)
        painter.setBrush(QBrush(QColor(15, 23, 42, 210)))
        painter.setPen(QPen(color, 1))
        painter.drawRoundedRect(tag_rect, 3, 3)

        painter.setPen(QColor("#ffffff"))
        painter.drawText(tag_rect, Qt.AlignCenter, text)


class DiskHeadPlotWidget(QWidget):
    """Complete visual component including the Service Flow Bar, Interactive Head Plot, and Legend."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        # 1. Top sequence flow bar
        self.flow_bar = DiskSequenceFlowBar(self)
        self.sequence_bar = self.flow_bar
        layout.addWidget(self.flow_bar)

        # 2. Interactive canvas
        self.canvas = DiskHeadPlotCanvas(self)
        layout.addWidget(self.canvas)

        # 3. Legend Bar
        legend_frame = QFrame()
        legend_frame.setObjectName("DiskLegendFrame")
        legend_frame.setStyleSheet(
            f"""
            QFrame#DiskLegendFrame {{
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
            ("Initial Head Position", ACCENT_AMBER, "diamond"),
            ("Serviced Cylinder Request", ACCENT, "circle"),
            ("Physical Boundary (SCAN)", ACCENT_VIOLET, "square"),
            ("Wraparound Seek (C-SCAN/C-LOOK)", ACCENT_AMBER, "dashed"),
            ("Normal Arm Seek Path", ACCENT, "solid"),
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
            elif style == "square":
                icon.setStyleSheet(f"background-color: {col}; border-radius: 1px;")
            elif style == "diamond":
                icon.setStyleSheet(f"background-color: {col}; border-radius: 4px;")
            else:
                icon.setStyleSheet(f"background-color: {col}; border-radius: 5px;")
            lbl = QLabel(text)
            lbl.setStyleSheet(f"font-size: 11px; color: {TEXT_SECONDARY};")
            item_box.addWidget(icon)
            item_box.addWidget(lbl)

            row = idx // 3
            col_idx = idx % 3
            l_layout.addLayout(item_box, row, col_idx)

        layout.addWidget(legend_frame)

    def set_result(
        self,
        result: Optional[DiskSchedulingResultModel],
        min_cyl: int = 0,
        max_cyl: int = 199,
    ) -> None:
        """Update both the sequence flow bar and interactive canvas."""
        self.flow_bar.update_result(result)
        self.canvas.set_data(result, min_cyl, max_cyl)
