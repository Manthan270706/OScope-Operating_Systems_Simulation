#ifndef OSCOPE_SCHEDULING_ROUND_ROBIN_HPP
#define OSCOPE_SCHEDULING_ROUND_ROBIN_HPP

#include "oscope/scheduling_algorithm.hpp"

namespace oscope {

class RoundRobin : public SchedulingAlgorithm {
public:
    explicit RoundRobin(int time_quantum);

    int time_quantum() const noexcept;

    SchedulingSimulationResult
    schedule(const std::vector<Process>& processes) override;

private:
    int time_quantum_;
};

} // namespace oscope

#endif // OSCOPE_SCHEDULING_ROUND_ROBIN_HPP
