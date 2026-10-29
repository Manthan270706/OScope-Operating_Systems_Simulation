#include "oscope/scheduling/fcfs.hpp"

#include <algorithm>
#include <vector>

namespace oscope {

SchedulingSimulationResult
FCFS::schedule(const std::vector<Process>& processes) {
    SchedulingSimulationResult result;

    std::vector<Process> sorted_processes = processes;

    std::sort(
        sorted_processes.begin(),
        sorted_processes.end(),
        [](const Process& a, const Process& b) {
            return a.arrival_time < b.arrival_time;
        }
    );

    int current_time = 0;

    for (const Process& process : sorted_processes) {
        if (current_time < process.arrival_time) {
            current_time = process.arrival_time;
        }

        const int start_time = current_time;
        const int completion_time = start_time + process.burst_time;
        const int turnaround_time =
            completion_time - process.arrival_time;
        const int waiting_time =
            turnaround_time - process.burst_time;
        const int response_time =
            start_time - process.arrival_time;

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

        current_time = completion_time;
    }

    return result;
}

} // namespace oscope
