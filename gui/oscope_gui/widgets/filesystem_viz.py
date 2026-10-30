"""Visualizations for Simulated File System: Disk block allocation map, directory tree browser, and metadata panels."""

from typing import Dict, List, Optional, Tuple

from PySide6.QtCore import QPointF, QRectF, Qt, Signal
from PySide6.QtGui import (
    QBrush,
    QColor,
    QFont,
    QPainter,
    QPainterPath,
    QPen,
)
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QProgressBar,
    QSplitter,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ..models.filesystem import (
    AllocationTraceModel,
    FileInodeModel,
    FilesystemStatusModel,
)
from ..theme import (
    ACCENT,
    ACCENT_AMBER,
    ACCENT_CYAN,
    ACCENT_EMERALD,
    ACCENT_VIOLET,
    ACCENT_ROSE,
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
from .stat_card import StatCard


class BlockAllocationMapWidget(QWidget):
    """Custom QPainter-based visual representation of physical disk blocks (bitmap)."""

    block_clicked = Signal(int)  # Emits block index

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setMinimumHeight(160)
        self.setMouseTracking(True)

        self._status: Optional[FilesystemStatusModel] = None
        self._block_rects: List[Tuple[QRectF, int]] = []
        self._hovered_block: int = -1
        self._highlighted_blocks: set[int] = set()

    def set_status(self, status: Optional[FilesystemStatusModel]) -> None:
        self._status = status
        self._hovered_block = -1
        self._highlighted_blocks.clear()
        self.update()

    def highlight_file_blocks(self, blocks: List[int]) -> None:
        """Highlight blocks belonging to selected file."""
        self._highlighted_blocks = set(blocks)
        self.update()

    def clear_highlight(self) -> None:
        self._highlighted_blocks.clear()
        self.update()

    def mouseMoveEvent(self, event) -> None:
        pos = event.position()
        found = -1
        for rect, blk_idx in self._block_rects:
            if rect.contains(pos):
                found = blk_idx
                break

        if found != self._hovered_block:
            self._hovered_block = found
            if found >= 0:
                self.setCursor(Qt.PointingHandCursor)
                self._update_tooltip(found)
            else:
                self.unsetCursor()
            self.update()

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.LeftButton and self._hovered_block >= 0:
            self.block_clicked.emit(self._hovered_block)

    def leaveEvent(self, event) -> None:
        self._hovered_block = -1
        self.unsetCursor()
        self.update()

    def _update_tooltip(self, blk_idx: int) -> None:
        if not self._status:
            return
        is_alloc = blk_idx < len(self._status.block_bitmap) and self._status.block_bitmap[blk_idx]
        bs = self._status.block_size
        start_byte = blk_idx * bs
        end_byte = (blk_idx + 1) * bs - 1

        owner_info = "Status: Free (Unallocated)"
        if is_alloc:
            owner_info = "Status: Allocated"
            for in_obj in self._status.inodes:
                if not in_obj.is_directory:
                    if blk_idx == in_obj.index_block:
                        owner_info = f"Index Block for '{in_obj.name}' (Inode #{in_obj.inode_id})"
                        break
                    if blk_idx in in_obj.allocated_blocks:
                        owner_info = f"Data Block for '{in_obj.name}' (Inode #{in_obj.inode_id}, {in_obj.strategy})"
                        break

        tip = (
            f"Physical Block #{blk_idx}\n"
            f"Byte Range: {start_byte} - {end_byte} ({bs} bytes)\n"
            f"{owner_info}"
        )
        self.setToolTip(tip)

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()

        # Background container
        bg_rect = QRectF(0, 0, w, h)
        painter.fillRect(bg_rect, QColor(BG_CARD))
        painter.setPen(QPen(QColor(BORDER), 1))
        painter.drawRoundedRect(bg_rect.adjusted(0.5, 0.5, -0.5, -0.5), 8, 8)

        if not self._status or self._status.total_blocks <= 0:
            painter.setPen(QColor(TEXT_MUTED))
            font = QFont(FONT_FAMILY, 10)
            painter.setFont(font)
            painter.drawText(bg_rect, Qt.AlignCenter, "No file system simulation active.")
            return

        total_blocks = self._status.total_blocks
        cols = 16 if total_blocks >= 32 else (8 if total_blocks >= 8 else total_blocks)
        rows = (total_blocks + cols - 1) // cols

        margin_x = 16.0
        margin_y = 16.0
        spacing = 6.0

        available_w = w - (margin_x * 2) - (spacing * (cols - 1))
        available_h = h - (margin_y * 2) - (spacing * (rows - 1))

        tile_size = min(available_w / cols, available_h / rows, 42.0)
        tile_size = max(tile_size, 20.0)

        # Build mapping of block -> (strategy, is_index, file_name)
        block_owner: Dict[int, Tuple[str, bool, str]] = {}
        for in_obj in self._status.inodes:
            if not in_obj.is_directory:
                if in_obj.index_block >= 0:
                    block_owner[in_obj.index_block] = (in_obj.strategy, True, in_obj.name)
                for b in in_obj.allocated_blocks:
                    block_owner[b] = (in_obj.strategy, False, in_obj.name)

        self._block_rects.clear()

        # Draw grid of blocks
        font = QFont(FONT_FAMILY, max(7, int(tile_size * 0.32)), QFont.Bold)
        painter.setFont(font)

        for i in range(total_blocks):
            r = i // cols
            c = i % cols
            x = margin_x + c * (tile_size + spacing)
            y = margin_y + r * (tile_size + spacing)

            tile_rect = QRectF(x, y, tile_size, tile_size)
            self._block_rects.append((tile_rect, i))

            is_allocated = i < len(self._status.block_bitmap) and self._status.block_bitmap[i]
            is_hovered = (i == self._hovered_block)
            is_highlighted = (i in self._highlighted_blocks)

            # Determine colors
            if not is_allocated:
                fill_color = QColor("#F8FAFC")
                border_color = QColor(BORDER)
                text_color = QColor(TEXT_MUTED)
            else:
                strat_info = block_owner.get(i, ("Indexed", False, ""))
                is_index = strat_info[1]

                if is_index:
                    fill_color = QColor("#EEF2FF")
                    border_color = QColor("#4F46E5")
                    text_color = QColor("#3730A3")
                else:
                    fill_color = QColor("#EAF2FF")
                    border_color = QColor(ACCENT)
                    text_color = QColor("#1E40AF")

            if is_highlighted:
                border_color = QColor("#1D4ED8")
                fill_color = QColor(ACCENT)
                text_color = QColor("#FFFFFF")
            elif is_hovered:
                border_color = QColor(ACCENT)
                fill_color = fill_color.lighter(105)

            # Draw block tile
            path = QPainterPath()
            path.addRoundedRect(tile_rect, 4, 4)
            painter.fillPath(path, fill_color)
            painter.setPen(QPen(border_color, 2 if (is_highlighted or is_hovered) else 1))
            painter.drawPath(path)

            # Draw block index text
            painter.setPen(text_color)
            painter.drawText(tile_rect, Qt.AlignCenter, str(i))


class DirectoryTreeBrowserWidget(QFrame):
    """Interactive visual browser displaying directory hierarchy, inodes, and file entries."""

    file_selected = Signal(object)  # Emits FileInodeModel

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("DirectoryTreeBrowser")
        self.setStyleSheet(
            f"""
            QFrame#DirectoryTreeBrowser {{
                background-color: {BG_CARD};
                border: 1px solid {BORDER};
                border-radius: 8px;
            }}
            QTreeWidget {{
                background-color: transparent;
                border: none;
                color: {TEXT_PRIMARY};
                font-family: {FONT_FAMILY};
                font-size: 12px;
            }}
            QTreeWidget::item {{
                padding: 5px;
                border-radius: 4px;
            }}
            QTreeWidget::item:hover {{
                background-color: #1e293b;
            }}
            QTreeWidget::item:selected {{
                background-color: #334155;
                color: #ffffff;
            }}
            QHeaderView::section {{
                background-color: {BG_DARK};
                color: {TEXT_SECONDARY};
                padding: 6px 8px;
                font-weight: 600;
                font-size: 11px;
                border: none;
                border-bottom: 1px solid {BORDER};
            }}
            """
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        # Header label
        hdr_layout = QHBoxLayout()
        hdr_title = QLabel("Simulated File System Hierarchy")
        hdr_title.setStyleSheet(f"font-size: 13px; font-weight: 700; color: {TEXT_PRIMARY};")
        hdr_layout.addWidget(hdr_title)

        self.lbl_selected_path = QLabel("Path: /")
        self.lbl_selected_path.setStyleSheet(
            f"font-size: 11px; font-family: monospace; color: {ACCENT_CYAN}; padding: 2px 6px; background-color: #082f49; border-radius: 4px;"
        )
        hdr_layout.addStretch()
        hdr_layout.addWidget(self.lbl_selected_path)
        layout.addLayout(hdr_layout)

        # Tree Widget
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Name", "Type", "Inode", "Size", "Strategy", "Blocks"])
        self.tree.header().setSectionResizeMode(0, QHeaderView.Stretch)
        self.tree.header().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.tree.header().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.tree.header().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.tree.header().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.tree.header().setSectionResizeMode(5, QHeaderView.ResizeToContents)
        self.tree.itemClicked.connect(self._on_item_clicked)
        layout.addWidget(self.tree)

        self._nodes_by_path: Dict[str, QTreeWidgetItem] = {}
        self._inodes_by_path: Dict[str, FileInodeModel] = {}

    def populate(self, status: Optional[FilesystemStatusModel]) -> None:
        self.tree.clear()
        self._nodes_by_path.clear()
        self._inodes_by_path.clear()

        if not status or not status.inodes:
            empty_item = QTreeWidgetItem(["(Empty file system)", "-", "-", "-", "-", "-"])
            empty_item.setForeground(0, QColor(TEXT_MUTED))
            self.tree.addTopLevelItem(empty_item)
            return

        # Sort inodes by path depth
        sorted_inodes = sorted(status.inodes, key=lambda x: (x.path.count("/"), x.path))

        # Root item
        root_node = QTreeWidgetItem(["/ (Root)", "Directory", "0", "0 B", "-", "-"])
        root_node.setForeground(0, QColor(TEXT_PRIMARY))
        root_node.setData(0, Qt.UserRole, "/")
        self.tree.addTopLevelItem(root_node)
        self._nodes_by_path["/"] = root_node

        for in_obj in sorted_inodes:
            self._inodes_by_path[in_obj.path] = in_obj
            if in_obj.path == "/":
                continue

            parent_path = in_obj.path.rsplit("/", 1)[0]
            if not parent_path:
                parent_path = "/"

            parent_item = self._nodes_by_path.get(parent_path, root_node)

            type_label = "Directory" if in_obj.is_directory else "File"
            size_label = f"{in_obj.size_bytes} B"
            strat_label = in_obj.strategy if not in_obj.is_directory else "-"

            if in_obj.is_directory:
                icon_prefix = "[DIR] "
                block_str = "-"
            else:
                icon_prefix = "[FILE] "
                blks = in_obj.allocated_blocks
                block_str = f"{len(blks)} blk"
                if in_obj.index_block >= 0:
                    block_str += f" (idx: {in_obj.index_block})"

            item = QTreeWidgetItem([
                f"{icon_prefix}{in_obj.name}",
                type_label,
                str(in_obj.inode_id),
                size_label,
                strat_label,
                block_str,
            ])
            item.setData(0, Qt.UserRole, in_obj.path)

            # Styling badges
            if in_obj.is_directory:
                item.setForeground(0, QColor(ACCENT_AMBER))
            else:
                if in_obj.strategy == "Contiguous":
                    item.setForeground(4, QColor(ACCENT_EMERALD))
                elif in_obj.strategy == "Linked":
                    item.setForeground(4, QColor(ACCENT_CYAN))
                elif in_obj.strategy == "Indexed":
                    item.setForeground(4, QColor(ACCENT_VIOLET))

            parent_item.addChild(item)
            self._nodes_by_path[in_obj.path] = item

        self.tree.expandAll()

    def _on_item_clicked(self, item: QTreeWidgetItem, column: int) -> None:
        path = item.data(0, Qt.UserRole)
        if path:
            self.lbl_selected_path.setText(f"Path: {path}")
            in_obj = self._inodes_by_path.get(path)
            if in_obj:
                self.file_selected.emit(in_obj)


class FileMetadataPanel(QFrame):
    """Inspector panel displaying metadata, block mapping, and educational strategy notes."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("FileMetadataPanel")
        self.setStyleSheet(
            f"""
            QFrame#FileMetadataPanel {{
                background-color: {BG_CARD};
                border: 1px solid {BORDER};
                border-radius: 8px;
            }}
            """
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        # Header
        hdr = QLabel("File & Inode Inspector")
        hdr.setStyleSheet(f"font-size: 13px; font-weight: 700; color: {TEXT_PRIMARY};")
        layout.addWidget(hdr)

        # Property grid
        self.lbl_path = self._create_row("Path:", "/", layout)
        self.lbl_inode = self._create_row("Inode ID:", "0", layout)
        self.lbl_type = self._create_row("Type:", "Directory", layout)
        self.lbl_size = self._create_row("File Size:", "0 bytes", layout)
        self.lbl_strategy = self._create_row("Allocation Strategy:", "None", layout)
        self.lbl_start = self._create_row("Start / Index Block:", "None", layout)
        self.lbl_blocks = self._create_row("Allocated Blocks:", "None", layout)

        # Educational Strategy Explanation Box
        self.lbl_strategy_explain = QLabel(
            "Select an inode in the directory browser to inspect its metadata, allocation strategy, and physical block placement."
        )
        self.lbl_strategy_explain.setWordWrap(True)
        self.lbl_strategy_explain.setStyleSheet(
            f"font-size: 11px; color: {TEXT_SECONDARY}; line-height: 1.4; background-color: #0f172a; padding: 10px; border-radius: 6px; border: 1px solid #1e293b;"
        )
        layout.addWidget(self.lbl_strategy_explain)

        # Simulation bounds reminder
        notice = QLabel(
            "Note: Simulated in-memory file system models directory hierarchy, inode metadata, and physical block allocation. File byte content is not stored."
        )
        notice.setWordWrap(True)
        notice.setStyleSheet(f"font-size: 10px; color: {TEXT_MUTED}; font-style: italic;")
        layout.addWidget(notice)

        layout.addStretch()

    def _create_row(self, label_text: str, default_val: str, layout: QVBoxLayout) -> QLabel:
        row = QHBoxLayout()
        lbl = QLabel(label_text)
        lbl.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 11px; min-width: 120px;")
        val = QLabel(default_val)
        val.setStyleSheet(f"color: {TEXT_PRIMARY}; font-size: 11px; font-weight: 600;")
        val.setTextInteractionFlags(Qt.TextSelectableByMouse)
        row.addWidget(lbl)
        row.addWidget(val)
        row.addStretch()
        layout.addLayout(row)
        return val

    def inspect_file(self, in_obj: Optional[FileInodeModel]) -> None:
        if not in_obj:
            self.lbl_path.setText("/")
            self.lbl_inode.setText("0")
            self.lbl_type.setText("Directory")
            self.lbl_size.setText("0 bytes")
            self.lbl_strategy.setText("None")
            self.lbl_start.setText("None")
            self.lbl_blocks.setText("None")
            self.lbl_strategy_explain.setText("Select a file or directory above to inspect its metadata.")
            return

        self.lbl_path.setText(in_obj.path)
        self.lbl_inode.setText(str(in_obj.inode_id))
        self.lbl_type.setText("Directory" if in_obj.is_directory else "Regular File")
        self.lbl_size.setText(f"{in_obj.size_bytes} bytes ({in_obj.block_count} blocks)")

        if in_obj.is_directory:
            self.lbl_strategy.setText("-")
            self.lbl_start.setText("-")
            self.lbl_blocks.setText("-")
            self.lbl_strategy_explain.setText(
                "Directory Inode: Maintains namespace mapping of child files and directories. Requires an existing parent directory to create."
            )
        else:
            self.lbl_strategy.setText(in_obj.strategy)

            start_str = "None"
            if in_obj.strategy == "Indexed":
                start_str = f"Index Block #{in_obj.index_block}"
            elif in_obj.start_block >= 0:
                start_str = f"Start Block #{in_obj.start_block}"
            self.lbl_start.setText(start_str)

            if in_obj.allocated_blocks:
                blist = ", ".join(str(b) for b in in_obj.allocated_blocks)
                self.lbl_blocks.setText(f"[{blist}]")
            else:
                self.lbl_blocks.setText("[]")

            # Explanation of allocation strategy
            if in_obj.strategy == "Contiguous":
                self.lbl_strategy_explain.setText(
                    "Contiguous Allocation: Blocks are allocated sequentially on disk. Offers excellent sequential read/write performance, but is susceptible to external fragmentation if files are created and deleted dynamically."
                )
            elif in_obj.strategy == "Linked":
                self.lbl_strategy_explain.setText(
                    "Linked Allocation: Each physical block contains a pointer to the next block. Completely eliminates external fragmentation by using any available free block, but suffers from slower random access and pointer overhead."
                )
            elif in_obj.strategy == "Indexed":
                self.lbl_strategy_explain.setText(
                    "Indexed Allocation: A dedicated index block (block #" + str(in_obj.index_block) + ") stores direct pointers to all physical data blocks. Supports fast direct random access without external fragmentation, at the cost of 1 index block overhead."
                )


class FilesystemStatsBar(QWidget):
    """High-level storage capacity cards and utilization gauge."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        self.card_total = StatCard(
            title="Total Capacity",
            value="16 KB",
            subtitle="32 Blocks x 512 B",
            accent_color=ACCENT_CYAN,
        )
        self.card_used = StatCard(
            title="Used Storage",
            value="0 B",
            subtitle="0 / 32 Blocks",
            accent_color=ACCENT_EMERALD,
        )
        self.card_free = StatCard(
            title="Free Space",
            value="16 KB",
            subtitle="32 Blocks available",
            accent_color=ACCENT_AMBER,
        )
        self.card_inodes = StatCard(
            title="Inodes & Files",
            value="0 Files",
            subtitle="1 Directory (root)",
            accent_color=ACCENT_VIOLET,
        )

        layout.addWidget(self.card_total)
        layout.addWidget(self.card_used)
        layout.addWidget(self.card_free)
        layout.addWidget(self.card_inodes)

    def update_stats(self, status: Optional[FilesystemStatusModel]) -> None:
        if not status:
            self.card_total.set_value("--")
            self.card_used.set_value("--")
            self.card_free.set_value("--")
            self.card_inodes.set_value("--")
            return

        tot_kb = (status.total_blocks * status.block_size) / 1024.0
        used_kb = (status.used_blocks * status.block_size) / 1024.0
        free_kb = (status.free_blocks * status.block_size) / 1024.0

        self.card_total.set_value(f"{tot_kb:.1f} KB", f"{status.total_blocks} Blocks ({status.block_size} B/blk)")
        self.card_used.set_value(f"{used_kb:.1f} KB ({status.utilization_percent:.1f}%)", f"{status.used_blocks} / {status.total_blocks} Blocks allocated")
        self.card_free.set_value(f"{free_kb:.1f} KB", f"{status.free_blocks} Blocks available")
        self.card_inodes.set_value(f"{status.file_count} Files", f"{status.directory_count} Directories")

