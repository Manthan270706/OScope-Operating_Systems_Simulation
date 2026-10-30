"""Process Lifecycle State Machine Explorer GUI page.

Interactive visualization of discrete operating system process lifecycle states
(New, Ready, Running, Waiting, Terminated) and state transitions authoritative
to the C++ ProcessManager implementation.
"""

import os
from typing import Callable, List, Optional, Tuple

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpinBox,
    QSplitter,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from ..backend.executor import ProcessLifecycleWorker
from ..backend.runner import BaseBackendRunner
from ..models.process_lifecycle import (
    ProcessInstanceModel,
    ProcessLifecycleConfig,
    ProcessLifecycleSimulationResultModel,
    ProcessLifecycleState,
    ProcessTransitionModel,
)
from ..theme import (
    ACCENT,
    ACCENT_CYAN,
    ACCENT_EMERALD,
    ACCENT_HOVER,
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
    SUCCESS,
    TEXT_MUTED,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    WARNING,
)
from ..widgets.process_lifecycle_viz import (
    ProcessStateDiagramWidget,
    ProcessTableWidget,
    ProcessTransitionHistoryWidget,
)
from ..widgets.stat_card import StatCard
from ..widgets.status_badge import StatusBadge


class ProcessLifecyclePage(QWidget):
    """Process Lifecycle State Machine Explorer Page."""

    def __init__(
        self,
        runner: Optional[BaseBackendRunner] = None,
        runner_factory: Optional[Callable[[], BaseBackendRunner]] = None,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        if runner_factory is not None:
            self.runner_factory = runner_factory
        elif runner is not None:
            self.runner_factory = lambda: runner
        else:
            from ..backend.runner import discover_backend

            self.runner_factory = discover_backend

        self.worker: Optional[ProcessLifecycleWorker] = None
        self._last_result: Optional[ProcessLifecycleSimulationResultModel] = None

        # Interactive state operations buffer: list of ("create", pid, arr, burst, prio) or ("transition", pid, target_state)
        self._interactive_ops: List[Tuple] = []
        self._known_pids: List[int] = []

        self._init_ui()
        self._set_default_inputs()

    def _init_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(14)

        # 1. Header Section
        header_layout = QHBoxLayout()
        header_text_layout = QVBoxLayout()
        header_text_layout.setSpacing(4)

        title = QLabel("Process Lifecycle State Machine Explorer")
        title.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {TEXT_PRIMARY};")
        header_text_layout.addWidget(title)

        subtitle = QLabel(
            "Authoritative discrete process lifecycle states (New, Ready, Running, Waiting, Terminated) "
            "and transition validations backed by C++ ProcessManager."
        )
        subtitle.setStyleSheet(f"font-size: 13px; color: {TEXT_SECONDARY};")
        header_text_layout.addWidget(subtitle)
        header_layout.addLayout(header_text_layout)

        header_layout.addStretch()

        self.status_badge = StatusBadge("Ready", "neutral")
        header_layout.addWidget(self.status_badge)
        main_layout.addLayout(header_layout)

        # 2. Control Bar (Mode Selector, Run, Reset)
        control_card = QFrame()
        control_card.setStyleSheet(
            f"""
            QFrame {{
                background-color: {BG_CARD};
                border: 1px solid {BORDER};
                border-radius: 8px;
                padding: 10px;
            }}
            """
        )
        ctrl_layout = QHBoxLayout(control_card)
        ctrl_layout.setContentsMargins(10, 8, 10, 8)
        ctrl_layout.setSpacing(12)

        mode_lbl = QLabel("Mode:")
        mode_lbl.setStyleSheet(f"font-weight: bold; color: {TEXT_PRIMARY};")
        ctrl_layout.addWidget(mode_lbl)

        self.combo_mode = QComboBox()
        self.combo_mode.addItems(["Educational Demo Preset", "Interactive State Machine"])
        self.combo_mode.currentIndexChanged.connect(self._on_mode_changed)
        self.combo_mode.setStyleSheet(self._input_style())
        ctrl_layout.addWidget(self.combo_mode)

        ctrl_layout.addStretch()

        self.btn_run = QPushButton("Simulate State Machine")
        self.btn_run.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {ACCENT};
                color: #172033;
                font-weight: bold;
                font-size: 13px;
                border: none;
                border-radius: 6px;
                padding: 7px 18px;
            }}
            QPushButton:hover {{
                background-color: {ACCENT_HOVER};
            }}
            QPushButton:disabled {{
                background-color: {BG_DARK};
                color: {TEXT_MUTED};
            }}
            """
        )
        self.btn_run.clicked.connect(self.run_simulation)
        ctrl_layout.addWidget(self.btn_run)

        self.btn_reset = QPushButton("Reset Defaults")
        self.btn_reset.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {BG_DARK};
                color: {TEXT_SECONDARY};
                border: 1px solid {BORDER};
                border-radius: 6px;
                padding: 7px 14px;
            }}
            QPushButton:hover {{
                color: {TEXT_PRIMARY};
                border-color: {BORDER_LIGHT};
            }}
            """
        )
        self.btn_reset.clicked.connect(self._set_default_inputs)
        ctrl_layout.addWidget(self.btn_reset)

        main_layout.addWidget(control_card)

        # 3. Interactive Operations Panel (Visible in "Interactive State Machine" mode)
        self.interactive_panel = QFrame()
        self.interactive_panel.setStyleSheet(
            f"background-color: {BG_CARD}; border: 1px solid {BORDER}; border-radius: 8px; padding: 10px;"
        )
        inter_layout = QVBoxLayout(self.interactive_panel)
        inter_layout.setContentsMargins(10, 8, 10, 8)
        inter_layout.setSpacing(10)

        # Row A: Create New Process
        create_row = QHBoxLayout()
        create_row.setSpacing(10)

        create_title = QLabel("Create Process:")
        create_title.setStyleSheet(f"font-weight: bold; color: {ACCENT_CYAN}; font-size: 12px;")
        create_row.addWidget(create_title)

        create_row.addWidget(QLabel("PID:"))
        self.spin_pid = QSpinBox()
        self.spin_pid.setRange(1, 9999)
        self.spin_pid.setValue(1)
        self.spin_pid.setStyleSheet(self._input_style())
        create_row.addWidget(self.spin_pid)

        create_row.addWidget(QLabel("Arrival:"))
        self.spin_arrival = QSpinBox()
        self.spin_arrival.setRange(0, 1000)
        self.spin_arrival.setValue(0)
        self.spin_arrival.setStyleSheet(self._input_style())
        create_row.addWidget(self.spin_arrival)

        create_row.addWidget(QLabel("Burst:"))
        self.spin_burst = QSpinBox()
        self.spin_burst.setRange(1, 1000)
        self.spin_burst.setValue(8)
        self.spin_burst.setStyleSheet(self._input_style())
        create_row.addWidget(self.spin_burst)

        create_row.addWidget(QLabel("Priority:"))
        self.spin_priority = QSpinBox()
        self.spin_priority.setRange(1, 20)
        self.spin_priority.setValue(1)
        self.spin_priority.setStyleSheet(self._input_style())
        create_row.addWidget(self.spin_priority)

        self.btn_create_proc = QPushButton("+ Add Process (New)")
        self.btn_create_proc.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {ACCENT_INDIGO};
                color: #172033;
                font-weight: bold;
                border: none;
                border-radius: 5px;
                padding: 6px 14px;
            }}
            QPushButton:hover {{
                background-color: {ACCENT_VIOLET};
            }}
            """
        )
        self.btn_create_proc.clicked.connect(self._on_create_process_clicked)
        create_row.addWidget(self.btn_create_proc)

        create_row.addStretch()

        self.btn_clear_ops = QPushButton("Clear Interactive Buffer")
        self.btn_clear_ops.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {BG_DARK};
                color: {TEXT_MUTED};
                border: 1px solid {BORDER};
                border-radius: 5px;
                padding: 5px 12px;
                font-size: 11px;
            }}
            QPushButton:hover {{
                color: {DANGER};
                border-color: {DANGER};
            }}
            """
        )
        self.btn_clear_ops.clicked.connect(self._on_clear_ops_clicked)
        create_row.addWidget(self.btn_clear_ops)

        inter_layout.addLayout(create_row)

        # Row B: Transition Selected Process
        trans_row = QHBoxLayout()
        trans_row.setSpacing(8)

        target_lbl = QLabel("Target Process:")
        target_lbl.setStyleSheet(f"font-weight: bold; color: {ACCENT_EMERALD}; font-size: 12px;")
        trans_row.addWidget(target_lbl)

        self.combo_target_pid = QComboBox()
        self.combo_target_pid.setStyleSheet(self._input_style())
        self.combo_target_pid.currentIndexChanged.connect(self._on_target_pid_changed)
        trans_row.addWidget(self.combo_target_pid)

        lbl_ops = QLabel("Request Transition:")
        lbl_ops.setStyleSheet(f"font-weight: bold; color: {TEXT_PRIMARY}; font-size: 12px;")
        trans_row.addWidget(lbl_ops)

        # Action transition buttons
        btn_admit = QPushButton("Admit (➔ Ready)")
        btn_admit.setStyleSheet(self._trans_btn_style(ACCENT_CYAN))
        btn_admit.clicked.connect(lambda: self._on_transition_clicked("Ready"))
        trans_row.addWidget(btn_admit)

        btn_dispatch = QPushButton("Dispatch (➔ Running)")
        btn_dispatch.setStyleSheet(self._trans_btn_style(ACCENT_EMERALD))
        btn_dispatch.clicked.connect(lambda: self._on_transition_clicked("Running"))
        trans_row.addWidget(btn_dispatch)

        btn_interrupt = QPushButton("Interrupt (➔ Ready)")
        btn_interrupt.setStyleSheet(self._trans_btn_style(WARNING))
        btn_interrupt.clicked.connect(lambda: self._on_transition_clicked("Ready"))
        trans_row.addWidget(btn_interrupt)

        btn_iowait = QPushButton("I/O Wait (➔ Waiting)")
        btn_iowait.setStyleSheet(self._trans_btn_style(ACCENT_VIOLET))
        btn_iowait.clicked.connect(lambda: self._on_transition_clicked("Waiting"))
        trans_row.addWidget(btn_iowait)

        btn_iodone = QPushButton("I/O Done (➔ Ready)")
        btn_iodone.setStyleSheet(self._trans_btn_style(ACCENT_CYAN))
        btn_iodone.clicked.connect(lambda: self._on_transition_clicked("Ready"))
        trans_row.addWidget(btn_iodone)

        btn_exit = QPushButton("Exit (➔ Terminated)")
        btn_exit.setStyleSheet(self._trans_btn_style(DANGER))
        btn_exit.clicked.connect(lambda: self._on_transition_clicked("Terminated"))
        trans_row.addWidget(btn_exit)

        # Explicit illegal transition trigger to demonstrate authoritative rejection
        btn_illegal = QPushButton("Test Illegal (➔ Terminated)")
        btn_illegal.setToolTip("Request an illegal transition (e.g. from New/Ready/Waiting directly to Terminated)")
        btn_illegal.setStyleSheet(
            f"""
            QPushButton {{
                background-color: transparent;
                color: {TEXT_MUTED};
                border: 1px dashed {BORDER_LIGHT};
                border-radius: 5px;
                padding: 5px 10px;
                font-size: 11px;
            }}
            QPushButton:hover {{
                color: {DANGER};
                border-color: {DANGER};
            }}
            """
        )
        btn_illegal.clicked.connect(lambda: self._on_transition_clicked("Terminated"))
        trans_row.addWidget(btn_illegal)

        trans_row.addStretch()
        inter_layout.addLayout(trans_row)

        self.interactive_panel.setVisible(False)  # Hidden by default in demo preset
        main_layout.addWidget(self.interactive_panel)

        # 4. Progress Bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setFixedHeight(3)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet(
            f"""
            QProgressBar {{
                border: none;
                background-color: {BG_DARK};
            }}
            QProgressBar::chunk {{
                background-color: {ACCENT_CYAN};
            }}
            """
        )
        main_layout.addWidget(self.progress_bar)

        # 5. Stat Cards Bar
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(10)

        self.card_total_procs = StatCard("Total Processes", "0 Processes", "No simulation active")
        self.card_active_state = StatCard("Active Process State", "None", "No process selected")
        self.card_transitions = StatCard("Transitions Executed", "0 Events", "0 Valid / 0 Rejected")
        self.card_validity = StatCard("Transition Integrity", "100%", "C++ Authoritative Validation")

        stats_layout.addWidget(self.card_total_procs)
        stats_layout.addWidget(self.card_active_state)
        stats_layout.addWidget(self.card_transitions)
        stats_layout.addWidget(self.card_validity)
        main_layout.addLayout(stats_layout)

        # 6. Tabbed Visualization Area
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(
            f"""
            QTabWidget::pane {{
                border: 1px solid {BORDER};
                border-radius: 8px;
                background-color: {BG_CARD};
            }}
            QTabBar::tab {{
                background-color: {BG_DARK};
                color: {TEXT_SECONDARY};
                padding: 8px 16px;
                font-weight: bold;
                font-size: 12px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                margin-right: 4px;
            }}
            QTabBar::tab:selected {{
                background-color: {BG_CARD};
                color: {ACCENT_CYAN};
                border-bottom: 2px solid {ACCENT_CYAN};
            }}
            QTabBar::tab:hover:!selected {{
                color: {TEXT_PRIMARY};
            }}
            """
        )

        # Tab 1: State Diagram & Education
        tab1 = QWidget()
        tab1_layout = QHBoxLayout(tab1)
        tab1_layout.setContentsMargins(12, 12, 12, 12)
        tab1_layout.setSpacing(14)

        # Left: Interactive Diagram
        self.diagram_widget = ProcessStateDiagramWidget()
        tab1_layout.addWidget(self.diagram_widget, 3)

        # Right: Educational Guide Card
        guide_card = QFrame()
        guide_card.setStyleSheet(
            f"background-color: {BG_DARK}; border: 1px solid {BORDER}; border-radius: 8px; padding: 12px;"
        )
        guide_layout = QVBoxLayout(guide_card)
        guide_layout.setContentsMargins(8, 8, 8, 8)
        guide_layout.setSpacing(8)

        g_title = QLabel("OS Process Lifecycle Reference")
        g_title.setStyleSheet(f"font-size: 13px; font-weight: bold; color: {ACCENT_CYAN};")
        guide_layout.addWidget(g_title)

        states_info = [
            ("New (0x0)", "Process is being created. PCB initialized. Awaiting admission into Ready queue."),
            ("Ready (0x1)", "Loaded in memory, waiting to be assigned to a CPU by the scheduler."),
            ("Running (0x2)", "Instructions being executed on CPU. Only one process runs per core at a time."),
            ("Waiting (0x3)", "Blocked awaiting an I/O event, timer completion, or signal."),
            ("Terminated (0x4)", "Finished execution. Terminal state. OS deallocates resources."),
        ]
        for name, desc in states_info:
            row = QVBoxLayout()
            row.setSpacing(1)
            nlbl = QLabel(name)
            nlbl.setStyleSheet(f"font-weight: bold; font-size: 11px; color: {TEXT_PRIMARY};")
            dlbl = QLabel(desc)
            dlbl.setWordWrap(True)
            dlbl.setStyleSheet(f"font-size: 10px; color: {TEXT_SECONDARY};")
            row.addWidget(nlbl)
            row.addWidget(dlbl)
            guide_layout.addLayout(row)

        guide_layout.addStretch()

        rule_box = QFrame()
        rule_box.setStyleSheet(f"background-color: {BG_CARD}; border: 1px solid {BORDER_LIGHT}; border-radius: 6px; padding: 6px;")
        r_layout = QVBoxLayout(rule_box)
        r_layout.setSpacing(2)
        rt = QLabel("Permitted Transitions:")
        rt.setStyleSheet(f"font-weight: bold; font-size: 11px; color: {ACCENT_EMERALD};")
        r_layout.addWidget(rt)
        r_body = QLabel(
            "• New ➔ Ready (Admit)\n"
            "• Ready ➔ Running (Dispatch)\n"
            "• Running ➔ Ready (Interrupt / Preempt)\n"
            "• Running ➔ Waiting (I/O Wait)\n"
            "• Waiting ➔ Ready (I/O Done)\n"
            "• Running ➔ Terminated (Exit)\n"
            "All other transitions are REJECTED by C++ ProcessManager."
        )
        r_body.setStyleSheet(f"font-size: 10px; color: {TEXT_MUTED};")
        r_layout.addWidget(r_body)
        guide_layout.addWidget(rule_box)

        tab1_layout.addWidget(guide_card, 2)
        self.tabs.addTab(tab1, "State Transition Diagram")

        # Tab 2: Process Table & Transition History
        tab2 = QWidget()
        tab2_layout = QVBoxLayout(tab2)
        tab2_layout.setContentsMargins(10, 10, 10, 10)
        tab2_layout.setSpacing(12)

        # Top half: Process Table
        self.process_table = ProcessTableWidget()
        self.process_table.process_selected.connect(self._on_table_process_selected)
        tab2_layout.addWidget(self.process_table, 2)

        # Bottom half: History Table
        self.history_table = ProcessTransitionHistoryWidget()
        tab2_layout.addWidget(self.history_table, 3)

        self.tabs.addTab(tab2, "Process Control Blocks & History")

        # Tab 3: Execution Logs & C++ Trace
        tab3 = QWidget()
        tab3_layout = QVBoxLayout(tab3)
        tab3_layout.setContentsMargins(10, 10, 10, 10)
        tab3_layout.setSpacing(8)

        log_title = QLabel("C++ Backend Execution Output & Transition Traces:")
        log_title.setStyleSheet(f"font-weight: bold; color: {TEXT_PRIMARY}; font-size: 12px;")
        tab3_layout.addWidget(log_title)

        self.txt_logs = QTextEdit()
        self.txt_logs.setReadOnly(True)
        self.txt_logs.setStyleSheet(
            f"""
            QTextEdit {{
                background-color: {BG_DARK};
                color: {TEXT_SECONDARY};
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 11px;
                border: 1px solid {BORDER};
                border-radius: 6px;
                padding: 8px;
            }}
            """
        )
        tab3_layout.addWidget(self.txt_logs)
        self.tabs.addTab(tab3, "Backend Trace & Logs")

        main_layout.addWidget(self.tabs)

    def _input_style(self) -> str:
        return f"""
            QComboBox, QSpinBox, QLineEdit {{
                background-color: {BG_DARK};
                color: {TEXT_PRIMARY};
                border: 1px solid {BORDER};
                border-radius: 5px;
                padding: 4px 8px;
                font-size: 12px;
            }}
            QComboBox:focus, QSpinBox:focus, QLineEdit:focus {{
                border-color: {ACCENT_CYAN};
            }}
            QComboBox::drop-down {{
                border: none;
                width: 18px;
            }}
        """

    def _trans_btn_style(self, color_hex: str) -> str:
        return f"""
            QPushButton {{
                background-color: {BG_DARK};
                color: {color_hex};
                border: 1px solid {color_hex};
                border-radius: 5px;
                padding: 5px 10px;
                font-weight: bold;
                font-size: 11px;
            }}
            QPushButton:hover {{
                background-color: {color_hex};
                color: #172033;
            }}
            QPushButton:disabled {{
                background-color: {BG_DARK};
                color: {TEXT_MUTED};
                border-color: {BORDER};
            }}
        """

    def _on_mode_changed(self, index: int) -> None:
        is_interactive = index == 1
        self.interactive_panel.setVisible(is_interactive)
        if is_interactive:
            if not self._interactive_ops:
                # Seed with an initial process (PID 1)
                self._interactive_ops = [
                    ("create", 1, 0, 8, 1),
                ]
                self._known_pids = [1]
                self._sync_target_pids()
                self.run_simulation()
        else:
            self.run_simulation()

    def _set_default_inputs(self) -> None:
        self.combo_mode.setCurrentIndex(0)  # Demo Preset
        self.spin_pid.setValue(2)
        self.spin_arrival.setValue(0)
        self.spin_burst.setValue(10)
        self.spin_priority.setValue(1)
        self._interactive_ops = []
        self._known_pids = []
        self._sync_target_pids()

    def _sync_target_pids(self) -> None:
        current = self.combo_target_pid.currentText()
        self.combo_target_pid.blockSignals(True)
        self.combo_target_pid.clear()
        for pid in sorted(self._known_pids):
            self.combo_target_pid.addItem(f"PID {pid}", pid)
        # Restore selection if possible
        idx = self.combo_target_pid.findText(current)
        if idx >= 0:
            self.combo_target_pid.setCurrentIndex(idx)
        elif self.combo_target_pid.count() > 0:
            self.combo_target_pid.setCurrentIndex(0)
        self.combo_target_pid.blockSignals(False)

    def _on_create_process_clicked(self) -> None:
        pid = self.spin_pid.value()
        arr = self.spin_arrival.value()
        burst = self.spin_burst.value()
        prio = self.spin_priority.value()

        if pid in self._known_pids:
            if self.isVisible() and os.environ.get("QT_QPA_PLATFORM") != "offscreen":
                QMessageBox.warning(self, "Duplicate PID", f"Process with PID {pid} already exists in this simulation session.")
            return

        self._interactive_ops.append(("create", pid, arr, burst, prio))
        self._known_pids.append(pid)
        self._sync_target_pids()

        # Next PID suggestion
        self.spin_pid.setValue(pid + 1)

        # Trigger simulation with updated ops
        self.run_simulation()

    def _on_clear_ops_clicked(self) -> None:
        self._interactive_ops = []
        self._known_pids = []
        self._sync_target_pids()
        self.diagram_widget.set_active_state(None)
        self.process_table.populate([])
        self.history_table.populate([])
        self.card_total_procs.set_value("0 Processes", "Cleared")
        self.card_active_state.set_value("None", "No process")
        self.card_transitions.set_value("0 Events", "Cleared")
        self.card_validity.set_value("100%", "C++ Authoritative")
        self.txt_logs.setText("Interactive buffer cleared. Add a process to begin.")

    def _on_target_pid_changed(self) -> None:
        sel_pid = self.combo_target_pid.currentData()
        if sel_pid is not None and self._last_result:
            for p in self._last_result.processes:
                if p.pid == sel_pid:
                    self.diagram_widget.set_active_state(p.current_state)
                    self.card_active_state.set_value(p.current_state.value, f"PID {p.pid}")
                    break

    def _on_table_process_selected(self, pid: int) -> None:
        # Match combo to table selection
        idx = self.combo_target_pid.findData(pid)
        if idx >= 0:
            self.combo_target_pid.setCurrentIndex(idx)
        if self._last_result:
            for p in self._last_result.processes:
                if p.pid == pid:
                    self.diagram_widget.set_active_state(p.current_state)
                    self.card_active_state.set_value(p.current_state.value, f"PID {p.pid}")
                    break

    def _on_transition_clicked(self, target_state: str) -> None:
        sel_pid = self.combo_target_pid.currentData()
        if sel_pid is None:
            if self.isVisible() and os.environ.get("QT_QPA_PLATFORM") != "offscreen":
                QMessageBox.information(self, "No Process", "Please create or select an active process first.")
            return

        self._interactive_ops.append(("transition", sel_pid, target_state))
        self.run_simulation()

    def run_simulation(self) -> None:
        """Runs the C++ Process Lifecycle simulation via WSL runner."""
        if self.worker and self.worker.isRunning():
            return

        mode_str = "demo" if self.combo_mode.currentIndex() == 0 else "interactive"
        config = ProcessLifecycleConfig(
            mode=mode_str,
            operations=list(self._interactive_ops),
        )

        valid, err = config.validate()
        if not valid:
            if self.isVisible() and os.environ.get("QT_QPA_PLATFORM") != "offscreen":
                QMessageBox.warning(self, "Validation Warning", err)
            return

        # Prepare UI
        self.btn_run.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.status_badge.set_status("Simulating...", "running")

        # Launch Worker
        runner = self.runner_factory()
        self.worker = ProcessLifecycleWorker(runner, config, self)
        self.worker.finished_exec.connect(self._on_simulation_success)
        self.worker.failed_exec.connect(self._on_simulation_error)
        self.worker.start()

    def _on_simulation_success(self, result: ProcessLifecycleSimulationResultModel) -> None:
        self.btn_run.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.status_badge.set_status("Completed", "success")
        self._last_result = result

        # 1. Update Known PIDs if in demo mode
        if self.combo_mode.currentIndex() == 0:
            self._known_pids = [p.pid for p in result.processes]
            self._sync_target_pids()

        # 2. Update Process Table and History Table
        self.process_table.populate(result.processes)
        self.history_table.populate(result.transitions)

        # 3. Determine active process state
        active_proc = None
        sel_pid = self.combo_target_pid.currentData()
        if sel_pid is not None:
            for p in result.processes:
                if p.pid == sel_pid:
                    active_proc = p
                    break
        if active_proc is None and result.processes:
            active_proc = result.processes[0]
            idx = self.combo_target_pid.findData(active_proc.pid)
            if idx >= 0:
                self.combo_target_pid.setCurrentIndex(idx)

        # 4. Update State Diagram
        last_trans = result.transitions[-1] if result.transitions else None
        if active_proc:
            self.diagram_widget.set_active_state(active_proc.current_state, last_transition=last_trans)
            self.card_active_state.set_value(active_proc.current_state.value, f"PID {active_proc.pid}")
        else:
            self.diagram_widget.set_active_state(None)
            self.card_active_state.set_value("None", "No process")

        # 5. Update Stat Cards
        total_p = len(result.processes)
        term_p = sum(1 for p in result.processes if p.current_state == ProcessLifecycleState.TERMINATED)
        active_p = total_p - term_p
        self.card_total_procs.set_value(f"{total_p} Processes", f"{active_p} Active, {term_p} Terminated")

        total_t = len(result.transitions)
        succ_t = sum(1 for t in result.transitions if t.success)
        fail_t = total_t - succ_t
        self.card_transitions.set_value(f"{total_t} Events", f"{succ_t} Valid, {fail_t} Rejected")

        if total_t > 0:
            val_pct = (succ_t / total_t) * 100.0
            sub_text = "All transitions valid" if fail_t == 0 else f"{fail_t} illegal rejected safely"
            self.card_validity.set_value(f"{val_pct:.0f}%", sub_text)
        else:
            self.card_validity.set_value("100%", "C++ Authoritative")

        # 6. Update Logs
        log_text = "\n".join(result.logs) if result.logs else "C++ ProcessManager state machine simulation completed successfully."
        self.txt_logs.setText(log_text)

    def _on_simulation_error(self, message: str) -> None:
        self.btn_run.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.status_badge.set_status("Error", "danger")
        if self.isVisible() and os.environ.get("QT_QPA_PLATFORM") != "offscreen":
            QMessageBox.critical(self, "Simulation Error", message)
        self.txt_logs.setText(f"ERROR: {message}")

    def cleanup(self) -> None:
        """Safely stops any background worker thread."""
        if self.worker and self.worker.isRunning():
            self.worker.cancel()
            self.worker.wait(1500)
            self.worker = None
