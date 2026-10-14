#include "oscope/scheduling/srtf.hpp"

#include <cstddef>
#include <limits>
#include <vector>

namespace oscope {

namespace {

struct ProcessState {
    Process process;
    int remaining_time;
    int first_start_time{-1};
    int completion_time{-1};
    bool completed{false};
};

bool is_better_candidate(const ProcessState& a, const ProcessState& b) {
    if (a.remaining_time != b.remaining_time) {
        return a.remaining_time < b.remaining_time;
    }
    if (a.process.arrival_time != b.process.arrival_time) {
        return a.process.arrival_time < b.process.arrival_time;
    }
    return a.process.pid < b.process.pid;
}

} // namespace

SchedulingSimulationResult
SRTF::schedule(const std::vector<Process>& processes) {
    SchedulingSimulationResult result;
    if (processes.empty()) {
        return result;
    }

    const std::size_t n = processes.size();
    std::vector<ProcessState> proc_table;
    proc_table.reserve(n);
    for (const auto& p : processes) {
        proc_table.push_back({p, p.burst_time, -1, -1, false});
    }

    std::size_t completed_count = 0;
    int current_time = 0;
    int running_index = -1;
    int current_segment_start = -1;

    while (completed_count < n) {
        if (running_index == -1) {
            // Find the best ready process at current_time
            int best_index = -1;
            for (std::size_t i = 0; i < n; ++i) {
                if (proc_table[i].completed || proc_table[i].process.arrival_time > current_time) {
                    continue;
                }
                if (best_index == -1 || is_better_candidate(proc_table[i], proc_table[best_index])) {
                    best_index = static_cast<int>(i);
                }
            }

            if (best_index == -1) {
                // No process is ready; advance simulation time to earliest next arrival
                int next_arrival = std::numeric_limits<int>::max();
                for (std::size_t i = 0; i < n; ++i) {
                    if (!proc_table[i].completed && proc_table[i].process.arrival_time < next_arrival) {
                        next_arrival = proc_table[i].process.arrival_time;
                    }
                }
                current_time = next_arrival;
                continue;
            }

            running_index = best_index;
            current_segment_start = current_time;
            if (proc_table[running_index].first_start_time == -1) {
                proc_table[running_index].first_start_time = current_time;
            }
        }

        // Determine next event (process completion vs future arrival)
        int next_arrival = std::numeric_limits<int>::max();
        for (std::size_t i = 0; i < n; ++i) {
            if (!proc_table[i].completed && proc_table[i].process.arrival_time > current_time) {
                if (proc_table[i].process.arrival_time < next_arrival) {
                    next_arrival = proc_table[i].process.arrival_time;
                }
            }
        }

        if (next_arrival >= current_time + proc_table[running_index].remaining_time) {
            // Process runs until completion
            current_time += proc_table[running_index].remaining_time;
            proc_table[running_index].remaining_time = 0;
            proc_table[running_index].completed = true;
            proc_table[running_index].completion_time = current_time;
            ++completed_count;

            result.timeline.push_back({
                proc_table[running_index].process.pid,
                current_segment_start,
                current_time
            });

            const auto& p = proc_table[running_index].process;
            const int comp = proc_table[running_index].completion_time;
            const int tat = comp - p.arrival_time;
            const int wait = tat - p.burst_time;
            const int resp = proc_table[running_index].first_start_time - p.arrival_time;

            result.process_results.push_back({
                p.pid,
                comp,
                tat,
                wait,
                resp
            });

            running_index = -1;
        } else {
            // Process runs until next_arrival
            const int run_duration = next_arrival - current_time;
            proc_table[running_index].remaining_time -= run_duration;
            current_time = next_arrival;

            // Check if any newly arrived ready process strictly preempts running_index
            int best_candidate = -1;
            for (std::size_t i = 0; i < n; ++i) {
                if (proc_table[i].completed || proc_table[i].process.arrival_time > current_time) {
                    continue;
                }
                if (best_candidate == -1 || is_better_candidate(proc_table[i], proc_table[best_candidate])) {
                    best_candidate = static_cast<int>(i);
                }
            }

            if (best_candidate != -1 &&
                proc_table[best_candidate].remaining_time < proc_table[running_index].remaining_time) {
                // Strictly shorter remaining time: preemption occurs
                result.timeline.push_back({
                    proc_table[running_index].process.pid,
                    current_segment_start,
                    current_time
                });

                running_index = best_candidate;
                current_segment_start = current_time;
                if (proc_table[running_index].first_start_time == -1) {
                    proc_table[running_index].first_start_time = current_time;
                }
            }
            // Otherwise: running_index continues running without splitting timeline segment
        }
    }

    return result;
}

} // namespace oscope
