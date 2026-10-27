#ifndef OSCOPE_DEADLOCK_TYPES_HPP
#define OSCOPE_DEADLOCK_TYPES_HPP

#include <string>
#include <vector>

namespace oscope::deadlock {

/**
 * @brief Represents the state of resources and processes for deadlock management.
 */
struct DeadlockState {
    int num_processes = 0;
    int num_resources = 0;
    std::vector<int> available;
    std::vector<std::vector<int>> allocation;
    std::vector<std::vector<int>> max;
    std::vector<std::vector<int>> need;

    /**
     * @brief Validates state dimensions, nonnegative values, and that Allocation <= Max.
     * @param error Output parameter for validation error description.
     * @return true if valid, false otherwise.
     */
    bool validate(std::string* error = nullptr) const;

    /**
     * @brief Calculates or recalculates the Need matrix: Need[i][j] = Max[i][j] - Allocation[i][j].
     */
    void compute_need();
};

/**
 * @brief Result of Banker's safety algorithm analysis.
 */
struct SafetyResult {
    bool is_valid = false;
    bool is_safe = false;
    std::vector<int> safe_sequence;
    std::vector<int> blocked_processes;
    std::string message;
};

/**
 * @brief Status enumeration for resource-request simulation.
 */
enum class RequestStatus {
    Granted,
    DeniedExceedsNeed,
    DeniedExceedsAvailable,
    DeniedUnsafeState,
    InvalidRequest
};

/**
 * @brief Result of Banker's resource-request algorithm.
 */
struct ResourceRequestResult {
    RequestStatus status = RequestStatus::InvalidRequest;
    bool granted = false;
    int process_id = -1;
    std::vector<int> request;
    std::vector<int> safe_sequence;
    std::string message;
    DeadlockState resulting_state;
};

/**
 * @brief Result of Deadlock Detection algorithm.
 */
struct DetectionResult {
    bool is_valid = false;
    bool is_deadlocked = false;
    std::vector<int> deadlocked_processes;
    std::vector<int> finished_processes;
    std::string message;
};

} // namespace oscope::deadlock

#endif // OSCOPE_DEADLOCK_TYPES_HPP
