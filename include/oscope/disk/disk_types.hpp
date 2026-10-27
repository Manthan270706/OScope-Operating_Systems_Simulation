#ifndef OSCOPE_DISK_TYPES_HPP
#define OSCOPE_DISK_TYPES_HPP

#include <cstdint>
#include <string>
#include <vector>

namespace oscope::disk {

/**
 * @brief Direction of disk arm movement for direction-dependent algorithms.
 */
enum class Direction {
    Increasing = 1, // Higher cylinders / outward
    Decreasing = 2  // Lower cylinders / inward
};

/**
 * @brief Disk scheduling algorithm choices.
 */
enum class DiskAlgorithm {
    FCFS = 1,
    SSTF = 2,
    SCAN = 3,
    CSCAN = 4,
    LOOK = 5,
    CLOOK = 6
};

/**
 * @brief Configuration parameters for disk scheduling.
 */
struct DiskConfig {
    int min_cylinder = 0;
    int max_cylinder = 199;
    int initial_head = 53;
    Direction direction = Direction::Increasing;

    /**
     * @brief Validates cylinder range and initial head position.
     * @param error Output parameter for validation error description.
     * @return true if valid, false otherwise.
     */
    bool validate(std::string* error = nullptr) const;
};

/**
 * @brief Structured result for a disk scheduling simulation run.
 */
struct DiskSchedulingResult {
    DiskAlgorithm algorithm = DiskAlgorithm::FCFS;
    std::string algorithm_name;
    std::vector<int> serviced_requests;
    std::vector<int> head_path;
    int64_t total_head_movement = 0;
    int64_t wraparound_movement = 0;
    double average_head_movement = 0.0;
    int initial_head_position = 0;
    int final_head_position = 0;
    bool success = true;
    std::string message;
};

/**
 * @brief Result of comparing multiple disk scheduling algorithms on the same workload.
 */
struct DiskComparisonResult {
    std::vector<int> original_requests;
    DiskConfig config;
    std::vector<DiskSchedulingResult> results;
};

} // namespace oscope::disk

#endif // OSCOPE_DISK_TYPES_HPP
