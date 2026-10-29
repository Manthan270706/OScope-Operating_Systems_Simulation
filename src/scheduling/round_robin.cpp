#include "oscope/scheduling/round_robin.hpp"

#include <algorithm>
#include <cstddef>
#include <limits>
#include <queue>
#include <stdexcept>
#include <vector>

namespace oscope {

namespace {

struct ProcessState {
    Process process;
    std::size_t original_index;
    int remaining_time;
    int first_start_time{-1};
    int completion_time{-1};
    bool enqueued{false};
};

} // namespace

RoundRobin::RoundRobin(int time_quantum) : time_quantum_(time_quantum) {
    if (time_quantum <= 0) {
        throw std::invalid_argument("Time quantum must be a positive integer.");
    }
}

int RoundRobin::time_quantum() const noexcept {
    return time_quantum_;
}

SchedulingSimulationResult
RoundRobin::schedule(const std::vector<Process>& processes) {
    SchedulingSimulationResult result;
    if (processes.empty()) {
        return result;
    }

    const std::size_t n = processes.size();
    std::vector<ProcessState> proc_table;
    proc_table.reserve(n);
    for (std::size_t i = 0; i < n; ++i) {
        proc_table.push_back({processes[i], i, processes[i].burst_time, -1, -1, false});
    }

    std::queue<std::size_t> ready_queue;
    int current_time = 0;
    std::size_t completed_count = 0;

    auto enqueue_arrivals = [&](int up_to_time) {
        std::vector<std::size_t> newly_arrived;
        for (std::size_t i = 0; i < n; ++i) {
            if (!proc_table[i].enqueued && proc_table[i].process.arrival_time <= up_to_time) {
                newly_arrived.push_back(i);
            }
        }

        // Arrival-order policy: ascending arrival time; preserve relative input order on ties
        std::sort(newly_arrived.begin(), newly_arrived.end(), [&](std::size_t a, std::size_t b) {
            if (proc_table[a].process.arrival_time != proc_table[b].process.arrival_time) {
                return proc_table[a].process.arrival_time < proc_table[b].process.arrival_time;
            }
            return proc_table[a].original_index < proc_table[b].original_index;
        });

        for (std::size_t idx : newly_arrived) {
            proc_table[idx].enqueued = true;
            ready_queue.push(idx);
        }
    };

    // Initial enqueue of processes available at t=0
    enqueue_arrivals(current_time);

    while (completed_count < n) {
        if (ready_queue.empty()) {
            // CPU is idle: advance simulation time to next earliest arrival
            int next_arrival = std::numeric_limits<int>::max();
            for (std::size_t i = 0; i < n; ++i) {
                if (!proc_table[i].enqueued && proc_table[i].process.arrival_time < next_arrival) {
                    next_arrival = proc_table[i].process.arrival_time;
                }
            }
            current_time = next_arrival;
            enqueue_arrivals(current_time);
            continue;
        }

        const std::size_t curr_idx = ready_queue.front();
        ready_queue.pop();
        auto& curr = proc_table[curr_idx];

        if (curr.first_start_time == -1) {
            curr.first_start_time = current_time;
        }

        const int slice = std::min(time_quantum_, curr.remaining_time);
        const int start_time = current_time;
        const int end_time = current_time + slice;
        current_time = end_time;
        curr.remaining_time -= slice;

        result.timeline.push_back({
            curr.process.pid,
            start_time,
            end_time
        });

        // Enqueue processes arriving during this slice before re-enqueuing the running process
        enqueue_arrivals(current_time);

        if (curr.remaining_time == 0) {
            curr.completion_time = current_time;
            ++completed_count;

            const int comp = curr.completion_time;
            const int tat = comp - curr.process.arrival_time;
            const int wait = tat - curr.process.burst_time;
            const int resp = curr.first_start_time - curr.process.arrival_time;

            result.process_results.push_back({
                curr.process.pid,
                comp,
                tat,
                wait,
                resp
            });
        } else {
            // Re-enqueue unfinished process to the back of the FIFO ready queue
            ready_queue.push(curr_idx);
        }
    }

    return result;
}

} // namespace oscope
