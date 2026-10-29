#ifndef OSCOPE_SCHEDULING_MLFQ_HPP
#define OSCOPE_SCHEDULING_MLFQ_HPP

#include "oscope/scheduling_algorithm.hpp"

namespace oscope {

class MLFQ : public SchedulingAlgorithm {
public:
    explicit MLFQ(int q0, int q1, int q2);

    int q0() const noexcept;
    int q1() const noexcept;
    int q2() const noexcept;

    SchedulingSimulationResult
    schedule(const std::vector<Process>& processes) override;

private:
    int q0_;
    int q1_;
    int q2_;
};

} // namespace oscope

#endif // OSCOPE_SCHEDULING_MLFQ_HPP
