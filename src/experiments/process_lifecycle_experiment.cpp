#include "oscope/experiments/process_lifecycle_experiment.hpp"

#include <chrono>
#include <fstream>
#include <sstream>
#include <sys/wait.h>
#include <thread>
#include <unistd.h>

namespace oscope::experiments {

namespace {

char read_proc_state(pid_t pid) {
    std::string path = "/proc/" + std::to_string(pid) + "/stat";
    std::ifstream file(path);
    if (!file.is_open()) {
        return '?';
    }
    std::string line;
    if (std::getline(file, line)) {
        size_t rparen = line.rfind(')');
        if (rparen != std::string::npos && rparen + 2 < line.size()) {
            return line[rparen + 2];
        }
    }
    return '?';
}

} // namespace

ZombieDemonstrationResult run_zombie_demonstration() {
    ZombieDemonstrationResult result;

    pid_t pid = ::fork();
    if (pid < 0) {
        result.details = "fork() failed.";
        return result;
    }

    if (pid == 0) {
        // Child terminates immediately, becoming a zombie until parent reaps it
        ::_exit(42);
    }

    result.child_pid = pid;

    // Give kernel a few milliseconds to process child exit
    std::this_thread::sleep_for(std::chrono::milliseconds(25));

    // Check child state in /proc/<pid>/stat before reaping
    result.observed_state = read_proc_state(pid);
    if (result.observed_state == 'Z') {
        result.zombie_observed = true;
    }

    // Now reap the zombie process
    int wait_status = 0;
    pid_t reaped = ::waitpid(pid, &wait_status, 0);

    if (reaped == pid && WIFEXITED(wait_status) && WEXITSTATUS(wait_status) == 42) {
        result.reaped_successfully = true;
        result.details = "Child terminated and entered 'Z' (Zombie) state in process table. "
                         "Parent subsequently reaped child with waitpid(), freeing its PCB.";
    } else {
        result.reaped_successfully = false;
        result.details = "Failed to reap child process cleanly.";
    }

    return result;
}

OrphanDemonstrationResult run_orphan_demonstration() {
    OrphanDemonstrationResult result;

    int pipe_fds[2];
    int sync_fds[2];
    if (::pipe(pipe_fds) < 0 || ::pipe(sync_fds) < 0) {
        result.details = "pipe() failed.";
        return result;
    }

    pid_t helper_pid = ::fork();
    if (helper_pid < 0) {
        ::close(pipe_fds[0]); ::close(pipe_fds[1]);
        ::close(sync_fds[0]); ::close(sync_fds[1]);
        result.details = "fork() failed.";
        return result;
    }

    if (helper_pid == 0) {
        ::close(pipe_fds[0]);
        ::close(sync_fds[1]);

        pid_t helper_self_pid = ::getpid();

        pid_t orphan_pid = ::fork();
        if (orphan_pid < 0) {
            ::_exit(1);
        }

        if (orphan_pid == 0) {
            // Grandchild (orphan)
            pid_t original_ppid = helper_self_pid;

            // Wait for signal from main parent confirming helper is reaped
            char dummy = 0;
            ssize_t sread = ::read(sync_fds[0], &dummy, 1);
            (void)sread;
            ::close(sync_fds[0]);

            // Now intermediate parent is reaped and reparenting has occurred
            pid_t adopted_ppid = ::getppid();
            pid_t pids[3] = {::getpid(), original_ppid, adopted_ppid};
            ssize_t written = ::write(pipe_fds[1], pids, sizeof(pids));
            (void)written;
            ::close(pipe_fds[1]);
            ::_exit(0);
        }

        ::close(sync_fds[0]);
        // Intermediate parent exits immediately to orphan grandchild
        ::_exit(0);
    }

    ::close(pipe_fds[1]);
    ::close(sync_fds[0]);

    // Reap the intermediate helper process
    int helper_status = 0;
    ::waitpid(helper_pid, &helper_status, 0);

    // Notify orphan that helper has been reaped
    char token = 'K';
    ssize_t swr = ::write(sync_fds[1], &token, 1);
    (void)swr;
    ::close(sync_fds[1]);

    // Read orphan process transition info
    pid_t pids[3] = {0, 0, 0};
    ssize_t bytes_read = ::read(pipe_fds[0], pids, sizeof(pids));
    ::close(pipe_fds[0]);

    if (bytes_read == sizeof(pids)) {
        result.child_pid = pids[0];
        result.initial_parent_pid = pids[1];
        result.adopted_parent_pid = pids[2];
        result.reparented_to_init_or_subreaper = (result.adopted_parent_pid != result.initial_parent_pid);
        result.details = "Child was reparented from original parent (PID " +
                         std::to_string(result.initial_parent_pid) + ") to init/subreaper (PID " +
                         std::to_string(result.adopted_parent_pid) + ") upon parent termination.";
    } else {
        result.details = "Failed to communicate with orphan process.";
    }

    return result;
}

} // namespace oscope::experiments
