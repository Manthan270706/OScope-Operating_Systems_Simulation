# -*- coding: utf-8 -*-
"""Formats Mid Sem PPT.pptx using Lato and Lato Bold fonts across all 9 slides,
ensuring clean visual hierarchy, generous margins, and no text/image overflow.
"""

from pathlib import Path
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN

repo_root = Path(__file__).resolve().parent.parent
ppt_path = repo_root / "Mid Sem PPT.pptx"

prs = Presentation(str(ppt_path))

# Color Palette
COLOR_PRIMARY = RGBColor(15, 23, 42)    # Slate-900 (Headings, bold labels)
COLOR_SECONDARY = RGBColor(51, 65, 85)  # Slate-700 (Body text, citations)
COLOR_ACCENT = RGBColor(37, 99, 235)    # Royal Blue (Section titles, list numbers)
COLOR_MUTED = RGBColor(100, 116, 139)   # Slate-500 (Captions, dates)

def apply_title_style(shape, title_text):
    shape.top = Inches(0.85)
    shape.left = Inches(1.2)
    shape.width = Inches(14.0)
    shape.height = Inches(1.2)
    
    tf = shape.text_frame
    tf.text = ""
    tf.word_wrap = True
    
    p = tf.paragraphs[0]
    r = p.add_run()
    r.text = title_text
    r.font.name = "Lato"
    r.font.bold = True
    r.font.size = Pt(44)
    r.font.color.rgb = COLOR_PRIMARY

def set_split_slide(slide, title_text, items, img_path):
    # 1. Format Title
    title_shape = next((s for s in slide.shapes if s.name == "TextBox 17"), None)
    if title_shape:
        apply_title_style(title_shape, title_text)
        
    # 2. Format Body Text (Left Column)
    body_shape = next((s for s in slide.shapes if s.name == "Rectangle 11"), None)
    if body_shape:
        body_shape.left = Inches(1.2)
        body_shape.top = Inches(2.4)
        body_shape.width = Inches(8.8)
        body_shape.height = Inches(7.8)
        
        tf = body_shape.text_frame
        tf.text = ""
        tf.word_wrap = True
        
        for idx, item in enumerate(items):
            p = tf.paragraphs[0] if idx == 0 else tf.add_paragraph()
            p.level = 0
            p.space_after = Pt(14)
            p.line_spacing = 1.18
            
            if ":" in item:
                prefix, rest = item.split(":", 1)
                r1 = p.add_run()
                r1.text = prefix + ":"
                r1.font.name = "Lato"
                r1.font.bold = True
                r1.font.size = Pt(17)
                r1.font.color.rgb = COLOR_PRIMARY
                
                r2 = p.add_run()
                r2.text = rest
                r2.font.name = "Lato"
                r2.font.bold = False
                r2.font.size = Pt(17)
                r2.font.color.rgb = COLOR_SECONDARY
            else:
                r = p.add_run()
                r.text = item
                r.font.name = "Lato"
                r.font.bold = False
                r.font.size = Pt(17)
                r.font.color.rgb = COLOR_SECONDARY

    # 3. Position Pictures: distinguish header logo (< 50KB) vs technical diagram (> 50KB)
    for s in slide.shapes:
        if s.shape_type == 13: # picture
            blob_size = len(s.image.blob)
            if blob_size < 50000:
                # College Logo -> top right
                s.left = Inches(16.15)
                s.top = Inches(0.0)
                s.width = Inches(2.71)
                s.height = Inches(2.29)
            else:
                # Technical Diagram -> right column below title
                s.left = Inches(10.4)
                s.top = Inches(2.4)
                s.width = Inches(8.8)
                s.height = Inches(5.8)

def set_full_slide(slide, title_text, items, font_size_pt=19, space_after_pt=18):
    # 1. Format Title
    title_shape = next((s for s in slide.shapes if s.name == "TextBox 17"), None)
    if title_shape:
        apply_title_style(title_shape, title_text)
        
    # 2. Format Body Text (Full Width)
    body_shape = next((s for s in slide.shapes if s.name == "Rectangle 11"), None)
    if body_shape:
        body_shape.left = Inches(1.8)
        body_shape.top = Inches(2.4)
        body_shape.width = Inches(16.4)
        body_shape.height = Inches(7.8)
        
        tf = body_shape.text_frame
        tf.text = ""
        tf.word_wrap = True
        
        for idx, item in enumerate(items):
            p = tf.paragraphs[0] if idx == 0 else tf.add_paragraph()
            p.level = 0
            p.space_after = Pt(space_after_pt)
            p.line_spacing = 1.22
            
            if ":" in item:
                prefix, rest = item.split(":", 1)
                r1 = p.add_run()
                r1.text = prefix + ":"
                r1.font.name = "Lato"
                r1.font.bold = True
                r1.font.size = Pt(font_size_pt)
                r1.font.color.rgb = COLOR_PRIMARY
                
                r2 = p.add_run()
                r2.text = rest
                r2.font.name = "Lato"
                r2.font.bold = False
                r2.font.size = Pt(font_size_pt)
                r2.font.color.rgb = COLOR_SECONDARY
            else:
                r = p.add_run()
                r.text = item
                r.font.name = "Lato"
                r.font.bold = False
                r.font.size = Pt(font_size_pt)
                r.font.color.rgb = COLOR_SECONDARY
                
    # Ensure header logo stays in position
    for s in slide.shapes:
        if s.shape_type == 13 and len(s.image.blob) < 50000:
            s.left = Inches(16.15)
            s.top = Inches(0.0)
            s.width = Inches(2.71)
            s.height = Inches(2.29)

# ==========================================================
# SLIDE 1: Title Slide Formatting
# ==========================================================
slide1 = prs.slides[0]
for s in slide1.shapes:
    if s.has_text_frame:
        name = s.name
        tf = s.text_frame
        
        if name == "TextBox 18":  # Project Title
            tf.text = ""
            p = tf.paragraphs[0]
            r1 = p.add_run()
            r1.text = "Project Title :- "
            r1.font.name = "Lato"
            r1.font.bold = True
            r1.font.size = Pt(24)
            r1.font.color.rgb = COLOR_ACCENT
            
            r2 = p.add_run()
            r2.text = "OScope: Operating Systems Simulation & Experimentation Laboratory"
            r2.font.name = "Lato"
            r2.font.bold = True
            r2.font.size = Pt(24)
            r2.font.color.rgb = COLOR_PRIMARY
            
        elif name == "TextBox 19":  # DIV
            tf.text = ""
            p = tf.paragraphs[0]
            r1 = p.add_run()
            r1.text = "DIV :- "
            r1.font.name = "Lato"
            r1.font.bold = True
            r1.font.size = Pt(18)
            r1.font.color.rgb = COLOR_PRIMARY
            
            r2 = p.add_run()
            r2.text = "CSE(AI)-E"
            r2.font.name = "Lato"
            r2.font.bold = False
            r2.font.size = Pt(18)
            r2.font.color.rgb = COLOR_SECONDARY
            
        elif name == "TextBox 21":  # Day
            tf.text = ""
            p = tf.paragraphs[0]
            r1 = p.add_run()
            r1.text = "Day - "
            r1.font.name = "Lato"
            r1.font.bold = True
            r1.font.size = Pt(18)
            r1.font.color.rgb = COLOR_PRIMARY
            
            r2 = p.add_run()
            r2.text = "Friday"
            r2.font.name = "Lato"
            r2.font.bold = False
            r2.font.size = Pt(18)
            r2.font.color.rgb = COLOR_SECONDARY
            
        elif name == "TextBox 22":  # Date
            tf.text = ""
            p = tf.paragraphs[0]
            r1 = p.add_run()
            r1.text = "Date : "
            r1.font.name = "Lato"
            r1.font.bold = True
            r1.font.size = Pt(18)
            r1.font.color.rgb = COLOR_PRIMARY
            
            r2 = p.add_run()
            r2.text = "30/10/2026"
            r2.font.name = "Lato"
            r2.font.bold = False
            r2.font.size = Pt(18)
            r2.font.color.rgb = COLOR_SECONDARY
            
        elif name == "TextBox 23":  # Presented by
            tf.text = ""
            p0 = tf.paragraphs[0]
            p0.space_after = Pt(8)
            r0 = p0.add_run()
            r0.text = "Presented by :-"
            r0.font.name = "Lato"
            r0.font.bold = True
            r0.font.size = Pt(20)
            r0.font.color.rgb = COLOR_PRIMARY
            
            members = [
                ("Aditya Rana", "12413107"),
                ("Nitish Sahu", "12412096"),
                ("Palash Sahuji", "12414915"),
                ("Manthan Sali", "12411978")
            ]
            for m_name, m_prn in members:
                p = tf.add_paragraph()
                p.space_after = Pt(4)
                r_n = p.add_run()
                r_n.text = f"{m_name} "
                r_n.font.name = "Lato"
                r_n.font.bold = True
                r_n.font.size = Pt(17)
                r_n.font.color.rgb = COLOR_PRIMARY
                
                r_dash = p.add_run()
                r_dash.text = "  —  PRN: "
                r_dash.font.name = "Lato"
                r_dash.font.bold = False
                r_dash.font.size = Pt(17)
                r_dash.font.color.rgb = COLOR_MUTED
                
                r_id = p.add_run()
                r_id.text = m_prn
                r_id.font.name = "Lato"
                r_id.font.bold = True
                r_id.font.size = Pt(17)
                r_id.font.color.rgb = COLOR_ACCENT
                
        elif name == "TextBox 24":  # Project Guide
            tf.text = ""
            p = tf.paragraphs[0]
            r1 = p.add_run()
            r1.text = "Project Guide :- "
            r1.font.name = "Lato"
            r1.font.bold = True
            r1.font.size = Pt(20)
            r1.font.color.rgb = COLOR_PRIMARY
            
            r2 = p.add_run()
            r2.text = "Prof. Priyanka Khalate"
            r2.font.name = "Lato"
            r2.font.bold = True
            r2.font.size = Pt(20)
            r2.font.color.rgb = COLOR_ACCENT
            
        elif name == "TextBox 25":  # Department
            tf.text = ""
            p = tf.paragraphs[0]
            p.alignment = PP_ALIGN.CENTER
            r1 = p.add_run()
            r1.text = "DEPARTMENT OF COMPUTER SCIENCE ENGINEERING\n(ARTIFICIAL INTELLIGENCE)"
            r1.font.name = "Lato"
            r1.font.bold = True
            r1.font.size = Pt(20)
            r1.font.color.rgb = COLOR_PRIMARY
            
        elif name == "TextBox 26":  # Institution
            tf.text = ""
            p = tf.paragraphs[0]
            p.alignment = PP_ALIGN.CENTER
            r1 = p.add_run()
            r1.text = "VISHWAKARMA INSTITUTE OF TECHNOLOGY, PUNE"
            r1.font.name = "Lato"
            r1.font.bold = True
            r1.font.size = Pt(22)
            r1.font.color.rgb = COLOR_ACCENT

# ==========================================================
# SLIDE 2: Overview (Agenda)
# ==========================================================
slide2 = prs.slides[1]
overview_items = [
    "1. Introduction & Project Scope",
    "2. Motivation & Problem Statement",
    "3. Project Objectives & Deliverables",
    "4. Design & 4-Tier System Architecture",
    "5. Technical Stack & Implementation Details",
    "6. Academic References & Citations",
    "7. Conclusion & Project Summary"
]
set_full_slide(slide2, "Overview", overview_items, font_size_pt=22, space_after_pt=18)

# ==========================================================
# SLIDE 3: Introduction (Split Layout)
# ==========================================================
slide3 = prs.slides[2]
intro_items = [
    "Interactive Systems Laboratory: Connects theoretical Operating System principles with real algorithmic execution, measurement, vector visualization, and comparative benchmarks.",
    "Bridging Abstract Theory: Eliminates black-box confusion by demystifying how CPU dispatching, dynamic memory placement, virtual paging, and deadlocks function in practice.",
    "Dual-Pillar Architecture: Couples an authoritative C++20 simulation core with real Linux/POSIX kernel interfaces (fork/execve process trees, anonymous pipes, semaphores, and /proc telemetry).",
    "Production-Grade Web Experience: Delivers an accessible, zero-dependency modern light-mode engineering platform inspired by Linear/Geist design guidelines across 10 distinct OS domains."
]
set_split_slide(slide3, "Introduction", intro_items, repo_root / "modules_matrix.png")

# ==========================================================
# SLIDE 4: Motivation (Split Layout)
# ==========================================================
slide4 = prs.slides[3]
motivation_items = [
    "High Cognitive Barrier: Abstract kernel concepts (address translation, multi-queue preemption, Belady's anomaly) are hidden in kernel space and difficult to grasp from static textbook diagrams.",
    "Severe Tool Fragmentation: Students are forced to switch between disconnected, single-topic CLI programs or abandoned 2000s Java applets with no unified workflow.",
    "Lack of Empirical Verification: Inability to systematically test and benchmark edge cases (convoy effects, priority inversions, memory fragmentation, and safe vs unsafe state sequences).",
    "Active Learning Methodology: Addresses the proven pedagogical pipeline: Learn -> Configure Workloads -> Execute C++ Simulation -> Observe Vector Visualizers -> Measure Metrics -> Analyze."
]
set_split_slide(slide4, "Motivation", motivation_items, repo_root / "visualizers_showcase.png")

# ==========================================================
# SLIDE 5: Objective (Full Slide)
# ==========================================================
slide5 = prs.slides[4]
obj_items = [
    "Unified 10-Module Suite: Build a comprehensive laboratory covering CPU Scheduling, Dynamic Memory, Page Replacement, Banker's Deadlock Avoidance, Disk Arm Seek, Virtual Memory MMU, File Systems, Process Lifecycle, POSIX Concurrency, and Host Telemetry.",
    "High-Precision Vector Visualizers: Implement native SVG rendering for Gantt charts with millisecond guidelines, memory maps with fragmentation analysis, step-by-step frame steppers, and cylinder seek plots.",
    "Authoritative C++ Core & Deterministic Benchmarking: Connect simulations to a compiled C++20 engine verified by 356 GoogleTests, providing reproducible textbook presets (Belady's anomaly, convoy effect, safe sequence).",
    "Dual Modern Interface: Deliver a zero-dependency light-mode web application and a native PySide6 desktop GUI with 150 automated end-to-end pytest tests."
]
set_full_slide(slide5, "Objective", obj_items, font_size_pt=19, space_after_pt=18)

# ==========================================================
# SLIDE 6: System Architecture (Split Layout)
# ==========================================================
slide6 = prs.slides[5]
arch_items = [
    "Tier 1 (Presentation Layer): Modern Light-Mode Single Page Application (HTML5 / CSS3 / Vanilla ES6+) + Native PySide6 (Qt 6) Desktop GUI. Features custom inline SVG stroke icons.",
    "Tier 2 (Application & REST API Layer): Python 3.12 Multi-Threaded HTTP Server (ThreadingHTTPServer) with zero external pip dependencies routing JSON endpoints (/api/*/run).",
    "Tier 3 (Platform Execution Bridge): Automated environment runner supporting native Linux and Windows WSL 2 (wsl.exe), handling CLI argument marshaling and telemetry streaming.",
    "Tier 4 (Authoritative Simulation Core): Compiled C++20 engine executing deterministic algorithms, real POSIX system calls (fork, execve, pipe, sem_t), and /proc parser."
]
set_split_slide(slide6, "System Architecture", arch_items, repo_root / "architecture_diagram.png")

# ==========================================================
# SLIDE 7: Tech Stack (Full Slide)
# ==========================================================
slide7 = prs.slides[6]
stack_items = [
    "Core Simulation Engine: C++20 (Modern ISO C++), CMake 3.20+, GoogleTest (356 unit tests), POSIX APIs (<unistd.h>, <semaphore.h>).",
    "Backend & API Server: Python 3.12 Standard Library (http.server.ThreadingHTTPServer - zero external pip dependencies), Subprocess / WSL 2 execution runner.",
    "Modern Web Frontend: Vanilla JavaScript (ES6+), HTML5, CSS3 Custom Properties (Linear/Geist Light Mode Design System), Vector SVG Engine (Lucide-standard icons).",
    "Desktop GUI & Testing: PySide6 (Qt 6), Pytest 9.2 (150 automated tests), GitHub Actions CI pipeline."
]
set_full_slide(slide7, "Tech Stack", stack_items, font_size_pt=20, space_after_pt=20)

# ==========================================================
# SLIDE 8: References (Full Slide)
# ==========================================================
slide8 = prs.slides[7]
ref_items = [
    "Silberschatz, A., Galvin, P. B., & Gagne, G. (2021). Operating System Concepts (10th ed.). John Wiley & Sons.",
    "Tanenbaum, A. S., & Bos, H. (2023). Modern Operating Systems (5th ed.). Pearson Education.",
    "Al-Kharabsheh, K. et al. (2022). \"Evaluating Interactive Visual Simulators for Operating Systems Education.\" IEEE Transactions on Learning Technologies, 15(3), 340-352.",
    "Robbins, K. A., & Robbins, S. (2020). \"Practical UNIX and Systems Programming Visualization.\" ACM Technical Symposium on Computer Science Education (SIGCSE), 52(1), 112-118.",
    "Love, R. (2018). Linux Kernel Development (3rd ed.). Addison-Wesley Professional."
]
set_full_slide(slide8, "References", ref_items, font_size_pt=18, space_after_pt=16)

# ==========================================================
# SLIDE 9: Conclusion (Full Slide)
# ==========================================================
slide9 = prs.slides[8]
conclusion_items = [
    "Comprehensive Integration: Successfully unified 10 core Operating Systems domains into a single production-quality laboratory platform.",
    "Pedagogical Impact: Bridges abstract theoretical textbook models with concrete visual execution, enabling intuitive experimentation for CS students.",
    "Engineering Rigor: Combines high-performance C++20 simulation accuracy with real POSIX kernel integration and 150 automated verification tests.",
    "Accessible Deployment: Zero external pip dependencies, instant browser launch, and modern light-theme devtool ergonomics."
]
set_full_slide(slide9, "Conclusion", conclusion_items, font_size_pt=20, space_after_pt=20)

prs.save(str(ppt_path))
print("Successfully formatted Mid Sem PPT.pptx with Lato and Lato Bold fonts across all 9 slides!")
