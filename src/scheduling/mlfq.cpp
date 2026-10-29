#include "oscope/scheduling/mlfq.hpp"

#include <algorithm>
#include <cstddef>
#include <deque>
#include <limits>
#include <stdexcept>
#include <vector>

namespace oscope {

namespace {

struct ProcessState {
    Process process;
    std::size_t original_index;
    int remaining_burst;
    int current_queue{0};
    int remaining_quantum{0};
    int first_start_time{-1};
    int completion_time{-1};
    bool arrived{false};
};

} // namespace

MLFQ::MLFQ(int q0, int q1, int q2) : q0_(q0), q1_(q1), q2_(q2) {
    if (q0 <= 0 || q1 <= 0 || q2 <= 0) {
        throw std::invalid_argument("Time quanta for all queues must be positive integers.");
    }
}

int MLFQ::q0() const noexcept {
    return q0_;
}

int MLFQ::q1() const noexcept {
    return q1_;
}

int MLFQ::q2() const noexcept {
    return q2_;
}

SchedulingSimulationResult
MLFQ::schedule(const std::vector<Process>& processes) {
    SchedulingSimulationResult result;
    if (processes.empty()) {
        return result;
    }

    const std::size_t n = processes.size();
    std::vector<ProcessState> proc_table;
    proc_table.reserve(n);
    for (std::size_t i = 0; i < n; ++i) {
        proc_table.push_back({processes[i], i, processes[i].burst_time, 0, 0, -1, -1, false});
    }

    std::deque<std::size_t> queues[3];
    int current_time = 0;
    std::size_t completed_count = 0;

    auto enqueue_arrivals = [&](int up_to_time) {
        std::vector<std::size_t> newly_arrived;
        for (std::size_t i = 0; i < n; ++i) {
            if (!proc_table[i].arrived && proc_table[i].process.arrival_time <= up_to_time) {
                newly_arrived.push_back(i);
            }
        }

        // Ascending arrival time; preserve original input order on ties
        std::sort(newly_arrived.begin(), newly_arrived.end(), [&](std::size_t a, std::size_t b) {
            if (proc_table[a].process.arrival_time != proc_table[b].process.arrival_time) {
                return proc_table[a].process.arrival_time < proc_table[b].process.arrival_time;
            }
            return proc_table[a].original_index < proc_table[b].original_index;
        });

        for (std::size_t idx : newly_arrived) {
            proc_table[idx].arrived = true;
            proc_table[idx].current_queue = 0;
            proc_table[idx].remaining_quantum = q0_;
            queues[0].push_back(idx);
        }
    };

    // Initial enqueue at t=0
    enqueue_arrivals(current_time);

    while (completed_count < n) {
        int q_curr = -1;
        for (int q = 0; q < 3; ++q) {
            if (!queues[q].empty()) {
                q_curr = q;
                break;
            }
        }

        if (q_curr == -1) {
            // CPU is idle: advance simulation time to earliest next arrival
            int next_arrival = std::numeric_limits<int>::max();
            for (std::size_t i = 0; i < n; ++i) {
                if (!proc_table[i].arrived && proc_table[i].process.arrival_time < next_arrival) {
                    next_arrival = proc_table[i].process.arrival_time;
                }
            }
            current_time = next_arrival;
            enqueue_arrivals(current_time);
            continue;
        }

        const std::size_t curr_idx = queues[q_curr].front();
        queues[q_curr].pop_front();
        auto& curr = proc_table[curr_idx];

        if (curr.first_start_time == -1) {
            curr.first_start_time = current_time;
        }

        const int max_run = std::min(curr.remaining_burst, curr.remaining_quantum);
        int run_duration = max_run;
        bool preempted = false;

        // If running in Q1 or Q2, check if any future arrival enters Q0 before max_run completes
        if (q_curr > 0) {
            int next_higher_arrival = std::numeric_limits<int>::max();
            for (std::size_t i = 0; i < n; ++i) {
                if (!proc_table[i].arrived && proc_table[i].process.arrival_time > current_time) {
                    if (proc_table[i].process.arrival_time < next_higher_arrival) {
                        next_higher_arrival = proc_table[i].process.arrival_time;
                    }
                }
            }

            if (next_higher_arrival < current_time + max_run) {
                run_duration = next_higher_arrival - current_time;
                preempted = true;
            }
        }

        const int start_time = current_time;
        const int end_time = current_time + run_duration;
        current_time = end_time;
        curr.remaining_burst -= run_duration;
        curr.remaining_quantum -= run_duration;

        result.timeline.push_back({
            curr.process.pid,
            start_time,
            end_time
        });

        // Enqueue any processes that arrived up to current_time
        enqueue_arrivals(current_time);

        if (curr.remaining_burst == 0) {
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
        } else if (preempted) {
            // Interrupted by higher-priority arrival: return to front of current queue with remaining allotment preserved
            queues[q_curr].push_front(curr_idx);
        } else {
            // Process consumed its full quantum in current queue: demote or requeue at tail
            if (q_curr == 0) {
                curr.current_queue = 1;
                curr.remaining_quantum = q1_;
                queues[1].push_back(curr_idx);
            } else if (q_curr == 1) {
                curr.current_queue = 2;
                curr.remaining_quantum = q2_;
                queues[2].push_back(curr_idx);
            } else {
                curr.current_queue = 2;
                curr.remaining_quantum = q2_;
                queues[2].push_back(curr_idx);
            }
        }
    }

    return result;
}

} // namespace oscope
