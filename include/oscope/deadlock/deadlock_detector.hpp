#ifndef OSCOPE_DEADLOCK_DETECTOR_HPP
#define OSCOPE_DEADLOCK_DETECTOR_HPP

#include "oscope/deadlock/deadlock_types.hpp"

namespace oscope::deadlock {

/**
 * @brief Executes the Deadlock Detection algorithm on active allocations and outstanding requests.
 *
 * Distinct from Banker's avoidance: evaluates whether existing processes with outstanding requests
 * can finish given current Available resources and already-held Allocations. Identifies processes
 * that cannot finish and reports the exact set of deadlocked processes.
 *
 * @param num_processes Number of processes in the system.
 * @param num_resources Number of resource types in the system.
 * @param available Currently available instances of each resource type.
 * @param allocation Current allocation matrix (num_processes x num_resources).
 * @param request Current outstanding request matrix (num_processes x num_resources).
 * @return DetectionResult containing deadlocked status, list of deadlocked processes, and message.
 */
DetectionResult detect_deadlock(int num_processes,
                                int num_resources,
                                const std::vector<int>& available,
                                const std::vector<std::vector<int>>& allocation,
                                const std::vector<std::vector<int>>& request);

} // namespace oscope::deadlock

#endif // OSCOPE_DEADLOCK_DETECTOR_HPP
