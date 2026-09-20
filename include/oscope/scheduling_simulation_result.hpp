#ifndef OSCOPE_SCHEDULING_SIMULATION_RESULT_HPP
#define OSCOPE_SCHEDULING_SIMULATION_RESULT_HPP

#include <vector>

#include "oscope/execution_segment.hpp"
#include "oscope/scheduling_result.hpp"

namespace oscope {

struct SchedulingSimulationResult {
    std::vector<SchedulingResult> process_results;
    std::vector<ExecutionSegment> timeline;
};

} // namespace oscope

#endif // OSCOPE_SCHEDULING_SIMULATION_RESULT_HPP

