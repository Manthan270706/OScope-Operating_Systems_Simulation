#ifndef OSCOPE_SCHEDULING_COMPARISON_HPP
#define OSCOPE_SCHEDULING_COMPARISON_HPP

#include <cstddef>
#include <memory>
#include <string>
#include <utility>
#include <vector>

#include "oscope/process.hpp"
#include "oscope/scheduling_algorithm.hpp"
#include "oscope/scheduling_metrics.hpp"
#include "oscope/scheduling_simulation_result.hpp"

namespace oscope {

/**
 * @brief Evaluation result for an individual scheduling algorithm in a comparison.
 */
struct SchedulingComparisonEntry {
    std::string algorithm_name;
    SchedulingSimulationResult simulation_result;
    SchedulingMetrics metrics;

    double average_waiting_time() const noexcept {
        return metrics.average_waiting_time;
    }

    double average_turnaround_time() const noexcept {
        return metrics.average_turnaround_time;
    }

    double average_response_time() const noexcept {
        return metrics.average_response_time;
    }
};

/**
 * @brief Evaluates and compares multiple CPU scheduling algorithms on a given workload.
 */
class SchedulingComparator {
public:
    SchedulingComparator() = default;

    void add_algorithm(std::string name, std::shared_ptr<SchedulingAlgorithm> algorithm);
    void add_algorithm(std::string name, SchedulingAlgorithm& algorithm);

    void clear() noexcept;
    std::size_t size() const noexcept;
    bool empty() const noexcept;

    std::vector<SchedulingComparisonEntry> compare(const std::vector<Process>& processes) const;

    static std::vector<SchedulingComparisonEntry> compare(
        const std::vector<Process>& processes,
        const std::vector<std::pair<std::string, std::shared_ptr<SchedulingAlgorithm>>>& algorithms);

    static std::vector<SchedulingComparisonEntry> compare(
        const std::vector<Process>& processes,
        const std::vector<std::pair<std::string, SchedulingAlgorithm*>>& algorithms);

private:
    std::vector<std::pair<std::string, std::shared_ptr<SchedulingAlgorithm>>> algorithms_;
};

} // namespace oscope

#endif // OSCOPE_SCHEDULING_COMPARISON_HPP
