"""Metric stat card widget for dashboard and scheduling results."""

from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from ..theme import (
    BG_SURFACE,
    BORDER,
    BORDER_LIGHT,
    TEXT_MUTED,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
)


class StatCard(QFrame):
    """Compact metric card displaying title, formatted value, subtitle, and explanation tooltip."""

    def __init__(
        self,
        title: str,
        value: str = "--",
        subtitle: str = "",
        tooltip: str = "",
        accent_color: Optional[str] = None,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("StatCard")
        self.setProperty("card", True)
        self.accent_color = accent_color

        self.setStyleSheet(
            f"""
            QFrame#StatCard {{
                background-color: {BG_SURFACE};
                border: 1px solid {BORDER};
                border-radius: 8px;
            }}
            QFrame#StatCard:hover {{
                border-color: {BORDER_LIGHT};
                background-color: #F8FAFC;
            }}
            """
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(4)

        # Header with title
        hdr_layout = QHBoxLayout()
        hdr_layout.setContentsMargins(0, 0, 0, 0)
        hdr_layout.setSpacing(6)

        self.title_label = QLabel(title)
        self.title_label.setStyleSheet(
            f"color: {TEXT_SECONDARY}; font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.6px; background: transparent;"
        )
        hdr_layout.addWidget(self.title_label)
        hdr_layout.addStretch()

        self.value_label = QLabel(value)
        self.value_label.setStyleSheet(
            f"color: {TEXT_PRIMARY}; font-size: 22px; font-weight: 700; background: transparent; padding-top: 2px;"
        )

        self.subtitle_label = QLabel(subtitle)
        self.subtitle_label.setStyleSheet(
            f"color: {TEXT_MUTED}; font-size: 11px; background: transparent;"
        )
        if not subtitle:
            self.subtitle_label.hide()

        if tooltip:
            self.setToolTip(tooltip)
            self.title_label.setToolTip(tooltip)

        layout.addLayout(hdr_layout)
        layout.addWidget(self.value_label)
        layout.addWidget(self.subtitle_label)

    def set_value(self, value: str, subtitle: Optional[str] = None) -> None:
        self.value_label.setText(value)
        if subtitle is not None:
            self.subtitle_label.setText(subtitle)
            self.subtitle_label.setVisible(bool(subtitle))

    def update_values(self, value: str, subtitle: Optional[str] = None) -> None:
        """Alias for set_value to support updating status and subtitle."""
        self.set_value(value, subtitle)
