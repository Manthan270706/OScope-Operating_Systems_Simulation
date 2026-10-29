#include "oscope/experiments/pipe_ipc_experiment.hpp"

#include <cerrno>
#include <cstring>
#include <sys/types.h>
#include <sys/wait.h>
#include <unistd.h>

namespace oscope::experiments {

namespace {

class ScopedFd {
public:
    explicit ScopedFd(int fd = -1) noexcept : fd_(fd) {}
    ~ScopedFd() noexcept { reset(); }

    ScopedFd(const ScopedFd&) = delete;
    ScopedFd& operator=(const ScopedFd&) = delete;

    ScopedFd(ScopedFd&& other) noexcept : fd_(other.fd_) {
        other.fd_ = -1;
    }

    ScopedFd& operator=(ScopedFd&& other) noexcept {
        if (this != &other) {
            reset();
            fd_ = other.fd_;
            other.fd_ = -1;
        }
        return *this;
    }

    int get() const noexcept { return fd_; }

    void reset(int new_fd = -1) noexcept {
        if (fd_ >= 0) {
            ::close(fd_);
        }
        fd_ = new_fd;
    }

private:
    int fd_{-1};
};

// Write all bytes to fd, retrying on EINTR and handling partial writes
bool write_all(int fd, const char* data, std::size_t length) {
    std::size_t written = 0;
    while (written < length) {
        ssize_t res = ::write(fd, data + written, length - written);
        if (res < 0) {
            if (errno == EINTR) {
                continue;
            }
            return false;
        }
        if (res == 0) {
            return false;
        }
        written += static_cast<std::size_t>(res);
    }
    return true;
}

// Read from fd until EOF, retrying on EINTR
bool read_all(int fd, std::string& buffer) {
    char chunk[512];
    buffer.clear();
    while (true) {
        ssize_t bytes_read = ::read(fd, chunk, sizeof(chunk));
        if (bytes_read < 0) {
            if (errno == EINTR) {
                continue;
            }
            return false;
        }
        if (bytes_read == 0) {
            // EOF cleanly reached
            break;
        }
        buffer.append(chunk, static_cast<std::size_t>(bytes_read));
    }
    return true;
}

} // namespace

PipeIpcExperimentResult run_pipe_ipc_experiment(std::string_view message) {
    PipeIpcExperimentResult result;
    result.parent_pid = ::getpid();
    result.sent_message = std::string(message);

    int pipefds[2] = {-1, -1};
    if (::pipe(pipefds) < 0) {
        result.status = PipeIpcStatus::PipeCreationFailed;
        result.error_message = std::string("pipe() failed: ") + std::strerror(errno);
        return result;
    }

    ScopedFd read_end(pipefds[0]);
    ScopedFd write_end(pipefds[1]);

    pid_t pid = ::fork();
    if (pid < 0) {
        result.status = PipeIpcStatus::ForkFailed;
        result.error_message = std::string("fork() failed: ") + std::strerror(errno);
        return result;
    }

    if (pid == 0) {
        // Child process:
        // Close unused read end immediately
        read_end.reset();

        // Write message to pipe
        bool ok = write_all(write_end.get(), message.data(), message.size());
        write_end.reset();

        if (ok) {
            ::_exit(kPipeChildSuccessExitCode);
        } else {
            ::_exit(kPipeChildWriteErrorExitCode);
        }
    }

    // Parent process:
    result.child_pid = pid;

    // Close unused write end immediately so read_all will encounter EOF when child closes write end
    write_end.reset();

    // Read message from pipe
    std::string received;
    int read_errno = 0;
    bool read_ok = read_all(read_end.get(), received);
    if (!read_ok) {
        read_errno = errno;
    }
    read_end.reset();
    result.received_message = received;

    // Reap child process with waitpid and EINTR handling
    int wait_status = 0;
    pid_t wait_res;
    do {
        wait_res = ::waitpid(pid, &wait_status, 0);
    } while (wait_res < 0 && errno == EINTR);

    if (wait_res < 0) {
        result.status = PipeIpcStatus::WaitFailed;
        result.error_message = std::string("waitpid() failed: ") + std::strerror(errno);
        return result;
    }

    if (WIFEXITED(wait_status)) {
        result.child_exited_normally = true;
        result.child_exit_code = WEXITSTATUS(wait_status);
    } else if (WIFSIGNALED(wait_status)) {
        result.child_exited_normally = false;
        result.child_termination_signal = WTERMSIG(wait_status);
        result.status = PipeIpcStatus::ChildTerminatedAbnormally;
        result.error_message = "Child process terminated abnormally by signal " +
                               std::to_string(result.child_termination_signal) + ".";
        return result;
    } else {
        result.child_exited_normally = false;
        result.status = PipeIpcStatus::ChildTerminatedAbnormally;
        result.error_message = "Child process terminated with unhandled wait status.";
        return result;
    }

    if (!read_ok) {
        result.status = PipeIpcStatus::ReadFailed;
        result.error_message = std::string("read() from pipe failed: ") + std::strerror(read_errno);
        return result;
    }

    if (result.child_exit_code != kPipeChildSuccessExitCode) {
        result.status = PipeIpcStatus::ChildReportedError;
        result.error_message = "Child process exited with error code " +
                               std::to_string(result.child_exit_code) + ".";
        return result;
    }

    if (result.received_message != result.sent_message) {
        result.status = PipeIpcStatus::MessageMismatch;
        result.error_message = "Received message does not match sent message.";
        return result;
    }

    result.status = PipeIpcStatus::Success;
    return result;
}

} // namespace oscope::experiments
