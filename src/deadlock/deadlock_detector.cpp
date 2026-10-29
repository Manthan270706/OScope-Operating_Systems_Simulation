#include "oscope/deadlock/deadlock_detector.hpp"

#include <sstream>

namespace oscope::deadlock {

DetectionResult detect_deadlock(int num_processes,
                                int num_resources,
                                const std::vector<int>& available,
                                const std::vector<std::vector<int>>& allocation,
                                const std::vector<std::vector<int>>& request) {
    DetectionResult result;

    if (num_processes <= 0) {
        result.is_valid = false;
        result.message = "Invalid process count: must be greater than 0.";
        return result;
    }
    if (num_resources <= 0) {
        result.is_valid = false;
        result.message = "Invalid resource count: must be greater than 0.";
        return result;
    }
    if (static_cast<int>(available.size()) != num_resources) {
        result.is_valid = false;
        result.message = "Available vector size does not match resource count.";
        return result;
    }
    for (int j = 0; j < num_resources; ++j) {
        if (available[j] < 0) {
            result.is_valid = false;
            result.message = "Available resource quantities cannot be negative.";
            return result;
        }
    }
    if (static_cast<int>(allocation.size()) != num_processes) {
        result.is_valid = false;
        result.message = "Allocation matrix row count does not match process count.";
        return result;
    }
    for (int i = 0; i < num_processes; ++i) {
        if (static_cast<int>(allocation[i].size()) != num_resources) {
            result.is_valid = false;
            result.message = "Allocation matrix column count does not match resource count.";
            return result;
        }
        for (int j = 0; j < num_resources; ++j) {
            if (allocation[i][j] < 0) {
                result.is_valid = false;
                result.message = "Allocation values cannot be negative.";
                return result;
            }
        }
    }
    if (static_cast<int>(request.size()) != num_processes) {
        result.is_valid = false;
        result.message = "Request matrix row count does not match process count.";
        return result;
    }
    for (int i = 0; i < num_processes; ++i) {
        if (static_cast<int>(request[i].size()) != num_resources) {
            result.is_valid = false;
            result.message = "Request matrix column count does not match resource count.";
            return result;
        }
        for (int j = 0; j < num_resources; ++j) {
            if (request[i][j] < 0) {
                result.is_valid = false;
                result.message = "Request values cannot be negative.";
                return result;
            }
        }
    }

    result.is_valid = true;
    std::vector<int> work = available;
    std::vector<bool> finish(num_processes, false);

    // Initialize finish vector: if a process holds no resources, it cannot contribute to deadlock
    for (int i = 0; i < num_processes; ++i) {
        bool holds_resources = false;
        for (int j = 0; j < num_resources; ++j) {
            if (allocation[i][j] > 0) {
                holds_resources = true;
                break;
            }
        }
        if (!holds_resources) {
            finish[i] = true;
            result.finished_processes.push_back(i);
        }
    }

    while (true) {
        bool found = false;
        for (int i = 0; i < num_processes; ++i) {
            if (!finish[i]) {
                bool can_satisfy = true;
                for (int j = 0; j < num_resources; ++j) {
                    if (request[i][j] > work[j]) {
                        can_satisfy = false;
                        break;
                    }
                }
                if (can_satisfy) {
                    for (int j = 0; j < num_resources; ++j) {
                        work[j] += allocation[i][j];
                    }
                    finish[i] = true;
                    result.finished_processes.push_back(i);
                    found = true;
                    break;
                }
            }
        }
        if (!found) {
            break;
        }
    }

    for (int i = 0; i < num_processes; ++i) {
        if (!finish[i]) {
            result.deadlocked_processes.push_back(i);
        }
    }

    if (result.deadlocked_processes.empty()) {
        result.is_deadlocked = false;
        result.message = "No deadlock detected. All active processes can acquire requested resources and complete.";
    } else {
        result.is_deadlocked = true;
        std::ostringstream oss;
        oss << "Deadlock detected! Deadlocked processes: [";
        for (size_t k = 0; k < result.deadlocked_processes.size(); ++k) {
            if (k > 0) oss << ", ";
            oss << "P" << result.deadlocked_processes[k];
        }
        oss << "].";
        result.message = oss.str();
    }

    return result;
}

} // namespace oscope::deadlock
