"""Status badge widget for indicating experiment and availability status."""

from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QLabel, QWidget

from ..theme import (
    DANGER,
    DANGER_TEXT,
    SUCCESS,
    SUCCESS_TEXT,
    TEXT_MUTED,
    TEXT_SECONDARY,
    WARNING,
    WARNING_TEXT,
)


class StatusBadge(QWidget):
    """Pill badge showing user-oriented status (e.g. Ready, Available, Planned)."""

    def __init__(
        self,
        text: str = "Ready",
        state: str = "success",
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("StatusBadge")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(9, 3, 9, 3)
        layout.setSpacing(6)

        self.dot = QLabel()
        self.dot.setFixedSize(7, 7)

        self.label = QLabel(text)

        layout.addWidget(self.dot)
        layout.addWidget(self.label)

        self.set_state(state, text)

    def set_state(self, state: str, text: Optional[str] = None) -> None:
        """Update badge state: 'success', 'warning', 'error', 'pending', 'info'."""
        if text:
            self.label.setText(text)

        colors = {
            "success": (SUCCESS, SUCCESS_TEXT, "rgba(16, 185, 129, 0.15)"),
            "warning": (WARNING, WARNING_TEXT, "rgba(245, 158, 11, 0.15)"),
            "error": (DANGER, DANGER_TEXT, "rgba(244, 63, 94, 0.15)"),
            "info": ("#0284c7", "#38bdf8", "rgba(56, 189, 248, 0.15)"),
            "pending": ("#334155", TEXT_MUTED, "#131927"),
        }

        border_col, text_col, bg_col = colors.get(state, colors["pending"])

        self.dot.setStyleSheet(f"background-color: {text_col}; border-radius: 3px; border: none;")
        self.label.setStyleSheet(f"color: {text_col}; font-size: 11px; font-weight: 600; background: transparent; border: none;")
        self.setStyleSheet(
            f"""
            #StatusBadge {{
                background-color: {bg_col};
                border: 1px solid {border_col};
                border-radius: 11px;
            }}
            """
        )

    def set_status(self, text: str, state: str = "success") -> None:
        """Convenience method accepting (text, state)."""
        # Map danger -> error
        st = "error" if state == "danger" else ("info" if state == "running" else state)
        self.set_state(st, text)
