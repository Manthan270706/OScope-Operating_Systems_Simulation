#ifndef OSCOPE_SCHEDULING_METRICS_HPP
#define OSCOPE_SCHEDULING_METRICS_HPP

#include "oscope/scheduling_simulation_result.hpp"

namespace oscope {

/**
 * @brief Summary evaluation metrics for a scheduling simulation.
 *
 * Defines average waiting, turnaround, and response times as floating-point values.
 */
struct SchedulingMetrics {
    double average_waiting_time{0.0};
    double average_turnaround_time{0.0};
    double average_response_time{0.0};
};

/**
 * @brief Computes average scheduling metrics from a SchedulingSimulationResult.
 *
 * If result.process_results is empty, all averages safely evaluate to 0.0 without
 * division by zero.
 */
SchedulingMetrics calculate_metrics(const SchedulingSimulationResult& result);

double calculate_average_waiting_time(const SchedulingSimulationResult& result);
double calculate_average_turnaround_time(const SchedulingSimulationResult& result);
double calculate_average_response_time(const SchedulingSimulationResult& result);

} // namespace oscope

#endif // OSCOPE_SCHEDULING_METRICS_HPP
