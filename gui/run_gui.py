"""Entry point for the OScope Windows Desktop GUI."""

import sys
from pathlib import Path

# Ensure gui package is on sys.path
gui_root = Path(__file__).resolve().parent
if str(gui_root) not in sys.path:
    sys.path.insert(0, str(gui_root))

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from oscope_gui.backend.runner import discover_backend
from oscope_gui.main_window import MainWindow


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("OScope")
    app.setOrganizationName("OSCourse")

    # Discover and connect C++ backend (Native or WSL bridge)
    runner, info = discover_backend()

    window = MainWindow(runner)
    window.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
