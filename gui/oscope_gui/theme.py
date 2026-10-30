"""Theme constants and refined Qt Style Sheets for OScope bright minimal dashboard.

Designed for high contrast, clean typography, zero black-text-box artifacts, readable table headers,
and professional desktop presentation matching the modern blue/white/neutral visual identity.
"""

# Color Palette - Professional Bright & Minimal Simulation Theme
# Blue, white, and neutral gray dominate the interface.
BG_APP = "#F7F9FC"               # Soft cool-white/gray canvas
BG_CANVAS = BG_APP                # Canvas alias
BG_SIDEBAR = "#F3F6FA"           # Subtle cool-gray sidebar
BG_SURFACE = "#FFFFFF"           # Clean white card and panel surface
BG_CARD = BG_SURFACE              # Card alias
BG_SURFACE_HOVER = "#F1F5F9"     # Card hover state
BG_INPUT = "#FFFFFF"             # Form input background
BG_DARK = "#F8FAFC"               # Neutral recessed panel alias
BG_ELEVATED = "#F1F5F9"          # Elevated headers, subpanels, table headers
BORDER = "#E2E8F0"               # Crisp neutral border
BORDER_LIGHT = "#CBD5E1"         # Secondary structural border
BORDER_FOCUS = "#2563EB"         # Primary blue focus ring

TEXT_PRIMARY = "#172033"         # Deep navy-slate main text
TEXT_SECONDARY = "#64748B"       # Refined slate for secondary text and descriptions
TEXT_MUTED = "#94A3B8"           # Slate metadata, footnotes, hints

# Primary Blue Accents
ACCENT = "#2563EB"               # Primary blue accent
ACCENT_HOVER = "#1D4ED8"         # Darker blue hover
ACCENT_PRESSED = "#1E40AF"       # Active dark blue
ACCENT_LIGHT = "#EAF2FF"         # Subtle light blue container background
ACCENT_LIGHT_HOVER = "#DBEAFE"   # Light blue hover

# Cohesive Aliases (mapped to primary blue/slate to eliminate rainbow appearance)
ACCENT_CYAN = "#2563EB"
ACCENT_VIOLET = "#2563EB"
ACCENT_PURPLE = "#2563EB"
ACCENT_INDIGO = "#2563EB"
ACCENT_AMBER = "#D97706"
ACCENT_EMERALD = "#16A34A"
ACCENT_ROSE = "#DC2626"
ACCENT_RED = "#DC2626"

# Semantic Status (green reserved primarily for availability/success status)
SUCCESS = "#16A34A"
SUCCESS_TEXT = "#16A34A"
SUCCESS_BG = "#DCFCE7"

WARNING = "#D97706"
WARNING_TEXT = "#D97706"
WARNING_BG = "#FEF3C7"

DANGER = "#DC2626"
DANGER_TEXT = "#DC2626"
DANGER_BG = "#FEE2E2"

# Harmonious, restrained blue/slate palette for CPU scheduling Gantt chart
PROCESS_COLORS = [
    "#2563EB",  # Process 1 - Primary Blue
    "#3B82F6",  # Process 2 - Royal Blue
    "#60A5FA",  # Process 3 - Soft Sky Blue
    "#1D4ED8",  # Process 4 - Deep Navy Blue
    "#4F46E5",  # Process 5 - Indigo Blue
    "#0284C7",  # Process 6 - Ocean Blue
    "#0D9488",  # Process 7 - Deep Teal
    "#475569",  # Process 8 - Slate
    "#64748B",  # Process 9 - Cool Slate
    "#1E40AF",  # Process 10 - Midnight Blue
]

IDLE_COLOR = "#F1F5F9"
IDLE_BORDER_COLOR = "#CBD5E1"
IDLE_TEXT_COLOR = "#64748B"

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
    padding: 9px 12px;
    border: none;
    border-radius: 6px;
    font-size: 13px;
    font-weight: 500;
}}

QPushButton.nav-btn:hover {{
    background-color: {BORDER};
    color: {TEXT_PRIMARY};
}}

QPushButton.nav-btn:checked {{
    background-color: {ACCENT_LIGHT};
    color: {ACCENT};
    font-weight: 600;
    border-left: 3px solid {ACCENT};
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

/* Clean Standard Buttons */
QPushButton {{
    background-color: {BG_SURFACE};
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER_LIGHT};
    border-radius: 6px;
    padding: 7px 14px;
    font-weight: 500;
    font-size: 13px;
}}

QPushButton:hover {{
    background-color: {BG_DARK};
    border-color: {TEXT_MUTED};
}}

QPushButton:pressed {{
    background-color: {BG_ELEVATED};
}}

QPushButton:disabled {{
    background-color: {BG_ELEVATED};
    color: {TEXT_MUTED};
    border-color: {BORDER};
}}

/* Primary Blue Action Buttons */
QPushButton.btn-primary {{
    background-color: {ACCENT};
    color: #ffffff;
    border: 1px solid {ACCENT};
    border-radius: 6px;
    font-weight: 600;
}}

QPushButton.btn-primary:hover {{
    background-color: {ACCENT_HOVER};
    border-color: {ACCENT_HOVER};
}}

QPushButton.btn-primary:pressed {{
    background-color: {ACCENT_PRESSED};
}}

QPushButton.btn-primary:disabled {{
    background-color: {BORDER_LIGHT};
    color: {TEXT_MUTED};
    border-color: {BORDER_LIGHT};
}}

/* Secondary Light Blue Action Buttons */
QPushButton.btn-secondary {{
    background-color: {ACCENT_LIGHT};
    color: {ACCENT};
    border: 1px solid #DBEAFE;
    border-radius: 6px;
    font-weight: 600;
}}

QPushButton.btn-secondary:hover {{
    background-color: {ACCENT_LIGHT_HOVER};
    border-color: #BFDBFE;
}}

/* Danger Action Buttons */
QPushButton.btn-danger {{
    background-color: {DANGER_BG};
    color: {DANGER_TEXT};
    border: 1px solid #FECACA;
    border-radius: 6px;
}}

QPushButton.btn-danger:hover {{
    background-color: #FCA5A5;
}}

/* Form Controls */
QLineEdit, QSpinBox, QComboBox {{
    background-color: {BG_INPUT};
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER_LIGHT};
    border-radius: 6px;
    padding: 6px 10px;
    selection-background-color: {ACCENT};
    selection-color: #ffffff;
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
    selection-background-color: {ACCENT_LIGHT};
    selection-color: {ACCENT};
    padding: 4px;
}}

/* Clean Tables with Clear Visible Headers */
QTableWidget {{
    background-color: {BG_SURFACE};
    alternate-background-color: #F8FAFC;
    border: 1px solid {BORDER};
    border-radius: 6px;
    gridline-color: {BORDER};
    outline: none;
}}

QTableWidget::item {{
    padding: 7px 10px;
    border-bottom: 1px solid {BORDER};
    color: {TEXT_PRIMARY};
}}

QTableWidget::item:selected {{
    background-color: {ACCENT_LIGHT};
    color: {ACCENT};
}}

QHeaderView {{
    background-color: {BG_ELEVATED};
    border: none;
}}

QHeaderView::section {{
    background-color: {BG_ELEVATED};
    color: {TEXT_SECONDARY};
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
    background-color: {BORDER_LIGHT};
    min-height: 24px;
    border-radius: 3px;
}}

QScrollBar::handle:vertical:hover {{
    background-color: {TEXT_MUTED};
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
    background-color: {BORDER_LIGHT};
    min-width: 24px;
    border-radius: 3px;
}}

QScrollBar::handle:horizontal:hover {{
    background-color: {TEXT_MUTED};
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
    background-color: {BG_ELEVATED};
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
    color: {ACCENT};
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
    background-color: {BG_SURFACE};
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER_LIGHT};
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
