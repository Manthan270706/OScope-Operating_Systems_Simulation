#include "oscope/scheduling/sjf.hpp"

#include <cstddef>
#include <limits>
#include <vector>

namespace oscope {

SchedulingSimulationResult
SJF::schedule(const std::vector<Process>& processes) {
    SchedulingSimulationResult result;
    if (processes.empty()) {
        return result;
    }

    const std::size_t process_count = processes.size();
    std::vector<bool> completed(process_count, false);
    std::size_t completed_count = 0;
    int current_time = 0;

    while (completed_count < process_count) {
        int selected_index = -1;

        for (std::size_t i = 0; i < process_count; ++i) {
            if (completed[i] || processes[i].arrival_time > current_time) {
                continue;
            }

            if (selected_index == -1) {
                selected_index = static_cast<int>(i);
                continue;
            }

            const Process& candidate = processes[i];
            const Process& current_best = processes[selected_index];

            if (candidate.burst_time < current_best.burst_time) {
                selected_index = static_cast<int>(i);
            } else if (candidate.burst_time == current_best.burst_time) {
                if (candidate.arrival_time < current_best.arrival_time) {
                    selected_index = static_cast<int>(i);
                } else if (candidate.arrival_time == current_best.arrival_time) {
                    if (candidate.pid < current_best.pid) {
                        selected_index = static_cast<int>(i);
                    }
                }
            }
        }

        if (selected_index == -1) {
            int next_arrival = std::numeric_limits<int>::max();
            for (std::size_t i = 0; i < process_count; ++i) {
                if (!completed[i] && processes[i].arrival_time < next_arrival) {
                    next_arrival = processes[i].arrival_time;
                }
            }
            current_time = next_arrival;
            continue;
        }

        const Process& process = processes[selected_index];
        const int start_time = current_time;
        const int completion_time = start_time + process.burst_time;
        const int turnaround_time = completion_time - process.arrival_time;
        const int waiting_time = turnaround_time - process.burst_time;
        const int response_time = start_time - process.arrival_time;

        result.process_results.push_back({
            process.pid,
            completion_time,
            turnaround_time,
            waiting_time,
            response_time
        });

        result.timeline.push_back({
            process.pid,
            start_time,
            completion_time
        });

        completed[selected_index] = true;
        ++completed_count;
        current_time = completion_time;
    }

    return result;
}

} // namespace oscope
