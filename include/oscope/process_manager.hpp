#ifndef OSCOPE_PROCESS_MANAGER_HPP
#define OSCOPE_PROCESS_MANAGER_HPP

#include <cstddef>
#include <optional>
#include <unordered_map>

#include "oscope/process.hpp"
#include "oscope/process_state.hpp"

namespace oscope {

/**
 * @brief Manages process lifecycle states and transitions.
 */
class ProcessManager {
public:
    ProcessManager() = default;

    /**
     * @brief Registers an existing process with initial state New.
     *
     * Rejects duplicate PIDs, nonpositive PIDs (<= 0), negative arrival
     * times (< 0), and nonpositive burst times (<= 0).
     *
     * @param process The process to register.
     * @return true if successfully registered, false otherwise.
     */
    bool register_process(const Process& process);

    /**
     * @brief Transitions a registered process to a target lifecycle state.
     *
     * Permitted transitions:
     * - New -> Ready
     * - Ready -> Running
     * - Running -> Ready
     * - Running -> Waiting
     * - Running -> Terminated
     * - Waiting -> Ready
     *
     * Rejects unknown PIDs and illegal transitions without modifying stored state.
     *
     * @param pid Process ID.
     * @param target_state The target lifecycle state.
     * @return true if transition succeeded, false otherwise.
     */
    bool transition_to(int pid, ProcessState target_state);

    /**
     * @brief Alias for transition_to.
     */
    bool transition_state(int pid, ProcessState target_state) {
        return transition_to(pid, target_state);
    }

    /**
     * @brief Queries the current state of a registered process.
     *
     * @param pid Process ID.
     * @return std::optional<ProcessState> if registered, std::nullopt otherwise.
     */
    std::optional<ProcessState> get_state(int pid) const;

    /**
     * @brief Alias for get_state.
     */
    std::optional<ProcessState> process_state(int pid) const {
        return get_state(pid);
    }

    /**
     * @brief Queries process metadata if registered.
     */
    std::optional<Process> get_process(int pid) const;

    /**
     * @brief Checks if a process with the given PID is registered.
     */
    bool has_process(int pid) const noexcept;

    /**
     * @brief Returns the number of registered processes (including terminated).
     */
    std::size_t process_count() const noexcept;

    /**
     * @brief Returns the number of registered processes.
     */
    std::size_t size() const noexcept {
        return process_count();
    }

    /**
     * @brief Checks if the manager contains no registered processes.
     */
    bool empty() const noexcept;

    /**
     * @brief Clears all registered processes.
     */
    void clear() noexcept;

private:
    struct ProcessEntry {
        Process process;
        ProcessState state{ProcessState::New};
    };

    static bool is_valid_process(const Process& process) noexcept;
    static bool is_valid_transition(ProcessState current, ProcessState target) noexcept;

    std::unordered_map<int, ProcessEntry> processes_;
};

} // namespace oscope

#endif // OSCOPE_PROCESS_MANAGER_HPP
