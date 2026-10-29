"""Shared pytest fixtures for OScope GUI test suite."""

import os
import pytest
from PySide6.QtWidgets import QApplication

os.environ["QT_QPA_PLATFORM"] = "offscreen"


@pytest.fixture(scope="session")
def qapp():
    """Shared single QApplication instance for all GUI tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(["oscope_test", "-platform", "offscreen"])
    return app


@pytest.fixture(autouse=True)
def cleanup_widgets():
    """Clean up any pending Qt events and deferred deletions after each test."""
    yield
    QApplication.closeAllWindows()
    for widget in QApplication.topLevelWidgets():
        widget.deleteLater()
    QApplication.processEvents()
