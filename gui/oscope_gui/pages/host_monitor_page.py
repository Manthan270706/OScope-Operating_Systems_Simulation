"""Host Resource Monitoring interactive telemetry page.

Displays real-time CPU utilization, memory allocation, storage/disk stats,
process state, and system load observed directly from the Linux / WSL host kernel.
"""

from typing import Callable, Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from ..backend.executor import HostMonitorWorker
from ..backend.runner import BaseBackendRunner
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
from ..widgets.host_monitor_viz import (
    HostDiskTableWidget,
    HostMetricCard,
    HostMetricHistoryPlotWidget,
    HostProcessTableWidget,
)
from ..widgets.status_badge import StatusBadge


class HostMonitorPage(QWidget):
    """Main desktop page for real-time Linux host resource monitoring and telemetry."""

    def __init__(
        self,
        runner: Optional[BaseBackendRunner] = None,
        on_execution_completed: Optional[Callable[[str, int, float, float, bool], None]] = None,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.runner = runner
        self.on_execution_completed = on_execution_completed
        self._active_worker: Optional[HostMonitorWorker] = None
        self._is_monitoring_active: bool = False
        self._sample_count: int = 0
        self._last_snapshot: Optional[HostMonitoringSnapshotModel] = None

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

        # 1. Header
        header = self._build_header()
        self.content_layout.addLayout(header)

        # 2. Control Action Bar Card
        action_card = self._build_action_card()
        self.content_layout.addWidget(action_card)

        # 3. Educational Guidance & Environment Transparency Section
        guidance = self._build_guidance_section()
        self.content_layout.addWidget(guidance)

        # 4. Top Telemetry Cards Row (4 cards)
        self.cards_layout = self._build_cards_row()
        self.content_layout.addLayout(self.cards_layout)

        # 5. Detailed Telemetry Tabs
        self.tabs_container = self._build_results_tabs()
        self.content_layout.addWidget(self.tabs_container)

        scroll.setWidget(content)
        main_layout.addWidget(scroll)

    def _build_header(self) -> QVBoxLayout:
        layout = QVBoxLayout()
        layout.setSpacing(6)

        title_row = QHBoxLayout()
        title_row.setSpacing(12)

        title = QLabel("Host Resource Monitoring")
        title.setStyleSheet("font-size: 24px; font-weight: 800; color: #172033; letter-spacing: 0.5px;")
        title_row.addWidget(title)

        self.scope_badge = StatusBadge("WSL Linux Kernel Observation", "success")
        title_row.addWidget(self.scope_badge)
        title_row.addStretch()

        subtitle = QLabel(
            "Live real-time Linux host telemetry observed directly through kernel /proc/stat, /proc/meminfo, "
            "/proc/uptime, /proc/loadavg, /proc/diskstats, and POSIX statvfs interfaces."
        )
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet(f"font-size: 13px; color: {TEXT_SECONDARY}; line-height: 1.4;")

        layout.addLayout(title_row)
        layout.addWidget(subtitle)
        return layout

    def _build_action_card(self) -> QFrame:
        card = QFrame()
        card.setProperty("card", True)
        card.setObjectName("HostMonitorActionCard")
        card.setStyleSheet(
            f"""
            QFrame#HostMonitorActionCard {{
                background-color: {BG_SURFACE};
                border: 1px solid {BORDER};
                border-radius: 10px;
            }}
            """
        )
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)

        top_row = QHBoxLayout()
        top_row.setSpacing(10)

        lbl_controls = QLabel("Telemetry Sampling & Polling Engine")
        lbl_controls.setStyleSheet("font-size: 14px; font-weight: 700; color: #172033;")
        top_row.addWidget(lbl_controls)
        top_row.addStretch()

        self.lbl_status = QLabel("Ready — Live monitoring stopped")
        self.lbl_status.setStyleSheet(f"font-size: 12px; color: {TEXT_MUTED}; font-style: italic;")
        top_row.addWidget(self.lbl_status)
        layout.addLayout(top_row)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)

        # Primary Toggle Start / Pause
        self.btn_toggle_live = QPushButton("  ▶  Start Live Monitoring")
        self.btn_toggle_live.setProperty("class", "btn-primary")
        self.btn_toggle_live.setFixedHeight(38)
        self.btn_toggle_live.setStyleSheet(
            f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {ACCENT}, stop:1 {ACCENT_INDIGO});
                color: #172033;
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
            """
        )
        self.btn_toggle_live.clicked.connect(self.toggle_live_monitoring)
        btn_row.addWidget(self.btn_toggle_live)

        # Single Shot Sample
        self.btn_sample_once = QPushButton("  ↻  Sample Once")
        self.btn_sample_once.setFixedHeight(38)
        self.btn_sample_once.setStyleSheet(
            f"""
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
                border-color: {ACCENT_CYAN};
                color: #172033;
            }}
            """
        )
        self.btn_sample_once.clicked.connect(self.sample_once)
        btn_row.addWidget(self.btn_sample_once)

        # Polling Interval Selector
        lbl_int = QLabel("Polling Interval:")
        lbl_int.setStyleSheet(f"font-size: 12px; color: {TEXT_SECONDARY}; margin-left: 8px;")
        btn_row.addWidget(lbl_int)

        self.combo_interval = QComboBox()
        self.combo_interval.setFixedHeight(36)
        self.combo_interval.addItem("1.0 Second", 1000)
        self.combo_interval.addItem("2.0 Seconds (Recommended)", 2000)
        self.combo_interval.addItem("3.0 Seconds", 3000)
        self.combo_interval.addItem("5.0 Seconds", 5000)
        self.combo_interval.setCurrentIndex(1)
        self.combo_interval.setStyleSheet(
            f"""
            QComboBox {{
                background-color: {BG_ELEVATED};
                color: #172033;
                border: 1px solid {BORDER};
                border-radius: 6px;
                padding: 4px 12px;
                font-size: 12px;
            }}
            QComboBox::drop-down {{
                border: none;
            }}
            QComboBox QAbstractItemView {{
                background-color: {BG_SURFACE};
                color: #172033;
                border: 1px solid {BORDER};
                selection-background-color: {ACCENT};
            }}
            """
        )
        self.combo_interval.currentIndexChanged.connect(self._on_interval_changed)
        btn_row.addWidget(self.combo_interval)

        btn_row.addStretch()

        self.lbl_sample_badge = QLabel("Samples: 0")
        self.lbl_sample_badge.setStyleSheet(
            f"font-size: 11px; font-weight: 700; color: {TEXT_MUTED}; background-color: {BG_CANVAS}; "
            f"padding: 4px 10px; border-radius: 4px; border: 1px solid {BORDER};"
        )
        btn_row.addWidget(self.lbl_sample_badge)

        layout.addLayout(btn_row)
        return card

    def _build_guidance_section(self) -> QFrame:
        panel = QFrame()
        panel.setProperty("card", True)
        panel.setObjectName("HostMonitorGuidancePanel")
        panel.setStyleSheet(
            f"""
            QFrame#HostMonitorGuidancePanel {{
                background-color: {BG_SURFACE};
                border: 1px solid {BORDER};
                border-left: 4px solid {ACCENT_CYAN};
                border-radius: 8px;
            }}
            """
        )
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(6)

        header_row = QHBoxLayout()
        icon = QLabel("🔍")
        icon.setStyleSheet("font-size: 15px;")
        lbl_title = QLabel("Telemetry Scope & Ground Truth Transparency")
        lbl_title.setStyleSheet("font-size: 13px; font-weight: 700; color: #172033;")
        header_row.addWidget(icon)
        header_row.addWidget(lbl_title)
        header_row.addStretch()
        layout.addLayout(header_row)

        desc = QLabel(
            "• <b>Live WSL Linux Host Observation:</b> These measurements represent real operating system metrics from the "
            "WSL Linux kernel environment (not simulated OS algorithms and not native Windows host metrics).<br>"
            "• <b>Zero Fabrication Guarantee:</b> Metrics are parsed directly from authoritative kernel interfaces "
            "(<code>/proc/stat</code> for CPU jiffies, <code>/proc/meminfo</code> for RAM pages, <code>/proc/uptime</code>, "
            "<code>/proc/loadavg</code>, <code>/proc/diskstats</code>, and <code>statvfs</code>). If collection fails, "
            "measurements are flagged as unavailable rather than approximated.<br>"
            "• <b>Background Polling:</b> Telemetry is sampled asynchronously on a background worker thread, ensuring "
            "that the desktop UI thread remains completely fluid and responsive."
        )
        desc.setWordWrap(True)
        desc.setStyleSheet(f"font-size: 12px; color: {TEXT_SECONDARY}; line-height: 1.45;")
        layout.addWidget(desc)
        return panel

    def _build_cards_row(self) -> QHBoxLayout:
        layout = QHBoxLayout()
        layout.setSpacing(14)

        self.card_cpu = HostMetricCard("CPU UTILIZATION (/proc/stat)", ACCENT_CYAN)
        self.card_mem = HostMetricCard("MEMORY UTILIZATION (/proc/meminfo)", ACCENT_EMERALD)
        self.card_disk = HostMetricCard("STORAGE & FILESYSTEM (statvfs)", ACCENT_AMBER)
        self.card_sys = HostMetricCard("SYSTEM LOAD & UPTIME (/proc/loadavg)", ACCENT_VIOLET)

        layout.addWidget(self.card_cpu)
        layout.addWidget(self.card_mem)
        layout.addWidget(self.card_disk)
        layout.addWidget(self.card_sys)
        return layout

    def _build_results_tabs(self) -> QTabWidget:
        tabs = QTabWidget()
        tabs.setObjectName("HostMonitorTabs")
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
                color: #172033;
                border-top: 2px solid {ACCENT_CYAN};
            }}
            QTabBar::tab:hover:!selected {{
                background-color: {BG_ELEVATED};
                color: {TEXT_PRIMARY};
            }}
            """
        )

        # Tab 0: Live Telemetry Charts
        tab_chart = QWidget()
        l_chart = QVBoxLayout(tab_chart)
        l_chart.setContentsMargins(8, 8, 8, 8)
        l_chart.setSpacing(10)

        lbl_chart_desc = QLabel("Historical Trend (Last 40 Telemetry Samples):")
        lbl_chart_desc.setStyleSheet(f"font-size: 12px; font-weight: 700; color: {TEXT_PRIMARY};")
        l_chart.addWidget(lbl_chart_desc)

        self.history_plot = HostMetricHistoryPlotWidget(self)
        l_chart.addWidget(self.history_plot)

        tabs.addTab(tab_chart, "📈  Live Telemetry Charts")

        # Tab 1: Process & Kernel State
        tab_proc = QWidget()
        l_proc = QVBoxLayout(tab_proc)
        l_proc.setContentsMargins(8, 8, 8, 8)
        l_proc.setSpacing(10)

        lbl_proc_desc = QLabel("Self-Process Observation (/proc/[pid]/stat):")
        lbl_proc_desc.setStyleSheet(f"font-size: 12px; font-weight: 700; color: {TEXT_PRIMARY};")
        l_proc.addWidget(lbl_proc_desc)

        self.proc_table = HostProcessTableWidget(self)
        l_proc.addWidget(self.proc_table)

        tabs.addTab(tab_proc, "🖥  Process & Kernel State")

        # Tab 2: Storage & Block Device I/O
        tab_disk = QWidget()
        l_disk = QVBoxLayout(tab_disk)
        l_disk.setContentsMargins(8, 8, 8, 8)
        l_disk.setSpacing(10)

        lbl_disk_desc = QLabel("Host Block Device I/O Counters (/proc/diskstats):")
        lbl_disk_desc.setStyleSheet(f"font-size: 12px; font-weight: 700; color: {TEXT_PRIMARY};")
        l_disk.addWidget(lbl_disk_desc)

        self.disk_table = HostDiskTableWidget(self)
        l_disk.addWidget(self.disk_table)

        tabs.addTab(tab_disk, "💽  Storage & Block Device I/O")

        # Tab 3: Diagnostics & Raw Output
        tab_diag = QWidget()
        l_diag = QVBoxLayout(tab_diag)
        l_diag.setContentsMargins(8, 8, 8, 8)
        l_diag.setSpacing(10)

        self.lbl_diag_summary = QLabel("Awaiting live telemetry samples...")
        self.lbl_diag_summary.setStyleSheet(f"font-size: 12px; color: {TEXT_SECONDARY};")
        l_diag.addWidget(self.lbl_diag_summary)

        lbl_raw = QLabel("Raw C++ Backend Execution Output (/proc snapshot):")
        lbl_raw.setStyleSheet("font-size: 12px; font-weight: 700; color: #172033;")
        l_diag.addWidget(lbl_raw)

        self.txt_raw = QTextEdit()
        self.txt_raw.setReadOnly(True)
        self.txt_raw.setMinimumHeight(240)
        self.txt_raw.setFont(QFont("Consolas", 10))
        self.txt_raw.setStyleSheet(
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
        self.txt_raw.setPlaceholderText("Raw stdout from oscope --demo-monitor will appear here...")
        l_diag.addWidget(self.txt_raw)

        tabs.addTab(tab_diag, "🗎  Diagnostics & Raw Output")

        return tabs

    def toggle_live_monitoring(self) -> None:
        """Start or pause continuous background telemetry polling."""
        if self._is_monitoring_active:
            self.stop_monitoring()
        else:
            self.start_monitoring()

    def start_monitoring(self) -> None:
        """Launch background polling worker thread."""
        if not self.runner:
            self._set_status("Error: Backend runner not configured", is_error=True)
            return

        self._stop_active_worker()

        interval_ms = self.combo_interval.currentData() or 2000
        self._active_worker = HostMonitorWorker(
            runner=self.runner,
            poll_interval_ms=interval_ms,
            continuous=True,
            parent=self,
        )
        self._active_worker.sample_received.connect(self._on_sample_received)
        self._active_worker.failed_sample.connect(self._on_sample_failed)
        self._active_worker.monitoring_started.connect(self._on_monitoring_started)
        self._active_worker.monitoring_stopped.connect(self._on_monitoring_stopped)

        self._active_worker.start()
        self._on_monitoring_started()

    def stop_monitoring(self) -> None:
        """Pause continuous polling and update button state."""
        self._stop_active_worker()
        self._on_monitoring_stopped()

    def sample_once(self) -> Optional[HostMonitorWorker]:
        """Take a single telemetry snapshot without continuous polling."""
        if not self.runner:
            self._set_status("Error: Backend runner not configured", is_error=True)
            return None

        self._set_status("Sampling host telemetry from WSL backend...")
        worker = HostMonitorWorker(
            runner=self.runner,
            continuous=False,
            parent=self,
        )
        self._single_worker = worker
        worker.sample_received.connect(self._on_sample_received)
        worker.failed_sample.connect(self._on_sample_failed)
        worker.start()
        return worker

    def _stop_active_worker(self) -> None:
        if self._active_worker and self._active_worker.isRunning():
            self._active_worker.stop()
            self._active_worker.wait(1000)
            self._active_worker = None

    def _on_interval_changed(self) -> None:
        """Restart worker with new interval if currently active."""
        if self._is_monitoring_active:
            self.start_monitoring()

    def _on_monitoring_started(self) -> None:
        self._is_monitoring_active = True
        self.btn_toggle_live.setText("  ⏸  Pause Live Monitoring")
        self.btn_toggle_live.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {BG_ELEVATED};
                color: #172033;
                font-weight: 700;
                font-size: 13px;
                padding: 0 20px;
                border-radius: 6px;
                border: 1px solid {ACCENT_AMBER};
            }}
            QPushButton:hover {{
                border-color: #fde047;
            }}
            """
        )
        interval_sec = (self.combo_interval.currentData() or 2000) / 1000.0
        self._set_status(f"Live telemetry active — sampling every {interval_sec:.1f}s")

    def _on_monitoring_stopped(self) -> None:
        self._is_monitoring_active = False
        self.btn_toggle_live.setText("  ▶  Start Live Monitoring")
        self.btn_toggle_live.setStyleSheet(
            f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {ACCENT}, stop:1 {ACCENT_INDIGO});
                color: #172033;
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
            """
        )
        self._set_status("Live monitoring paused")

    def _on_sample_received(self, snapshot: HostMonitoringSnapshotModel) -> None:
        self._sample_count += 1
        self._last_snapshot = snapshot
        self.lbl_sample_badge.setText(f"Samples: {self._sample_count}")
        self._set_status(f"Live telemetry updated at {snapshot.timestamp}")

        # 1. Update CPU Card
        if snapshot.cpu.valid:
            self.card_cpu.update_metric(
                value_text=f"{snapshot.cpu.total_usage_percent:.1f} %",
                percentage=snapshot.cpu.total_usage_percent,
                detail_text=f"User: {snapshot.cpu.user_percent:.1f}% | Kernel: {snapshot.cpu.system_percent:.1f}% | Idle: {snapshot.cpu.idle_percent:.1f}%",
                is_active=True,
            )
        else:
            self.card_cpu.update_metric("Unavailable", 0.0, "/proc/stat unavailable", is_active=False)

        # 2. Update Memory Card
        if snapshot.memory.valid:
            used_mb = snapshot.memory.used_mb
            tot_mb = snapshot.memory.total_mb
            avail_mb = snapshot.memory.available_mb
            self.card_mem.update_metric(
                value_text=f"{used_mb:.0f} / {tot_mb:.0f} MB ({snapshot.memory.used_percent:.1f}%)",
                percentage=snapshot.memory.used_percent,
                detail_text=f"Available: {avail_mb:.0f} MB | Free RAM: {snapshot.memory.free_kb / 1024.0:.0f} MB",
                is_active=True,
            )
        else:
            self.card_mem.update_metric("Unavailable", 0.0, "/proc/meminfo unavailable", is_active=False)

        # 3. Update Disk Card
        if snapshot.system.valid and snapshot.system.disk_total_bytes > 0:
            used_gb = snapshot.system.disk_used_gb
            tot_gb = snapshot.system.disk_total_gb
            avail_gb = snapshot.system.disk_available_gb
            self.card_disk.update_metric(
                value_text=f"{used_gb:.1f} / {tot_gb:.1f} GB ({snapshot.system.disk_used_percent:.1f}%)",
                percentage=snapshot.system.disk_used_percent,
                detail_text=f"Available: {avail_gb:.1f} GB on '{snapshot.system.root_mount}' filesystem",
                is_active=True,
            )
        else:
            self.card_disk.update_metric("Active", 0.0, f"{len(snapshot.disks)} block devices observed", is_active=True)

        # 4. Update System Card
        if snapshot.system.valid:
            load_str = f"{snapshot.system.load_1min:.2f}, {snapshot.system.load_5min:.2f}, {snapshot.system.load_15min:.2f}"
            proc_str = f"{snapshot.system.total_processes} total ({snapshot.system.running_processes} running)"
            self.card_sys.update_metric(
                value_text=f"Load: {snapshot.system.load_1min:.2f}",
                percentage=min(100.0, snapshot.system.load_1min * 25.0),
                detail_text=f"1/5/15m: [{load_str}] | Procs: {proc_str} | Uptime: {snapshot.system.uptime_formatted}",
                is_active=True,
            )
        else:
            self.card_sys.update_metric("Unavailable", 0.0, "/proc/loadavg unavailable", is_active=False)

        # 5. Update Time-Series History Chart
        cpu_val = snapshot.cpu.total_usage_percent if snapshot.cpu.valid else 0.0
        mem_val = snapshot.memory.used_percent if snapshot.memory.valid else 0.0
        self.history_plot.add_sample(cpu_val, mem_val, snapshot.timestamp)

        # 6. Update Tables
        self.proc_table.update_process(snapshot.self_process)
        self.disk_table.update_disks(snapshot.disks)

        # 7. Update Raw Output
        self.txt_raw.setPlainText(snapshot.raw_output)
        self.lbl_diag_summary.setText(
            f"Source: {snapshot.source} | Environment: {snapshot.environment} | Timestamp: {snapshot.timestamp} | "
            f"Success: {'YES' if snapshot.success else 'NO'}"
        )

        # Dashboard telemetry callback
        if self.on_execution_completed:
            self.on_execution_completed(
                "Host Resource Monitoring",
                0 if snapshot.success else 1,
                0.0,
                float(snapshot.self_process.rss_kb),
                snapshot.success,
            )

    def _on_sample_failed(self, error_msg: str) -> None:
        self._set_status(f"Sampling warning: {error_msg}", is_error=True)
        # Mark cards as stale
        if self._last_snapshot:
            self.card_cpu.update_metric(self.card_cpu.lbl_value.text(), 0.0, "Stale telemetry", is_active=False)
            self.card_mem.update_metric(self.card_mem.lbl_value.text(), 0.0, "Stale telemetry", is_active=False)

    def _set_status(self, text: str, is_error: bool = False) -> None:
        color = ACCENT_ROSE if is_error else TEXT_MUTED
        self.lbl_status.setText(text)
        self.lbl_status.setStyleSheet(f"font-size: 12px; color: {color};")
