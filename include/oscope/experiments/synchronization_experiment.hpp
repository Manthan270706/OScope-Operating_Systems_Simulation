#ifndef OSCOPE_EXPERIMENTS_SYNCHRONIZATION_EXPERIMENT_HPP
#define OSCOPE_EXPERIMENTS_SYNCHRONIZATION_EXPERIMENT_HPP

#include <cstddef>
#include <cstdint>
#include <string>

namespace oscope::experiments {

inline constexpr std::size_t kDefaultSyncThreadCount = 4;
inline constexpr std::size_t kDefaultIterationsPerThread = 10000;

struct SynchronizationExperimentResult {
    bool success{false};
    std::size_t num_threads{0};
    std::size_t iterations_per_thread{0};
    std::size_t threads_completed{0};
    std::uint64_t expected_counter{0};
    std::uint64_t actual_counter{0};
    std::string error_message;
};

/**
 * @brief Runs a real multithreaded synchronization experiment with a shared counter and std::mutex.
 *
 * Multiple threads increment a shared counter iterations_per_thread times. Access to the
 * shared counter is protected using std::mutex with std::lock_guard. All joinable threads
 * are joined prior to reading the counter.
 *
 * @param num_threads Number of concurrent worker threads.
 * @param iterations_per_thread Number of increments each thread performs.
 * @return SynchronizationExperimentResult with expected vs actual counts and completion info.
 */
SynchronizationExperimentResult run_synchronization_experiment(
    std::size_t num_threads = kDefaultSyncThreadCount,
    std::size_t iterations_per_thread = kDefaultIterationsPerThread);

} // namespace oscope::experiments

#endif // OSCOPE_EXPERIMENTS_SYNCHRONIZATION_EXPERIMENT_HPP
