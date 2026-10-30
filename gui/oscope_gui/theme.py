"""Theme constants and refined Qt Style Sheets for OScope dark dashboard.

Designed for high contrast, vibrant visuals, zero black-text-box artifacts, readable table headers,
and professional desktop presentation.
"""

# Color Palette - High-Tech Scientific Lab & Modern Dark Simulation Theme
BG_APP = "#0a0e17"               # Deep Obsidian Midnight canvas
BG_CANVAS = BG_APP                # Canvas alias
BG_SIDEBAR = "#0e1422"           # Dark slate-navy sidebar
BG_SURFACE = "#131927"           # Card and panel surface
BG_CARD = BG_SURFACE              # Card alias
BG_SURFACE_HOVER = "#182133"     # Card hover state
BG_INPUT = "#0b0f19"             # Form input recessed background
BG_DARK = BG_INPUT               # Dark recessed alias
BG_ELEVATED = "#1c2438"          # Elevated headers, subpanels, table headers
BORDER = "#1e293b"               # Subtle structural border
BORDER_LIGHT = "#334155"         # Secondary lighter border
BORDER_FOCUS = "#38bdf8"         # Electric sky blue focus ring

TEXT_PRIMARY = "#f8fafc"         # Ultra-crisp readable white
TEXT_SECONDARY = "#94a3b8"       # Clean slate gray for descriptions and body
TEXT_MUTED = "#64748b"           # Secondary metadata, footnotes, hints

# Vibrant Accents
ACCENT = "#0284c7"               # Primary blue-cyan accent
ACCENT_HOVER = "#0ea5e9"         # Hover cyan
ACCENT_PRESSED = "#0369a1"       # Active dark cyan
ACCENT_CYAN = "#00e5ff"          # Glowing highlight cyan
ACCENT_VIOLET = "#8b5cf6"        # Vivid violet for active tags & nav
ACCENT_PURPLE = ACCENT_VIOLET    # Purple alias
ACCENT_INDIGO = "#6366f1"        # Primary gradient endpoint
ACCENT_AMBER = "#f59e0b"         # Amber highlight
ACCENT_EMERALD = "#10b981"       # Emerald highlight
ACCENT_ROSE = "#f43f5e"          # Rose highlight
ACCENT_RED = ACCENT_ROSE         # Red alias

SUCCESS = "#10b981"
SUCCESS_TEXT = "#34d399"
SUCCESS_BG = "rgba(16, 185, 129, 0.15)"

WARNING = "#f59e0b"
WARNING_TEXT = "#fbbf24"
WARNING_BG = "rgba(245, 158, 11, 0.15)"

DANGER = "#f43f5e"
DANGER_TEXT = "#fb7185"
DANGER_BG = "rgba(244, 63, 94, 0.15)"

# Vibrant, distinguishable palette for process scheduling Gantt chart
PROCESS_COLORS = [
    "#0ea5e9",  # Process 1 - Electric Sky Blue
    "#8b5cf6",  # Process 2 - Vivid Violet
    "#10b981",  # Process 3 - Emerald Mint
    "#f59e0b",  # Process 4 - Bright Amber
    "#f43f5e",  # Process 5 - Radiant Rose
    "#06b6d4",  # Process 6 - Cyan Teal
    "#d946ef",  # Process 7 - Fuchsia Neon
    "#f97316",  # Process 8 - Tangerine Coral
    "#84cc16",  # Process 9 - Electric Lime
    "#6366f1",  # Process 10 - Deep Indigo
]

IDLE_COLOR = "#1e293b"
IDLE_BORDER_COLOR = "#334155"
IDLE_TEXT_COLOR = "#94a3b8"

FONT_FAMILY = "Segoe UI"

MAIN_STYLESHEET = f"""
/* Top-level windows and containers */
QMainWindow, QDialog {{
    background-color: {BG_APP};
    color: {TEXT_PRIMARY};
}}

/* Universal font and text color without forcing background on children */
QWidget {{
    color: {TEXT_PRIMARY};
    font-family: "Segoe UI";
    font-size: 13px;
}}

/* CRITICAL: Labels must be completely transparent to avoid black rectangles */
QLabel {{
    background-color: transparent;
    color: {TEXT_PRIMARY};
    padding: 0px;
    margin: 0px;
}}

/* Sidebar navigation */
QFrame#SidebarFrame {{
    background-color: {BG_SIDEBAR};
    border-right: 1px solid {BORDER};
}}

QPushButton.nav-btn {{
    background-color: transparent;
    color: {TEXT_SECONDARY};
    text-align: left;
    padding: 10px 14px;
    border: none;
    border-radius: 6px;
    font-size: 13px;
    font-weight: 500;
}}

QPushButton.nav-btn:hover {{
    background-color: {BG_SURFACE};
    color: {TEXT_PRIMARY};
}}

QPushButton.nav-btn:checked {{
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 rgba(14, 165, 233, 0.22), stop:1 rgba(99, 102, 241, 0.08));
    color: #ffffff;
    font-weight: 600;
    border-left: 3px solid {ACCENT_HOVER};
}}

QPushButton.nav-btn:disabled {{
    color: {TEXT_MUTED};
    background-color: transparent;
}}

/* Cards and Panels */
QFrame[card="true"] {{
    background-color: {BG_SURFACE};
    border: 1px solid {BORDER};
    border-radius: 8px;
}}

/* Buttons */
QPushButton {{
    background-color: {BG_ELEVATED};
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER_LIGHT};
    border-radius: 6px;
    padding: 7px 14px;
    font-weight: 500;
    font-size: 13px;
}}

QPushButton:hover {{
    background-color: #28354d;
    border-color: #475569;
}}

QPushButton:pressed {{
    background-color: #161e30;
}}

QPushButton:disabled {{
    background-color: #131927;
    color: {TEXT_MUTED};
    border-color: {BORDER};
}}

QPushButton.btn-primary {{
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {ACCENT}, stop:1 {ACCENT_INDIGO});
    color: #ffffff;
    border: 1px solid rgba(56, 189, 248, 0.4);
    font-weight: 600;
}}

QPushButton.btn-primary:hover {{
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {ACCENT_HOVER}, stop:1 #818cf8);
    border-color: #7dd3fc;
}}

QPushButton.btn-primary:pressed {{
    background-color: {ACCENT_PRESSED};
}}

QPushButton.btn-primary:disabled {{
    background-color: #1c2438;
    color: {TEXT_MUTED};
    border-color: {BORDER};
}}

QPushButton.btn-danger {{
    background-color: {DANGER_BG};
    color: {DANGER_TEXT};
    border: 1px solid {DANGER};
}}

QPushButton.btn-danger:hover {{
    background-color: rgba(244, 63, 94, 0.28);
}}

/* Form Controls */
QLineEdit, QSpinBox, QComboBox {{
    background-color: {BG_INPUT};
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER};
    border-radius: 6px;
    padding: 6px 10px;
    selection-background-color: {ACCENT};
    min-height: 20px;
}}

QLineEdit:focus, QSpinBox:focus, QComboBox:focus {{
    border: 1px solid {BORDER_FOCUS};
}}

QComboBox {{
    padding-right: 22px;
}}

QComboBox::drop-down {{
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 24px;
    border: none;
}}

QComboBox QAbstractItemView {{
    background-color: {BG_SURFACE};
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER_LIGHT};
    selection-background-color: {ACCENT};
    selection-color: #ffffff;
    padding: 4px;
}}

/* Clean Tables with Clear Visible Headers */
QTableWidget {{
    background-color: {BG_SURFACE};
    alternate-background-color: #0f1420;
    border: 1px solid {BORDER};
    border-radius: 6px;
    gridline-color: #1a2338;
    outline: none;
}}

QTableWidget::item {{
    padding: 7px 10px;
    border-bottom: 1px solid #1a2338;
    color: {TEXT_PRIMARY};
}}

QTableWidget::item:selected {{
    background-color: rgba(14, 165, 233, 0.35);
    color: #ffffff;
}}

QHeaderView {{
    background-color: {BG_ELEVATED};
    border: none;
}}

QHeaderView::section {{
    background-color: {BG_ELEVATED};
    color: {TEXT_PRIMARY};
    padding: 8px 12px;
    border: none;
    border-right: 1px solid {BORDER};
    border-bottom: 1px solid {BORDER};
    font-weight: 600;
    font-size: 12px;
}}

/* Scrollbars */
QScrollBar:vertical {{
    background-color: transparent;
    width: 7px;
    margin: 0px;
}}

QScrollBar::handle:vertical {{
    background-color: #283548;
    min-height: 24px;
    border-radius: 3px;
}}

QScrollBar::handle:vertical:hover {{
    background-color: #475569;
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}

QScrollBar:horizontal {{
    background-color: transparent;
    height: 7px;
    margin: 0px;
}}

QScrollBar::handle:horizontal {{
    background-color: #283548;
    min-width: 24px;
    border-radius: 3px;
}}

QScrollBar::handle:horizontal:hover {{
    background-color: #475569;
}}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0px;
}}

/* Tabs */
QTabWidget::pane {{
    border: 1px solid {BORDER};
    background-color: {BG_SURFACE};
    border-radius: 6px;
    padding: 8px;
}}

QTabBar::tab {{
    background-color: {BG_APP};
    color: {TEXT_SECONDARY};
    padding: 8px 16px;
    margin-right: 4px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    border: 1px solid transparent;
    font-weight: 500;
}}

QTabBar::tab:selected {{
    background-color: {BG_SURFACE};
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER};
    border-bottom: 1px solid {BG_SURFACE};
    font-weight: 600;
}}

QTabBar::tab:hover:!selected {{
    background-color: {BG_SURFACE};
    color: {TEXT_PRIMARY};
}}

/* Text browser / logs */
QTextEdit, QPlainTextEdit {{
    background-color: {BG_INPUT};
    color: #e2e8f0;
    border: 1px solid {BORDER};
    border-radius: 6px;
    font-family: "Cascadia Code", "Consolas", "Courier New", monospace;
    font-size: 12px;
    padding: 8px;
}}

/* ScrollArea */
QScrollArea {{
    background-color: transparent;
    border: none;
}}
"""
