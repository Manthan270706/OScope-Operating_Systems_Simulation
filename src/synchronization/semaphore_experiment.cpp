#include "oscope/synchronization/semaphore_experiment.hpp"

#include <algorithm>
#include <atomic>
#include <cerrno>
#include <cstring>
#include <limits>
#include <mutex>
#include <semaphore.h>
#include <thread>
#include <vector>

namespace oscope::synchronization {

namespace {

sem_t* get_sem_ptr(unsigned char* storage) {
    return reinterpret_cast<sem_t*>(storage);
}

const sem_t* get_sem_ptr(const unsigned char* storage) {
    return reinterpret_cast<const sem_t*>(storage);
}

} // namespace

PosixSemaphore::PosixSemaphore(unsigned int initial_value) {
    static_assert(sizeof(sem_t) <= sizeof(sem_storage_), "sem_t exceeds storage capacity");
    if (::sem_init(get_sem_ptr(sem_storage_), 0, initial_value) == 0) {
        initialized_ = true;
    }
}

PosixSemaphore::~PosixSemaphore() {
    if (initialized_) {
        ::sem_destroy(get_sem_ptr(sem_storage_));
        initialized_ = false;
    }
}

bool PosixSemaphore::wait() {
    if (!initialized_) return false;
    while (::sem_wait(get_sem_ptr(sem_storage_)) == -1) {
        if (errno == EINTR) {
            continue;
        }
        return false;
    }
    return true;
}

bool PosixSemaphore::try_wait() {
    if (!initialized_) return false;
    return (::sem_trywait(get_sem_ptr(sem_storage_)) == 0);
}

bool PosixSemaphore::post() {
    if (!initialized_) return false;
    return (::sem_post(get_sem_ptr(sem_storage_)) == 0);
}

int PosixSemaphore::get_value() const {
    if (!initialized_) return -1;
    int val = 0;
    if (::sem_getvalue(const_cast<sem_t*>(get_sem_ptr(sem_storage_)), &val) == 0) {
        return val;
    }
    return -1;
}

SemaphoreExperimentResult run_semaphore_experiment(
    std::size_t num_threads,
    std::size_t iterations_per_thread) {

    SemaphoreExperimentResult result;
    result.num_threads = num_threads;
    result.iterations_per_thread = iterations_per_thread;

    if (num_threads > 0 && iterations_per_thread > std::numeric_limits<std::uint64_t>::max() / num_threads) {
        result.success = false;
        result.error_message = "Counter calculation would overflow uint64_t.";
        return result;
    }

    result.expected_counter = static_cast<std::uint64_t>(num_threads) * iterations_per_thread;
    result.initial_value = 1;

    if (num_threads == 0) {
        result.actual_counter = 0;
        result.threads_completed = 0;
        result.success = true;
        result.details = "No worker threads requested; counter remains 0.";
        return result;
    }

    PosixSemaphore sem(1);
    if (!sem.is_valid()) {
        result.success = false;
        result.error_message = "Failed to initialize POSIX semaphore via sem_init.";
        return result;
    }

    std::uint64_t shared_counter = 0;
    std::atomic<std::size_t> completed_count{0};
    std::vector<std::thread> workers;
    workers.reserve(num_threads);

    struct ThreadJoiner {
        std::vector<std::thread>& ths;
        ~ThreadJoiner() {
            for (auto& t : ths) {
                if (t.joinable()) {
                    t.join();
                }
            }
        }
    } joiner{workers};

    for (std::size_t t = 0; t < num_threads; ++t) {
        workers.emplace_back([&sem, &shared_counter, &completed_count, iterations_per_thread]() {
            for (std::size_t i = 0; i < iterations_per_thread; ++i) {
                if (sem.wait()) {
                    ++shared_counter;
                    sem.post();
                }
            }
            completed_count.fetch_add(1, std::memory_order_relaxed);
        });
    }

    for (auto& t : workers) {
        if (t.joinable()) {
            t.join();
        }
    }

    result.threads_completed = completed_count.load(std::memory_order_relaxed);
    result.actual_counter = shared_counter;

    if (result.threads_completed == num_threads &&
        result.actual_counter == result.expected_counter) {
        result.success = true;
        result.details = "POSIX semaphore successfully protected critical section across " +
                         std::to_string(num_threads) + " concurrent threads.";
    } else {
        result.success = false;
        result.error_message = "Counter mismatch or thread execution incomplete.";
    }

    return result;
}

ProducerConsumerResult run_producer_consumer_experiment(
    std::size_t buffer_capacity,
    std::size_t items_to_produce,
    std::size_t num_producers,
    std::size_t num_consumers) {

    ProducerConsumerResult result;
    result.buffer_capacity = std::max<std::size_t>(1, buffer_capacity);
    result.total_items_produced = items_to_produce;
    result.num_producers = std::max<std::size_t>(1, num_producers);
    result.num_consumers = std::max<std::size_t>(1, num_consumers);

    if (items_to_produce == 0) {
        result.success = true;
        result.total_items_consumed = 0;
        result.items_preserved = true;
        result.details = "Zero items requested; producer-consumer completed trivially.";
        return result;
    }

    PosixSemaphore empty_slots(static_cast<unsigned int>(result.buffer_capacity));
    PosixSemaphore occupied_slots(0);

    if (!empty_slots.is_valid() || !occupied_slots.is_valid()) {
        result.success = false;
        result.error_message = "Failed to initialize POSIX counting semaphores.";
        return result;
    }

    std::vector<int> circular_buffer(result.buffer_capacity, -1);
    std::size_t in_idx = 0;
    std::size_t out_idx = 0;
    std::size_t current_occupancy = 0;
    std::size_t max_occupancy = 0;

    std::mutex buffer_mutex;
    std::atomic<int> next_item{1};
    std::vector<int> consumed_items;
    consumed_items.reserve(items_to_produce);

    std::vector<ProducerConsumerStep> trace;
    std::mutex trace_mutex;
    std::size_t step_counter = 0;

    auto record_step = [&](const std::string& role, std::size_t worker_id, int item, std::size_t occ) {
        std::lock_guard<std::mutex> tlock(trace_mutex);
        if (trace.size() < 40) {
            ProducerConsumerStep step;
            step.step_id = ++step_counter;
            step.role = role;
            step.worker_id = worker_id;
            step.item = item;
            step.buffer_occupancy = occ;
            trace.push_back(std::move(step));
        }
    };

    // Consumers
    std::vector<std::thread> consumers;
    consumers.reserve(result.num_consumers);

    for (std::size_t c = 0; c < result.num_consumers; ++c) {
        consumers.emplace_back([&, c]() {
            while (true) {
                occupied_slots.wait();

                int item = -1;
                std::size_t occ = 0;
                {
                    std::lock_guard<std::mutex> lock(buffer_mutex);
                    item = circular_buffer[out_idx];
                    out_idx = (out_idx + 1) % result.buffer_capacity;
                    if (item != -1) {
                        --current_occupancy;
                        consumed_items.push_back(item);
                    }
                    occ = current_occupancy;
                }

                empty_slots.post();

                if (item == -1) {
                    // Sentinel reached; consumer terminates
                    break;
                }

                record_step("Consumer", c, item, occ);
            }
        });
    }

    // Producers
    std::vector<std::thread> producers;
    producers.reserve(result.num_producers);

    for (std::size_t p = 0; p < result.num_producers; ++p) {
        producers.emplace_back([&, p]() {
            while (true) {
                int item = next_item.fetch_add(1);
                if (item > static_cast<int>(items_to_produce)) {
                    break;
                }

                empty_slots.wait();

                std::size_t occ = 0;
                {
                    std::lock_guard<std::mutex> lock(buffer_mutex);
                    circular_buffer[in_idx] = item;
                    in_idx = (in_idx + 1) % result.buffer_capacity;
                    ++current_occupancy;
                    if (current_occupancy > max_occupancy) {
                        max_occupancy = current_occupancy;
                    }
                    occ = current_occupancy;
                }

                occupied_slots.post();
                record_step("Producer", p, item, occ);
            }
        });
    }

    // Wait for all producers to finish producing real items
    for (auto& t : producers) {
        if (t.joinable()) {
            t.join();
        }
    }

    // Inject sentinel values (-1) into buffer to cleanly wake and terminate each consumer
    for (std::size_t c = 0; c < result.num_consumers; ++c) {
        empty_slots.wait();
        {
            std::lock_guard<std::mutex> lock(buffer_mutex);
            circular_buffer[in_idx] = -1;
            in_idx = (in_idx + 1) % result.buffer_capacity;
        }
        occupied_slots.post();
    }

    // Wait for all consumers to finish
    for (auto& t : consumers) {
        if (t.joinable()) {
            t.join();
        }
    }

    result.total_items = items_to_produce;
    result.items_produced = items_to_produce;
    result.items_consumed = consumed_items.size();
    result.total_items_consumed = consumed_items.size();
    result.max_buffer_occupancy_observed = max_occupancy;
    result.sample_trace = std::move(trace);

    // Validate item preservation: exactly 1..items_to_produce with no loss or duplicates
    std::sort(consumed_items.begin(), consumed_items.end());
    bool preserved = (consumed_items.size() == items_to_produce);
    for (std::size_t i = 0; i < items_to_produce && preserved; ++i) {
        if (consumed_items[i] != static_cast<int>(i + 1)) {
            preserved = false;
        }
    }
    result.items_preserved = preserved;

    if (result.total_items_consumed == items_to_produce &&
        result.items_preserved &&
        result.max_buffer_occupancy_observed <= result.buffer_capacity) {
        result.success = true;
        result.details = "Bounded-buffer Producer-Consumer completed: " +
                         std::to_string(items_to_produce) + " items safely transferred across " +
                         std::to_string(result.num_producers) + " producers and " +
                         std::to_string(result.num_consumers) + " consumers with max buffer occupancy " +
                         std::to_string(max_occupancy) + "/" + std::to_string(result.buffer_capacity) + ".";
    } else {
        result.success = false;
        result.error_message = "Buffer bounds violated or item loss/duplication detected.";
    }

    return result;
}

} // namespace oscope::synchronization
