#include "oscope/experiments/thread_experiment.hpp"

#include <atomic>
#include <exception>
#include <system_error>
#include <thread>
#include <vector>

namespace oscope::experiments {

ThreadExperimentResult run_thread_experiment(std::size_t num_threads) {
    ThreadExperimentResult result;
    result.requested_threads = num_threads;

    if (num_threads > kMaxSupportedThreads) {
        result.success = false;
        result.error_message = "Requested thread count (" + std::to_string(num_threads) +
                               ") exceeds maximum supported limit of " +
                               std::to_string(kMaxSupportedThreads) + ".";
        return result;
    }

    if (num_threads == 0) {
        result.success = true;
        return result;
    }

    try {
        result.worker_results.resize(num_threads, 0);
    } catch (const std::exception& e) {
        result.success = false;
        result.error_message = std::string("Failed to allocate worker results: ") + e.what();
        return result;
    }

    std::vector<std::thread> threads;
    threads.reserve(num_threads);

    std::atomic<std::size_t> completed_count{0};
    bool thread_creation_failed = false;

    // RAII guard to guarantee every joinable thread is joined before leaving scope
    struct ThreadJoiner {
        std::vector<std::thread>& ths;
        ~ThreadJoiner() {
            for (auto& t : ths) {
                if (t.joinable()) {
                    t.join();
                }
            }
        }
    } joiner{threads};

    for (std::size_t i = 0; i < num_threads; ++i) {
        try {
            threads.emplace_back([i, &result, &completed_count]() {
                // Deterministic task: store computed distinct integer based on worker index
                // Safe calculation and conversion bounded by kMaxSupportedThreads <= INT_MAX / 100
                const std::size_t scaled = (i + 1) * 100;
                result.worker_results[i] = static_cast<int>(scaled);
                completed_count.fetch_add(1, std::memory_order_relaxed);
            });
            result.started_threads++;
        } catch (const std::system_error& e) {
            thread_creation_failed = true;
            result.error_message = std::string("Thread creation failed: ") + e.what();
            break;
        } catch (const std::exception& e) {
            thread_creation_failed = true;
            result.error_message = std::string("Unexpected exception during thread creation: ") + e.what();
            break;
        }
    }

    // Join all started threads safely
    for (auto& t : threads) {
        if (t.joinable()) {
            t.join();
        }
    }

    result.completed_threads = completed_count.load(std::memory_order_relaxed);
    result.success = (!thread_creation_failed && result.completed_threads == num_threads);

    return result;
}

} // namespace oscope::experiments
