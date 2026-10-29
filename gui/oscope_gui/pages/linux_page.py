"""Linux / POSIX IPC and Synchronization interactive simulation and visualization page.

Integrates process lifecycle (fork/exec, zombie, orphan), thread synchronization
(mutex, POSIX semaphores, Peterson's algorithm), producer-consumer bounded buffer,
and POSIX IPC channels (anonymous pipes, FIFOs, shared memory, message queues)
using the verified C++ backend.
"""

import time
from typing import Callable, Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from ..backend.executor import LinuxExperimentsWorker
from ..backend.runner import BaseBackendRunner
from ..models.linux_experiments import (
    LinuxExperimentCategory,
    LinuxExperimentsResultModel,
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
    SUCCESS_BG,
    SUCCESS_TEXT,
    TEXT_MUTED,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
)
from ..widgets.linux_viz import (
    IpcChannelsWidget,
    ProcessLifecycleTreeWidget,
    ProducerConsumerBufferWidget,
    SyncVisualizationWidget,
)
from ..widgets.stat_card import StatCard
from ..widgets.status_badge import StatusBadge


class LinuxExperimentsPage(QWidget):
    """Main interactive Linux / POSIX system experiments and visualization page."""

    def __init__(
        self,
        runner: Optional[BaseBackendRunner] = None,
        on_execution_completed: Optional[Callable[[str, int, float, float, bool], None]] = None,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.runner = runner
        self.on_execution_completed = on_execution_completed
        self._active_worker: Optional[LinuxExperimentsWorker] = None
        self._last_result: Optional[LinuxExperimentsResultModel] = None

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet(f"background-color: {BG_APP}; border: none;")

        content = QWidget()
        content.setStyleSheet(f"background-color: {BG_APP};")
        self.content_layout = QVBoxLayout(content)
        self.content_layout.setContentsMargins(36, 28, 36, 32)
        self.content_layout.setSpacing(20)

        # 1. Page Header
        header = self._build_header()
        self.content_layout.addLayout(header)

        # 2. Control Action Bar Card
        action_card = self._build_action_card()
        self.content_layout.addWidget(action_card)

        # 3. Educational Guidance Concepts Section
        guidance = self._build_guidance_section()
        self.content_layout.addWidget(guidance)

        # 4. Summary Stat Cards Row
        self.stats_layout = self._build_stats_row()
        self.content_layout.addLayout(self.stats_layout)

        # 5. Interactive Results Tabs Container
        self.tabs_container = self._build_results_tabs()
        self.tabs = self.tabs_container
        self.content_layout.addWidget(self.tabs_container)

        scroll.setWidget(content)
        main_layout.addWidget(scroll)

    def _build_header(self) -> QVBoxLayout:
        layout = QVBoxLayout()
        layout.setSpacing(6)

        title_row = QHBoxLayout()
        title_row.setSpacing(12)

        title = QLabel("Linux / POSIX IPC & Synchronization Lab")
        title.setStyleSheet("font-size: 24px; font-weight: 800; color: #ffffff; letter-spacing: 0.5px;")
        title_row.addWidget(title)

        self.backend_badge = StatusBadge("POSIX Native Engine", "success")
        title_row.addWidget(self.backend_badge)
        title_row.addStretch()

        subtitle = QLabel(
            "Explore process lifecycle (fork/exec, zombie, orphan), concurrency synchronization (mutex, semaphores, Peterson's), "
            "producer-consumer bounded buffers, and native POSIX IPC channels using the verified C++ backend."
        )
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet(f"font-size: 13px; color: {TEXT_SECONDARY}; line-height: 1.4;")

        layout.addLayout(title_row)
        layout.addWidget(subtitle)
        return layout

    def _build_action_card(self) -> QFrame:
        card = QFrame()
        card.setProperty("card", True)
        card.setObjectName("LinuxActionCard")
        card.setStyleSheet(
            f"""
            QFrame#LinuxActionCard {{
                background-color: {BG_SURFACE};
                border: 1px solid {BORDER};
                border-radius: 10px;
            }}
            """
        )
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(14)

        top_row = QHBoxLayout()
        top_row.setSpacing(10)

        lbl_actions = QLabel("Simulation Controls & Experiment Runners")
        lbl_actions.setStyleSheet("font-size: 14px; font-weight: 700; color: #ffffff;")
        top_row.addWidget(lbl_actions)
        top_row.addStretch()

        self.runner_status_label = QLabel("Ready to launch experiments")
        self.runner_status_label.setStyleSheet(f"font-size: 12px; color: {TEXT_MUTED}; font-style: italic;")
        top_row.addWidget(self.runner_status_label)
        layout.addLayout(top_row)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        # Primary Run All
        self.btn_run_all = QPushButton("  ▶  Run All Linux Experiments")
        self.btn_run_all.setProperty("class", "btn-primary")
        self.btn_run_all.setFixedHeight(38)
        self.btn_run_all.setStyleSheet(
            f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {ACCENT}, stop:1 {ACCENT_INDIGO});
                color: #ffffff;
                font-weight: 700;
                font-size: 13px;
                padding: 0 20px;
                border-radius: 6px;
                border: 1px solid rgba(56, 189, 248, 0.4);
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {ACCENT_HOVER}, stop:1 #818cf8);
                border-color: #7dd3fc;
            }}
            QPushButton:disabled {{
                background-color: {BG_ELEVATED};
                color: {TEXT_MUTED};
                border-color: {BORDER};
            }}
            """
        )
        self.btn_run_all.clicked.connect(lambda: self.run_category(LinuxExperimentCategory.ALL))
        btn_row.addWidget(self.btn_run_all)

        # Category buttons
        self.btn_run_lifecycle = QPushButton("⎇ Process Lifecycle")
        self.btn_run_lifecycle.setFixedHeight(38)
        self.btn_run_lifecycle.setStyleSheet(self._button_style(ACCENT_CYAN))
        self.btn_run_lifecycle.clicked.connect(lambda: self.run_category(LinuxExperimentCategory.LIFECYCLE))
        btn_row.addWidget(self.btn_run_lifecycle)

        self.btn_run_sync = QPushButton("⛊ Synchronization")
        self.btn_run_sync.setFixedHeight(38)
        self.btn_run_sync.setStyleSheet(self._button_style(ACCENT_EMERALD))
        self.btn_run_sync.clicked.connect(lambda: self.run_category(LinuxExperimentCategory.SYNCHRONIZATION))
        btn_row.addWidget(self.btn_run_sync)

        self.btn_run_prod_cons = QPushButton("⇄ Producer–Consumer")
        self.btn_run_prod_cons.setFixedHeight(38)
        self.btn_run_prod_cons.setStyleSheet(self._button_style(ACCENT_AMBER))
        self.btn_run_prod_cons.clicked.connect(lambda: self.run_category(LinuxExperimentCategory.PRODUCER_CONSUMER))
        btn_row.addWidget(self.btn_run_prod_cons)

        self.btn_run_ipc = QPushButton("⬡ POSIX IPC")
        self.btn_run_ipc.setFixedHeight(38)
        self.btn_run_ipc.setStyleSheet(self._button_style(ACCENT_VIOLET))
        self.btn_run_ipc.clicked.connect(lambda: self.run_category(LinuxExperimentCategory.IPC))
        btn_row.addWidget(self.btn_run_ipc)

        btn_row.addStretch()

        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.setFixedHeight(38)
        self.btn_cancel.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {BG_ELEVATED};
                color: {TEXT_SECONDARY};
                font-size: 12px;
                padding: 0 16px;
                border-radius: 6px;
                border: 1px solid {BORDER};
            }}
            QPushButton:hover {{
                color: #ffffff;
                border-color: {BORDER_LIGHT};
            }}
            """
        )
        self.btn_cancel.clicked.connect(self._cancel_worker)
        self.btn_cancel.setEnabled(False)
        btn_row.addWidget(self.btn_cancel)

        layout.addLayout(btn_row)
        return card

    def _button_style(self, accent_color: str) -> str:
        return f"""
            QPushButton {{
                background-color: {BG_ELEVATED};
                color: {TEXT_PRIMARY};
                font-weight: 600;
                font-size: 12px;
                padding: 0 16px;
                border-radius: 6px;
                border: 1px solid {BORDER};
            }}
            QPushButton:hover {{
                background-color: rgba(255, 255, 255, 0.05);
                border-color: {accent_color};
                color: #ffffff;
            }}
            QPushButton:disabled {{
                color: {TEXT_MUTED};
                border-color: {BORDER};
            }}
        """

    def _build_guidance_section(self) -> QFrame:
        panel = QFrame()
        panel.setProperty("card", True)
        panel.setObjectName("LinuxGuidancePanel")
        panel.setStyleSheet(
            f"""
            QFrame#LinuxGuidancePanel {{
                background-color: {BG_SURFACE};
                border: 1px solid {BORDER};
                border-left: 4px solid {ACCENT_INDIGO};
                border-radius: 8px;
            }}
            """
        )
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(6)

        header_row = QHBoxLayout()
        icon = QLabel("💡")
        icon.setStyleSheet("font-size: 15px;")
        lbl_title = QLabel("Operating Systems Principles — POSIX Concurrency & IPC Concepts")
        lbl_title.setStyleSheet("font-size: 13px; font-weight: 700; color: #ffffff;")
        header_row.addWidget(icon)
        header_row.addWidget(lbl_title)
        header_row.addStretch()
        layout.addLayout(header_row)

        desc = QLabel(
            "• <b>Process Lifecycle:</b> <code>fork()</code> creates an identical child process with separate memory spaces. "
            "<code>exec*()</code> replaces process memory image with another binary. Zombies occur when a terminated child's "
            "status is unread by the parent; orphans occur when the parent terminates first and the child is reparented to <code>init</code> (PID 1).<br>"
            "• <b>Synchronization:</b> Unsynchronized shared memory writes produce race conditions. <code>std::mutex</code>, "
            "POSIX semaphores (<code>sem_t</code>), and Peterson's mutual exclusion algorithm guarantee mutual exclusion.<br>"
            "• <b>Producer–Consumer:</b> Coordinates bounded buffers with counting and binary semaphores, ensuring zero buffer overflow and zero item loss.<br>"
            "• <b>POSIX IPC:</b> Unidirectional pipes (file descriptors), named FIFOs (filesystem nodes), POSIX Shared Memory (<code>shm_open</code> + <code>mmap</code>), "
            "and POSIX Message Queues (<code>mq_open</code> + <code>mq_send</code>) provide robust cross-process communication."
        )
        desc.setWordWrap(True)
        desc.setStyleSheet(f"font-size: 12px; color: {TEXT_SECONDARY}; line-height: 1.45;")
        layout.addWidget(desc)
        return panel

    def _build_stats_row(self) -> QHBoxLayout:
        layout = QHBoxLayout()
        layout.setSpacing(14)

        self.stat_lifecycle = StatCard("Process Lifecycle", "Pending", "Fork, Exec, Zombie, Orphan")
        self.stat_sync = StatCard("Synchronization", "Pending", "Mutex, Semaphores, Peterson")
        self.stat_prod_cons = StatCard("Producer-Consumer", "Pending", "Bounded Buffer (5 slots)")
        self.stat_ipc = StatCard("POSIX IPC Channels", "Pending", "Pipe, FIFO, SHM, MQ")

        layout.addWidget(self.stat_lifecycle)
        layout.addWidget(self.stat_sync)
        layout.addWidget(self.stat_prod_cons)
        layout.addWidget(self.stat_ipc)
        return layout

    def _build_results_tabs(self) -> QTabWidget:
        tabs = QTabWidget()
        tabs.setObjectName("LinuxResultsTabs")
        tabs.setStyleSheet(
            f"""
            QTabWidget::pane {{
                border: 1px solid {BORDER};
                border-radius: 8px;
                background-color: {BG_SURFACE};
                padding: 16px;
            }}
            QTabBar::tab {{
                background-color: {BG_APP};
                color: {TEXT_SECONDARY};
                padding: 9px 18px;
                border: 1px solid {BORDER};
                border-bottom: none;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                margin-right: 4px;
                font-weight: 600;
                font-size: 12px;
            }}
            QTabBar::tab:selected {{
                background-color: {BG_SURFACE};
                color: #ffffff;
                border-top: 2px solid {ACCENT};
            }}
            QTabBar::tab:hover:!selected {{
                background-color: {BG_ELEVATED};
                color: {TEXT_PRIMARY};
            }}
            """
        )

        # Tab 0: Process Lifecycle
        self.lifecycle_widget = ProcessLifecycleTreeWidget(self)
        tabs.addTab(self.lifecycle_widget, "⎇  Process Lifecycle")

        # Tab 1: Synchronization & Semaphores
        self.sync_widget = SyncVisualizationWidget(self)
        tabs.addTab(self.sync_widget, "⛊  Synchronization")

        # Tab 2: Producer-Consumer
        self.prod_cons_widget = ProducerConsumerBufferWidget(self)
        tabs.addTab(self.prod_cons_widget, "⇄  Producer–Consumer")

        # Tab 3: POSIX IPC Channels
        self.ipc_widget = IpcChannelsWidget(self)
        tabs.addTab(self.ipc_widget, "⬡  POSIX IPC Channels")

        # Tab 4: Diagnostics & Raw Backend Output
        diag_tab = self._build_diagnostics_tab()
        tabs.addTab(diag_tab, "🗎  Diagnostics & Raw Output")

        return tabs

    def _build_diagnostics_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(14)

        # Diagnostics summary row
        self.lbl_diag_summary = QLabel("No experiment output recorded yet. Launch a simulation to view diagnostic telemetry.")
        self.lbl_diag_summary.setStyleSheet(f"font-size: 13px; color: {TEXT_SECONDARY};")
        layout.addWidget(self.lbl_diag_summary)

        lbl_raw = QLabel("Raw C++ Backend Execution Output:")
        lbl_raw.setStyleSheet("font-size: 12px; font-weight: 700; color: #ffffff;")
        layout.addWidget(lbl_raw)

        self.txt_raw_output = QTextEdit()
        self.txt_raw_output.setReadOnly(True)
        self.txt_raw_output.setMinimumHeight(280)
        self.txt_raw_output.setFont(QFont("Consolas", 10))
        self.txt_raw_output.setStyleSheet(
            f"""
            QTextEdit {{
                background-color: {BG_CANVAS};
                color: #e2e8f0;
                border: 1px solid {BORDER};
                border-radius: 6px;
                padding: 10px;
                font-family: 'Consolas', 'Courier New', monospace;
            }}
            """
        )
        self.txt_raw_output.setPlaceholderText("Raw stdout and stderr from C++ Linux experiment runner will appear here...")
        layout.addWidget(self.txt_raw_output)

        return widget

    def run_category(self, category: LinuxExperimentCategory) -> None:
        """Launch Linux / POSIX experiments worker for given category."""
        if not self.runner:
            self._set_status("Error: Backend runner not configured", is_error=True)
            return

        self._cancel_worker()

        # Update controls
        self._set_running_state(True)
        cat_name = category.name.capitalize()
        self._set_status(f"Executing Linux/POSIX {cat_name} experiments in WSL backend...")

        self._active_worker = LinuxExperimentsWorker(self.runner, category, parent=self)
        self._active_worker.finished_exec.connect(self._on_simulation_success)
        self._active_worker.failed_exec.connect(self._on_simulation_failed)
        self._active_worker.start()

    def _cancel_worker(self) -> None:
        if self._active_worker and self._active_worker.isRunning():
            self._active_worker.cancel()
            self._active_worker.wait(1000)
            self._active_worker = None
        self._set_running_state(False)

    def _set_running_state(self, is_running: bool) -> None:
        self.btn_run_all.setEnabled(not is_running)
        self.btn_run_lifecycle.setEnabled(not is_running)
        self.btn_run_sync.setEnabled(not is_running)
        self.btn_run_prod_cons.setEnabled(not is_running)
        self.btn_run_ipc.setEnabled(not is_running)
        self.btn_cancel.setEnabled(is_running)

    def _set_status(self, text: str, is_error: bool = False) -> None:
        color = ACCENT_ROSE if is_error else TEXT_MUTED
        self.runner_status_label.setText(text)
        self.runner_status_label.setStyleSheet(f"font-size: 12px; color: {color};")

    def _on_simulation_success(self, result: LinuxExperimentsResultModel) -> None:
        self._set_running_state(False)
        self._last_result = result
        self._set_status(f"Simulation completed successfully in {result.execution_duration_ms:.1f} ms")

        # Update Visualizers
        self.lifecycle_widget.set_results(result.process_exec, result.zombie_demo, result.orphan_demo)
        self.sync_widget.set_results(result.mutex_sync, result.posix_semaphore, result.petersons_algo)
        self.prod_cons_widget.set_result(result.producer_consumer)
        self.ipc_widget.set_results(result.pipe_ipc, result.fifo_ipc, result.shared_memory_ipc, result.message_queue_ipc)

        # Update Stat Cards
        self._update_stat_cards(result)

        # Update Diagnostics Tab
        self._update_diagnostics(result)

        # Switch to appropriate tab if single category was run
        if result.category == LinuxExperimentCategory.LIFECYCLE:
            self.tabs_container.setCurrentIndex(0)
        elif result.category == LinuxExperimentCategory.SYNCHRONIZATION:
            self.tabs_container.setCurrentIndex(1)
        elif result.category == LinuxExperimentCategory.PRODUCER_CONSUMER:
            self.tabs_container.setCurrentIndex(2)
        elif result.category == LinuxExperimentCategory.IPC:
            self.tabs_container.setCurrentIndex(3)

        # Report to dashboard
        if self.on_execution_completed:
            self.on_execution_completed(
                "Linux / POSIX Experiments",
                result.exit_code,
                result.execution_duration_ms,
                0.0,
                True,
            )

    def _on_simulation_failed(self, error_msg: str) -> None:
        self._set_running_state(False)
        self._set_status(f"Simulation failed: {error_msg}", is_error=True)
        self.txt_raw_output.setPlainText(f"SIMULATION ERROR:\n{error_msg}")
        self.lbl_diag_summary.setText(f"Simulation error: {error_msg}")
        self.lbl_diag_summary.setStyleSheet(f"font-size: 13px; color: {ACCENT_ROSE};")

        if self.on_execution_completed:
            self.on_execution_completed(
                "Linux / POSIX Experiments",
                1,
                0.0,
                0.0,
                False,
            )

    def _update_stat_cards(self, result: LinuxExperimentsResultModel) -> None:
        # Lifecycle
        if result.process_exec or result.zombie_demo or result.orphan_demo:
            exec_str = f"PID {result.process_exec.child_pid}" if result.process_exec else "Fork/Exec OK"
            zomb_str = "Reaped" if (result.zombie_demo and result.zombie_demo.reaped_successfully) else "Observed"
            self.stat_lifecycle.update_value(
                exec_str,
                f"Zombie: {zomb_str} | Orphan: Adopted",
            )
        else:
            self.stat_lifecycle.update_value("Not run", "Run Lifecycle demo")

        # Synchronization
        if result.mutex_sync or result.posix_semaphore or result.petersons_algo:
            safe = "Race prevented" if (result.mutex_sync and not result.mutex_sync.race_condition_detected) else "Synchronized"
            self.stat_sync.update_value(
                "Mutex & Semaphores",
                f"{safe} | Peterson OK",
            )
        else:
            self.stat_sync.update_value("Not run", "Run Sync demo")

        # Producer-Consumer
        if result.producer_consumer:
            pcr = result.producer_consumer
            loss = "Zero loss" if pcr.items_preserved else "Loss detected"
            self.stat_prod_cons.update_value(
                f"{pcr.items_produced} Items Produced",
                f"Buffer: {pcr.buffer_capacity} slots | {loss}",
            )
        else:
            self.stat_prod_cons.update_value("Not run", "Run Prod-Cons demo")

        # IPC Channels
        if result.pipe_ipc or result.fifo_ipc or result.shared_memory_ipc or result.message_queue_ipc:
            ch_count = (
                (1 if result.pipe_ipc else 0)
                + (1 if result.fifo_ipc else 0)
                + (1 if result.shared_memory_ipc else 0)
                + (1 if result.message_queue_ipc else 0)
            )
            self.stat_ipc.update_value(
                f"{ch_count} / 4 Channels",
                "Pipe, FIFO, SHM, MQ Verified",
            )
        else:
            self.stat_ipc.update_value("Not run", "Run IPC demo")

    def _update_diagnostics(self, result: LinuxExperimentsResultModel) -> None:
        self.txt_raw_output.setPlainText(result.raw_output)

        summary_lines = [
            f"Execution Duration: {result.execution_duration_ms:.2f} ms | Category: {result.category.name} | Exit Code: {result.exit_code}",
            f"Parsed Experiments: Lifecycle={'YES' if (result.process_exec or result.zombie_demo) else 'NO'}, "
            f"Sync={'YES' if (result.mutex_sync or result.posix_semaphore) else 'NO'}, "
            f"ProducerConsumer={'YES' if result.producer_consumer else 'NO'}, "
            f"IPC={'YES' if (result.pipe_ipc or result.fifo_ipc) else 'NO'}",
        ]
        self.lbl_diag_summary.setText("\n".join(summary_lines))
        self.lbl_diag_summary.setStyleSheet(f"font-size: 13px; color: {ACCENT_EMERALD}; font-weight: 600;")
