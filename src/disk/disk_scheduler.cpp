#include "oscope/disk/disk_scheduler.hpp"

#include <algorithm>
#include <cmath>
#include <sstream>

namespace oscope::disk {

std::string to_string(DiskAlgorithm algo) {
    switch (algo) {
        case DiskAlgorithm::FCFS: return "First-Come, First-Served (FCFS)";
        case DiskAlgorithm::SSTF: return "Shortest Seek Time First (SSTF)";
        case DiskAlgorithm::SCAN: return "SCAN (Elevator)";
        case DiskAlgorithm::CSCAN: return "Circular SCAN (C-SCAN)";
        case DiskAlgorithm::LOOK: return "LOOK";
        case DiskAlgorithm::CLOOK: return "Circular LOOK (C-LOOK)";
    }
    return "Unknown";
}

std::string to_string(Direction dir) {
    switch (dir) {
        case Direction::Increasing: return "Increasing (Higher cylinders)";
        case Direction::Decreasing: return "Decreasing (Lower cylinders)";
    }
    return "Unknown";
}

bool DiskConfig::validate(std::string* error) const {
    if (min_cylinder < 0) {
        if (error) *error = "Minimum cylinder cannot be negative.";
        return false;
    }
    if (max_cylinder <= min_cylinder) {
        if (error) *error = "Maximum cylinder must be strictly greater than minimum cylinder.";
        return false;
    }
    if (initial_head < min_cylinder || initial_head > max_cylinder) {
        if (error) {
            std::ostringstream oss;
            oss << "Initial head position (" << initial_head
                << ") must be within valid cylinder range ["
                << min_cylinder << ", " << max_cylinder << "].";
            *error = oss.str();
        }
        return false;
    }
    return true;
}

bool validate_disk_requests(const std::vector<int>& requests,
                            const DiskConfig& config,
                            std::string* error) {
    if (!config.validate(error)) {
        return false;
    }
    for (size_t i = 0; i < requests.size(); ++i) {
        int req = requests[i];
        if (req < config.min_cylinder || req > config.max_cylinder) {
            if (error) {
                std::ostringstream oss;
                oss << "Request #" << (i + 1) << " cylinder (" << req
                    << ") is out of valid range [" << config.min_cylinder
                    << ", " << config.max_cylinder << "].";
                *error = oss.str();
            }
            return false;
        }
    }
    return true;
}

namespace {

void populate_metrics(DiskSchedulingResult& result, size_t request_count) {
    result.total_head_movement = 0;
    for (size_t i = 1; i < result.head_path.size(); ++i) {
        int64_t diff = std::abs(static_cast<int64_t>(result.head_path[i]) -
                                static_cast<int64_t>(result.head_path[i - 1]));
        result.total_head_movement += diff;
    }

    if (request_count > 0) {
        result.average_head_movement =
            static_cast<double>(result.total_head_movement) / static_cast<double>(request_count);
    } else {
        result.average_head_movement = 0.0;
    }

    result.initial_head_position = result.head_path.empty() ? 0 : result.head_path.front();
    result.final_head_position = result.head_path.empty() ? 0 : result.head_path.back();
}

DiskSchedulingResult handle_empty_or_invalid(DiskAlgorithm algo,
                                             const std::vector<int>& requests,
                                             const DiskConfig& config,
                                             bool is_invalid,
                                             const std::string& error_msg) {
    DiskSchedulingResult res;
    res.algorithm = algo;
    res.algorithm_name = to_string(algo);
    if (is_invalid) {
        res.success = false;
        res.message = error_msg;
        return res;
    }

    // Valid empty workload
    res.success = true;
    res.head_path = {config.initial_head};
    res.initial_head_position = config.initial_head;
    res.final_head_position = config.initial_head;
    res.total_head_movement = 0;
    res.wraparound_movement = 0;
    res.average_head_movement = 0.0;
    res.message = "Workload contains 0 cylinder requests; head remains stationary.";
    return res;
}

} // namespace

DiskSchedulingResult schedule_fcfs(const std::vector<int>& requests, const DiskConfig& config) {
    std::string err;
    if (!validate_disk_requests(requests, config, &err)) {
        return handle_empty_or_invalid(DiskAlgorithm::FCFS, requests, config, true, err);
    }
    if (requests.empty()) {
        return handle_empty_or_invalid(DiskAlgorithm::FCFS, requests, config, false, "");
    }

    DiskSchedulingResult res;
    res.algorithm = DiskAlgorithm::FCFS;
    res.algorithm_name = to_string(DiskAlgorithm::FCFS);
    res.serviced_requests = requests;
    res.head_path.reserve(requests.size() + 1);
    res.head_path.push_back(config.initial_head);

    for (int req : requests) {
        res.head_path.push_back(req);
    }

    populate_metrics(res, requests.size());
    res.success = true;
    res.message = "FCFS scheduling completed successfully.";
    return res;
}

DiskSchedulingResult schedule_sstf(const std::vector<int>& requests, const DiskConfig& config) {
    std::string err;
    if (!validate_disk_requests(requests, config, &err)) {
        return handle_empty_or_invalid(DiskAlgorithm::SSTF, requests, config, true, err);
    }
    if (requests.empty()) {
        return handle_empty_or_invalid(DiskAlgorithm::SSTF, requests, config, false, "");
    }

    DiskSchedulingResult res;
    res.algorithm = DiskAlgorithm::SSTF;
    res.algorithm_name = to_string(DiskAlgorithm::SSTF);
    res.head_path.push_back(config.initial_head);

    std::vector<int> pending = requests;
    int current_head = config.initial_head;

    while (!pending.empty()) {
        size_t best_idx = 0;
        int min_dist = std::abs(pending[0] - current_head);

        for (size_t i = 1; i < pending.size(); ++i) {
            int dist = std::abs(pending[i] - current_head);
            if (dist < min_dist) {
                min_dist = dist;
                best_idx = i;
            } else if (dist == min_dist) {
                // Deterministic tie-breaker: prefer lowest cylinder number
                if (pending[i] < pending[best_idx]) {
                    best_idx = i;
                }
            }
        }

        int next_cyl = pending[best_idx];
        res.serviced_requests.push_back(next_cyl);
        res.head_path.push_back(next_cyl);
        current_head = next_cyl;
        pending.erase(pending.begin() + best_idx);
    }

    populate_metrics(res, requests.size());
    res.success = true;
    res.message = "SSTF scheduling completed successfully.";
    return res;
}

DiskSchedulingResult schedule_scan(const std::vector<int>& requests, const DiskConfig& config) {
    std::string err;
    if (!validate_disk_requests(requests, config, &err)) {
        return handle_empty_or_invalid(DiskAlgorithm::SCAN, requests, config, true, err);
    }
    if (requests.empty()) {
        return handle_empty_or_invalid(DiskAlgorithm::SCAN, requests, config, false, "");
    }

    DiskSchedulingResult res;
    res.algorithm = DiskAlgorithm::SCAN;
    res.algorithm_name = to_string(DiskAlgorithm::SCAN);
    res.head_path.push_back(config.initial_head);

    std::vector<int> greater_or_equal;
    std::vector<int> lesser;

    for (int req : requests) {
        if (req >= config.initial_head) {
            greater_or_equal.push_back(req);
        } else {
            lesser.push_back(req);
        }
    }

    std::sort(greater_or_equal.begin(), greater_or_equal.end());
    std::sort(lesser.begin(), lesser.end(), std::greater<int>());

    if (config.direction == Direction::Increasing) {
        for (int r : greater_or_equal) {
            res.serviced_requests.push_back(r);
            res.head_path.push_back(r);
        }
        if (!lesser.empty()) {
            if (res.head_path.back() != config.max_cylinder) {
                res.head_path.push_back(config.max_cylinder);
            }
            for (int r : lesser) {
                res.serviced_requests.push_back(r);
                res.head_path.push_back(r);
            }
            if (res.head_path.back() != config.min_cylinder) {
                res.head_path.push_back(config.min_cylinder);
            }
        }
    } else { // Decreasing
        for (int r : lesser) {
            res.serviced_requests.push_back(r);
            res.head_path.push_back(r);
        }
        if (!greater_or_equal.empty()) {
            if (res.head_path.back() != config.min_cylinder) {
                res.head_path.push_back(config.min_cylinder);
            }
            // Service remaining in increasing order
            std::sort(greater_or_equal.begin(), greater_or_equal.end());
            for (int r : greater_or_equal) {
                res.serviced_requests.push_back(r);
                res.head_path.push_back(r);
            }
            if (res.head_path.back() != config.max_cylinder) {
                res.head_path.push_back(config.max_cylinder);
            }
        }
    }

    populate_metrics(res, requests.size());
    res.success = true;
    res.message = "SCAN (Elevator) scheduling completed successfully.";
    return res;
}

DiskSchedulingResult schedule_cscan(const std::vector<int>& requests, const DiskConfig& config) {
    std::string err;
    if (!validate_disk_requests(requests, config, &err)) {
        return handle_empty_or_invalid(DiskAlgorithm::CSCAN, requests, config, true, err);
    }
    if (requests.empty()) {
        return handle_empty_or_invalid(DiskAlgorithm::CSCAN, requests, config, false, "");
    }

    DiskSchedulingResult res;
    res.algorithm = DiskAlgorithm::CSCAN;
    res.algorithm_name = to_string(DiskAlgorithm::CSCAN);
    res.head_path.push_back(config.initial_head);

    std::vector<int> greater_or_equal;
    std::vector<int> lesser;

    for (int req : requests) {
        if (req >= config.initial_head) {
            greater_or_equal.push_back(req);
        } else {
            lesser.push_back(req);
        }
    }

    if (config.direction == Direction::Increasing) {
        std::sort(greater_or_equal.begin(), greater_or_equal.end());
        std::sort(lesser.begin(), lesser.end());

        for (int r : greater_or_equal) {
            res.serviced_requests.push_back(r);
            res.head_path.push_back(r);
        }
        if (!lesser.empty()) {
            if (res.head_path.back() != config.max_cylinder) {
                res.head_path.push_back(config.max_cylinder);
            }
            res.head_path.push_back(config.min_cylinder);
            res.wraparound_movement = config.max_cylinder - config.min_cylinder;

            for (int r : lesser) {
                res.serviced_requests.push_back(r);
                res.head_path.push_back(r);
            }
        }
    } else { // Decreasing
        std::sort(lesser.begin(), lesser.end(), std::greater<int>());
        std::sort(greater_or_equal.begin(), greater_or_equal.end(), std::greater<int>());

        for (int r : lesser) {
            res.serviced_requests.push_back(r);
            res.head_path.push_back(r);
        }
        if (!greater_or_equal.empty()) {
            if (res.head_path.back() != config.min_cylinder) {
                res.head_path.push_back(config.min_cylinder);
            }
            res.head_path.push_back(config.max_cylinder);
            res.wraparound_movement = config.max_cylinder - config.min_cylinder;

            for (int r : greater_or_equal) {
                res.serviced_requests.push_back(r);
                res.head_path.push_back(r);
            }
        }
    }

    populate_metrics(res, requests.size());
    res.success = true;
    res.message = "C-SCAN scheduling completed successfully.";
    return res;
}

DiskSchedulingResult schedule_look(const std::vector<int>& requests, const DiskConfig& config) {
    std::string err;
    if (!validate_disk_requests(requests, config, &err)) {
        return handle_empty_or_invalid(DiskAlgorithm::LOOK, requests, config, true, err);
    }
    if (requests.empty()) {
        return handle_empty_or_invalid(DiskAlgorithm::LOOK, requests, config, false, "");
    }

    DiskSchedulingResult res;
    res.algorithm = DiskAlgorithm::LOOK;
    res.algorithm_name = to_string(DiskAlgorithm::LOOK);
    res.head_path.push_back(config.initial_head);

    std::vector<int> greater_or_equal;
    std::vector<int> lesser;

    for (int req : requests) {
        if (req >= config.initial_head) {
            greater_or_equal.push_back(req);
        } else {
            lesser.push_back(req);
        }
    }

    if (config.direction == Direction::Increasing) {
        std::sort(greater_or_equal.begin(), greater_or_equal.end());
        std::sort(lesser.begin(), lesser.end(), std::greater<int>());

        for (int r : greater_or_equal) {
            res.serviced_requests.push_back(r);
            res.head_path.push_back(r);
        }
        // Reverses directly from the highest request, without visiting max_cylinder
        for (int r : lesser) {
            res.serviced_requests.push_back(r);
            res.head_path.push_back(r);
        }
    } else { // Decreasing
        std::sort(lesser.begin(), lesser.end(), std::greater<int>());
        std::sort(greater_or_equal.begin(), greater_or_equal.end());

        for (int r : lesser) {
            res.serviced_requests.push_back(r);
            res.head_path.push_back(r);
        }
        // Reverses directly from the lowest request, without visiting min_cylinder
        for (int r : greater_or_equal) {
            res.serviced_requests.push_back(r);
            res.head_path.push_back(r);
        }
    }

    populate_metrics(res, requests.size());
    res.success = true;
    res.message = "LOOK scheduling completed successfully.";
    return res;
}

DiskSchedulingResult schedule_clook(const std::vector<int>& requests, const DiskConfig& config) {
    std::string err;
    if (!validate_disk_requests(requests, config, &err)) {
        return handle_empty_or_invalid(DiskAlgorithm::CLOOK, requests, config, true, err);
    }
    if (requests.empty()) {
        return handle_empty_or_invalid(DiskAlgorithm::CLOOK, requests, config, false, "");
    }

    DiskSchedulingResult res;
    res.algorithm = DiskAlgorithm::CLOOK;
    res.algorithm_name = to_string(DiskAlgorithm::CLOOK);
    res.head_path.push_back(config.initial_head);

    std::vector<int> greater_or_equal;
    std::vector<int> lesser;

    for (int req : requests) {
        if (req >= config.initial_head) {
            greater_or_equal.push_back(req);
        } else {
            lesser.push_back(req);
        }
    }

    if (config.direction == Direction::Increasing) {
        std::sort(greater_or_equal.begin(), greater_or_equal.end());
        std::sort(lesser.begin(), lesser.end());

        for (int r : greater_or_equal) {
            res.serviced_requests.push_back(r);
            res.head_path.push_back(r);
        }
        if (!lesser.empty()) {
            // Jump directly from highest served request to lowest pending request
            int highest_served = res.head_path.back();
            int lowest_pending = lesser.front();
            res.wraparound_movement = std::abs(highest_served - lowest_pending);

            for (int r : lesser) {
                res.serviced_requests.push_back(r);
                res.head_path.push_back(r);
            }
        }
    } else { // Decreasing
        std::sort(lesser.begin(), lesser.end(), std::greater<int>());
        std::sort(greater_or_equal.begin(), greater_or_equal.end(), std::greater<int>());

        for (int r : lesser) {
            res.serviced_requests.push_back(r);
            res.head_path.push_back(r);
        }
        if (!greater_or_equal.empty()) {
            // Jump directly from lowest served request to highest pending request
            int lowest_served = res.head_path.back();
            int highest_pending = greater_or_equal.front();
            res.wraparound_movement = std::abs(highest_pending - lowest_served);

            for (int r : greater_or_equal) {
                res.serviced_requests.push_back(r);
                res.head_path.push_back(r);
            }
        }
    }

    populate_metrics(res, requests.size());
    res.success = true;
    res.message = "C-LOOK scheduling completed successfully.";
    return res;
}

DiskSchedulingResult schedule_disk(DiskAlgorithm algo,
                                   const std::vector<int>& requests,
                                   const DiskConfig& config) {
    switch (algo) {
        case DiskAlgorithm::FCFS: return schedule_fcfs(requests, config);
        case DiskAlgorithm::SSTF: return schedule_sstf(requests, config);
        case DiskAlgorithm::SCAN: return schedule_scan(requests, config);
        case DiskAlgorithm::CSCAN: return schedule_cscan(requests, config);
        case DiskAlgorithm::LOOK: return schedule_look(requests, config);
        case DiskAlgorithm::CLOOK: return schedule_clook(requests, config);
    }
    return handle_empty_or_invalid(algo, requests, config, true, "Unknown disk scheduling algorithm.");
}

DiskComparisonResult compare_all_disk(const std::vector<int>& requests,
                                      const DiskConfig& config) {
    DiskComparisonResult comparison;
    comparison.original_requests = requests;
    comparison.config = config;

    comparison.results.push_back(schedule_fcfs(requests, config));
    comparison.results.push_back(schedule_sstf(requests, config));
    comparison.results.push_back(schedule_scan(requests, config));
    comparison.results.push_back(schedule_cscan(requests, config));
    comparison.results.push_back(schedule_look(requests, config));
    comparison.results.push_back(schedule_clook(requests, config));

    return comparison;
}

} // namespace oscope::disk
