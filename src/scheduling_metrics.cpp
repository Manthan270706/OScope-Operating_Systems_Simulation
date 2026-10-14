#include "oscope/scheduling_metrics.hpp"

namespace oscope {

SchedulingMetrics calculate_metrics(const SchedulingSimulationResult& result) {
    if (result.process_results.empty()) {
        return {0.0, 0.0, 0.0};
    }

    double total_waiting_time = 0.0;
    double total_turnaround_time = 0.0;
    double total_response_time = 0.0;

    for (const auto& pr : result.process_results) {
        total_waiting_time += static_cast<double>(pr.waiting_time);
        total_turnaround_time += static_cast<double>(pr.turnaround_time);
        total_response_time += static_cast<double>(pr.response_time);
    }

    const double count = static_cast<double>(result.process_results.size());
    return {
        total_waiting_time / count,
        total_turnaround_time / count,
        total_response_time / count
    };
}

double calculate_average_waiting_time(const SchedulingSimulationResult& result) {
    return calculate_metrics(result).average_waiting_time;
}

double calculate_average_turnaround_time(const SchedulingSimulationResult& result) {
    return calculate_metrics(result).average_turnaround_time;
}

double calculate_average_response_time(const SchedulingSimulationResult& result) {
    return calculate_metrics(result).average_response_time;
}

} // namespace oscope
