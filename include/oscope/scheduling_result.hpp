#ifndef OSCOPE_SCHEDULING_RESULT_HPP
#define OSCOPE_SCHEDULING_RESULT_HPP

namespace oscope {

struct SchedulingResult {
    int pid;
    int completion_time;
    int turnaround_time;
    int waiting_time;
    int response_time;
};

} // namespace oscope

#endif // OSCOPE_SCHEDULING_RESULT_HPP
