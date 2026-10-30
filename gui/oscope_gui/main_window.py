"""Main desktop application window for OScope Operating Systems Simulation Lab."""

from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QButtonGroup,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from .backend.runner import BaseBackendRunner
from .pages.address_translation_page import AddressTranslationPage
from .pages.dashboard_page import DashboardPage
from .pages.deadlock_page import DeadlockPage
from .pages.disk_page import DiskPage
from .pages.filesystem_page import FilesystemPage
from .pages.host_monitor_page import HostMonitorPage
from .pages.linux_page import LinuxExperimentsPage
from .pages.memory_page import MemoryAllocationPage
from .pages.paging_page import PageReplacementPage
from .pages.process_lifecycle_page import ProcessLifecyclePage
from .pages.scheduling_page import SchedulingPage

from .theme import (
    ACCENT,
    ACCENT_HOVER,
    ACCENT_INDIGO,
    BG_APP,
    BG_SIDEBAR,
    BG_SURFACE,
    BORDER,
    MAIN_STYLESHEET,
    TEXT_MUTED,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
)
from .widgets.status_badge import StatusBadge


class MainWindow(QMainWindow):
    """Main desktop application window for OScope Operating Systems Simulation Lab."""

    def __init__(self, runner: BaseBackendRunner, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.runner = runner

        self.setWindowTitle("OScope — Operating Systems Simulation Platform")
        self.resize(1260, 800)
        self.setMinimumSize(1024, 660)

        # Apply global theme stylesheet
        self.setStyleSheet(MAIN_STYLESHEET)

        # Root layout: Sidebar on left, StackedWidget on right
        central_widget = QWidget()
        central_widget.setStyleSheet(f"background-color: {BG_APP};")
        self.setCentralWidget(central_widget)

        root_layout = QHBoxLayout(central_widget)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # 1. Sidebar Frame
        self.sidebar = self._build_sidebar()
        root_layout.addWidget(self.sidebar)

        # 2. Main Content Stack
        self.stack = QStackedWidget()
        self.stack.setStyleSheet(f"background-color: {BG_APP};")

        # Pages
        self.dashboard_page = DashboardPage(
            runner=self.runner,
            navigate_to_page=self.navigate_to_page,
        )
        self.scheduling_page = SchedulingPage(
            runner=self.runner,
            on_execution_completed=self.dashboard_page.record_execution,
        )
        self.memory_page = MemoryAllocationPage(
            runner=self.runner,
            on_execution_completed=self.dashboard_page.record_execution,
        )
        self.paging_page = PageReplacementPage(
            runner=self.runner,
            on_execution_completed=self.dashboard_page.record_execution,
        )
        self.deadlock_page = DeadlockPage(
            runner=self.runner,
            on_execution_completed=self.dashboard_page.record_execution,
        )
        self.disk_page = DiskPage(
            runner=self.runner,
            on_execution_completed=self.dashboard_page.record_execution,
        )
        self.linux_page = LinuxExperimentsPage(
            runner=self.runner,
            on_execution_completed=self.dashboard_page.record_execution,
        )
        self.host_monitor_page = HostMonitorPage(
            runner=self.runner,
            on_execution_completed=self.dashboard_page.record_execution,
        )
        self.filesystem_page = FilesystemPage(
            runner=self.runner,
            on_execution_completed=self.dashboard_page.record_execution,
        )
        self.address_translation_page = AddressTranslationPage(
            runner=self.runner,
        )
        self.process_lifecycle_page = ProcessLifecyclePage(
            runner=self.runner,
        )

        self.stack.addWidget(self.dashboard_page)              # Index 0
        self.stack.addWidget(self.scheduling_page)             # Index 1
        self.stack.addWidget(self.memory_page)                 # Index 2
        self.stack.addWidget(self.paging_page)                 # Index 3
        self.stack.addWidget(self.deadlock_page)               # Index 4
        self.stack.addWidget(self.disk_page)                   # Index 5
        self.stack.addWidget(self.linux_page)                  # Index 6
        self.stack.addWidget(self.host_monitor_page)           # Index 7
        self.stack.addWidget(self.filesystem_page)             # Index 8
        self.stack.addWidget(self.address_translation_page)     # Index 9
        self.stack.addWidget(self.process_lifecycle_page)       # Index 10

        root_layout.addWidget(self.stack, stretch=1)



        # Default to Dashboard
        self.nav_btn_dash.setChecked(True)

    def _build_sidebar(self) -> QFrame:
        frame = QFrame()
        frame.setObjectName("SidebarFrame")
        frame.setFixedWidth(240)
        frame.setStyleSheet(
            f"""
            QFrame#SidebarFrame {{
                background-color: {BG_SIDEBAR};
                border-right: 1px solid {BORDER};
            }}
            """
        )

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(14, 20, 14, 16)
        layout.setSpacing(8)

        # App Brand Header with Emblem
        brand_container = QHBoxLayout()
        brand_container.setSpacing(10)

        logo_badge = QLabel("OS")
        logo_badge.setFixedSize(32, 32)
        logo_badge.setAlignment(Qt.AlignCenter)
        logo_badge.setStyleSheet(
            f"""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {ACCENT}, stop:1 {ACCENT_INDIGO});
            color: #ffffff;
            font-size: 14px;
            font-weight: 800;
            border-radius: 6px;
            border: 1px solid rgba(255, 255, 255, 0.2);
            """
        )

        brand_text_layout = QVBoxLayout()
        brand_text_layout.setSpacing(1)

        lbl_app = QLabel("OScope")
        lbl_app.setStyleSheet("font-size: 18px; font-weight: 800; color: #ffffff; letter-spacing: 0.5px;")

        lbl_tag = QLabel("OS Simulation Lab")
        lbl_tag.setStyleSheet(f"font-size: 11px; color: {TEXT_SECONDARY};")

        brand_text_layout.addWidget(lbl_app)
        brand_text_layout.addWidget(lbl_tag)

        brand_container.addWidget(logo_badge)
        brand_container.addLayout(brand_text_layout)
        brand_container.addStretch()

        layout.addLayout(brand_container)
        layout.addSpacing(16)

        # Navigation Category: Active Experiments
        lbl_nav_header = QLabel("EXPERIMENTS")
        lbl_nav_header.setStyleSheet(
            f"font-size: 10px; font-weight: 700; color: {TEXT_MUTED}; letter-spacing: 1px; margin-left: 6px;"
        )
        layout.addWidget(lbl_nav_header)

        self.nav_group = QButtonGroup(self)
        self.nav_group.setExclusive(True)

        self.nav_btn_dash = QPushButton("  Overview Dashboard")
        self.nav_btn_dash.setProperty("class", "nav-btn")
        self.nav_btn_dash.setCheckable(True)
        self.nav_btn_dash.clicked.connect(lambda: self.navigate_to_page("dashboard"))
        self.nav_group.addButton(self.nav_btn_dash)
        layout.addWidget(self.nav_btn_dash)

        self.nav_btn_sched = QPushButton("  CPU Scheduling")
        self.nav_btn_sched.setProperty("class", "nav-btn")
        self.nav_btn_sched.setCheckable(True)
        self.nav_btn_sched.clicked.connect(lambda: self.navigate_to_page("scheduling"))
        self.nav_group.addButton(self.nav_btn_sched)
        layout.addWidget(self.nav_btn_sched)

        self.nav_btn_mem = QPushButton("  Memory Allocation")
        self.nav_btn_mem.setProperty("class", "nav-btn")
        self.nav_btn_mem.setCheckable(True)
        self.nav_btn_mem.clicked.connect(lambda: self.navigate_to_page("memory"))
        self.nav_group.addButton(self.nav_btn_mem)
        layout.addWidget(self.nav_btn_mem)

        self.nav_btn_page = QPushButton("  Page Replacement")
        self.nav_btn_page.setProperty("class", "nav-btn")
        self.nav_btn_page.setCheckable(True)
        self.nav_btn_page.clicked.connect(lambda: self.navigate_to_page("paging"))
        self.nav_group.addButton(self.nav_btn_page)
        layout.addWidget(self.nav_btn_page)

        self.nav_btn_deadlock = QPushButton("  Deadlock Management")
        self.nav_btn_deadlock.setProperty("class", "nav-btn")
        self.nav_btn_deadlock.setCheckable(True)
        self.nav_btn_deadlock.clicked.connect(lambda: self.navigate_to_page("deadlock"))
        self.nav_group.addButton(self.nav_btn_deadlock)
        layout.addWidget(self.nav_btn_deadlock)

        self.nav_btn_disk = QPushButton("  Disk Scheduling")
        self.nav_btn_disk.setProperty("class", "nav-btn")
        self.nav_btn_disk.setCheckable(True)
        self.nav_btn_disk.clicked.connect(lambda: self.navigate_to_page("disk"))
        self.nav_group.addButton(self.nav_btn_disk)
        layout.addWidget(self.nav_btn_disk)

        self.nav_btn_linux = QPushButton("  Linux / POSIX IPC")
        self.nav_btn_linux.setProperty("class", "nav-btn")
        self.nav_btn_linux.setCheckable(True)
        self.nav_btn_linux.clicked.connect(lambda: self.navigate_to_page("linux"))
        self.nav_group.addButton(self.nav_btn_linux)
        layout.addWidget(self.nav_btn_linux)

        self.nav_btn_monitor = QPushButton("  Host Monitoring")
        self.nav_btn_monitor.setProperty("class", "nav-btn")
        self.nav_btn_monitor.setCheckable(True)
        self.nav_btn_monitor.clicked.connect(lambda: self.navigate_to_page("monitor"))
        self.nav_group.addButton(self.nav_btn_monitor)
        layout.addWidget(self.nav_btn_monitor)

        self.nav_btn_fs = QPushButton("  Simulated File System")
        self.nav_btn_fs.setProperty("class", "nav-btn")
        self.nav_btn_fs.setCheckable(True)
        self.nav_btn_fs.clicked.connect(lambda: self.navigate_to_page("filesystem"))
        self.nav_group.addButton(self.nav_btn_fs)
        layout.addWidget(self.nav_btn_fs)

        self.nav_btn_vm = QPushButton("  Virtual Memory & MMU")
        self.nav_btn_vm.setProperty("class", "nav-btn")
        self.nav_btn_vm.setCheckable(True)
        self.nav_btn_vm.clicked.connect(lambda: self.navigate_to_page("translation"))
        self.nav_group.addButton(self.nav_btn_vm)
        layout.addWidget(self.nav_btn_vm)

        self.nav_btn_lifecycle = QPushButton("  Process Lifecycle")
        self.nav_btn_lifecycle.setProperty("class", "nav-btn")
        self.nav_btn_lifecycle.setCheckable(True)
        self.nav_btn_lifecycle.clicked.connect(lambda: self.navigate_to_page("lifecycle"))
        self.nav_group.addButton(self.nav_btn_lifecycle)
        layout.addWidget(self.nav_btn_lifecycle)

        layout.addSpacing(16)

        layout.addStretch()

        # Bottom: Student-friendly status indicator
        status_box = QFrame()
        status_box.setStyleSheet(
            f"""
            QFrame {{
                background-color: {BG_SURFACE};
                border: 1px solid {BORDER};
                border-radius: 8px;
                padding: 6px;
            }}
            """
        )
        sb_layout = QVBoxLayout(status_box)
        sb_layout.setContentsMargins(8, 8, 8, 8)
        sb_layout.setSpacing(4)

        info = self.runner.get_info()
        status_text = "Ready to run experiments" if info.is_available else "Engine unavailable"
        status_state = "success" if info.is_available else "error"

        self.sidebar_badge = StatusBadge(status_text, status_state)
        sb_layout.addWidget(self.sidebar_badge)

        layout.addWidget(status_box)

        return frame

    def navigate_to_page(self, page_name: str) -> None:
        """Switch stacked page between dashboard, scheduling, memory, paging, deadlock, disk, linux, monitor, filesystem, translation, and lifecycle."""
        self.current_page = page_name
        if page_name == "dashboard":
            self.stack.setCurrentIndex(0)
            self.nav_btn_dash.setChecked(True)
            self.dashboard_page.refresh_backend_status()
        elif page_name == "scheduling":
            self.stack.setCurrentIndex(1)
            self.nav_btn_sched.setChecked(True)
        elif page_name == "memory":
            self.stack.setCurrentIndex(2)
            self.nav_btn_mem.setChecked(True)
        elif page_name == "paging":
            self.stack.setCurrentIndex(3)
            self.nav_btn_page.setChecked(True)
        elif page_name == "deadlock":
            self.stack.setCurrentIndex(4)
            self.nav_btn_deadlock.setChecked(True)
        elif page_name == "disk":
            self.stack.setCurrentIndex(5)
            self.nav_btn_disk.setChecked(True)
        elif page_name == "linux":
            self.stack.setCurrentIndex(6)
            self.nav_btn_linux.setChecked(True)
        elif page_name == "monitor":
            self.stack.setCurrentIndex(7)
            self.nav_btn_monitor.setChecked(True)
        elif page_name in ("filesystem", "fs"):
            self.stack.setCurrentIndex(8)
            self.nav_btn_fs.setChecked(True)
        elif page_name in ("translation", "vm", "address_translation"):
            self.stack.setCurrentIndex(9)
            self.nav_btn_vm.setChecked(True)
        elif page_name in ("lifecycle", "process", "process_lifecycle"):
            self.stack.setCurrentIndex(10)
            self.nav_btn_lifecycle.setChecked(True)

    def closeEvent(self, event) -> None:
        """Ensure any background process worker is cancelled on window close."""
        if self.scheduling_page._active_worker:
            self.scheduling_page._active_worker.cancel()
        if self.memory_page._active_worker:
            self.memory_page._active_worker.cancel()
        if self.paging_page._active_worker:
            self.paging_page._active_worker.cancel()
        if self.deadlock_page._active_worker:
            self.deadlock_page._active_worker.cancel()
        if self.disk_page._active_worker:
            self.disk_page._active_worker.cancel()
        if self.linux_page._active_worker:
            self.linux_page._active_worker.cancel()
        if self.host_monitor_page._active_worker:
            self.host_monitor_page._active_worker.cancel()
        if self.filesystem_page._active_worker:
            self.filesystem_page._active_worker.cancel()
        self.address_translation_page.cleanup()
        self.process_lifecycle_page.cleanup()
        self.paging_page.frame_grid.stop_animation()
        self.runner.cancel()
        super().closeEvent(event)


