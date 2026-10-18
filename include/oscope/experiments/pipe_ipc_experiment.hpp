#ifndef OSCOPE_EXPERIMENTS_PIPE_IPC_EXPERIMENT_HPP
#define OSCOPE_EXPERIMENTS_PIPE_IPC_EXPERIMENT_HPP

#include <sys/types.h>
#include <string>
#include <string_view>

namespace oscope::experiments {

/// Documented default message sent from child to parent process via pipe.
inline constexpr std::string_view kDefaultPipeMessage =
    "Hello from OScope child process via POSIX pipe!";

inline constexpr int kPipeChildSuccessExitCode = 0;
inline constexpr int kPipeChildWriteErrorExitCode = 101;

enum class PipeIpcStatus {
    Success,
    PipeCreationFailed,
    ForkFailed,
    WriteFailed,
    ReadFailed,
    WaitFailed,
    MessageMismatch,
    ChildTerminatedAbnormally,
    ChildReportedError
};

struct PipeIpcExperimentResult {
    PipeIpcStatus status{PipeIpcStatus::PipeCreationFailed};
    pid_t parent_pid{-1};
    pid_t child_pid{-1};
    bool child_exited_normally{false};
    int child_exit_code{-1};
    int child_termination_signal{-1};
    std::string sent_message;
    std::string received_message;
    std::string error_message;

    bool is_success() const noexcept {
        return status == PipeIpcStatus::Success;
    }
};

/**
 * @brief Runs an inter-process communication experiment using a unidirectional POSIX pipe.
 *
 * Direction: Child process writes message to pipe, Parent process reads message from pipe.
 * The child writes the entire message (handling partial writes and EINTR) and exits with
 * kPipeChildSuccessExitCode. The parent closes the write end, reads the message to EOF
 * (handling partial reads and EINTR), and reaps the child using waitpid().
 *
 * @param message Message string to transmit through the pipe.
 * @return PipeIpcExperimentResult containing transmission details, PIDs, and exit status.
 */
PipeIpcExperimentResult run_pipe_ipc_experiment(std::string_view message = kDefaultPipeMessage);

} // namespace oscope::experiments

#endif // OSCOPE_EXPERIMENTS_PIPE_IPC_EXPERIMENT_HPP
