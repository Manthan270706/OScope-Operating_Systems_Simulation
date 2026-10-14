#include "oscope/scheduling_comparison.hpp"

#include <stdexcept>
#include <utility>

namespace oscope {

void SchedulingComparator::add_algorithm(std::string name, std::shared_ptr<SchedulingAlgorithm> algorithm) {
    if (!algorithm) {
        throw std::invalid_argument("Algorithm cannot be null.");
    }
    algorithms_.emplace_back(std::move(name), std::move(algorithm));
}

void SchedulingComparator::add_algorithm(std::string name, SchedulingAlgorithm& algorithm) {
    // Wrap reference in a non-owning shared_ptr with a no-op deleter
    std::shared_ptr<SchedulingAlgorithm> non_owning(&algorithm, [](SchedulingAlgorithm*) {});
    algorithms_.emplace_back(std::move(name), std::move(non_owning));
}

void SchedulingComparator::clear() noexcept {
    algorithms_.clear();
}

std::size_t SchedulingComparator::size() const noexcept {
    return algorithms_.size();
}

bool SchedulingComparator::empty() const noexcept {
    return algorithms_.empty();
}

std::vector<SchedulingComparisonEntry>
SchedulingComparator::compare(const std::vector<Process>& processes) const {
    std::vector<SchedulingComparisonEntry> entries;
    entries.reserve(algorithms_.size());

    for (const auto& [name, algorithm] : algorithms_) {
        SchedulingSimulationResult sim_result = algorithm->schedule(processes);
        SchedulingMetrics metrics = calculate_metrics(sim_result);
        entries.push_back({name, std::move(sim_result), metrics});
    }

    return entries;
}

std::vector<SchedulingComparisonEntry>
SchedulingComparator::compare(
    const std::vector<Process>& processes,
    const std::vector<std::pair<std::string, std::shared_ptr<SchedulingAlgorithm>>>& algorithms) {
    SchedulingComparator comparator;
    for (const auto& [name, algorithm] : algorithms) {
        comparator.add_algorithm(name, algorithm);
    }
    return comparator.compare(processes);
}

std::vector<SchedulingComparisonEntry>
SchedulingComparator::compare(
    const std::vector<Process>& processes,
    const std::vector<std::pair<std::string, SchedulingAlgorithm*>>& algorithms) {
    SchedulingComparator comparator;
    for (const auto& [name, algorithm] : algorithms) {
        if (!algorithm) {
            throw std::invalid_argument("Algorithm pointer cannot be null.");
        }
        comparator.add_algorithm(name, *algorithm);
    }
    return comparator.compare(processes);
}

} // namespace oscope
