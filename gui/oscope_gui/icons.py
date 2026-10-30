"""Vector SVG icon utilities for OScope desktop UI.

Renders clean, crisp, scalable SVG icons with dynamic colors for sidebar navigation,
dashboard cards, and module badges.
"""

from typing import Dict, Optional
from PySide6.QtCore import QByteArray, QSize, Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer

# Clean, professional vector SVG path definitions (24x24 viewBox, stroke-width=2)
_SVG_PATHS: Dict[str, str] = {
    # Home / Overview Dashboard
    "dashboard": (
        '<path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>'
        '<polyline points="9 22 9 12 15 12 15 22"/>'
    ),
    # CPU / Processor chip
    "cpu": (
        '<rect x="4" y="4" width="16" height="16" rx="2"/>'
        '<rect x="9" y="9" width="6" height="6"/>'
        '<line x1="9" y1="1" x2="9" y2="4"/>'
        '<line x1="15" y1="1" x2="15" y2="4"/>'
        '<line x1="9" y1="20" x2="9" y2="23"/>'
        '<line x1="15" y1="20" x2="15" y2="23"/>'
        '<line x1="20" y1="9" x2="23" y2="9"/>'
        '<line x1="20" y1="14" x2="23" y2="14"/>'
        '<line x1="1" y1="9" x2="4" y2="9"/>'
        '<line x1="1" y1="14" x2="4" y2="14"/>'
    ),
    # Memory / RAM microchip
    "memory": (
        '<rect x="2" y="6" width="20" height="12" rx="2"/>'
        '<line x1="6" y1="18" x2="6" y2="21"/>'
        '<line x1="10" y1="18" x2="10" y2="21"/>'
        '<line x1="14" y1="18" x2="14" y2="21"/>'
        '<line x1="18" y1="18" x2="18" y2="21"/>'
        '<line x1="6" y1="3" x2="6" y2="6"/>'
        '<line x1="10" y1="3" x2="10" y2="6"/>'
        '<line x1="14" y1="3" x2="14" y2="6"/>'
        '<line x1="18" y1="3" x2="18" y2="6"/>'
        '<line x1="6" y1="10" x2="18" y2="10"/>'
    ),
    # Page Replacement / Document
    "paging": (
        '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>'
        '<polyline points="14 2 14 8 20 8"/>'
        '<line x1="16" y1="13" x2="8" y2="13"/>'
        '<line x1="16" y1="17" x2="8" y2="17"/>'
        '<polyline points="10 9 9 9 8 9"/>'
    ),
    # Deadlock / Warning Triangle
    "deadlock": (
        '<path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>'
        '<line x1="12" y1="9" x2="12" y2="13"/>'
        '<line x1="12" y1="17" x2="12.01" y2="17"/>'
    ),
    # Disk Scheduling / Hard Drive Cylinders
    "disk": (
        '<ellipse cx="12" cy="5" rx="9" ry="3"/>'
        '<path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/>'
        '<path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/>'
    ),
    # Linux / Terminal Prompt
    "linux": (
        '<rect x="2" y="4" width="20" height="16" rx="2"/>'
        '<polyline points="6 9 10 12 6 15"/>'
        '<line x1="12" y1="15" x2="17" y2="15"/>'
    ),
    # Host Monitoring / Activity Bar Chart
    "monitor": (
        '<line x1="18" y1="20" x2="18" y2="10"/>'
        '<line x1="12" y1="20" x2="12" y2="4"/>'
        '<line x1="6" y1="20" x2="6" y2="14"/>'
    ),
    # File System / Folder
    "filesystem": (
        '<path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/>'
    ),
    # Virtual Memory & MMU / Stacked Layers
    "translation": (
        '<polygon points="12 2 2 7 12 12 22 7 12 2"/>'
        '<polyline points="2 17 12 22 22 17"/>'
        '<polyline points="2 12 12 17 22 12"/>'
    ),
    # Process Lifecycle / State Network Nodes
    "lifecycle": (
        '<circle cx="6" cy="18" r="3"/>'
        '<circle cx="6" cy="6" r="3"/>'
        '<circle cx="18" cy="12" r="3"/>'
        '<path d="M8.5 7.5l7 3"/>'
        '<path d="M8.5 16.5l7-3"/>'
        '<line x1="6" y1="9" x2="6" y2="15"/>'
    ),
    # Settings Gear
    "settings": (
        '<circle cx="12" cy="12" r="3"/>'
        '<path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/>'
    ),
    # Check status
    "check": (
        '<polyline points="20 6 9 17 4 12"/>'
    ),
}


def render_svg_pixmap(name: str, color: str = "#64748B", size: int = 20) -> QPixmap:
    """Render a named SVG icon into a transparent QPixmap of given size and color."""
    paths = _SVG_PATHS.get(name, _SVG_PATHS["dashboard"])
    svg_str = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" '
        f'viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" '
        f'stroke-linecap="round" stroke-linejoin="round">'
        f'{paths}'
        f'</svg>'
    )
    renderer = QSvgRenderer(QByteArray(svg_str.encode("utf-8")))
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    renderer.render(painter)
    painter.end()
    return pixmap


def render_svg_icon(name: str, normal_color: str = "#64748B", active_color: str = "#2563EB", size: int = 18) -> QIcon:
    """Render a QIcon with normal and checked/active state pixmaps."""
    icon = QIcon()
    pm_normal = render_svg_pixmap(name, normal_color, size)
    pm_active = render_svg_pixmap(name, active_color, size)
    icon.addPixmap(pm_normal, QIcon.Normal, QIcon.Off)
    icon.addPixmap(pm_active, QIcon.Normal, QIcon.On)
    icon.addPixmap(pm_active, QIcon.Active, QIcon.Off)
    icon.addPixmap(pm_active, QIcon.Active, QIcon.On)
    return icon

