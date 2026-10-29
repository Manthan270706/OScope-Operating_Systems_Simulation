#ifndef OSCOPE_EXPERIMENTS_PROCESS_EXPERIMENT_HPP
#define OSCOPE_EXPERIMENTS_PROCESS_EXPERIMENT_HPP

#include <sys/types.h>
#include <string>

namespace oscope::experiments {

/// Documented exit code used by the child process upon normal termination.
inline constexpr int kExpectedChildExitCode = 42;

enum class ProcessExperimentStatus {
    Success,
    ForkFailed,
    WaitFailed,
    AbnormalTermination,
    UnexpectedExitCode
};

struct ProcessExperimentResult {
    ProcessExperimentStatus status{ProcessExperimentStatus::ForkFailed};
    pid_t parent_pid{-1};
    pid_t child_pid{-1};
    bool exited_normally{false};
    int exit_code{-1};
    int termination_signal{-1};
    std::string message;

    bool is_success() const noexcept {
        return status == ProcessExperimentStatus::Success;
    }
};

/**
 * @brief Runs a POSIX process creation and lifecycle experiment using fork() and waitpid().
 *
 * Exactly one child process is created via fork(). The parent records both PIDs and
 * reaps the child using waitpid(), handling EINTR gracefully. The child terminates
 * immediately with kExpectedChildExitCode using _exit() so it never returns into the caller.
 *
 * @return ProcessExperimentResult detailing PIDs, exit code, and execution status.
 */
ProcessExperimentResult run_process_experiment();

struct ProcessExecResult {
    bool success{false};
    pid_t parent_pid{-1};
    pid_t child_pid{-1};
    std::string program_executed;
    std::string executable_path;
    std::string argument;
    std::string captured_output;
    int exit_code{-1};
    int child_exit_code{-1};
    bool exited_normally{false};
    bool image_replaced{false};
    std::string error_message;
    std::string message;
    std::string details;
};

/**
 * @brief Demonstrates fork(), exec*(), and waitpid() process image replacement (FR-PROC-004).
 *
 * Exactly one child process is created via fork(). The child replaces its process image
 * using an exec*() system call to execute a designated program (defaults to /bin/echo).
 * The parent captures the program's output via a pipe and uses waitpid() to retrieve
 * and validate the child's termination status.
 */
ProcessExecResult run_process_exec_experiment(
    const std::string& executable_path = "/bin/echo",
    const std::string& argument = "OScope Exec Process Replacement Verified");

} // namespace oscope::experiments

#endif // OSCOPE_EXPERIMENTS_PROCESS_EXPERIMENT_HPP
