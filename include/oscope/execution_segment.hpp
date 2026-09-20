#ifndef OSCOPE_EXECUTION_SEGMENT_HPP
#define OSCOPE_EXECUTION_SEGMENT_HPP

namespace oscope {

struct ExecutionSegment {
    int pid;
    int start_time;
    int end_time;
};

} // namespace oscope

#endif // OSCOPE_EXECUTION_SEGMENT_HPP
