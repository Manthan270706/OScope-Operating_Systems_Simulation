"""Automated GUI screenshot audit across all 10 OScope modules at 1366x768 and 1920x1080.

Runs offscreen using Qt and the live WSL C++ backend runner, navigates to every page,
triggers simulation views, and captures high-resolution screenshots for visual inspection.
"""

import os
import sys
import time
from pathlib import Path

# Allow native platform for crisp typography rendering
if "QT_QPA_PLATFORM" in os.environ:
    del os.environ["QT_QPA_PLATFORM"]

# Add gui directory to path
repo_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(repo_root / "gui"))

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QApplication

from oscope_gui.backend.runner import discover_backend
from oscope_gui.main_window import MainWindow


PAGES_TO_AUDIT = [
    ("dashboard", "Overview Dashboard"),
    ("scheduling", "CPU Scheduling"),
    ("memory", "Memory Allocation"),
    ("paging", "Page Replacement"),
    ("deadlock", "Deadlock Management"),
    ("disk", "Disk Scheduling"),
    ("linux", "Linux / POSIX Experiments"),
    ("monitor", "Host Resource Monitoring"),
    ("filesystem", "Simulated File System"),
    ("translation", "Virtual Memory & MMU Translation"),
    ("lifecycle", "Process Lifecycle State Machine"),
]

TARGET_RESOLUTIONS = [
    (1366, 768),
    (1920, 1080),
]


def run_audit():
    app = QApplication.instance() or QApplication(sys.argv)

    # Destination directories
    out_dir = repo_root / "results" / "screenshots"
    out_dir.mkdir(parents=True, exist_ok=True)

    # Artifacts directory
    artifacts_dir = Path(r"C:\Users\Nitish Sahu\.gemini\antigravity-ide\brain\d0f348d1-dbee-438f-8911-b98a5c9deca9")
    if artifacts_dir.exists():
        art_screens = artifacts_dir / "audit_screenshots"
        art_screens.mkdir(parents=True, exist_ok=True)
    else:
        art_screens = out_dir

    runner, info = discover_backend(str(repo_root))
    print(f"[AUDIT] Backend discovered: {info.runner_type} | available: {info.is_available} | msg: {info.status_message}")

    window = MainWindow(runner)
    window.show()

    # Pre-run or seed pages that have default presets so diagrams show rich content
    try:
        # Pre-seed address translation simulation
        if hasattr(window.address_translation_page, "run_simulation"):
            window.address_translation_page.run_simulation()
            # Wait briefly for worker if running
            if window.address_translation_page.worker:
                window.address_translation_page.worker.wait(2000)

        # Pre-seed process lifecycle simulation
        if hasattr(window.process_lifecycle_page, "run_simulation"):
            window.process_lifecycle_page.run_simulation()
            if window.process_lifecycle_page.worker:
                window.process_lifecycle_page.worker.wait(2000)

        # Pre-seed disk scheduling with preset
        if hasattr(window.disk_page, "run_simulation"):
            window.disk_page.run_simulation()
            if hasattr(window.disk_page, "_active_worker") and window.disk_page._active_worker:
                window.disk_page._active_worker.wait(2000)

        # Pre-seed deadlock safety
        if hasattr(window.deadlock_page, "run_simulation"):
            window.deadlock_page.run_simulation()
            if hasattr(window.deadlock_page, "_active_worker") and window.deadlock_page._active_worker:
                window.deadlock_page._active_worker.wait(2000)

        # Pre-seed filesystem simulation
        if hasattr(window.filesystem_page, "run_simulation"):
            window.filesystem_page.run_simulation()
            if hasattr(window.filesystem_page, "_active_worker") and window.filesystem_page._active_worker:
                window.filesystem_page._active_worker.wait(2000)
    except Exception as e:
        print(f"[AUDIT WARN] Seed execution exception: {e}")

    app.processEvents()

    audit_records = []

    for width, height in TARGET_RESOLUTIONS:
        print(f"\n[AUDIT] === Testing Target Resolution: {width}x{height} ===")
        window.resize(width, height)
        window.setFixedSize(width, height)
        app.processEvents()
        time.sleep(0.1)

        for page_key, page_title in PAGES_TO_AUDIT:
            window.navigate_to_page(page_key)
            app.processEvents()
            time.sleep(0.15)

            current_page_widget = window.stack.currentWidget()
            page_geom = current_page_widget.geometry()

            # Grab full window
            pixmap = window.grab()
            filename = f"audit_{page_key}_{width}x{height}.png"
            file_path = out_dir / filename
            pixmap.save(str(file_path), "PNG")

            art_path = art_screens / filename
            pixmap.save(str(art_path), "PNG")

            # Check for horizontal overflow
            content_width = current_page_widget.width()
            expected_content_width = width - window.sidebar.width()
            has_overflow = content_width > (expected_content_width + 10)

            status = "PASS" if not has_overflow else "OVERFLOW"
            audit_records.append({
                "page_key": page_key,
                "page_title": page_title,
                "resolution": f"{width}x{height}",
                "status": status,
                "screenshot": str(file_path),
                "artifact": str(art_path),
            })
            print(f"  [PAGE] {page_title:<35} | {width}x{height} | {status} | Saved: {filename}")

    window.close()
    print("\n[AUDIT COMPLETE] All 22 screenshots captured successfully.")
    return audit_records


if __name__ == "__main__":
    records = run_audit()
    overflows = [r for r in records if r["status"] != "PASS"]
    if overflows:
        print(f"[WARNING] Detected {len(overflows)} layout overflow(s)!")
        sys.exit(1)
    else:
        print("[SUCCESS] Zero layout overflows detected across all resolutions!")
        sys.exit(0)
