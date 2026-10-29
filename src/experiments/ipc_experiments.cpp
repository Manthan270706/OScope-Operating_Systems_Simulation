#include "oscope/experiments/ipc_experiments.hpp"

#include <cerrno>
#include <chrono>
#include <cstring>
#include <fcntl.h>
#include <mqueue.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <unistd.h>
#include <vector>

namespace oscope::experiments {

FifoExperimentResult run_fifo_experiment(const std::string& message) {
    FifoExperimentResult result;
    result.message_sent = message;
    result.fifo_path = "/tmp/oscope_fifo_" + std::to_string(::getpid());

    // Ensure stale FIFO is removed if it existed
    ::unlink(result.fifo_path.c_str());

    if (::mkfifo(result.fifo_path.c_str(), 0600) < 0) {
        result.success = false;
        result.error_message = "mkfifo() failed: " + std::string(std::strerror(errno));
        return result;
    }

    pid_t pid = ::fork();
    if (pid < 0) {
        result.success = false;
        result.error_message = "fork() failed: " + std::string(std::strerror(errno));
        ::unlink(result.fifo_path.c_str());
        return result;
    }

    if (pid == 0) {
        // Child: write message to FIFO
        int fd = ::open(result.fifo_path.c_str(), O_WRONLY);
        if (fd >= 0) {
            ssize_t written = ::write(fd, message.data(), message.size());
            (void)written;
            ::close(fd);
            ::_exit(0);
        }
        ::_exit(1);
    }

    // Parent: read message from FIFO
    int fd = ::open(result.fifo_path.c_str(), O_RDONLY);
    if (fd < 0) {
        result.success = false;
        result.error_message = "open(FIFO) failed: " + std::string(std::strerror(errno));
    } else {
        char buf[512] = {0};
        ssize_t bytes_read = ::read(fd, buf, sizeof(buf) - 1);
        if (bytes_read >= 0) {
            result.message_received = std::string(buf, static_cast<size_t>(bytes_read));
            result.success = (result.message_received == result.message_sent);
            result.details = "Data transferred successfully through POSIX FIFO filesystem node.";
        } else {
            result.success = false;
            result.error_message = "read(FIFO) failed: " + std::string(std::strerror(errno));
        }
        ::close(fd);
    }

    int status = 0;
    ::waitpid(pid, &status, 0);

    // Guaranteed RAII/explicit cleanup of the FIFO filesystem entry
    ::unlink(result.fifo_path.c_str());
    return result;
}

SharedMemoryExperimentResult run_shared_memory_experiment(const std::string& message) {
    SharedMemoryExperimentResult result;
    result.message_written = message;
    result.segment_name = "/oscope_shm_" + std::to_string(::getpid());
    result.size_bytes = 4096;

    // Remove any stale segment
    ::shm_unlink(result.segment_name.c_str());

    int fd = ::shm_open(result.segment_name.c_str(), O_CREAT | O_RDWR, 0600);
    if (fd < 0) {
        result.success = false;
        result.error_message = "shm_open() failed: " + std::string(std::strerror(errno));
        return result;
    }

    if (::ftruncate(fd, static_cast<off_t>(result.size_bytes)) < 0) {
        result.success = false;
        result.error_message = "ftruncate() failed: " + std::string(std::strerror(errno));
        ::close(fd);
        ::shm_unlink(result.segment_name.c_str());
        return result;
    }

    void* addr = ::mmap(nullptr, result.size_bytes, PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);
    if (addr == MAP_FAILED) {
        result.success = false;
        result.error_message = "mmap() failed: " + std::string(std::strerror(errno));
        ::close(fd);
        ::shm_unlink(result.segment_name.c_str());
        return result;
    }

    // Write message into shared memory
    std::memcpy(addr, message.c_str(), std::min(message.size() + 1, result.size_bytes));

    pid_t pid = ::fork();
    if (pid < 0) {
        result.success = false;
        result.error_message = "fork() failed: " + std::string(std::strerror(errno));
        ::munmap(addr, result.size_bytes);
        ::close(fd);
        ::shm_unlink(result.segment_name.c_str());
        return result;
    }

    if (pid == 0) {
        // Child: read data from mapped shared memory segment
        const char* mem_str = static_cast<const char*>(addr);
        if (mem_str && std::strcmp(mem_str, message.c_str()) == 0) {
            ::_exit(0);
        }
        ::_exit(1);
    }

    int wait_status = 0;
    ::waitpid(pid, &wait_status, 0);

    result.message_read = static_cast<const char*>(addr);
    if (WIFEXITED(wait_status) && WEXITSTATUS(wait_status) == 0 && result.message_read == result.message_written) {
        result.success = true;
        result.details = "Data verified in shared memory page mapped across parent and child process addresses.";
    } else {
        result.success = false;
        result.error_message = "Child process verification of shared memory data failed.";
    }

    // Explicit cleanup
    ::munmap(addr, result.size_bytes);
    ::close(fd);
    ::shm_unlink(result.segment_name.c_str());

    return result;
}

MessageQueueExperimentResult run_message_queue_experiment(
    const std::string& message,
    unsigned int priority) {

    MessageQueueExperimentResult result;
    result.message_sent = message;
    result.priority_sent = priority;
    result.max_messages = 5;
    result.max_message_size = 256;

    auto now = std::chrono::steady_clock::now().time_since_epoch().count();
    result.queue_name = "/oscope_mq_" + std::to_string(::getpid()) + "_" + std::to_string(now % 1000000);

    // Ensure any prior queue with the same name is cleanly unlinked
    ::mq_unlink(result.queue_name.c_str());

    struct mq_attr attr;
    std::memset(&attr, 0, sizeof(attr));
    attr.mq_flags = 0;
    attr.mq_maxmsg = result.max_messages;
    attr.mq_msgsize = result.max_message_size;

    mqd_t mq = ::mq_open(result.queue_name.c_str(), O_CREAT | O_RDWR, 0600, &attr);
    if (mq == static_cast<mqd_t>(-1)) {
        result.success = false;
        result.error_message = "mq_open() failed: " + std::string(std::strerror(errno));
        return result;
    }

    struct MqCleaner {
        std::string name;
        mqd_t desc;
        ~MqCleaner() {
            if (desc != static_cast<mqd_t>(-1)) {
                ::mq_close(desc);
            }
            ::mq_unlink(name.c_str());
        }
    } cleaner{result.queue_name, mq};

    pid_t pid = ::fork();
    if (pid < 0) {
        result.success = false;
        result.error_message = "fork() failed: " + std::string(std::strerror(errno));
        return result;
    }

    if (pid == 0) {
        // Child: open queue and send payload with priority
        mqd_t child_mq = ::mq_open(result.queue_name.c_str(), O_WRONLY);
        if (child_mq == static_cast<mqd_t>(-1)) {
            ::_exit(1);
        }

        int send_res = -1;
        while (true) {
            send_res = ::mq_send(child_mq, message.c_str(), message.size() + 1, priority);
            if (send_res == -1 && errno == EINTR) {
                continue;
            }
            break;
        }

        ::mq_close(child_mq);
        ::_exit(send_res == 0 ? 0 : 2);
    }

    // Parent: read message with bounded 5-second timeout to avoid hangs
    struct timespec ts;
    ::clock_gettime(CLOCK_REALTIME, &ts);
    ts.tv_sec += 5;

    std::vector<char> buffer(result.max_message_size, '\0');
    unsigned int recv_prio = 0;
    ssize_t bytes_recv = -1;

    while (true) {
        bytes_recv = ::mq_timedreceive(mq, buffer.data(), buffer.size(), &recv_prio, &ts);
        if (bytes_recv == -1 && errno == EINTR) {
            continue;
        }
        break;
    }

    int wait_status = 0;
    pid_t wait_res;
    do {
        wait_res = ::waitpid(pid, &wait_status, 0);
    } while (wait_res < 0 && errno == EINTR);

    if (bytes_recv > 0) {
        result.message_received = std::string(buffer.data());
        result.message_content = result.message_received;
        result.priority_received = recv_prio;
        result.messages_received = 1;
    }
    result.messages_sent = 1;

    if (bytes_recv > 0 &&
        WIFEXITED(wait_status) &&
        WEXITSTATUS(wait_status) == 0 &&
        result.message_received == result.message_sent &&
        result.priority_received == result.priority_sent) {
        result.success = true;
        result.details = "POSIX message queue safely delivered priority " +
                         std::to_string(result.priority_received) +
                         " message across processes and unlinked queue.";
    } else {
        result.success = false;
        if (result.error_message.empty()) {
            result.error_message = "Message queue communication or verification failed: " +
                                  std::string(std::strerror(errno));
        }
    }

    return result;
}

} // namespace oscope::experiments
