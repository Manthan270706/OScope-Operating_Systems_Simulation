#ifndef OSCOPE_PROCESS_STATE_HPP
#define OSCOPE_PROCESS_STATE_HPP

namespace oscope {

/**
 * @brief Represents the lifecycle states of a process.
 */
enum class ProcessState {
    New,
    Ready,
    Running,
    Waiting,
    Terminated
};

} // namespace oscope

#endif // OSCOPE_PROCESS_STATE_HPP
