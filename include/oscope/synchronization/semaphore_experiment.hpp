#ifndef OSCOPE_SYNCHRONIZATION_SEMAPHORE_EXPERIMENT_HPP
#define OSCOPE_SYNCHRONIZATION_SEMAPHORE_EXPERIMENT_HPP

#include <cstddef>
#include <cstdint>
#include <string>
#include <vector>

namespace oscope::synchronization {

inline constexpr std::size_t kDefaultSemThreadCount = 4;
inline constexpr std::size_t kDefaultSemIterationsPerThread = 10000;

struct SemaphoreExperimentResult {
    bool success{false};
    std::size_t num_threads{0};
    std::size_t iterations_per_thread{0};
    std::size_t threads_completed{0};
    std::uint64_t expected_counter{0};
    std::uint64_t actual_counter{0};
    unsigned int initial_value{1};
    std::string error_message;
    std::string details;
};

struct ProducerConsumerStep {
    std::size_t step_id{0};
    std::string role; // "Producer" or "Consumer"
    std::size_t worker_id{0};
    int item{0};
    std::size_t buffer_occupancy{0};
};

struct ProducerConsumerResult {
    bool success{false};
    std::size_t buffer_capacity{0};
    std::size_t total_items{0};
    std::size_t items_produced{0};
    std::size_t items_consumed{0};
    std::size_t total_items_produced{0};
    std::size_t total_items_consumed{0};
    std::size_t num_producers{0};
    std::size_t num_consumers{0};
    std::size_t max_buffer_occupancy_observed{0};
    bool items_preserved{false};
    std::string error_message;
    std::string details;
    std::vector<ProducerConsumerStep> sample_trace;
};

/**
 * @brief RAII wrapper around a POSIX unnamed semaphore (sem_t).
 */
class PosixSemaphore {
public:
    explicit PosixSemaphore(unsigned int initial_value = 1);
    ~PosixSemaphore();

    PosixSemaphore(const PosixSemaphore&) = delete;
    PosixSemaphore& operator=(const PosixSemaphore&) = delete;
    PosixSemaphore(PosixSemaphore&&) = delete;
    PosixSemaphore& operator=(PosixSemaphore&&) = delete;

    bool wait();     // Handles EINTR gracefully
    bool try_wait();
    bool post();
    int get_value() const;
    bool is_valid() const noexcept { return initialized_; }

private:
    alignas(void*) unsigned char sem_storage_[64]; // storage for sem_t without exposing <semaphore.h> in header
    bool initialized_{false};
};

/**
 * @brief Runs a POSIX semaphore mutual-exclusion and signaling experiment (FR-SYNC-003).
 */
SemaphoreExperimentResult run_semaphore_experiment(
    std::size_t num_threads = kDefaultSemThreadCount,
    std::size_t iterations_per_thread = kDefaultSemIterationsPerThread);

/**
 * @brief Runs the classical Bounded-Buffer Producer-Consumer experiment using counting semaphores and mutex (FR-SYNC-005).
 */
ProducerConsumerResult run_producer_consumer_experiment(
    std::size_t buffer_capacity = 5,
    std::size_t items_to_produce = 20,
    std::size_t num_producers = 2,
    std::size_t num_consumers = 2);

} // namespace oscope::synchronization

#endif // OSCOPE_SYNCHRONIZATION_SEMAPHORE_EXPERIMENT_HPP
