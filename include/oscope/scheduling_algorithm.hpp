#ifndef OSCOPE_SCHEDULING_ALGORITHM_HPP
#define OSCOPE_SCHEDULING_ALGORITHM_HPP

#include <vector>

#include "oscope/process.hpp"
#include "oscope/scheduling_simulation_result.hpp"

namespace oscope {

class SchedulingAlgorithm {
public:
    virtual ~SchedulingAlgorithm() = default;

    virtual SchedulingSimulationResult
    schedule(const std::vector<Process>& processes) = 0;
};

} // namespace oscope

#endif // OSCOPE_SCHEDULING_ALGORITHM_HPP
