#ifndef OSCOPE_PROCESS_HPP
#define OSCOPE_PROCESS_HPP

namespace oscope {

struct Process {
    int pid;
    int arrival_time;
    int burst_time;
    int priority;
};

} // namespace oscope

#endif // OSCOPE_PROCESS_HPP
