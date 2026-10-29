#ifndef OSCOPE_EXPERIMENTS_IPC_EXPERIMENTS_HPP
#define OSCOPE_EXPERIMENTS_IPC_EXPERIMENTS_HPP

#include <string>

namespace oscope::experiments {

struct FifoExperimentResult {
    std::string fifo_path;
    std::string message_sent;
    std::string message_received;
    bool success{false};
    std::string error_message;
    std::string details;
};

struct SharedMemoryExperimentResult {
    std::string segment_name;
    size_t size_bytes{4096};
    std::string message_written;
    std::string message_read;
    bool success{false};
    std::string error_message;
    std::string details;
};

struct MessageQueueExperimentResult {
    std::string queue_name;
    std::string message_sent;
    std::string message_received;
    std::string message_content;
    int messages_sent{0};
    int messages_received{0};
    long max_messages{10};
    long max_message_size{256};
    unsigned int priority_sent{0};
    unsigned int priority_received{0};
    bool success{false};
    std::string error_message;
    std::string details;
};

/**
 * @brief Demonstrates inter-process communication using a POSIX named pipe (FIFO).
 */
FifoExperimentResult run_fifo_experiment(const std::string& message = "Hello from POSIX Named Pipe (FIFO)!");

/**
 * @brief Demonstrates inter-process communication using POSIX shared memory (shm_open/mmap).
 */
SharedMemoryExperimentResult run_shared_memory_experiment(const std::string& message = "OScope Shared Memory Segment Data");

/**
 * @brief Demonstrates inter-process communication using POSIX message queues (mq_open/mq_send/mq_receive) (FR-IPC-003).
 */
MessageQueueExperimentResult run_message_queue_experiment(
    const std::string& message = "OScope POSIX Message Queue Payload",
    unsigned int priority = 1);

} // namespace oscope::experiments

#endif // OSCOPE_EXPERIMENTS_IPC_EXPERIMENTS_HPP
