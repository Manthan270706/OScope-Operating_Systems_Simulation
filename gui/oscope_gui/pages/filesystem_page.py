"""Simulated File System interactive page.

Visualizes educational in-memory file system simulation modeling contiguous, linked,
and indexed block allocations, directory tree hierarchies, inode metadata, and external fragmentation.
"""

import os
from typing import Callable, List, Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QRadioButton,
    QScrollArea,
    QSizePolicy,
    QSpinBox,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from ..backend.executor import FilesystemWorker
from ..backend.runner import BaseBackendRunner
from ..models.filesystem import (
    FileInodeModel,
    FilesystemAllocationStrategy,
    FilesystemConfig,
    FilesystemOperationInput,
    FilesystemOperationType,
    FilesystemPreset,
    FilesystemSimulationResultModel,
)
from ..theme import (
    ACCENT,
    ACCENT_AMBER,
    ACCENT_CYAN,
    ACCENT_EMERALD,
    ACCENT_HOVER,
    ACCENT_ROSE,
    ACCENT_VIOLET,
    BG_APP,
    BG_CARD,
    BG_DARK,
    BG_SURFACE,
    BORDER,
    BORDER_LIGHT,
    FONT_FAMILY,
    TEXT_MUTED,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
)
from ..widgets.filesystem_viz import (
    BlockAllocationMapWidget,
    DirectoryTreeBrowserWidget,
    FileMetadataPanel,
    FilesystemStatsBar,
)
from ..widgets.status_badge import StatusBadge


class CreateFileDialog(QDialog):
    """Dialog for defining a new simulated file with size and allocation strategy."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Create Simulated File")
        self.setMinimumWidth(380)
        self.setStyleSheet(
            f"""
            QDialog {{
                background-color: {BG_CARD};
                color: {TEXT_PRIMARY};
            }}
            QLabel {{
                color: {TEXT_PRIMARY};
                font-family: {FONT_FAMILY};
                font-size: 12px;
            }}
            QLineEdit, QSpinBox, QComboBox {{
                background-color: {BG_DARK};
                border: 1px solid {BORDER};
                border-radius: 4px;
                color: {TEXT_PRIMARY};
                padding: 6px;
                font-family: {FONT_FAMILY};
            }}
            QLineEdit:focus, QSpinBox:focus, QComboBox:focus {{
                border-color: {ACCENT};
            }}
            QPushButton {{
                background-color: {ACCENT};
                color: #ffffff;
                font-weight: 600;
                padding: 6px 14px;
                border-radius: 4px;
                border: none;
            }}
            QPushButton:hover {{
                background-color: {ACCENT_HOVER};
            }}
            """
        )

        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        form = QFormLayout()
        form.setSpacing(10)

        self.edit_path = QLineEdit("/home/new_file.dat")
        form.addRow("File Path:", self.edit_path)

        self.spin_size = QSpinBox()
        self.spin_size.setRange(1, 1_000_000)
        self.spin_size.setValue(1000)
        self.spin_size.setSuffix(" bytes")
        form.addRow("File Size:", self.spin_size)

        self.combo_strategy = QComboBox()
        self.combo_strategy.addItem("Contiguous Allocation", FilesystemAllocationStrategy.CONTIGUOUS)
        self.combo_strategy.addItem("Linked Allocation", FilesystemAllocationStrategy.LINKED)
        self.combo_strategy.addItem("Indexed Allocation", FilesystemAllocationStrategy.INDEXED)
        self.combo_strategy.setCurrentIndex(2)  # Indexed default
        form.addRow("Allocation Strategy:", self.combo_strategy)

        layout.addLayout(form)

        btn_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btn_box.accepted.connect(self.accept)
        btn_box.rejected.connect(self.reject)
        layout.addWidget(btn_box)

    def get_operation(self) -> FilesystemOperationInput:
        path = self.edit_path.text().strip()
        size_bytes = self.spin_size.value()
        strat = self.combo_strategy.currentData()
        return FilesystemOperationInput(
            op_type=FilesystemOperationType.CREATE,
            path=path,
            size_bytes=size_bytes,
            strategy=strat,
        )


class CreateDirectoryDialog(QDialog):
    """Dialog for creating a new directory path."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Create Simulated Directory")
        self.setMinimumWidth(340)
        self.setStyleSheet(
            f"""
            QDialog {{
                background-color: {BG_CARD};
                color: {TEXT_PRIMARY};
            }}
            QLabel {{
                color: {TEXT_PRIMARY};
                font-family: {FONT_FAMILY};
                font-size: 12px;
            }}
            QLineEdit {{
                background-color: {BG_DARK};
                border: 1px solid {BORDER};
                border-radius: 4px;
                color: {TEXT_PRIMARY};
                padding: 6px;
                font-family: {FONT_FAMILY};
            }}
            QLineEdit:focus {{
                border-color: {ACCENT};
            }}
            QPushButton {{
                background-color: {ACCENT};
                color: #ffffff;
                font-weight: 600;
                padding: 6px 14px;
                border-radius: 4px;
                border: none;
            }}
            QPushButton:hover {{
                background-color: {ACCENT_HOVER};
            }}
            """
        )

        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        form = QFormLayout()
        self.edit_path = QLineEdit("/home/new_folder")
        form.addRow("Directory Path:", self.edit_path)
        layout.addLayout(form)

        btn_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btn_box.accepted.connect(self.accept)
        btn_box.rejected.connect(self.reject)
        layout.addWidget(btn_box)

    def get_operation(self) -> FilesystemOperationInput:
        return FilesystemOperationInput(
            op_type=FilesystemOperationType.MKDIR,
            path=self.edit_path.text().strip(),
        )


class FilesystemPage(QWidget):
    """Dedicated Simulated File System page for the OScope desktop GUI."""

    def __init__(
        self,
        runner: Optional[BaseBackendRunner] = None,
        on_execution_completed: Optional[Callable[[str, int, float, float, bool], None]] = None,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.runner = runner
        self.on_execution_completed = on_execution_completed
        self._active_worker: Optional[FilesystemWorker] = None
        self._custom_operations: List[FilesystemOperationInput] = []
        self._last_result: Optional[FilesystemSimulationResultModel] = None

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet(f"background-color: {BG_APP}; border: none;")

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(24, 20, 24, 24)
        layout.setSpacing(18)

        # 1. Header & Title
        header_layout = QVBoxLayout()
        header_layout.setSpacing(4)
        title = QLabel("Simulated File System")
        title.setStyleSheet(f"font-size: 22px; font-weight: 800; color: {TEXT_PRIMARY}; font-family: {FONT_FAMILY};")
        subtitle = QLabel(
            "In-memory educational file system model analyzing contiguous, linked, and indexed block allocations, directory trees, inode metadata, and external fragmentation."
        )
        subtitle.setStyleSheet(f"font-size: 13px; color: {TEXT_SECONDARY}; font-family: {FONT_FAMILY};")
        header_layout.addWidget(title)
        header_layout.addWidget(subtitle)
        layout.addLayout(header_layout)

        # 2. Guidance / Simulation Notice Banner
        notice_banner = QFrame()
        notice_banner.setStyleSheet(
            f"""
            QFrame {{
                background-color: #0c1a2e;
                border: 1px solid #1e3a5f;
                border-left: 4px solid {ACCENT_CYAN};
                border-radius: 6px;
                padding: 10px 14px;
            }}
            """
        )
        notice_layout = QVBoxLayout(notice_banner)
        notice_layout.setContentsMargins(0, 0, 0, 0)
        notice_layout.setSpacing(4)
        notice_title = QLabel("EDUCATIONAL SIMULATION NOTICE")
        notice_title.setStyleSheet(f"font-size: 11px; font-weight: 700; color: {ACCENT_CYAN}; letter-spacing: 0.5px;")
        notice_text = QLabel(
            "This module interacts with the C++ SimpleFilesystem simulation running inside WSL. It models fixed-size disk blocks, allocation strategies, directory trees, and physical bitmaps in memory. File byte content is not stored. Results reflect true backend execution without fabrication."
        )
        notice_text.setWordWrap(True)
        notice_text.setStyleSheet(f"font-size: 11px; color: {TEXT_SECONDARY}; line-height: 1.4;")
        notice_layout.addWidget(notice_title)
        notice_layout.addWidget(notice_text)
        layout.addWidget(notice_banner)

        # 3. Action / Control Bar Card
        ctrl_card = QFrame()
        ctrl_card.setObjectName("ControlCard")
        ctrl_card.setStyleSheet(
            f"""
            QFrame#ControlCard {{
                background-color: {BG_CARD};
                border: 1px solid {BORDER};
                border-radius: 8px;
            }}
            QLabel {{
                color: {TEXT_PRIMARY};
                font-family: {FONT_FAMILY};
                font-size: 12px;
                font-weight: 600;
            }}
            QComboBox, QSpinBox {{
                background-color: {BG_DARK};
                border: 1px solid {BORDER};
                border-radius: 4px;
                color: {TEXT_PRIMARY};
                padding: 6px 8px;
                font-family: {FONT_FAMILY};
                font-size: 12px;
            }}
            QComboBox:focus, QSpinBox:focus {{
                border-color: {ACCENT};
            }}
            """
        )
        ctrl_layout = QVBoxLayout(ctrl_card)
        ctrl_layout.setContentsMargins(16, 14, 16, 14)
        ctrl_layout.setSpacing(12)

        ctrl_row = QHBoxLayout()
        ctrl_row.setSpacing(14)

        # Preset selector
        preset_box = QVBoxLayout()
        preset_box.setSpacing(4)
        preset_lbl = QLabel("Workload Preset:")
        self.combo_preset = QComboBox()
        self.combo_preset.addItem("Three-Strategy Comparison Demo", FilesystemPreset.STANDARD_DEMO)
        self.combo_preset.addItem("External Fragmentation Benchmark", FilesystemPreset.FRAGMENTATION)
        self.combo_preset.addItem("Disk Capacity Exhaustion & Recovery", FilesystemPreset.CAPACITY_LIMIT)
        self.combo_preset.addItem("Custom Operations Workload", FilesystemPreset.CUSTOM_WORKLOAD)
        self.combo_preset.currentIndexChanged.connect(self._on_preset_changed)
        preset_box.addWidget(preset_lbl)
        preset_box.addWidget(self.combo_preset)
        ctrl_row.addLayout(preset_box, 3)

        # Total blocks
        blocks_box = QVBoxLayout()
        blocks_box.setSpacing(4)
        blocks_lbl = QLabel("Total Blocks:")
        self.spin_blocks = QSpinBox()
        self.spin_blocks.setRange(4, 256)
        self.spin_blocks.setValue(32)
        blocks_box.addWidget(blocks_lbl)
        blocks_box.addWidget(self.spin_blocks)
        ctrl_row.addLayout(blocks_box, 1)

        # Block size
        bs_box = QVBoxLayout()
        bs_box.setSpacing(4)
        bs_lbl = QLabel("Block Size:")
        self.spin_block_size = QSpinBox()
        self.spin_block_size.setRange(64, 8192)
        self.spin_block_size.setValue(512)
        self.spin_block_size.setSuffix(" B")
        bs_box.addWidget(bs_lbl)
        bs_box.addWidget(self.spin_block_size)
        ctrl_row.addLayout(bs_box, 1)

        # Buttons
        btn_box = QVBoxLayout()
        btn_box.setSpacing(4)
        btn_box.addWidget(QLabel("Action:"))
        btn_h = QHBoxLayout()
        btn_h.setSpacing(8)

        self.btn_run = QPushButton("Run Simulation")
        self.btn_run.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {ACCENT};
                color: #ffffff;
                font-weight: 700;
                font-family: {FONT_FAMILY};
                font-size: 12px;
                padding: 7px 18px;
                border-radius: 4px;
                border: none;
            }}
            QPushButton:hover {{
                background-color: {ACCENT_HOVER};
            }}
            QPushButton:disabled {{
                background-color: #334155;
                color: #94a3b8;
            }}
            """
        )
        self.btn_run.clicked.connect(self.run_simulation)

        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.setEnabled(False)
        self.btn_cancel.setStyleSheet(
            f"""
            QPushButton {{
                background-color: #334155;
                color: {TEXT_PRIMARY};
                font-weight: 600;
                font-family: {FONT_FAMILY};
                font-size: 12px;
                padding: 7px 14px;
                border-radius: 4px;
                border: 1px solid {BORDER};
            }}
            QPushButton:hover {{
                background-color: #475569;
            }}
            QPushButton:disabled {{
                color: #64748b;
                border-color: #1e293b;
            }}
            """
        )
        self.btn_cancel.clicked.connect(self.cancel_simulation)

        btn_h.addWidget(self.btn_run)
        btn_h.addWidget(self.btn_cancel)
        btn_box.addLayout(btn_h)
        ctrl_row.addLayout(btn_box, 2)

        ctrl_layout.addLayout(ctrl_row)

        # Custom Workload Action Buttons (hidden by default unless Custom Workload is selected)
        self.custom_ops_widget = QWidget()
        custom_ops_layout = QVBoxLayout(self.custom_ops_widget)
        custom_ops_layout.setContentsMargins(0, 8, 0, 0)
        custom_ops_layout.setSpacing(8)

        ops_btn_row = QHBoxLayout()
        ops_btn_row.setSpacing(8)

        self.btn_add_dir = QPushButton("+ Create Directory")
        self.btn_add_dir.setStyleSheet(self._sub_btn_style(ACCENT_AMBER))
        self.btn_add_dir.clicked.connect(self._prompt_create_dir)

        self.btn_add_file = QPushButton("+ Create File")
        self.btn_add_file.setStyleSheet(self._sub_btn_style(ACCENT_EMERALD))
        self.btn_add_file.clicked.connect(self._prompt_create_file)

        self.btn_delete_file = QPushButton("− Delete File")
        self.btn_delete_file.setStyleSheet(self._sub_btn_style(ACCENT_ROSE))
        self.btn_delete_file.clicked.connect(self._prompt_delete_file)

        self.btn_rmdir = QPushButton("− Remove Directory")
        self.btn_rmdir.setStyleSheet(self._sub_btn_style(ACCENT_ROSE))
        self.btn_rmdir.clicked.connect(self._prompt_rmdir)

        self.btn_clear_ops = QPushButton("Clear Workload")
        self.btn_clear_ops.setStyleSheet(self._sub_btn_style("#64748b"))
        self.btn_clear_ops.clicked.connect(self._clear_custom_ops)

        ops_btn_row.addWidget(self.btn_add_dir)
        ops_btn_row.addWidget(self.btn_add_file)
        ops_btn_row.addWidget(self.btn_delete_file)
        ops_btn_row.addWidget(self.btn_rmdir)
        ops_btn_row.addStretch()
        ops_btn_row.addWidget(self.btn_clear_ops)
        custom_ops_layout.addLayout(ops_btn_row)

        # Operations table
        self.table_ops = QTableWidget(0, 4)
        self.table_ops.setHorizontalHeaderLabels(["#", "Operation", "Target Path", "Parameters"])
        self.table_ops.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table_ops.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table_ops.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table_ops.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.table_ops.setMaximumHeight(130)
        self.table_ops.setStyleSheet(
            f"""
            QTableWidget {{
                background-color: {BG_DARK};
                border: 1px solid {BORDER};
                border-radius: 4px;
                color: {TEXT_PRIMARY};
                font-size: 11px;
            }}
            QHeaderView::section {{
                background-color: #0f172a;
                color: {TEXT_SECONDARY};
                padding: 4px;
                font-weight: 600;
                font-size: 11px;
                border: none;
            }}
            """
        )
        custom_ops_layout.addWidget(self.table_ops)
        self.custom_ops_widget.setVisible(False)
        ctrl_layout.addWidget(self.custom_ops_widget)

        # Status / Progress indicator
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setFixedHeight(3)
        self.progress_bar.setVisible(False)
        ctrl_layout.addWidget(self.progress_bar)

        layout.addWidget(ctrl_card)

        # 4. Storage Capacity Stats Bar
        self.stats_bar = FilesystemStatsBar()
        layout.addWidget(self.stats_bar)

        # 5. Block Allocation Map (Physical Bitmap Grid)
        bitmap_card = QFrame()
        bitmap_card.setObjectName("BitmapCard")
        bitmap_card.setStyleSheet(
            f"""
            QFrame#BitmapCard {{
                background-color: {BG_CARD};
                border: 1px solid {BORDER};
                border-radius: 8px;
            }}
            """
        )
        bitmap_layout = QVBoxLayout(bitmap_card)
        bitmap_layout.setContentsMargins(14, 12, 14, 12)
        bitmap_layout.setSpacing(8)

        b_hdr = QHBoxLayout()
        b_title = QLabel("Physical Disk Block Allocation Map (Bitmap)")
        b_title.setStyleSheet(f"font-size: 13px; font-weight: 700; color: {TEXT_PRIMARY};")
        b_hdr.addWidget(b_title)

        b_hdr.addStretch()

        # Legend items
        legend_layout = QHBoxLayout()
        legend_layout.setSpacing(12)
        legend_layout.addWidget(self._create_legend_dot(ACCENT_EMERALD, "Contiguous"))
        legend_layout.addWidget(self._create_legend_dot(ACCENT_CYAN, "Linked"))
        legend_layout.addWidget(self._create_legend_dot(ACCENT_AMBER, "Indexed Data"))
        legend_layout.addWidget(self._create_legend_dot(ACCENT_VIOLET, "Index Block"))
        legend_layout.addWidget(self._create_legend_dot("#334155", "Free Block"))
        b_hdr.addLayout(legend_layout)
        bitmap_layout.addLayout(b_hdr)

        self.block_map = BlockAllocationMapWidget()
        bitmap_layout.addWidget(self.block_map)
        layout.addWidget(bitmap_card)

        # 6. Main Splitter: Left = Directory Tree Browser, Right = File Inode Metadata Panel
        splitter = QSplitter(Qt.Horizontal)
        splitter.setChildrenCollapsible(False)

        self.tree_browser = DirectoryTreeBrowserWidget()
        self.tree_browser.file_selected.connect(self._on_file_selected)
        splitter.addWidget(self.tree_browser)

        self.metadata_panel = FileMetadataPanel()
        splitter.addWidget(self.metadata_panel)

        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)
        layout.addWidget(splitter)

        # 7. Lower Tabs: Operation Log & Raw Backend Output
        tabs_card = QFrame()
        tabs_card.setStyleSheet(
            f"""
            QFrame {{
                background-color: {BG_CARD};
                border: 1px solid {BORDER};
                border-radius: 8px;
            }}
            QTabWidget::pane {{
                border: none;
                background-color: transparent;
            }}
            QTabBar::tab {{
                background-color: {BG_DARK};
                color: {TEXT_SECONDARY};
                padding: 6px 14px;
                font-size: 11px;
                font-weight: 600;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                margin-right: 4px;
            }}
            QTabBar::tab:selected {{
                background-color: {BG_SURFACE};
                color: {TEXT_PRIMARY};
                border-bottom: 2px solid {ACCENT};
            }}
            """
        )
        tabs_layout = QVBoxLayout(tabs_card)
        tabs_layout.setContentsMargins(12, 12, 12, 12)
        tabs_layout.setSpacing(6)

        self.tab_widget = QTabWidget()

        # Tab 1: Execution Log
        self.txt_log = QTextEdit()
        self.txt_log.setReadOnly(True)
        self.txt_log.setFont(QFont("Consolas", 10))
        self.txt_log.setStyleSheet(f"background-color: #0b0f19; border: 1px solid {BORDER}; border-radius: 4px; color: #e2e8f0; padding: 8px;")
        self.tab_widget.addTab(self.txt_log, "Operation Execution Trace")

        # Tab 2: Raw C++ stdout
        self.txt_raw = QTextEdit()
        self.txt_raw.setReadOnly(True)
        self.txt_raw.setFont(QFont("Consolas", 10))
        self.txt_raw.setStyleSheet(f"background-color: #0b0f19; border: 1px solid {BORDER}; border-radius: 4px; color: #94a3b8; padding: 8px;")
        self.tab_widget.addTab(self.txt_raw, "Raw C++ Backend Output")

        tabs_layout.addWidget(self.tab_widget)
        layout.addWidget(tabs_card)

        scroll.setWidget(container)
        main_layout.addWidget(scroll)

        # Prepopulate default custom operations if chosen
        self._populate_default_custom_ops()

        # Auto-run standard demo on initial load if runner is available
        self.run_simulation()

    def _sub_btn_style(self, color_hex: str) -> str:
        return f"""
        QPushButton {{
            background-color: #1e293b;
            color: {color_hex};
            font-size: 11px;
            font-weight: 600;
            padding: 5px 10px;
            border-radius: 4px;
            border: 1px solid #334155;
        }}
        QPushButton:hover {{
            background-color: #334155;
            border-color: {color_hex};
        }}
        """

    def _create_legend_dot(self, color_hex: str, label_text: str) -> QWidget:
        w = QWidget()
        l = QHBoxLayout(w)
        l.setContentsMargins(0, 0, 0, 0)
        l.setSpacing(5)
        dot = QFrame()
        dot.setFixedSize(10, 10)
        dot.setStyleSheet(f"background-color: {color_hex}; border-radius: 5px;")
        lbl = QLabel(label_text)
        lbl.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 10px;")
        l.addWidget(dot)
        l.addWidget(lbl)
        return w

    def _on_preset_changed(self, index: int) -> None:
        preset = self.combo_preset.currentData()
        is_custom = (preset == FilesystemPreset.CUSTOM_WORKLOAD)
        self.custom_ops_widget.setVisible(is_custom)

        if preset == FilesystemPreset.STANDARD_DEMO:
            self.spin_blocks.setValue(32)
            self.spin_block_size.setValue(512)
        elif preset == FilesystemPreset.FRAGMENTATION:
            self.spin_blocks.setValue(6)
            self.spin_block_size.setValue(512)
        elif preset == FilesystemPreset.CAPACITY_LIMIT:
            self.spin_blocks.setValue(8)
            self.spin_block_size.setValue(512)

    def _on_file_selected(self, in_obj: FileInodeModel) -> None:
        self.metadata_panel.inspect_file(in_obj)
        if not in_obj.is_directory:
            highlight_blocks = list(in_obj.allocated_blocks)
            if in_obj.index_block >= 0:
                highlight_blocks.append(in_obj.index_block)
            self.block_map.highlight_file_blocks(highlight_blocks)
        else:
            self.block_map.clear_highlight()

    def _populate_default_custom_ops(self) -> None:
        self._custom_operations = [
            FilesystemOperationInput(FilesystemOperationType.MKDIR, "/data"),
            FilesystemOperationInput(FilesystemOperationType.CREATE, "/data/report.bin", 1500, FilesystemAllocationStrategy.CONTIGUOUS),
            FilesystemOperationInput(FilesystemOperationType.CREATE, "/data/notes.txt", 1000, FilesystemAllocationStrategy.LINKED),
            FilesystemOperationInput(FilesystemOperationType.CREATE, "/data/index.db", 1000, FilesystemAllocationStrategy.INDEXED),
            FilesystemOperationInput(FilesystemOperationType.DELETE, "/data/report.bin"),
        ]
        self._refresh_operations_table()

    def _refresh_operations_table(self) -> None:
        self.table_ops.setRowCount(len(self._custom_operations))
        for r, op in enumerate(self._custom_operations):
            item_num = QTableWidgetItem(str(r + 1))
            item_op = QTableWidgetItem(op.op_type.value.upper())
            item_path = QTableWidgetItem(op.path)

            params = "-"
            if op.op_type == FilesystemOperationType.CREATE:
                params = f"{op.size_bytes} B, {op.strategy.value}"

            item_params = QTableWidgetItem(params)

            # Colors
            if op.op_type == FilesystemOperationType.CREATE:
                item_op.setForeground(QColor(ACCENT_EMERALD))
            elif op.op_type in (FilesystemOperationType.DELETE, FilesystemOperationType.RMDIR):
                item_op.setForeground(QColor(ACCENT_ROSE))
            elif op.op_type == FilesystemOperationType.MKDIR:
                item_op.setForeground(QColor(ACCENT_AMBER))

            self.table_ops.setItem(r, 0, item_num)
            self.table_ops.setItem(r, 1, item_op)
            self.table_ops.setItem(r, 2, item_path)
            self.table_ops.setItem(r, 3, item_params)

    def _prompt_create_dir(self) -> None:
        dlg = CreateDirectoryDialog(self)
        if dlg.exec() == QDialog.Accepted:
            op = dlg.get_operation()
            err = op.validate()
            if err:
                QMessageBox.warning(self, "Invalid Path", err)
                return
            self._custom_operations.append(op)
            self._refresh_operations_table()

    def _prompt_create_file(self) -> None:
        dlg = CreateFileDialog(self)
        if dlg.exec() == QDialog.Accepted:
            op = dlg.get_operation()
            err = op.validate()
            if err:
                QMessageBox.warning(self, "Invalid File Input", err)
                return
            self._custom_operations.append(op)
            self._refresh_operations_table()

    def _prompt_delete_file(self) -> None:
        if not self._custom_operations:
            target = "/data/notes.txt"
        else:
            target = self._custom_operations[-1].path

        ret = QMessageBox.question(
            self,
            "Confirm Delete Operation",
            f"Are you sure you want to queue a deletion for file '{target}'?\n"
            "This will free allocated physical blocks back to the free list.",
            QMessageBox.Yes | QMessageBox.No,
        )
        if ret == QMessageBox.Yes:
            op = FilesystemOperationInput(
                op_type=FilesystemOperationType.DELETE,
                path=target,
            )
            self._custom_operations.append(op)
            self._refresh_operations_table()

    def _prompt_rmdir(self) -> None:
        target = "/data"
        ret = QMessageBox.question(
            self,
            "Confirm Directory Removal",
            f"Are you sure you want to remove directory '{target}'?\n"
            "Note: The backend requires the directory to be completely empty before removal.",
            QMessageBox.Yes | QMessageBox.No,
        )
        if ret == QMessageBox.Yes:
            op = FilesystemOperationInput(
                op_type=FilesystemOperationType.RMDIR,
                path=target,
            )
            self._custom_operations.append(op)
            self._refresh_operations_table()

    def _clear_custom_ops(self) -> None:
        self._custom_operations.clear()
        self._refresh_operations_table()

    def run_simulation(self) -> None:
        """Execute selected simulation preset or custom workload on the C++ backend."""
        if not self.runner:
            return

        preset = self.combo_preset.currentData()
        config = FilesystemConfig(
            total_blocks=self.spin_blocks.value(),
            block_size=self.spin_block_size.value(),
            preset=preset,
            operations=list(self._custom_operations) if preset == FilesystemPreset.CUSTOM_WORKLOAD else [],
        )

        cfg_err = config.validate()
        if cfg_err:
            QMessageBox.warning(self, "Invalid Configuration", cfg_err)
            return

        self.btn_run.setEnabled(False)
        self.btn_cancel.setEnabled(True)
        self.progress_bar.setVisible(True)

        self._active_worker = FilesystemWorker(self.runner, config, parent=self)
        self._active_worker.finished_exec.connect(self._on_simulation_success)
        self._active_worker.failed_exec.connect(self._on_simulation_failed)
        self._active_worker.start()

    def cancel_simulation(self) -> None:
        if self._active_worker and self._active_worker.isRunning():
            self._active_worker.cancel()
        self.btn_run.setEnabled(True)
        self.btn_cancel.setEnabled(False)
        self.progress_bar.setVisible(False)

    def _on_simulation_success(self, result: FilesystemSimulationResultModel) -> None:
        self.btn_run.setEnabled(True)
        self.btn_cancel.setEnabled(False)
        self.progress_bar.setVisible(False)
        self._last_result = result

        # 1. Update stats bar
        self.stats_bar.update_stats(result.status)

        # 2. Update block map
        self.block_map.set_status(result.status)

        # 3. Update directory tree
        self.tree_browser.populate(result.status)

        # 4. Clear or set inspector
        if result.status.inodes:
            # Pick first file if available, otherwise root
            first_file = next((i for i in result.status.inodes if not i.is_directory), result.status.inodes[0])
            self.metadata_panel.inspect_file(first_file)
            if not first_file.is_directory:
                highlight_blks = list(first_file.allocated_blocks)
                if first_file.index_block >= 0:
                    highlight_blks.append(first_file.index_block)
                self.block_map.highlight_file_blocks(highlight_blks)

        # 5. Update execution log
        log_lines: List[str] = []
        preset_name = result.preset.value if hasattr(result.preset, "value") else str(result.preset)
        log_lines.append(f"Simulation Preset: {preset_name}")
        log_lines.append(f"Exit Code: {result.exit_code} | Execution Duration: {result.duration_ms:.2f} ms")
        log_lines.append(
            f"Capacity: {result.status.used_blocks}/{result.status.total_blocks} blocks allocated "
            f"({result.status.free_blocks} free, {result.status.utilization_percent:.1f}% used)"
        )
        log_lines.append("-" * 65)

        if result.status.operation_logs:
            log_lines.append("C++ Backend Execution Steps:")
            for l in result.status.operation_logs:
                log_lines.append(f"  • {l}")
        else:
            log_lines.append("Allocation Comparison Summary:")
            for tr in result.status.allocation_traces:
                log_lines.append(
                    f"  • {tr.name} ({tr.strategy}): Start {tr.start_block}, "
                    f"Blocks: {tr.allocated_blocks} (Index: {tr.index_block})"
                )

        self.txt_log.setPlainText("\n".join(log_lines))

        # 6. Raw stdout
        self.txt_raw.setPlainText(result.raw_stdout)

        # Notify dashboard / activity listener
        if self.on_execution_completed:
            self.on_execution_completed(
                "Simulated File System",
                result.exit_code,
                result.duration_ms,
                0.0,
                result.is_success,
            )

    def _on_simulation_failed(self, error_msg: str) -> None:
        self.btn_run.setEnabled(True)
        self.btn_cancel.setEnabled(False)
        self.progress_bar.setVisible(False)
        if self.isVisible() and os.environ.get("QT_QPA_PLATFORM") != "offscreen":
            QMessageBox.critical(self, "Simulation Error", error_msg)
        self.txt_log.setPlainText(f"SIMULATION FAILED:\n{error_msg}")
