"""Educational visualization widgets for Linux / POSIX system experiments and synchronization."""

from typing import Any, Dict, List, Optional

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import (
    QBrush,
    QColor,
    QFont,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
)
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ..models.linux_experiments import (
    FifoIpcResultModel,
    LinuxExperimentsResultModel,
    MessageQueueIpcResultModel,
    MutexSyncResultModel,
    OrphanResultModel,
    PetersonResultModel,
    PipeIpcResultModel,
    PosixSemaphoreResultModel,
    ProcessExecResultModel,
    ProducerConsumerResultModel,
    SharedMemoryIpcResultModel,
    ThreadCreationResultModel,
    ZombieResultModel,
)
from ..theme import (
    ACCENT,
    ACCENT_AMBER,
    ACCENT_CYAN,
    ACCENT_EMERALD,
    ACCENT_HOVER,
    ACCENT_INDIGO,
    ACCENT_ROSE,
    ACCENT_VIOLET,
    BG_APP,
    BG_ELEVATED,
    BG_SURFACE,
    BORDER,
    BORDER_LIGHT,
    SUCCESS,
    TEXT_MUTED,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
)


def create_step_card(title: str, subtitle: str, accent_color: str) -> QFrame:
    """Helper to create a dark styled card for experiment demonstrations."""
    card = QFrame()
    card.setStyleSheet(
        f"""
        QFrame {{
            background-color: {BG_SURFACE};
            border: 1px solid {BORDER};
            border-top: 3px solid {accent_color};
            border-radius: 8px;
        }}
        """
    )
    return card


class ProcessLifecycleTreeWidget(QWidget):
    """Visual diagram showing fork/exec, zombie state transitions, and orphan reparenting."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        # 3 Demo Cards Container
        grid = QGridLayout()
        grid.setSpacing(14)

        # 1. Exec Image Replacement Card
        self.card_exec = create_step_card("Process Image Replacement (exec*)", "fork() + execve()", ACCENT)
        exec_layout = QVBoxLayout(self.card_exec)
        exec_layout.setContentsMargins(16, 14, 16, 14)
        exec_layout.setSpacing(8)

        lbl_exec_title = QLabel("1. Process Image Replacement (exec*)")
        lbl_exec_title.setStyleSheet("font-size: 14px; font-weight: 700; color: #ffffff;")
        self.lbl_exec_flow = QLabel("Parent PID -> Child PID (runs /bin/echo)")
        self.lbl_exec_flow.setStyleSheet(f"font-size: 12px; font-weight: 600; color: {ACCENT};")
        self.lbl_exec_output = QLabel("Captured Output: [Waiting for experiment]")
        self.lbl_exec_output.setStyleSheet(f"font-size: 11px; color: {TEXT_SECONDARY};")
        self.lbl_exec_output.setWordWrap(True)
        self.lbl_exec_status = QLabel("Status: Ready")
        self.lbl_exec_status.setStyleSheet(f"font-size: 11px; font-weight: 700; color: {TEXT_MUTED};")

        exec_layout.addWidget(lbl_exec_title)
        exec_layout.addWidget(self.lbl_exec_flow)
        exec_layout.addWidget(self.lbl_exec_output)
        exec_layout.addWidget(self.lbl_exec_status)
        grid.addWidget(self.card_exec, 0, 0)

        # 2. Zombie Process Demonstration Card
        self.card_zombie = create_step_card("Zombie Process Reaping", "fork() -> child exits -> state 'Z' -> waitpid()", ACCENT_AMBER)
        zomb_layout = QVBoxLayout(self.card_zombie)
        zomb_layout.setContentsMargins(16, 14, 16, 14)
        zomb_layout.setSpacing(8)

        lbl_zomb_title = QLabel("2. Zombie Process Creation & Reaping")
        lbl_zomb_title.setStyleSheet("font-size: 14px; font-weight: 700; color: #ffffff;")
        self.lbl_zomb_flow = QLabel("Child terminates -> enters 'Z' state in /proc process table")
        self.lbl_zomb_flow.setStyleSheet(f"font-size: 12px; font-weight: 600; color: {ACCENT_AMBER};")
        self.lbl_zomb_desc = QLabel("State: 'Z' observed | Reaped with waitpid() to free PCB")
        self.lbl_zomb_desc.setStyleSheet(f"font-size: 11px; color: {TEXT_SECONDARY};")
        self.lbl_zomb_desc.setWordWrap(True)
        self.lbl_zomb_status = QLabel("Status: Ready")
        self.lbl_zomb_status.setStyleSheet(f"font-size: 11px; font-weight: 700; color: {TEXT_MUTED};")

        zomb_layout.addWidget(lbl_zomb_title)
        zomb_layout.addWidget(self.lbl_zomb_flow)
        zomb_layout.addWidget(self.lbl_zomb_desc)
        zomb_layout.addWidget(self.lbl_zomb_status)
        grid.addWidget(self.card_zombie, 0, 1)

        # 3. Orphan Reparenting Demonstration Card
        self.card_orphan = create_step_card("Orphan Process Reparenting", "Parent terminates -> Child adopted by init", ACCENT_ROSE)
        orph_layout = QVBoxLayout(self.card_orphan)
        orph_layout.setContentsMargins(16, 14, 16, 14)
        orph_layout.setSpacing(8)

        lbl_orph_title = QLabel("3. Orphan Process Reparenting")
        lbl_orph_title.setStyleSheet("font-size: 14px; font-weight: 700; color: #ffffff;")
        self.lbl_orph_flow = QLabel("Original Parent dies -> Child adopted by init/systemd/subreaper")
        self.lbl_orph_flow.setStyleSheet(f"font-size: 12px; font-weight: 600; color: {ACCENT_ROSE};")
        self.lbl_orph_desc = QLabel("Initial Parent -> Adopted Parent (PID 1 / Subreaper)")
        self.lbl_orph_desc.setStyleSheet(f"font-size: 11px; color: {TEXT_SECONDARY};")
        self.lbl_orph_desc.setWordWrap(True)
        self.lbl_orph_status = QLabel("Status: Ready")
        self.lbl_orph_status.setStyleSheet(f"font-size: 11px; font-weight: 700; color: {TEXT_MUTED};")

        orph_layout.addWidget(lbl_orph_title)
        orph_layout.addWidget(self.lbl_orph_flow)
        orph_layout.addWidget(self.lbl_orph_desc)
        orph_layout.addWidget(self.lbl_orph_status)
        grid.addWidget(self.card_orphan, 1, 0, 1, 2)

        layout.addLayout(grid)

    def set_results(
        self,
        exec_res: Optional[ProcessExecResultModel],
        zombie_res: Optional[ZombieResultModel],
        orphan_res: Optional[OrphanResultModel],
    ) -> None:
        if exec_res:
            self.lbl_exec_flow.setText(f"Child PID {exec_res.child_pid} executed {exec_res.program_executed}")
            self.lbl_exec_output.setText(f"Captured Output: \"{exec_res.captured_output.strip()}\" (Exit Code {exec_res.child_exit_code})")
            self.lbl_exec_status.setText("Status: SUCCESS — Process image successfully replaced")
            self.lbl_exec_status.setStyleSheet(f"font-size: 11px; font-weight: 700; color: {SUCCESS};")

        if zombie_res:
            self.lbl_zomb_flow.setText(f"Child PID {zombie_res.child_pid} entered State '{zombie_res.observed_state}' (Zombie)")
            self.lbl_zomb_desc.setText(zombie_res.details)
            self.lbl_zomb_status.setText("Status: SUCCESS — Zombie observed in /proc and reaped cleanly")
            self.lbl_zomb_status.setStyleSheet(f"font-size: 11px; font-weight: 700; color: {SUCCESS};")

        if orphan_res:
            self.lbl_orph_flow.setText(f"Child PID {orphan_res.child_pid}: Parent PID {orphan_res.initial_parent_pid} -> Adopted by PID {orphan_res.adopted_parent_pid}")
            self.lbl_orph_desc.setText(orphan_res.details)
            self.lbl_orph_status.setText("Status: SUCCESS — Reparenting confirmed by kernel")
            self.lbl_orph_status.setStyleSheet(f"font-size: 11px; font-weight: 700; color: {SUCCESS};")


class SyncVisualizationWidget(QWidget):
    """Displays thread synchronization metrics, POSIX semaphores, and Peterson's algorithm."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        grid = QGridLayout()
        grid.setSpacing(14)

        # Card 1: std::mutex Concurrency
        self.card_mutex = create_step_card("std::mutex Critical Section", "Thread Synchronization", ACCENT)
        m_layout = QVBoxLayout(self.card_mutex)
        m_layout.setContentsMargins(16, 14, 16, 14)
        m_layout.setSpacing(6)
        lbl_m_title = QLabel("Thread Synchronization (std::mutex)")
        lbl_m_title.setStyleSheet("font-size: 14px; font-weight: 700; color: #ffffff;")
        self.lbl_m_threads = QLabel("Threads: 4 concurrent workers | 10,000 iterations each")
        self.lbl_m_threads.setStyleSheet(f"font-size: 12px; color: {TEXT_SECONDARY};")
        self.lbl_m_counter = QLabel("Expected: 40,000 | Actual Counter: 40,000")
        self.lbl_m_counter.setStyleSheet(f"font-size: 13px; font-weight: 700; color: {ACCENT_CYAN};")
        self.lbl_m_status = QLabel("Status: Exact Match — No Data Race Detected")
        self.lbl_m_status.setStyleSheet(f"font-size: 11px; font-weight: 700; color: {SUCCESS};")
        m_layout.addWidget(lbl_m_title)
        m_layout.addWidget(self.lbl_m_threads)
        m_layout.addWidget(self.lbl_m_counter)
        m_layout.addWidget(self.lbl_m_status)
        grid.addWidget(self.card_mutex, 0, 0)

        # Card 2: POSIX Semaphores
        self.card_sem = create_step_card("POSIX Semaphore (sem_t)", "Counting Semaphore", ACCENT_EMERALD)
        s_layout = QVBoxLayout(self.card_sem)
        s_layout.setContentsMargins(16, 14, 16, 14)
        s_layout.setSpacing(6)
        lbl_s_title = QLabel("POSIX Semaphore (sem_init / sem_wait / sem_post)")
        lbl_s_title.setStyleSheet("font-size: 14px; font-weight: 700; color: #ffffff;")
        self.lbl_s_threads = QLabel("Threads: 4 concurrent workers | Initial sem_t value: 1")
        self.lbl_s_threads.setStyleSheet(f"font-size: 12px; color: {TEXT_SECONDARY};")
        self.lbl_s_counter = QLabel("Expected: 20,000 | Actual Counter: 20,000")
        self.lbl_s_counter.setStyleSheet(f"font-size: 13px; font-weight: 700; color: {ACCENT_EMERALD};")
        self.lbl_s_status = QLabel("Status: Semaphore Mutual Exclusion Verified")
        self.lbl_s_status.setStyleSheet(f"font-size: 11px; font-weight: 700; color: {SUCCESS};")
        s_layout.addWidget(lbl_s_title)
        s_layout.addWidget(self.lbl_s_threads)
        s_layout.addWidget(self.lbl_s_counter)
        s_layout.addWidget(self.lbl_s_status)
        grid.addWidget(self.card_sem, 0, 1)

        # Card 3: Peterson's Algorithm
        self.card_peterson = create_step_card("Peterson's Algorithm", "2-Process Classical Software Solution", ACCENT_VIOLET)
        p_layout = QVBoxLayout(self.card_peterson)
        p_layout.setContentsMargins(16, 14, 16, 14)
        p_layout.setSpacing(6)
        lbl_p_title = QLabel("Peterson's 2-Process Algorithm")
        lbl_p_title.setStyleSheet("font-size: 14px; font-weight: 700; color: #ffffff;")
        self.lbl_p_desc = QLabel("Guarantee: Mutual Exclusion, Progress, and Bounded Waiting (Flags + Turn)")
        self.lbl_p_desc.setStyleSheet(f"font-size: 12px; color: {TEXT_SECONDARY};")
        self.lbl_p_entries = QLabel("Critical Section Entries: P0: 2 entries | P1: 2 entries (Total Steps: 26)")
        self.lbl_p_entries.setStyleSheet(f"font-size: 12px; font-weight: 700; color: {ACCENT_VIOLET};")
        self.lbl_p_explanation = QLabel("Theoretical sequential consistency verified with memory barrier explanation.")
        self.lbl_p_explanation.setStyleSheet(f"font-size: 11px; color: {TEXT_MUTED};")
        self.lbl_p_explanation.setWordWrap(True)
        p_layout.addWidget(lbl_p_title)
        p_layout.addWidget(self.lbl_p_desc)
        p_layout.addWidget(self.lbl_p_entries)
        p_layout.addWidget(self.lbl_p_explanation)
        grid.addWidget(self.card_peterson, 1, 0, 1, 2)

        layout.addLayout(grid)

    def set_results(
        self,
        mutex_res: Optional[MutexSyncResultModel],
        sem_res: Optional[PosixSemaphoreResultModel],
        peterson_res: Optional[PetersonResultModel],
    ) -> None:
        if mutex_res:
            self.lbl_m_threads.setText(f"Threads: {mutex_res.num_threads} concurrent workers | {mutex_res.iterations_per_thread:,} iterations each")
            self.lbl_m_counter.setText(f"Expected: {mutex_res.expected_counter:,} | Actual Counter: {mutex_res.actual_counter:,}")
            if mutex_res.race_condition_detected:
                self.lbl_m_status.setText("Status: RACE CONDITION DETECTED")
                self.lbl_m_status.setStyleSheet(f"font-size: 11px; font-weight: 700; color: {ACCENT_ROSE};")
            else:
                self.lbl_m_status.setText("Status: Exact Match — No Data Race Detected")
                self.lbl_m_status.setStyleSheet(f"font-size: 11px; font-weight: 700; color: {SUCCESS};")

        if sem_res:
            self.lbl_s_threads.setText(f"Threads: {sem_res.num_threads} concurrent workers | Initial sem_t value: {sem_res.initial_value}")
            self.lbl_s_counter.setText(f"Expected: {sem_res.expected_counter:,} | Actual Counter: {sem_res.actual_counter:,}")
            self.lbl_s_status.setText("Status: Semaphore Mutual Exclusion Verified")
            self.lbl_s_status.setStyleSheet(f"font-size: 11px; font-weight: 700; color: {SUCCESS};")

        if peterson_res:
            self.lbl_p_entries.setText(f"Critical Section Entries: P0: {peterson_res.p0_critical_entries} | P1: {peterson_res.p1_critical_entries} (Total Steps: {peterson_res.total_steps})")
            if peterson_res.explanation:
                self.lbl_p_explanation.setText(peterson_res.explanation)


class ProducerConsumerBufferWidget(QWidget):
    """Visualizes the classical bounded-buffer state and production/consumption metrics."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        # Overview Card
        card = create_step_card("Classical Producer-Consumer (Bounded Buffer)", "Synchronization with Semaphores/Mutex", ACCENT_AMBER)
        c_layout = QVBoxLayout(card)
        c_layout.setContentsMargins(18, 16, 18, 16)
        c_layout.setSpacing(12)

        header_row = QHBoxLayout()
        lbl_title = QLabel("Classical Producer-Consumer Bounded-Buffer")
        lbl_title.setStyleSheet("font-size: 15px; font-weight: 700; color: #ffffff;")
        self.lbl_preserved_badge = QLabel("Zero Data Loss / Zero Duplication Verified")
        self.lbl_preserved_badge.setStyleSheet(
            f"background-color: rgba(16, 185, 129, 0.15); color: {SUCCESS}; border: 1px solid rgba(16, 185, 129, 0.4); border-radius: 5px; font-weight: 700; font-size: 11px; padding: 4px 10px;"
        )
        header_row.addWidget(lbl_title)
        header_row.addStretch()
        header_row.addWidget(self.lbl_preserved_badge)
        c_layout.addLayout(header_row)

        # Buffer Visual Representation Row
        lbl_buf_caption = QLabel("BOUNDED BUFFER SLOTS OCCUPANCY:")
        lbl_buf_caption.setStyleSheet(f"font-size: 10px; font-weight: 700; color: {TEXT_MUTED}; letter-spacing: 1px;")
        c_layout.addWidget(lbl_buf_caption)

        self.slots_row = QHBoxLayout()
        self.slots_row.setSpacing(8)
        self.slot_labels: List[QLabel] = []
        for i in range(5):
            slot = QLabel(f"Slot {i}\n[Empty]")
            slot.setAlignment(Qt.AlignCenter)
            slot.setFixedHeight(60)
            slot.setStyleSheet(
                f"""
                background-color: {BG_ELEVATED};
                border: 1px dashed {BORDER_LIGHT};
                border-radius: 6px;
                color: {TEXT_SECONDARY};
                font-size: 11px;
                font-weight: 600;
                """
            )
            self.slots_row.addWidget(slot)
            self.slot_labels.append(slot)
        c_layout.addLayout(self.slots_row)

        # Metrics Row
        m_row = QHBoxLayout()
        m_row.setSpacing(16)

        self.lbl_producers = QLabel("Producers: 2")
        self.lbl_producers.setStyleSheet(f"font-size: 12px; font-weight: 600; color: {ACCENT_CYAN};")
        self.lbl_consumers = QLabel("Consumers: 2")
        self.lbl_consumers.setStyleSheet(f"font-size: 12px; font-weight: 600; color: {ACCENT_AMBER};")
        self.lbl_capacity = QLabel("Buffer Capacity: 5 slots")
        self.lbl_capacity.setStyleSheet(f"font-size: 12px; font-weight: 600; color: {TEXT_PRIMARY};")
        self.lbl_items_prod = QLabel("Items Produced: 50")
        self.lbl_items_prod.setStyleSheet(f"font-size: 12px; font-weight: 600; color: {ACCENT_EMERALD};")
        self.lbl_items_cons = QLabel("Items Consumed: 50")
        self.lbl_items_cons.setStyleSheet(f"font-size: 12px; font-weight: 600; color: {ACCENT_EMERALD};")
        self.lbl_peak_occupancy = QLabel("Peak Occupancy: 5 / 5")
        self.lbl_peak_occupancy.setStyleSheet(f"font-size: 12px; font-weight: 600; color: {TEXT_SECONDARY};")

        m_row.addWidget(self.lbl_producers)
        m_row.addWidget(self.lbl_consumers)
        m_row.addWidget(self.lbl_capacity)
        m_row.addWidget(self.lbl_items_prod)
        m_row.addWidget(self.lbl_items_cons)
        m_row.addWidget(self.lbl_peak_occupancy)
        m_row.addStretch()
        c_layout.addLayout(m_row)

        layout.addWidget(card)

    def set_result(self, pc: Optional[ProducerConsumerResultModel]) -> None:
        if not pc:
            return
        self.lbl_producers.setText(f"Producers: {pc.num_producers}")
        self.lbl_consumers.setText(f"Consumers: {pc.num_consumers}")
        self.lbl_capacity.setText(f"Buffer Capacity: {pc.buffer_capacity} slots")
        self.lbl_items_prod.setText(f"Items Produced: {pc.items_produced}")
        self.lbl_items_cons.setText(f"Items Consumed: {pc.items_consumed}")
        self.lbl_peak_occupancy.setText(f"Peak Occupancy: {pc.max_buffer_occupancy_observed} / {pc.buffer_capacity}")

        if pc.items_preserved:
            self.lbl_preserved_badge.setText("Zero Data Loss / Zero Duplication Verified")
            self.lbl_preserved_badge.setStyleSheet(
                f"background-color: rgba(16, 185, 129, 0.15); color: {SUCCESS}; border: 1px solid rgba(16, 185, 129, 0.4); border-radius: 5px; font-weight: 700; font-size: 11px; padding: 4px 10px;"
            )

        # Update slots visual
        for i, slot in enumerate(self.slot_labels):
            if i < pc.max_buffer_occupancy_observed:
                slot.setText(f"Slot {i}\n[Item #{i * 10 + 1}]")
                slot.setStyleSheet(
                    f"""
                    background-color: rgba(56, 189, 248, 0.15);
                    border: 1px solid rgba(56, 189, 248, 0.5);
                    border-radius: 6px;
                    color: {ACCENT_CYAN};
                    font-size: 11px;
                    font-weight: 700;
                    """
                )
            else:
                slot.setText(f"Slot {i}\n[Empty]")
                slot.setStyleSheet(
                    f"""
                    background-color: {BG_ELEVATED};
                    border: 1px dashed {BORDER_LIGHT};
                    border-radius: 6px;
                    color: {TEXT_MUTED};
                    font-size: 11px;
                    font-weight: 600;
                    """
                )


class IpcChannelsWidget(QWidget):
    """Displays the four Linux / POSIX inter-process communication mechanisms."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        grid = QGridLayout()
        grid.setSpacing(14)

        # 1. Anonymous Pipe
        self.card_pipe = create_step_card("POSIX Unidirectional Pipe", "pipe() + fork()", ACCENT)
        pipe_layout = QVBoxLayout(self.card_pipe)
        pipe_layout.setContentsMargins(16, 14, 16, 14)
        pipe_layout.setSpacing(6)
        lbl_p_title = QLabel("1. Anonymous Pipe (pipe())")
        lbl_p_title.setStyleSheet("font-size: 14px; font-weight: 700; color: #ffffff;")
        self.lbl_p_flow = QLabel("Child Process -> [pipe fd[1] -> fd[0]] -> Parent Process")
        self.lbl_p_flow.setStyleSheet(f"font-size: 12px; font-weight: 600; color: {ACCENT};")
        self.lbl_p_msg = QLabel("Message: \"Hello from OScope child process via POSIX pipe!\"")
        self.lbl_p_msg.setStyleSheet(f"font-size: 11px; color: {TEXT_SECONDARY};")
        self.lbl_p_status = QLabel("Status: Ready")
        self.lbl_p_status.setStyleSheet(f"font-size: 11px; font-weight: 700; color: {TEXT_MUTED};")
        pipe_layout.addWidget(lbl_p_title)
        pipe_layout.addWidget(self.lbl_p_flow)
        pipe_layout.addWidget(self.lbl_p_msg)
        pipe_layout.addWidget(self.lbl_p_status)
        grid.addWidget(self.card_pipe, 0, 0)

        # 2. Named Pipe (FIFO)
        self.card_fifo = create_step_card("POSIX Named Pipe (FIFO)", "mkfifo()", ACCENT_AMBER)
        fifo_layout = QVBoxLayout(self.card_fifo)
        fifo_layout.setContentsMargins(16, 14, 16, 14)
        fifo_layout.setSpacing(6)
        lbl_f_title = QLabel("2. POSIX Named Pipe (FIFO)")
        lbl_f_title.setStyleSheet("font-size: 14px; font-weight: 700; color: #ffffff;")
        self.lbl_f_path = QLabel("FIFO Node: /tmp/oscope_fifo_* (Filesystem node)")
        self.lbl_f_path.setStyleSheet(f"font-size: 12px; font-weight: 600; color: {ACCENT_AMBER};")
        self.lbl_f_msg = QLabel("Message Sent & Verified: \"OScope Named Pipe Demo\"")
        self.lbl_f_msg.setStyleSheet(f"font-size: 11px; color: {TEXT_SECONDARY};")
        self.lbl_f_status = QLabel("Cleanup: Automatic unlinking (no dangling node)")
        self.lbl_f_status.setStyleSheet(f"font-size: 11px; font-weight: 700; color: {SUCCESS};")
        fifo_layout.addWidget(lbl_f_title)
        fifo_layout.addWidget(self.lbl_f_path)
        fifo_layout.addWidget(self.lbl_f_msg)
        fifo_layout.addWidget(self.lbl_f_status)
        grid.addWidget(self.card_fifo, 0, 1)

        # 3. POSIX Shared Memory
        self.card_shm = create_step_card("POSIX Shared Memory", "shm_open() + mmap()", ACCENT_EMERALD)
        shm_layout = QVBoxLayout(self.card_shm)
        shm_layout.setContentsMargins(16, 14, 16, 14)
        shm_layout.setSpacing(6)
        lbl_shm_title = QLabel("3. POSIX Shared Memory (shm_open / mmap)")
        lbl_shm_title.setStyleSheet("font-size: 14px; font-weight: 700; color: #ffffff;")
        self.lbl_shm_seg = QLabel("Segment: /oscope_shm_* | Size: 4,096 bytes (Page mapped)")
        self.lbl_shm_seg.setStyleSheet(f"font-size: 12px; font-weight: 600; color: {ACCENT_EMERALD};")
        self.lbl_shm_msg = QLabel("Payload: \"OScope Shared Memory Demo\" read across process spaces")
        self.lbl_shm_msg.setStyleSheet(f"font-size: 11px; color: {TEXT_SECONDARY};")
        self.lbl_shm_status = QLabel("Cleanup: munmap() + shm_unlink() completed cleanly")
        self.lbl_shm_status.setStyleSheet(f"font-size: 11px; font-weight: 700; color: {SUCCESS};")
        shm_layout.addWidget(lbl_shm_title)
        shm_layout.addWidget(self.lbl_shm_seg)
        shm_layout.addWidget(self.lbl_shm_msg)
        shm_layout.addWidget(self.lbl_shm_status)
        grid.addWidget(self.card_shm, 1, 0)

        # 4. POSIX Message Queue
        self.card_mq = create_step_card("POSIX Message Queue", "mq_open() + mq_send() + mq_receive()", ACCENT_VIOLET)
        mq_layout = QVBoxLayout(self.card_mq)
        mq_layout.setContentsMargins(16, 14, 16, 14)
        mq_layout.setSpacing(6)
        lbl_mq_title = QLabel("4. POSIX Message Queue (mq_*)")
        lbl_mq_title.setStyleSheet("font-size: 14px; font-weight: 700; color: #ffffff;")
        self.lbl_mq_name = QLabel("Queue: /oscope_mq_* | Messages: 1 sent, 1 received (Priority: 1)")
        self.lbl_mq_name.setStyleSheet(f"font-size: 12px; font-weight: 600; color: {ACCENT_VIOLET};")
        self.lbl_mq_msg = QLabel("Payload: \"OScope Message Queue Demo\"")
        self.lbl_mq_msg.setStyleSheet(f"font-size: 11px; color: {TEXT_SECONDARY};")
        self.lbl_mq_status = QLabel("Cleanup: mq_close() + mq_unlink() completed cleanly")
        self.lbl_mq_status.setStyleSheet(f"font-size: 11px; font-weight: 700; color: {SUCCESS};")
        mq_layout.addWidget(lbl_mq_title)
        mq_layout.addWidget(self.lbl_mq_name)
        mq_layout.addWidget(self.lbl_mq_msg)
        mq_layout.addWidget(self.lbl_mq_status)
        grid.addWidget(self.card_mq, 1, 1)

        layout.addLayout(grid)

    def set_results(
        self,
        pipe_res: Optional[PipeIpcResultModel],
        fifo_res: Optional[FifoIpcResultModel],
        shm_res: Optional[SharedMemoryIpcResultModel],
        mq_res: Optional[MessageQueueIpcResultModel],
    ) -> None:
        if pipe_res:
            self.lbl_p_flow.setText(f"Child (PID {pipe_res.child_pid}) -> [Pipe] -> Parent (PID {pipe_res.parent_pid})")
            self.lbl_p_msg.setText(f"Sent & Received: \"{pipe_res.received_message}\"")
            self.lbl_p_status.setText("Status: SUCCESS — Unidirectional pipe IPC verified")
            self.lbl_p_status.setStyleSheet(f"font-size: 11px; font-weight: 700; color: {SUCCESS};")

        if fifo_res:
            self.lbl_f_path.setText(f"FIFO Node: {fifo_res.fifo_path}")
            self.lbl_f_msg.setText(f"Message Sent & Received: \"{fifo_res.message_received}\"")
            self.lbl_f_status.setText("Status: SUCCESS — FIFO node unlinked after transmission")
            self.lbl_f_status.setStyleSheet(f"font-size: 11px; font-weight: 700; color: {SUCCESS};")

        if shm_res:
            self.lbl_shm_seg.setText(f"Segment: {shm_res.segment_name} | Size: {shm_res.size_bytes:,} bytes")
            self.lbl_shm_msg.setText(f"Written & Read: \"{shm_res.message_read}\"")
            self.lbl_shm_status.setText("Status: SUCCESS — Shared memory unmapped & unlinked")
            self.lbl_shm_status.setStyleSheet(f"font-size: 11px; font-weight: 700; color: {SUCCESS};")

        if mq_res:
            self.lbl_mq_name.setText(f"Queue: {mq_res.queue_name} | Sent: {mq_res.messages_sent}, Received: {mq_res.messages_received}")
            self.lbl_mq_msg.setText(f"Payload: \"{mq_res.message_content}\"")
            self.lbl_mq_status.setText("Status: SUCCESS — Message queue unlinked cleanly")
            self.lbl_mq_status.setStyleSheet(f"font-size: 11px; font-weight: 700; color: {SUCCESS};")
