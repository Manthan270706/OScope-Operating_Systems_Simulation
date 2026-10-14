#include "oscope/process_manager.hpp"

namespace oscope {

bool ProcessManager::is_valid_process(const Process& process) noexcept {
    return process.pid > 0 && process.arrival_time >= 0 && process.burst_time > 0;
}

bool ProcessManager::is_valid_transition(ProcessState current, ProcessState target) noexcept {
    switch (current) {
        case ProcessState::New:
            return target == ProcessState::Ready;
        case ProcessState::Ready:
            return target == ProcessState::Running;
        case ProcessState::Running:
            return target == ProcessState::Ready ||
                   target == ProcessState::Waiting ||
                   target == ProcessState::Terminated;
        case ProcessState::Waiting:
            return target == ProcessState::Ready;
        case ProcessState::Terminated:
            return false;
    }
    return false;
}

bool ProcessManager::register_process(const Process& process) {
    if (!is_valid_process(process)) {
        return false;
    }

    if (processes_.find(process.pid) != processes_.end()) {
        return false;
    }

    processes_[process.pid] = ProcessEntry{process, ProcessState::New};
    return true;
}

bool ProcessManager::transition_to(int pid, ProcessState target_state) {
    auto it = processes_.find(pid);
    if (it == processes_.end()) {
        return false;
    }

    if (!is_valid_transition(it->second.state, target_state)) {
        return false;
    }

    it->second.state = target_state;
    return true;
}

std::optional<ProcessState> ProcessManager::get_state(int pid) const {
    auto it = processes_.find(pid);
    if (it == processes_.end()) {
        return std::nullopt;
    }
    return it->second.state;
}

std::optional<Process> ProcessManager::get_process(int pid) const {
    auto it = processes_.find(pid);
    if (it == processes_.end()) {
        return std::nullopt;
    }
    return it->second.process;
}

bool ProcessManager::has_process(int pid) const noexcept {
    return processes_.find(pid) != processes_.end();
}

std::size_t ProcessManager::process_count() const noexcept {
    return processes_.size();
}

bool ProcessManager::empty() const noexcept {
    return processes_.empty();
}

void ProcessManager::clear() noexcept {
    processes_.clear();
}

} // namespace oscope
