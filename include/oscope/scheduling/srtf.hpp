#ifndef OSCOPE_SCHEDULING_SRTF_HPP
#define OSCOPE_SCHEDULING_SRTF_HPP

#include "oscope/scheduling_algorithm.hpp"

namespace oscope {

class SRTF : public SchedulingAlgorithm {
public:
    SchedulingSimulationResult
    schedule(const std::vector<Process>& processes) override;
};

} // namespace oscope

#endif // OSCOPE_SCHEDULING_SRTF_HPP
