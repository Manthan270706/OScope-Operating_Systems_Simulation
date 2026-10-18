#include "oscope/experiments/synchronization_experiment.hpp"

#include <atomic>
#include <cstdint>
#include <exception>
#include <limits>
#include <mutex>
#include <system_error>
#include <thread>
#include <vector>

namespace oscope::experiments {

SynchronizationExperimentResult run_synchronization_experiment(
    std::size_t num_threads,
    std::size_t iterations_per_thread) {

    SynchronizationExperimentResult result;
    result.num_threads = num_threads;
    result.iterations_per_thread = iterations_per_thread;

    // Guard against integer overflow when calculating expected counter
    if (num_threads > 0 && iterations_per_thread > std::numeric_limits<std::uint64_t>::max() / num_threads) {
        result.success = false;
        result.error_message = "Expected counter calculation would overflow uint64_t.";
        return result;
    }

    std::uint64_t expected_total = static_cast<std::uint64_t>(num_threads) *
                                   static_cast<std::uint64_t>(iterations_per_thread);
    result.expected_counter = expected_total;

    if (num_threads == 0) {
        result.actual_counter = 0;
        result.threads_completed = 0;
        result.success = true;
        return result;
    }

    std::uint64_t shared_counter = 0;
    std::mutex counter_mutex;
    std::atomic<std::size_t> completed_count{0};

    std::vector<std::thread> threads;
    threads.reserve(num_threads);
    bool creation_failed = false;

    // RAII guard ensuring all joinable threads are joined upon exit
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
            threads.emplace_back([iterations_per_thread, &shared_counter, &counter_mutex, &completed_count]() {
                for (std::size_t j = 0; j < iterations_per_thread; ++j) {
                    std::lock_guard<std::mutex> lock(counter_mutex);
                    ++shared_counter;
                }
                completed_count.fetch_add(1, std::memory_order_relaxed);
            });
        } catch (const std::system_error& e) {
            creation_failed = true;
            result.error_message = std::string("Thread creation failed: ") + e.what();
            break;
        } catch (const std::exception& e) {
            creation_failed = true;
            result.error_message = std::string("Unexpected exception during thread creation: ") + e.what();
            break;
        }
    }

    // Join all started threads before reading final counter
    for (auto& t : threads) {
        if (t.joinable()) {
            t.join();
        }
    }

    result.threads_completed = completed_count.load(std::memory_order_relaxed);
    result.actual_counter = shared_counter;

    if (!creation_failed &&
        result.threads_completed == num_threads &&
        result.actual_counter == result.expected_counter) {
        result.success = true;
    } else {
        result.success = false;
        if (result.error_message.empty()) {
            result.error_message = "Counter mismatch or incomplete thread execution.";
        }
    }

    return result;
}

} // namespace oscope::experiments
