#include "oscope/deadlock/bankers_algorithm.hpp"

#include <sstream>

namespace oscope::deadlock {

bool DeadlockState::validate(std::string* error) const {
    if (num_processes <= 0) {
        if (error) *error = "Invalid process count: must be greater than 0.";
        return false;
    }
    if (num_resources <= 0) {
        if (error) *error = "Invalid resource count: must be greater than 0.";
        return false;
    }
    if (static_cast<int>(available.size()) != num_resources) {
        if (error) *error = "Available vector size does not match resource count.";
        return false;
    }
    for (int j = 0; j < num_resources; ++j) {
        if (available[j] < 0) {
            if (error) *error = "Available resource count cannot be negative.";
            return false;
        }
    }
    if (static_cast<int>(allocation.size()) != num_processes) {
        if (error) *error = "Allocation matrix row count does not match process count.";
        return false;
    }
    for (int i = 0; i < num_processes; ++i) {
        if (static_cast<int>(allocation[i].size()) != num_resources) {
            if (error) *error = "Allocation matrix column count does not match resource count.";
            return false;
        }
        for (int j = 0; j < num_resources; ++j) {
            if (allocation[i][j] < 0) {
                if (error) *error = "Allocation values cannot be negative.";
                return false;
            }
        }
    }
    if (static_cast<int>(max.size()) != num_processes) {
        if (error) *error = "Max matrix row count does not match process count.";
        return false;
    }
    for (int i = 0; i < num_processes; ++i) {
        if (static_cast<int>(max[i].size()) != num_resources) {
            if (error) *error = "Max matrix column count does not match resource count.";
            return false;
        }
        for (int j = 0; j < num_resources; ++j) {
            if (max[i][j] < 0) {
                if (error) *error = "Max matrix values cannot be negative.";
                return false;
            }
            if (allocation[i][j] > max[i][j]) {
                if (error) {
                    std::ostringstream oss;
                    oss << "Process " << i << " allocation (" << allocation[i][j]
                        << ") exceeds maximum claim (" << max[i][j]
                        << ") for resource " << j << ".";
                    *error = oss.str();
                }
                return false;
            }
        }
    }
    return true;
}

void DeadlockState::compute_need() {
    need.assign(num_processes, std::vector<int>(num_resources, 0));
    for (int i = 0; i < num_processes; ++i) {
        for (int j = 0; j < num_resources; ++j) {
            need[i][j] = max[i][j] - allocation[i][j];
        }
    }
}

SafetyResult check_safety(const DeadlockState& state) {
    SafetyResult result;
    std::string err;
    if (!state.validate(&err)) {
        result.is_valid = false;
        result.is_safe = false;
        result.message = err;
        return result;
    }
    result.is_valid = true;

    // Use current need matrix if populated and valid, otherwise compute it
    std::vector<std::vector<int>> need_matrix = state.need;
    if (static_cast<int>(need_matrix.size()) != state.num_processes) {
        need_matrix.assign(state.num_processes, std::vector<int>(state.num_resources, 0));
        for (int i = 0; i < state.num_processes; ++i) {
            for (int j = 0; j < state.num_resources; ++j) {
                need_matrix[i][j] = state.max[i][j] - state.allocation[i][j];
            }
        }
    }

    std::vector<int> work = state.available;
    std::vector<bool> finish(state.num_processes, false);
    result.safe_sequence.clear();
    result.safe_sequence.reserve(state.num_processes);

    while (true) {
        bool found = false;
        for (int i = 0; i < state.num_processes; ++i) {
            if (!finish[i]) {
                bool can_finish = true;
                for (int j = 0; j < state.num_resources; ++j) {
                    if (need_matrix[i][j] > work[j]) {
                        can_finish = false;
                        break;
                    }
                }
                if (can_finish) {
                    for (int j = 0; j < state.num_resources; ++j) {
                        work[j] += state.allocation[i][j];
                    }
                    finish[i] = true;
                    result.safe_sequence.push_back(i);
                    found = true;
                    break; // Restart scan from beginning to maintain deterministic lowest-index preference
                }
            }
        }
        if (!found) {
            break;
        }
    }

    if (static_cast<int>(result.safe_sequence.size()) == state.num_processes) {
        result.is_safe = true;
        result.message = "System is in a safe state.";
    } else {
        result.is_safe = false;
        for (int i = 0; i < state.num_processes; ++i) {
            if (!finish[i]) {
                result.blocked_processes.push_back(i);
            }
        }
        std::ostringstream oss;
        oss << "System is in an unsafe state. Unfinished processes: [";
        for (size_t k = 0; k < result.blocked_processes.size(); ++k) {
            if (k > 0) oss << ", ";
            oss << "P" << result.blocked_processes[k];
        }
        oss << "].";
        result.message = oss.str();
    }

    return result;
}

ResourceRequestResult request_resources(const DeadlockState& current_state,
                                        int process_id,
                                        const std::vector<int>& request) {
    ResourceRequestResult result;
    result.process_id = process_id;
    result.request = request;
    result.resulting_state = current_state;

    std::string err;
    if (!current_state.validate(&err)) {
        result.status = RequestStatus::InvalidRequest;
        result.granted = false;
        result.message = "Invalid system state: " + err;
        return result;
    }

    if (process_id < 0 || process_id >= current_state.num_processes) {
        result.status = RequestStatus::InvalidRequest;
        result.granted = false;
        result.message = "Invalid process ID: out of range.";
        return result;
    }

    if (static_cast<int>(request.size()) != current_state.num_resources) {
        result.status = RequestStatus::InvalidRequest;
        result.granted = false;
        result.message = "Request vector dimension does not match resource count.";
        return result;
    }

    for (int j = 0; j < current_state.num_resources; ++j) {
        if (request[j] < 0) {
            result.status = RequestStatus::InvalidRequest;
            result.granted = false;
            result.message = "Requested resource quantities cannot be negative.";
            return result;
        }
    }

    // Ensure need matrix is available
    DeadlockState working_state = current_state;
    working_state.compute_need();

    // Check 1: Request <= Need
    for (int j = 0; j < current_state.num_resources; ++j) {
        if (request[j] > working_state.need[process_id][j]) {
            result.status = RequestStatus::DeniedExceedsNeed;
            result.granted = false;
            std::ostringstream oss;
            oss << "Process P" << process_id << " requested " << request[j]
                << " units of resource R" << j
                << ", which exceeds its maximum declared need of "
                << working_state.need[process_id][j] << ".";
            result.message = oss.str();
            return result;
        }
    }

    // Check 2: Request <= Available
    for (int j = 0; j < current_state.num_resources; ++j) {
        if (request[j] > working_state.available[j]) {
            result.status = RequestStatus::DeniedExceedsAvailable;
            result.granted = false;
            std::ostringstream oss;
            oss << "Process P" << process_id << " must wait: requested " << request[j]
                << " units of resource R" << j
                << ", but only " << working_state.available[j]
                << " units are currently available.";
            result.message = oss.str();
            return result;
        }
    }

    // Tentative allocation
    DeadlockState tentative_state = working_state;
    for (int j = 0; j < current_state.num_resources; ++j) {
        tentative_state.available[j] -= request[j];
        tentative_state.allocation[process_id][j] += request[j];
        tentative_state.need[process_id][j] -= request[j];
    }

    // Check safety of tentative state
    SafetyResult safety = check_safety(tentative_state);
    if (safety.is_safe) {
        result.status = RequestStatus::Granted;
        result.granted = true;
        result.safe_sequence = safety.safe_sequence;
        result.resulting_state = tentative_state;
        result.message = "Request granted. System remains in a safe state.";
    } else {
        result.status = RequestStatus::DeniedUnsafeState;
        result.granted = false;
        result.resulting_state = current_state; // Leave original state completely uncorrupted
        result.message = "Request denied. Granting this request would leave the system in an unsafe state.";
    }

    return result;
}

} // namespace oscope::deadlock
