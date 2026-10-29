"""Visualizations for Virtual Memory Address Translation, MMU Paging, and Thrashing."""

import math
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
    QScrollArea,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ..models.address_translation import (
    AddressTranslationSimulationResultModel,
    DemandPagingResultModel,
    DemandPagingStepModel,
    PageTableEntryModel,
    ThrashingPointModel,
    ThrashingResultModel,
    TranslationResultModel,
)
from ..theme import (
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


class VirtualAddressDecomposerWidget(QFrame):
    """Visualizes the MMU bit decomposition of a Virtual Address into Page Number and Offset."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("vaDecomposerCard")
        self.setStyleSheet(
            f"""
            QFrame#vaDecomposerCard {{
                background-color: {BG_CARD};
                border: 1px solid {BORDER};
                border-radius: 10px;
                padding: 12px;
            }}
            """
        )
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Title
        title_label = QLabel("MMU Hardware Address Translation Flow")
        title_label.setStyleSheet(f"font-size: 13px; font-weight: bold; color: {ACCENT_CYAN};")
        layout.addWidget(title_label)

        # Container for interactive visual boxes
        self.flow_container = QHBoxLayout()
        self.flow_container.setSpacing(10)

        # 1. Virtual Address Box
        self.va_box = self._create_box("Virtual Address (Input)", "VA: -", f"border: 1px solid {ACCENT_VIOLET};")
        self.flow_container.addWidget(self.va_box)

        arrow1 = QLabel("➔")
        arrow1.setStyleSheet(f"font-size: 18px; color: {TEXT_MUTED}; font-weight: bold;")
        arrow1.setAlignment(Qt.AlignCenter)
        self.flow_container.addWidget(arrow1)

        # 2. Decomposed Bits Box (VPN + Offset)
        self.decomp_box = self._create_decomposition_box()
        self.flow_container.addWidget(self.decomp_box)

        arrow2 = QLabel("➔")
        arrow2.setStyleSheet(f"font-size: 18px; color: {TEXT_MUTED}; font-weight: bold;")
        arrow2.setAlignment(Qt.AlignCenter)
        self.flow_container.addWidget(arrow2)

        # 3. Translation Outcome Box (PFN + PA or FAULT)
        self.outcome_box = self._create_box("Physical Address (Output)", "PA: -", f"border: 1px solid {ACCENT_EMERALD};")
        self.flow_container.addWidget(self.outcome_box)

        layout.addLayout(self.flow_container)

        # Explanatory status banner
        self.status_banner = QLabel("Select or run address translation to inspect bit-level translation flow.")
        self.status_banner.setWordWrap(True)
        self.status_banner.setStyleSheet(
            f"background-color: {BG_DARK}; border: 1px solid {BORDER}; border-radius: 6px; padding: 8px; color: {TEXT_SECONDARY}; font-size: 12px;"
        )
        layout.addWidget(self.status_banner)

    def _create_box(self, title: str, main_text: str, custom_border: str) -> QFrame:
        frame = QFrame()
        frame.setStyleSheet(
            f"""
            background-color: {BG_DARK};
            border-radius: 8px;
            padding: 8px;
            {custom_border}
            """
        )
        vbox = QVBoxLayout(frame)
        vbox.setContentsMargins(6, 6, 6, 6)
        vbox.setSpacing(4)

        t_lbl = QLabel(title)
        t_lbl.setStyleSheet(f"font-size: 11px; color: {TEXT_MUTED}; font-weight: bold;")
        vbox.addWidget(t_lbl)

        val_lbl = QLabel(main_text)
        val_lbl.setObjectName("mainValueLabel")
        val_lbl.setStyleSheet(f"font-size: 14px; font-weight: bold; color: {TEXT_PRIMARY}; font-family: monospace;")
        val_lbl.setAlignment(Qt.AlignCenter)
        vbox.addWidget(val_lbl)

        sub_lbl = QLabel("Decimal: -")
        sub_lbl.setObjectName("subValueLabel")
        sub_lbl.setStyleSheet(f"font-size: 11px; color: {TEXT_SECONDARY}; font-family: monospace;")
        sub_lbl.setAlignment(Qt.AlignCenter)
        vbox.addWidget(sub_lbl)

        return frame

    def _create_decomposition_box(self) -> QFrame:
        frame = QFrame()
        frame.setStyleSheet(
            f"""
            background-color: {BG_DARK};
            border: 1px dashed {ACCENT_INDIGO};
            border-radius: 8px;
            padding: 8px;
            """
        )
        vbox = QVBoxLayout(frame)
        vbox.setContentsMargins(6, 6, 6, 6)
        vbox.setSpacing(4)

        title = QLabel("MMU Bit Decomposition")
        title.setStyleSheet(f"font-size: 11px; color: {ACCENT_INDIGO}; font-weight: bold;")
        vbox.addWidget(title)

        hbox = QHBoxLayout()
        hbox.setSpacing(6)

        # Page Number Box
        p_frame = QFrame()
        p_frame.setStyleSheet(f"background-color: rgba(139, 92, 246, 0.15); border: 1px solid {ACCENT_VIOLET}; border-radius: 4px; padding: 4px;")
        pvbox = QVBoxLayout(p_frame)
        pvbox.setContentsMargins(4, 4, 4, 4)
        pvbox.setSpacing(2)
        plbl1 = QLabel("Page Number (p)")
        plbl1.setStyleSheet(f"font-size: 10px; color: {ACCENT_VIOLET};")
        self.vpn_lbl = QLabel("p = -")
        self.vpn_lbl.setStyleSheet(f"font-size: 13px; font-weight: bold; color: {TEXT_PRIMARY}; font-family: monospace;")
        pvbox.addWidget(plbl1)
        pvbox.addWidget(self.vpn_lbl)
        hbox.addWidget(p_frame)

        # Offset Box
        d_frame = QFrame()
        d_frame.setStyleSheet(f"background-color: rgba(2, 132, 199, 0.15); border: 1px solid {ACCENT_CYAN}; border-radius: 4px; padding: 4px;")
        dvbox = QVBoxLayout(d_frame)
        dvbox.setContentsMargins(4, 4, 4, 4)
        dvbox.setSpacing(2)
        dlbl1 = QLabel("Page Offset (d)")
        dlbl1.setStyleSheet(f"font-size: 10px; color: {ACCENT_CYAN};")
        self.offset_lbl = QLabel("d = -")
        self.offset_lbl.setStyleSheet(f"font-size: 13px; font-weight: bold; color: {TEXT_PRIMARY}; font-family: monospace;")
        dvbox.addWidget(dlbl1)
        dvbox.addWidget(self.offset_lbl)
        hbox.addWidget(d_frame)

        vbox.addLayout(hbox)

        self.offset_bits_lbl = QLabel("Offset width: 12 bits (4096-byte page)")
        self.offset_bits_lbl.setStyleSheet(f"font-size: 10px; color: {TEXT_MUTED};")
        self.offset_bits_lbl.setAlignment(Qt.AlignCenter)
        vbox.addWidget(self.offset_bits_lbl)

        return frame

    def update_translation(self, trans: TranslationResultModel, page_size: int = 4096) -> None:
        """Update display with active address translation outcome."""
        offset_bits = int(math.log2(page_size)) if page_size > 0 else 12

        # Update Virtual Address Box
        val_lbl = self.va_box.findChild(QLabel, "mainValueLabel")
        sub_lbl = self.va_box.findChild(QLabel, "subValueLabel")
        if val_lbl:
            val_lbl.setText(f"0x{trans.virtual_address:X}")
        if sub_lbl:
            sub_lbl.setText(f"Dec: {trans.virtual_address:,} B")

        # Update Decomposed Bits
        self.vpn_lbl.setText(f"Page {trans.page_number} (0x{trans.page_number:X})")
        self.offset_lbl.setText(f"Offset {trans.offset} (0x{trans.offset:X})")
        self.offset_bits_lbl.setText(f"Offset width: {offset_bits} bits ({page_size} bytes/page)")

        # Update Output Box
        out_val = self.outcome_box.findChild(QLabel, "mainValueLabel")
        out_sub = self.outcome_box.findChild(QLabel, "subValueLabel")
        if not trans.page_fault:
            self.outcome_box.setStyleSheet(
                f"background-color: {BG_DARK}; border: 1px solid {SUCCESS}; border-radius: 8px; padding: 8px;"
            )
            if out_val:
                out_val.setText(f"0x{trans.physical_address:X}")
                out_val.setStyleSheet(f"font-size: 14px; font-weight: bold; color: {SUCCESS_TEXT}; font-family: monospace;")
            if out_sub:
                out_sub.setText(f"Frame {trans.frame_number} | PA: {trans.physical_address:,} B")
            self.status_banner.setStyleSheet(
                f"background-color: {SUCCESS_BG}; border: 1px solid {SUCCESS}; border-radius: 6px; padding: 8px; color: {SUCCESS_TEXT}; font-size: 12px;"
            )
            self.status_banner.setText(
                f"✓ Translation Successful: Page {trans.page_number} is resident in Frame {trans.frame_number}. "
                f"Offset {trans.offset} is preserved verbatim to compute Physical Address {trans.physical_address} (0x{trans.physical_address:X})."
            )
        else:
            self.outcome_box.setStyleSheet(
                f"background-color: {BG_DARK}; border: 1px solid {DANGER}; border-radius: 8px; padding: 8px;"
            )
            if out_val:
                out_val.setText("PAGE FAULT")
                out_val.setStyleSheet(f"font-size: 14px; font-weight: bold; color: {DANGER_TEXT}; font-family: monospace;")
            if out_sub:
                out_sub.setText("Frame: Not In Memory")
            self.status_banner.setStyleSheet(
                f"background-color: {DANGER_BG}; border: 1px solid {DANGER}; border-radius: 6px; padding: 8px; color: {DANGER_TEXT}; font-size: 12px;"
            )
            self.status_banner.setText(
                f"⚠ Page Fault Occurred: Page {trans.page_number} is marked invalid / unmapped in the page table. "
                "Hardware MMU triggers an interrupt trap to the operating system kernel demand-paging handler."
            )


class PageTableMappingWidget(QFrame):
    """Displays the active page table entries and physical frame mappings."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("pageTableCard")
        self.setStyleSheet(
            f"""
            QFrame#pageTableCard {{
                background-color: {BG_CARD};
                border: 1px solid {BORDER};
                border-radius: 10px;
                padding: 10px;
            }}
            """
        )
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)

        title = QLabel("Process Page Table (MMU Resident State)")
        title.setStyleSheet(f"font-size: 12px; font-weight: bold; color: {TEXT_PRIMARY};")
        layout.addWidget(title)

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "Page #", "Frame #", "Valid Bit", "Dirty Bit", "Ref Bit", "Frame Physical Base"
        ])
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
        layout.addWidget(self.table)

    def populate(self, entries: List[PageTableEntryModel], page_size: int = 4096, highlight_page: Optional[int] = None) -> None:
        self.table.setRowCount(len(entries))
        for row, entry in enumerate(entries):
            # Page Number
            p_item = QTableWidgetItem(f"Page {entry.page_number}")
            p_item.setTextAlignment(Qt.AlignCenter)

            # Frame Number
            fn_text = f"Frame {entry.frame_number}" if entry.frame_number >= 0 else "Unmapped"
            f_item = QTableWidgetItem(fn_text)
            f_item.setTextAlignment(Qt.AlignCenter)

            # Valid Bit
            v_item = QTableWidgetItem("1 (Resident)" if entry.valid else "0 (Fault)")
            v_item.setTextAlignment(Qt.AlignCenter)
            v_item.setForeground(QColor(SUCCESS_TEXT if entry.valid else DANGER_TEXT))

            # Dirty Bit
            d_item = QTableWidgetItem("1" if entry.dirty else "0")
            d_item.setTextAlignment(Qt.AlignCenter)

            # Ref Bit
            r_item = QTableWidgetItem("1" if entry.referenced else "0")
            r_item.setTextAlignment(Qt.AlignCenter)

            # Frame Base Address
            base_addr = entry.frame_number * page_size if entry.frame_number >= 0 else 0
            base_text = f"0x{base_addr:X} ({base_addr:,} B)" if entry.frame_number >= 0 else "-"
            b_item = QTableWidgetItem(base_text)
            b_item.setTextAlignment(Qt.AlignCenter)

            self.table.setItem(row, 0, p_item)
            self.table.setItem(row, 1, f_item)
            self.table.setItem(row, 2, v_item)
            self.table.setItem(row, 3, d_item)
            self.table.setItem(row, 4, r_item)
            self.table.setItem(row, 5, b_item)

            if highlight_page is not None and entry.page_number == highlight_page:
                self.table.selectRow(row)


class DemandPagingTraceWidget(QFrame):
    """Step-by-step trace of demand paging access sequence, page faults, and evictions."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("demandPagingCard")
        self.setStyleSheet(
            f"""
            QFrame#demandPagingCard {{
                background-color: {BG_CARD};
                border: 1px solid {BORDER};
                border-radius: 10px;
                padding: 10px;
            }}
            """
        )
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)

        title = QLabel("Demand Paging Access Trace (FIFO Eviction)")
        title.setStyleSheet(f"font-size: 12px; font-weight: bold; color: {TEXT_PRIMARY};")
        layout.addWidget(title)

        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "Step", "Virtual Addr", "Page", "Offset", "Status", "Frame Allocated", "Evicted Victim"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
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

    def populate(self, result: DemandPagingResultModel) -> None:
        self.table.setRowCount(len(result.steps))
        for row, step in enumerate(result.steps):
            s_item = QTableWidgetItem(f"#{row + 1}")
            s_item.setTextAlignment(Qt.AlignCenter)

            va_item = QTableWidgetItem(f"{step.virtual_address:,} (0x{step.virtual_address:X})")
            va_item.setTextAlignment(Qt.AlignCenter)

            p_item = QTableWidgetItem(f"P{step.page_number}")
            p_item.setTextAlignment(Qt.AlignCenter)

            off_item = QTableWidgetItem(str(step.offset))
            off_item.setTextAlignment(Qt.AlignCenter)

            status_item = QTableWidgetItem("PAGE FAULT" if step.page_fault else "HIT")
            status_item.setTextAlignment(Qt.AlignCenter)
            status_item.setForeground(QColor(DANGER_TEXT if step.page_fault else SUCCESS_TEXT))

            fn_item = QTableWidgetItem(f"Frame {step.frame_number}")
            fn_item.setTextAlignment(Qt.AlignCenter)

            vic_text = f"Page {step.victim_page}" if step.victim_page >= 0 else "None (Free Frame)"
            vic_item = QTableWidgetItem(vic_text)
            vic_item.setTextAlignment(Qt.AlignCenter)
            if step.victim_page >= 0:
                vic_item.setForeground(QColor(WARNING_TEXT))

            self.table.setItem(row, 0, s_item)
            self.table.setItem(row, 1, va_item)
            self.table.setItem(row, 2, p_item)
            self.table.setItem(row, 3, off_item)
            self.table.setItem(row, 4, status_item)
            self.table.setItem(row, 5, fn_item)
            self.table.setItem(row, 6, vic_item)


class ThrashingCurvePlotWidget(QWidget):
    """Custom QPainter plotting page fault count & rate vs available frame allocation."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setMinimumHeight(240)
        self._data: Optional[ThrashingResultModel] = None

    def set_data(self, data: Optional[ThrashingResultModel]) -> None:
        self._data = data
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()

        # Canvas background
        painter.fillRect(0, 0, w, h, QColor(BG_CARD))

        # Card border
        painter.setPen(QPen(QColor(BORDER), 1))
        painter.drawRoundedRect(0, 0, w - 1, h - 1, 8, 8)

        if not self._data or not self._data.points:
            painter.setPen(QColor(TEXT_MUTED))
            painter.setFont(QFont("Segoe UI", 11))
            painter.drawText(self.rect(), Qt.AlignCenter, "No Thrashing Simulation Data Available")
            return

        margin_left = 60
        margin_right = 30
        margin_top = 40
        margin_bottom = 45

        plot_w = w - margin_left - margin_right
        plot_h = h - margin_top - margin_bottom

        if plot_w <= 10 or plot_h <= 10:
            return

        # Title
        painter.setFont(QFont("Segoe UI", 11, QFont.Bold))
        painter.setPen(QColor(TEXT_PRIMARY))
        painter.drawText(margin_left, 24, "Thrashing Curve: Page Faults vs Frame Allocation")

        # Find min/max values
        pts = self._data.points
        min_frames = min(p.frames for p in pts)
        max_frames = max(p.frames for p in pts)
        max_faults = max(p.page_faults for p in pts) if pts else 10
        if max_faults == 0:
            max_faults = 1

        # Coordinate mapper
        def to_screen(frames: int, faults: int) -> QPointF:
            denom_f = (max_frames - min_frames) if (max_frames > min_frames) else 1
            x = margin_left + ((frames - min_frames) / denom_f) * plot_w
            y = margin_top + plot_h - (faults / max_faults) * plot_h
            return QPointF(x, y)

        # Draw horizontal gridlines & Y labels
        painter.setFont(QFont("Segoe UI", 9))
        grid_steps = 4
        for i in range(grid_steps + 1):
            val = int(i * (max_faults / grid_steps))
            y = margin_top + plot_h - (val / max_faults) * plot_h

            painter.setPen(QPen(QColor(BORDER), 1, Qt.DashLine))
            painter.drawLine(int(margin_left), int(y), int(margin_left + plot_w), int(y))

            painter.setPen(QColor(TEXT_MUTED))
            painter.drawText(10, int(y + 4), margin_left - 15, 20, Qt.AlignRight, str(val))

        # Y Axis title
        painter.setPen(QColor(TEXT_SECONDARY))
        painter.drawText(margin_left, margin_top - 10, "Page Faults")

        # X Axis labels
        for p in pts:
            pt = to_screen(p.frames, p.page_faults)
            painter.setPen(QPen(QColor(BORDER), 1))
            painter.drawLine(int(pt.x()), int(margin_top + plot_h), int(pt.x()), int(margin_top + plot_h + 5))

            painter.setPen(QColor(TEXT_SECONDARY))
            painter.drawText(int(pt.x() - 15), int(margin_top + plot_h + 8), 30, 20, Qt.AlignCenter, f"{p.frames}F")

        # Draw Area Gradient under curve
        path = QPainterPath()
        first_pt = to_screen(pts[0].frames, pts[0].page_faults)
        path.moveTo(first_pt.x(), margin_top + plot_h)
        for p in pts:
            pt = to_screen(p.frames, p.page_faults)
            path.lineTo(pt)
        last_pt = to_screen(pts[-1].frames, pts[-1].page_faults)
        path.lineTo(last_pt.x(), margin_top + plot_h)
        path.closeSubpath()

        grad = QLinearGradient(0, margin_top, 0, margin_top + plot_h)
        grad.setColorAt(0.0, QColor(244, 63, 94, 90))   # Rose tint for high faults
        grad.setColorAt(0.6, QColor(139, 92, 246, 50))  # Violet
        grad.setColorAt(1.0, QColor(2, 132, 199, 10))   # Soft blue
        painter.fillPath(path, QBrush(grad))

        # Draw Line
        line_path = QPainterPath()
        line_path.moveTo(first_pt)
        for p in pts[1:]:
            line_path.lineTo(to_screen(p.frames, p.page_faults))

        painter.setPen(QPen(QColor(ACCENT_ROSE), 2.5))
        painter.drawPath(line_path)

        # Highlight Thrashing Knee / Working Set Threshold
        knee_frames = self._data.thrashing_threshold_frames
        knee_pt = None
        for p in pts:
            if p.frames == knee_frames:
                knee_pt = to_screen(p.frames, p.page_faults)
                break

        if knee_pt:
            # Draw vertical dashed guide line
            painter.setPen(QPen(QColor(ACCENT_EMERALD), 1.5, Qt.DashLine))
            painter.drawLine(int(knee_pt.x()), int(margin_top), int(knee_pt.x()), int(margin_top + plot_h))

            # Knee annotation badge
            badge_rect = QRectF(knee_pt.x() - 65, margin_top + 5, 130, 22)
            painter.setBrush(QColor(BG_ELEVATED))
            painter.setPen(QPen(QColor(ACCENT_EMERALD), 1))
            painter.drawRoundedRect(badge_rect, 4, 4)

            painter.setPen(QColor(SUCCESS_TEXT))
            painter.setFont(QFont("Segoe UI", 9, QFont.Bold))
            painter.drawText(badge_rect, Qt.AlignCenter, f"Knee: {knee_frames} Frames")

        # Draw Point Markers
        for p in pts:
            pt = to_screen(p.frames, p.page_faults)
            painter.setBrush(QColor(BG_CARD))
            painter.setPen(QPen(QColor(ACCENT_CYAN), 2))
            painter.drawEllipse(pt, 4.5, 4.5)

            # Fault rate label
            rate_pct = f"{p.fault_rate * 100:.0f}%"
            painter.setFont(QFont("Segoe UI", 8))
            painter.setPen(QColor(TEXT_MUTED))
            painter.drawText(int(pt.x() - 20), int(pt.y() - 18), 40, 16, Qt.AlignCenter, rate_pct)
