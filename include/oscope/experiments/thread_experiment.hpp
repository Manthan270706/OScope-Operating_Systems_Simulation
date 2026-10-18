#ifndef OSCOPE_EXPERIMENTS_THREAD_EXPERIMENT_HPP
#define OSCOPE_EXPERIMENTS_THREAD_EXPERIMENT_HPP

#include <cstddef>
#include <limits>
#include <string>
#include <vector>

namespace oscope::experiments {

inline constexpr std::size_t kDefaultThreadExperimentCount = 4;
inline constexpr std::size_t kMaxSupportedThreads = 1024;

static_assert(kMaxSupportedThreads <= static_cast<std::size_t>(std::numeric_limits<int>::max()) / 100,
              "kMaxSupportedThreads scaled by 100 must not exceed the range of int");

struct ThreadExperimentResult {
    bool success{false};
    std::size_t requested_threads{0};
    std::size_t started_threads{0};
    std::size_t completed_threads{0};
    std::vector<int> worker_results;
    std::string error_message;
};

/**
 * @brief Runs a real multithreaded creation and joining experiment using std::thread.
 *
 * Spawns requested worker threads, assigns each a deterministic computational task,
 * joins all joinable threads safely using RAII cleanup, handles creation exceptions,
 * and tracks completed workers.
 *
 * @param num_threads Number of worker threads to start (defaults to 4).
 * @return ThreadExperimentResult containing started, completed counts and worker outputs.
 */
ThreadExperimentResult run_thread_experiment(std::size_t num_threads = kDefaultThreadExperimentCount);

} // namespace oscope::experiments

#endif // OSCOPE_EXPERIMENTS_THREAD_EXPERIMENT_HPP
