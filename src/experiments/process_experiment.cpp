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

ProcessExecResult run_process_exec_experiment(
    const std::string& executable_path,
    const std::string& argument) {

    ProcessExecResult result;
    result.parent_pid = ::getpid();
    result.executable_path = executable_path;
    result.argument = argument;

    int pipe_fds[2] = {-1, -1};
    if (::pipe(pipe_fds) < 0) {
        result.message = "pipe() failed: " + std::string(std::strerror(errno));
        return result;
    }

    pid_t pid = ::fork();
    if (pid < 0) {
        ::close(pipe_fds[0]);
        ::close(pipe_fds[1]);
        result.message = "fork() failed: " + std::string(std::strerror(errno));
        return result;
    }

    if (pid == 0) {
        // Child:
        ::close(pipe_fds[0]); // Close read end
        // Redirect stdout to pipe write end
        if (::dup2(pipe_fds[1], STDOUT_FILENO) < 0) {
            ::close(pipe_fds[1]);
            ::_exit(125);
        }
        ::close(pipe_fds[1]);

        char* const argv[] = {
            const_cast<char*>(executable_path.c_str()),
            const_cast<char*>(argument.c_str()),
            nullptr
        };

        ::execv(executable_path.c_str(), argv);

        // Fallback to execvp in case executable is found in PATH
        ::execvp(executable_path.c_str(), argv);

        ::_exit(127);
    }

    // Parent:
    result.child_pid = pid;
    ::close(pipe_fds[1]); // Close write end

    std::string output;
    char buf[256];
    ssize_t bytes = 0;
    while ((bytes = ::read(pipe_fds[0], buf, sizeof(buf) - 1)) > 0) {
        buf[bytes] = '\0';
        output += buf;
    }
    ::close(pipe_fds[0]);

    result.parent_pid = ::getpid();
    result.executable_path = executable_path;
    result.program_executed = executable_path;
    result.argument = argument;
    result.captured_output = output;

    int wait_status = 0;
    pid_t wait_res;
    do {
        wait_res = ::waitpid(pid, &wait_status, 0);
    } while (wait_res < 0 && errno == EINTR);

    if (wait_res < 0) {
        result.message = "waitpid() failed: " + std::string(std::strerror(errno));
        result.error_message = result.message;
        return result;
    }

    if (WIFEXITED(wait_status)) {
        result.exited_normally = true;
        result.exit_code = WEXITSTATUS(wait_status);
        result.child_exit_code = result.exit_code;
        if (result.exit_code == 0 && output.find(argument) != std::string::npos) {
            result.success = true;
            result.image_replaced = true;
            result.message = "Process image successfully replaced via execv() and executed to completion.";
            result.details = "Child (PID " + std::to_string(pid) + ") executed '" + executable_path +
                             "', emitted verified payload through redirected stdout, and exited with status 0.";
        } else {
            result.success = false;
            result.image_replaced = false;
            result.error_message = "Process executed with exit code " + std::to_string(result.exit_code) +
                             " (exec failure or unexpected output).";
            result.message = result.error_message;
        }
    } else {
        result.exited_normally = false;
        result.image_replaced = false;
        result.error_message = "Process terminated abnormally by signal.";
        result.message = result.error_message;
    }

    return result;
}

} // namespace oscope::experiments
