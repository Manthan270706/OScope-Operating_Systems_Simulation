"""Interactive Frame-by-Frame Timeline and Memory Grid visualization for Page Replacement."""

from typing import List, Optional

from PySide6.QtCore import QPoint, QRect, QSize, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from ..models.paging import PagingStepModel
from ..theme import (
    ACCENT,
    ACCENT_AMBER,
    ACCENT_CYAN,
    ACCENT_EMERALD,
    ACCENT_HOVER,
    ACCENT_INDIGO,
    ACCENT_LIGHT,
    ACCENT_ROSE,
    ACCENT_VIOLET,
    BG_APP,
    BG_ELEVATED,
    BG_INPUT,
    BG_SURFACE,
    BORDER,
    BORDER_LIGHT,
    PROCESS_COLORS,
    TEXT_MUTED,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
)


class StepColumnWidget(QFrame):
    """Visual column for a single reference step in the page replacement timeline."""

    clicked = Signal(int)

    def __init__(
        self,
        step: PagingStepModel,
        prev_step: Optional[PagingStepModel],
        frame_count: int,
        is_active: bool = False,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.step = step
        self.prev_step = prev_step
        self.frame_count = frame_count
        self.is_active = is_active

        self.setFixedWidth(80)
        self.setCursor(Qt.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
        self._build_ui()
        self.set_active(is_active)

    def mousePressEvent(self, event) -> None:
        self.clicked.emit(self.step.step_number - 1)
        super().mousePressEvent(event)

    def set_active(self, active: bool) -> None:
        self.is_active = active
        if active:
            self.setStyleSheet(
                f"""
                QFrame {{
                    background-color: {ACCENT_LIGHT};
                    border: 2px solid {ACCENT};
                    border-radius: 8px;
                }}
                """
            )
        else:
            self.setStyleSheet(
                f"""
                QFrame {{
                    background-color: {BG_SURFACE};
                    border: 1px solid {BORDER};
                    border-radius: 8px;
                }}
                QFrame:hover {{
                    border-color: {BORDER_LIGHT};
                    background-color: #F8FAFC;
                }}
                """
            )

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 8, 6, 8)
        layout.setSpacing(6)
        layout.setAlignment(Qt.AlignHCenter)

        # 1. Step Header Badge (#1)
        lbl_step = QLabel(f"#{self.step.step_number}")
        lbl_step.setAlignment(Qt.AlignCenter)
        lbl_step.setStyleSheet(f"font-size: 11px; font-weight: 700; color: {TEXT_MUTED}; background: transparent; border: none;")
        layout.addWidget(lbl_step)

        # 2. Page Reference Pill (P7)
        lbl_page = QLabel(f"P{self.step.page}")
        lbl_page.setFixedSize(54, 28)
        lbl_page.setAlignment(Qt.AlignCenter)
        lbl_page.setStyleSheet(
            f"""
            background-color: {ACCENT_LIGHT};
            color: {ACCENT};
            font-size: 13px;
            font-weight: 800;
            border-radius: 6px;
            border: 1px solid #BFDBFE;
            """
        )
        layout.addWidget(lbl_page, alignment=Qt.AlignHCenter)

        # 3. Outcome Pill (Fault vs Hit)
        lbl_outcome = QLabel("FAULT" if self.step.is_fault else "HIT")
        lbl_outcome.setFixedSize(56, 22)
        lbl_outcome.setAlignment(Qt.AlignCenter)
        if self.step.is_fault:
            lbl_outcome.setStyleSheet(
                """
                background-color: #FEE2E2;
                color: #DC2626;
                font-size: 10px;
                font-weight: 800;
                border-radius: 4px;
                border: 1px solid #FECACA;
                """
            )
        else:
            lbl_outcome.setStyleSheet(
                """
                background-color: #DCFCE7;
                color: #16A34A;
                font-size: 10px;
                font-weight: 800;
                border-radius: 4px;
                border: 1px solid #BBF7D0;
                """
            )
        layout.addWidget(lbl_outcome, alignment=Qt.AlignHCenter)

        layout.addSpacing(4)

        # 4. Frame slots (Frame 0..frame_count-1)
        for f_idx in range(self.frame_count):
            p_val = self.step.frames[f_idx] if f_idx < len(self.step.frames) else -1
            prev_val = (
                self.prev_step.frames[f_idx]
                if self.prev_step and f_idx < len(self.prev_step.frames)
                else -1
            )
            is_newly_loaded = (self.step.is_fault and p_val != -1 and p_val != prev_val)

            frame_cell = QLabel()
            frame_cell.setFixedSize(54, 32)
            frame_cell.setAlignment(Qt.AlignCenter)

            if p_val == -1:
                frame_cell.setText("—")
                frame_cell.setStyleSheet(
                    f"""
                    background-color: #F8FAFC;
                    color: {TEXT_MUTED};
                    font-size: 12px;
                    border: 1px dashed {BORDER_LIGHT};
                    border-radius: 5px;
                    """
                )
            else:
                frame_cell.setText(str(p_val))
                if is_newly_loaded:
                    # Highlight freshly loaded frame with accent
                    frame_cell.setStyleSheet(
                        f"""
                        background-color: {ACCENT};
                        color: #ffffff;
                        font-size: 13px;
                        font-weight: 800;
                        border: 2px solid {ACCENT_HOVER};
                        border-radius: 5px;
                        """
                    )
                else:
                    frame_cell.setStyleSheet(
                        f"""
                        background-color: {ACCENT_LIGHT};
                        color: #1E40AF;
                        font-size: 13px;
                        font-weight: 700;
                        border: 1px solid #BFDBFE;
                        border-radius: 5px;
                        """
                    )
            layout.addWidget(frame_cell, alignment=Qt.AlignHCenter)

        layout.addSpacing(4)

        # 5. Evicted page slot
        lbl_evicted = QLabel()
        lbl_evicted.setFixedSize(54, 24)
        lbl_evicted.setAlignment(Qt.AlignCenter)
        if self.step.evicted_page is not None:
            lbl_evicted.setText(f"P{self.step.evicted_page}")
            lbl_evicted.setStyleSheet(
                """
                background-color: #FEF3C7;
                color: #D97706;
                font-size: 10px;
                font-weight: 700;
                border-radius: 4px;
                border: 1px solid #FDE68A;
                """
            )
            lbl_evicted.setToolTip(f"Page P{self.step.evicted_page} was evicted from memory.")
        else:
            lbl_evicted.setText("—")
            lbl_evicted.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 11px; border: none; background: transparent;")
        layout.addWidget(lbl_evicted, alignment=Qt.AlignHCenter)


class FrameGridWidget(QWidget):
    """Complete interactive timeline and step-by-step frame inspection widget."""

    step_changed = Signal(int)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._steps: List[PagingStepModel] = []
        self._frame_count: int = 3
        self._current_step_idx: int = 0
        self._step_widgets: List[StepColumnWidget] = []

        # Playback animation timer
        self._timer = QTimer(self)
        self._timer.setInterval(1000)
        self._timer.timeout.connect(self._on_timer_tick)
        self._is_playing: bool = False

        self._build_ui()

    def _build_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(10)

        # 1. Navigation and Animation Toolbar
        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)

        self.btn_first = QPushButton("⏮ First")
        self.btn_first.setFixedHeight(30)
        self.btn_first.setStyleSheet(
            f"background-color: {BG_ELEVATED}; color: {TEXT_PRIMARY}; border: 1px solid {BORDER}; border-radius: 5px; font-size: 11px; font-weight: 600; padding: 2px 10px;"
        )
        self.btn_first.clicked.connect(self.go_to_first)
        toolbar.addWidget(self.btn_first)

        self.btn_prev = QPushButton("◀ Prev")
        self.btn_prev.setFixedHeight(30)
        self.btn_prev.setStyleSheet(
            f"background-color: {BG_ELEVATED}; color: {TEXT_PRIMARY}; border: 1px solid {BORDER}; border-radius: 5px; font-size: 11px; font-weight: 600; padding: 2px 10px;"
        )
        self.btn_prev.clicked.connect(self.go_to_prev)
        toolbar.addWidget(self.btn_prev)

        self.btn_play = QPushButton("▶ Play Animation")
        self.btn_play.setFixedHeight(30)
        self.btn_play.setFixedWidth(130)
        self.btn_play.setStyleSheet(
            f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {ACCENT}, stop:1 {ACCENT_INDIGO});
                color: #ffffff;
                border: 1px solid rgba(56, 189, 248, 0.4);
                border-radius: 5px;
                font-size: 11px;
                font-weight: 700;
            }}
            QPushButton:hover {{
                border-color: #7dd3fc;
            }}
            """
        )
        self.btn_play.clicked.connect(self.toggle_playback)
        toolbar.addWidget(self.btn_play)

        self.btn_next = QPushButton("Next ▶")
        self.btn_next.setFixedHeight(30)
        self.btn_next.setStyleSheet(
            f"background-color: {BG_ELEVATED}; color: {TEXT_PRIMARY}; border: 1px solid {BORDER}; border-radius: 5px; font-size: 11px; font-weight: 600; padding: 2px 10px;"
        )
        self.btn_next.clicked.connect(self.go_to_next)
        toolbar.addWidget(self.btn_next)

        self.btn_last = QPushButton("Last ⏭")
        self.btn_last.setFixedHeight(30)
        self.btn_last.setStyleSheet(
            f"background-color: {BG_ELEVATED}; color: {TEXT_PRIMARY}; border: 1px solid {BORDER}; border-radius: 5px; font-size: 11px; font-weight: 600; padding: 2px 10px;"
        )
        self.btn_last.clicked.connect(self.go_to_last)
        toolbar.addWidget(self.btn_last)

        # Speed selector
        self.speed_combo = QComboBox()
        self.speed_combo.setFixedHeight(30)
        self.speed_combo.addItem("Normal (1.0s)", 1000)
        self.speed_combo.addItem("Fast (0.5s)", 500)
        self.speed_combo.addItem("Slow (2.0s)", 2000)
        self.speed_combo.currentIndexChanged.connect(self._on_speed_changed)
        toolbar.addWidget(self.speed_combo)

        toolbar.addSpacing(10)

        self.lbl_counter = QLabel("Step 0 of 0")
        self.lbl_counter.setStyleSheet(f"color: {ACCENT_HOVER}; font-size: 12px; font-weight: 700;")
        toolbar.addWidget(self.lbl_counter)

        toolbar.addStretch()

        # Legend pills
        legend_layout = QHBoxLayout()
        legend_layout.setSpacing(10)

        leg_fault = QLabel("● Fault (Rose)")
        leg_fault.setStyleSheet(f"color: {ACCENT_ROSE}; font-size: 11px; font-weight: 600;")
        leg_hit = QLabel("● Hit (Emerald)")
        leg_hit.setStyleSheet(f"color: {ACCENT_EMERALD}; font-size: 11px; font-weight: 600;")
        leg_evict = QLabel("● Evicted (Amber)")
        leg_evict.setStyleSheet(f"color: {ACCENT_AMBER}; font-size: 11px; font-weight: 600;")

        legend_layout.addWidget(leg_fault)
        legend_layout.addWidget(leg_hit)
        legend_layout.addWidget(leg_evict)
        toolbar.addLayout(legend_layout)

        main_layout.addLayout(toolbar)

        # 2. Main Horizontal Scroll Area for the Grid
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.NoFrame)
        self.scroll_area.setStyleSheet(f"background-color: {BG_SURFACE}; border: 1px solid {BORDER}; border-radius: 8px;")
        self.scroll_area.setMinimumHeight(240)

        self.grid_container = QWidget()
        self.grid_container.setStyleSheet(f"background-color: {BG_SURFACE};")
        self.grid_layout = QHBoxLayout(self.grid_container)
        self.grid_layout.setContentsMargins(14, 14, 14, 14)
        self.grid_layout.setSpacing(10)
        self.grid_layout.setAlignment(Qt.AlignLeft | Qt.AlignTop)

        self.scroll_area.setWidget(self.grid_container)
        main_layout.addWidget(self.scroll_area)

        # 3. Active Step Inspector / Natural Language Breakdown Card
        self.inspector_card = QFrame()
        self.inspector_card.setStyleSheet(
            f"""
            QFrame {{
                background-color: {BG_ELEVATED};
                border: 1px solid {BORDER};
                border-left: 3px solid {ACCENT_HOVER};
                border-radius: 6px;
                padding: 10px 14px;
            }}
            """
        )
        insp_layout = QVBoxLayout(self.inspector_card)
        insp_layout.setContentsMargins(4, 2, 4, 2)
        insp_layout.setSpacing(4)

        self.lbl_insp_title = QLabel("Step Analysis Inspector")
        self.lbl_insp_title.setStyleSheet(f"font-size: 12px; font-weight: 700; color: {ACCENT_HOVER};")

        self.lbl_insp_narrative = QLabel(
            "Execute a page replacement simulation or click any step above to inspect memory frame transitions."
        )
        self.lbl_insp_narrative.setWordWrap(True)
        self.lbl_insp_narrative.setStyleSheet(f"font-size: 12px; color: {TEXT_PRIMARY}; line-height: 1.4;")

        insp_layout.addWidget(self.lbl_insp_title)
        insp_layout.addWidget(self.lbl_insp_narrative)
        main_layout.addWidget(self.inspector_card)

        self._update_controls_state()

    def set_simulation_result(self, frame_count: int, steps: List[PagingStepModel]) -> None:
        """Populate the grid with genuine step data from the C++ backend."""
        self.stop_animation()
        self._frame_count = max(1, frame_count)
        self._steps = steps or []
        self._current_step_idx = 0
        self._step_widgets.clear()

        # Clear existing items in grid_layout
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        if not self._steps:
            lbl_empty = QLabel("No steps recorded. Run a simulation to visualize page frame transitions.")
            lbl_empty.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 12px; padding: 20px;")
            self.grid_layout.addWidget(lbl_empty)
            self._update_controls_state()
            return

        # Add fixed Header Label Column
        header_col = self._build_header_column(self._frame_count)
        self.grid_layout.addWidget(header_col)

        # Add Step Columns
        for idx, step in enumerate(self._steps):
            prev_s = self._steps[idx - 1] if idx > 0 else None
            col_w = StepColumnWidget(step, prev_s, self._frame_count, is_active=(idx == 0))
            col_w.clicked.connect(self.go_to_step)
            self._step_widgets.append(col_w)
            self.grid_layout.addWidget(col_w)

        self.grid_layout.addStretch()
        self._update_active_step_view()
        self._update_controls_state()

    def _build_header_column(self, frame_count: int) -> QFrame:
        frame = QFrame()
        frame.setFixedWidth(82)
        frame.setStyleSheet(
            f"background-color: {BG_SURFACE}; border-right: 1px solid {BORDER}; padding-right: 6px;"
        )
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(4, 8, 8, 8)
        layout.setSpacing(6)
        layout.setAlignment(Qt.AlignRight)

        lbl_step_hdr = QLabel("Step")
        lbl_step_hdr.setStyleSheet(f"font-size: 11px; font-weight: 700; color: {TEXT_MUTED};")
        layout.addWidget(lbl_step_hdr)

        lbl_page_hdr = QLabel("Reference")
        lbl_page_hdr.setFixedHeight(28)
        lbl_page_hdr.setStyleSheet(f"font-size: 11px; font-weight: 700; color: {TEXT_SECONDARY};")
        layout.addWidget(lbl_page_hdr)

        lbl_out_hdr = QLabel("Result")
        lbl_out_hdr.setFixedHeight(22)
        lbl_out_hdr.setStyleSheet(f"font-size: 11px; font-weight: 700; color: {TEXT_SECONDARY};")
        layout.addWidget(lbl_out_hdr)

        layout.addSpacing(4)

        for f in range(frame_count):
            lbl_f = QLabel(f"Frame {f}")
            lbl_f.setFixedHeight(32)
            lbl_f.setStyleSheet(f"font-size: 11px; font-weight: 600; color: {TEXT_MUTED};")
            layout.addWidget(lbl_f)

        layout.addSpacing(4)

        lbl_ev = QLabel("Evicted")
        lbl_ev.setFixedHeight(24)
        lbl_ev.setStyleSheet(f"font-size: 11px; font-weight: 600; color: {ACCENT_AMBER};")
        layout.addWidget(lbl_ev)

        return frame

    def clear(self) -> None:
        self.set_simulation_result(3, [])

    def go_to_step(self, step_idx: int) -> None:
        if not self._steps:
            return
        self._current_step_idx = max(0, min(len(self._steps) - 1, step_idx))
        self._update_active_step_view()
        self.step_changed.emit(self._current_step_idx)

    def go_to_first(self) -> None:
        self.go_to_step(0)

    def go_to_prev(self) -> None:
        self.go_to_step(self._current_step_idx - 1)

    def go_to_next(self) -> None:
        self.go_to_step(self._current_step_idx + 1)

    def go_to_last(self) -> None:
        if self._steps:
            self.go_to_step(len(self._steps) - 1)

    def toggle_playback(self) -> None:
        if self._is_playing:
            self.stop_animation()
        else:
            self.start_animation()

    def start_animation(self) -> None:
        if not self._steps:
            return
        if self._current_step_idx >= len(self._steps) - 1:
            self.go_to_first()
        self._is_playing = True
        self.btn_play.setText("⏸ Pause Animation")
        self._timer.start()

    def stop_animation(self) -> None:
        self._is_playing = False
        self._timer.stop()
        self.btn_play.setText("▶ Play Animation")

    def _on_timer_tick(self) -> None:
        if self._current_step_idx < len(self._steps) - 1:
            self.go_to_next()
        else:
            self.stop_animation()

    def _on_speed_changed(self, index: int) -> None:
        interval = self.speed_combo.currentData()
        if interval:
            self._timer.setInterval(int(interval))

    def _update_active_step_view(self) -> None:
        if not self._steps:
            self.lbl_counter.setText("Step 0 of 0")
            self.lbl_insp_narrative.setText(
                "Execute a page replacement simulation to inspect memory frame transitions."
            )
            return

        total = len(self._steps)
        current = self._current_step_idx + 1
        active_step = self._steps[self._current_step_idx]

        self.lbl_counter.setText(f"Step {current} of {total} (Page {active_step.page})")

        # Update widget active states
        for idx, w in enumerate(self._step_widgets):
            w.set_active(idx == self._current_step_idx)

        # Scroll active column into visible range
        if 0 <= self._current_step_idx < len(self._step_widgets):
            active_w = self._step_widgets[self._current_step_idx]
            self.scroll_area.ensureWidgetVisible(active_w, 100, 0)

        # Build educational narrative
        p_val = active_step.page
        narrative = f"<b>Step {current}:</b> Process referenced <b>Page {p_val}</b>. "

        if active_step.is_fault:
            narrative += f"<span style='color: {ACCENT_ROSE}; font-weight: 700;'>PAGE FAULT!</span> "
            if active_step.evicted_page is not None:
                narrative += (
                    f"All physical frames were occupied. Page <b>P{active_step.evicted_page}</b> was "
                    f"<span style='color: {ACCENT_AMBER}; font-weight: 600;'>evicted</span> from memory to make room, "
                    f"and Page <b>P{p_val}</b> was loaded into the liberated frame."
                )
            else:
                empty_slot = len(active_step.frames) - active_step.frames.count(-1) - 1
                narrative += (
                    f"An empty physical frame was available (Frame {max(0, empty_slot)}). "
                    f"Page <b>P{p_val}</b> was loaded directly into physical memory without eviction."
                )
        else:
            found_frame = -1
            for f_idx, pf in enumerate(active_step.frames):
                if pf == p_val:
                    found_frame = f_idx
                    break
            narrative += (
                f"<span style='color: {ACCENT_EMERALD}; font-weight: 700;'>PAGE HIT!</span> "
                f"Page <b>P{p_val}</b> was already resident in <b>Frame {found_frame}</b>. "
                "Instantaneous memory access occurred with zero disk I/O latency."
            )

        self.lbl_insp_narrative.setText(narrative)
        self._update_controls_state()

    def _update_controls_state(self) -> None:
        has_steps = bool(self._steps)
        self.btn_first.setEnabled(has_steps and self._current_step_idx > 0)
        self.btn_prev.setEnabled(has_steps and self._current_step_idx > 0)
        self.btn_next.setEnabled(has_steps and self._current_step_idx < len(self._steps) - 1)
        self.btn_last.setEnabled(has_steps and self._current_step_idx < len(self._steps) - 1)
        self.btn_play.setEnabled(has_steps)
