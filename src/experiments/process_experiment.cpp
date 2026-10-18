#include "oscope/experiments/process_experiment.hpp"

#include <cerrno>
#include <cstring>
#include <sys/types.h>
#include <sys/wait.h>
#include <unistd.h>

namespace oscope::experiments {

ProcessExperimentResult run_process_experiment() {
    ProcessExperimentResult result;
    result.parent_pid = ::getpid();

    pid_t pid = ::fork();
    if (pid < 0) {
        result.status = ProcessExperimentStatus::ForkFailed;
        result.message = std::string("fork() failed: ") + std::strerror(errno);
        return result;
    }

    if (pid == 0) {
        // Child process:
        // Must NOT return into normal application flow. Terminate immediately with documented exit code.
        ::_exit(kExpectedChildExitCode);
    }

    // Parent process:
    result.child_pid = pid;

    int wait_status = 0;
    pid_t wait_res;
    do {
        wait_res = ::waitpid(pid, &wait_status, 0);
    } while (wait_res < 0 && errno == EINTR);

    if (wait_res < 0) {
        result.status = ProcessExperimentStatus::WaitFailed;
        result.message = std::string("waitpid() failed: ") + std::strerror(errno);
        return result;
    }

    if (WIFEXITED(wait_status)) {
        result.exited_normally = true;
        result.exit_code = WEXITSTATUS(wait_status);
        if (result.exit_code == kExpectedChildExitCode) {
            result.status = ProcessExperimentStatus::Success;
            result.message = "Child process exited normally with expected exit code " +
                             std::to_string(kExpectedChildExitCode) + ".";
        } else {
            result.status = ProcessExperimentStatus::UnexpectedExitCode;
            result.message = "Child process exited with unexpected exit code " +
                             std::to_string(result.exit_code) + " (expected " +
                             std::to_string(kExpectedChildExitCode) + ").";
        }
    } else if (WIFSIGNALED(wait_status)) {
        result.exited_normally = false;
        result.termination_signal = WTERMSIG(wait_status);
        result.status = ProcessExperimentStatus::AbnormalTermination;
        result.message = "Child process terminated abnormally by signal " +
                         std::to_string(result.termination_signal) + ".";
    } else {
        result.exited_normally = false;
        result.status = ProcessExperimentStatus::AbnormalTermination;
        result.message = "Child process terminated with unknown status.";
    }

    return result;
}

} // namespace oscope::experiments
