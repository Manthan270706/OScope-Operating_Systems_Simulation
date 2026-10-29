"""Render high-resolution visual snapshots of Disk Scheduling page at 1366x768 and 1920x1080."""

import os
import sys

# Use native Windows QPA for full system font rendering

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QFont, QPixmap
from PySide6.QtWidgets import QApplication

from oscope_gui.main_window import MainWindow
from oscope_gui.models.disk import (
    DiskAlgorithm,
    DiskConfig,
    DiskDirection,
)
from oscope_gui.backend.parser import parse_disk_output, parse_disk_comparison_output
from tests.test_disk import (
    DummyDiskRunner,
    SAMPLE_FCFS_STDOUT,
    SAMPLE_SCAN_STDOUT,
    SAMPLE_CSCAN_STDOUT,
    SAMPLE_COMPARISON_STDOUT,
)


def capture_snapshots():
    app = QApplication.instance() or QApplication(sys.argv)
    app.setFont(QFont("Segoe UI", 10))

    artifact_dir = r"C:\Users\Nitish Sahu\.gemini\antigravity-ide\brain\d0f348d1-dbee-438f-8911-b98a5c9deca9"
    os.makedirs(artifact_dir, exist_ok=True)

    resolutions = [
        ("1366x768", 1366, 768),
        ("1920x1080", 1920, 1080),
    ]

    for res_name, width, height in resolutions:
        runner = DummyDiskRunner(SAMPLE_SCAN_STDOUT)
        window = MainWindow(runner=runner)
        window.resize(width, height)
        window.show()
        app.processEvents()

        # 1. Dashboard View
        window.navigate_to_page("dashboard")
        app.processEvents()
        dash_pixmap = window.grab()
        dash_path = os.path.join(artifact_dir, f"disk_stage5_dashboard_{res_name}.png")
        dash_pixmap.save(dash_path, "PNG")
        print(f"Saved: {dash_path}")

        # 2. Disk Initial Default View
        window.navigate_to_page("disk")
        app.processEvents()
        init_pixmap = window.grab()
        init_path = os.path.join(artifact_dir, f"disk_stage5_initial_{res_name}.png")
        init_pixmap.save(init_path, "PNG")
        print(f"Saved: {init_path}")

        # 3. Disk Simulation Result View (SCAN with Plot and Step Table)
        cfg_scan = DiskConfig(
            algorithm=DiskAlgorithm.SCAN,
            direction=DiskDirection.INCREASING,
            min_cylinder=0,
            max_cylinder=199,
            initial_head=53,
            requests=[98, 183, 37, 122, 14, 124, 65, 67],
        )
        scan_res = parse_disk_output(SAMPLE_SCAN_STDOUT, cfg_scan)
        window.disk_page._on_simulation_success(scan_res)
        app.processEvents()

        scan_pixmap = window.grab()
        scan_path = os.path.join(artifact_dir, f"disk_stage5_scan_result_{res_name}.png")
        scan_pixmap.save(scan_path, "PNG")
        print(f"Saved: {scan_path}")

        # 4. Disk Comparison Result View (7 algorithms ranked)
        cfg_comp = DiskConfig(
            algorithm=DiskAlgorithm.COMPARE_ALL,
            direction=DiskDirection.INCREASING,
            min_cylinder=0,
            max_cylinder=199,
            initial_head=53,
            requests=[98, 183, 37, 122, 14, 124, 65, 67],
        )
        comp_res = parse_disk_comparison_output(SAMPLE_COMPARISON_STDOUT, cfg_comp)
        window.disk_page._on_simulation_success(comp_res)
        window.disk_page.tabs.setCurrentIndex(1)  # Comparison tab
        app.processEvents()

        comp_pixmap = window.grab()
        comp_path = os.path.join(artifact_dir, f"disk_stage5_comparison_{res_name}.png")
        comp_pixmap.save(comp_path, "PNG")
        print(f"Saved: {comp_path}")

        # Component Grabs
        plot_pix = window.disk_page.plot_widget.grab()
        plot_pix.save(os.path.join(artifact_dir, f"disk_stage5_plot_{res_name}.png"), "PNG")

        table_pix = window.disk_page.tabs_container.grab()
        table_pix.save(os.path.join(artifact_dir, f"disk_stage5_tabs_{res_name}.png"), "PNG")

        window.close()


if __name__ == "__main__":
    capture_snapshots()
