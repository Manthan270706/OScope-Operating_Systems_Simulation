#ifndef OSCOPE_PROCESS_STATE_HPP
#define OSCOPE_PROCESS_STATE_HPP

#include <optional>
#include <string>

namespace oscope {

/**
 * @brief Represents the lifecycle states of a process.
 */
enum class ProcessState {
    New,
    Ready,
    Running,
    Waiting,
    Terminated
};

inline std::string to_string(ProcessState state) {
    switch (state) {
        case ProcessState::New: return "New";
        case ProcessState::Ready: return "Ready";
        case ProcessState::Running: return "Running";
        case ProcessState::Waiting: return "Waiting";
        case ProcessState::Terminated: return "Terminated";
    }
    return "Unknown";
}

inline std::optional<ProcessState> process_state_from_string(const std::string& str) {
    if (str == "New" || str == "new") return ProcessState::New;
    if (str == "Ready" || str == "ready") return ProcessState::Ready;
    if (str == "Running" || str == "running") return ProcessState::Running;
    if (str == "Waiting" || str == "waiting" || str == "Blocked" || str == "blocked") return ProcessState::Waiting;
    if (str == "Terminated" || str == "terminated" || str == "Exit" || str == "exit") return ProcessState::Terminated;
    return std::nullopt;
}

} // namespace oscope

#endif // OSCOPE_PROCESS_STATE_HPP
