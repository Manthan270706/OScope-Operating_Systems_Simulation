#ifndef OSCOPE_DEADLOCK_BANKERS_ALGORITHM_HPP
#define OSCOPE_DEADLOCK_BANKERS_ALGORITHM_HPP

#include "oscope/deadlock/deadlock_types.hpp"

namespace oscope::deadlock {

/**
 * @brief Executes the Banker's safety algorithm to determine whether the system is in a safe state.
 *
 * Evaluates the Work and Finish vectors. Finds processes whose Need <= Work, simulates their completion,
 * and adds their Allocation back to Work. Returns the full safe sequence if one exists.
 *
 * @param state The resource allocation and claim state to analyze.
 * @return SafetyResult containing safe status, sequence, and detailed diagnostic message.
 */
SafetyResult check_safety(const DeadlockState& state);

/**
 * @brief Simulates a resource allocation request from a process using the Banker's algorithm.
 *
 * Validates process ID, dimensions, nonnegative values, checks against Need and Available.
 * Tentatively allocates the resources, executes the safety algorithm, and commits the state
 * only if safe. If denied, leaves original state completely uncorrupted.
 *
 * @param current_state The current deadlock state (not mutated if request is denied).
 * @param process_id The index of the requesting process.
 * @param request The vector of requested resource counts.
 * @return ResourceRequestResult containing decision status, resulting state, and explanation.
 */
ResourceRequestResult request_resources(const DeadlockState& current_state,
                                        int process_id,
                                        const std::vector<int>& request);

} // namespace oscope::deadlock

#endif // OSCOPE_DEADLOCK_BANKERS_ALGORITHM_HPP
