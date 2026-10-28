#ifndef OSCOPE_EXPERIMENTS_PROCESS_LIFECYCLE_EXPERIMENT_HPP
#define OSCOPE_EXPERIMENTS_PROCESS_LIFECYCLE_EXPERIMENT_HPP

#include <string>
#include <sys/types.h>

namespace oscope::experiments {

struct ZombieDemonstrationResult {
    pid_t child_pid{0};
    char observed_state{'?'};
    bool zombie_observed{false};
    bool reaped_successfully{false};
    std::string details;
};

struct OrphanDemonstrationResult {
    pid_t child_pid{0};
    pid_t initial_parent_pid{0};
    pid_t adopted_parent_pid{0};
    bool reparented_to_init_or_subreaper{false};
    std::string details;
};

/**
 * @brief Demonstrates the creation of a zombie process and its subsequent reaping.
 */
ZombieDemonstrationResult run_zombie_demonstration();

/**
 * @brief Demonstrates process adoption/reparenting when the parent terminates before the child.
 */
OrphanDemonstrationResult run_orphan_demonstration();

} // namespace oscope::experiments

#endif // OSCOPE_EXPERIMENTS_PROCESS_LIFECYCLE_EXPERIMENT_HPP
