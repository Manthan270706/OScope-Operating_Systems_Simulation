#ifndef OSCOPE_DISK_SCHEDULER_HPP
#define OSCOPE_DISK_SCHEDULER_HPP

#include "oscope/disk/disk_types.hpp"

namespace oscope::disk {

std::string to_string(DiskAlgorithm algo);
std::string to_string(Direction dir);

/**
 * @brief Validates a sequence of cylinder requests against the disk configuration.
 * @param requests Sequence of cylinder requests.
 * @param config Disk configuration.
 * @param error Output error message if validation fails.
 * @return true if valid, false otherwise.
 */
bool validate_disk_requests(const std::vector<int>& requests,
                            const DiskConfig& config,
                            std::string* error = nullptr);

DiskSchedulingResult schedule_fcfs(const std::vector<int>& requests, const DiskConfig& config);
DiskSchedulingResult schedule_sstf(const std::vector<int>& requests, const DiskConfig& config);
DiskSchedulingResult schedule_scan(const std::vector<int>& requests, const DiskConfig& config);
DiskSchedulingResult schedule_cscan(const std::vector<int>& requests, const DiskConfig& config);
DiskSchedulingResult schedule_look(const std::vector<int>& requests, const DiskConfig& config);
DiskSchedulingResult schedule_clook(const std::vector<int>& requests, const DiskConfig& config);
DiskSchedulingResult schedule_lifo(const std::vector<int>& requests, const DiskConfig& config);

/**
 * @brief Dispatches the specified disk scheduling algorithm.
 */
DiskSchedulingResult schedule_disk(DiskAlgorithm algo,
                                   const std::vector<int>& requests,
                                   const DiskConfig& config);

/**
 * @brief Evaluates all 6 disk scheduling algorithms on the exact same input without mutating it.
 */
DiskComparisonResult compare_all_disk(const std::vector<int>& requests,
                                      const DiskConfig& config);

} // namespace oscope::disk

#endif // OSCOPE_DISK_SCHEDULER_HPP
