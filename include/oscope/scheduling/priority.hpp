#ifndef OSCOPE_SCHEDULING_PRIORITY_HPP
#define OSCOPE_SCHEDULING_PRIORITY_HPP

#include "oscope/scheduling_algorithm.hpp"

namespace oscope {

class Priority : public SchedulingAlgorithm {
public:
    SchedulingSimulationResult
    schedule(const std::vector<Process>& processes) override;
};

} // namespace oscope

#endif // OSCOPE_SCHEDULING_PRIORITY_HPP
