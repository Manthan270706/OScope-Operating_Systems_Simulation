#include "oscope/paging/optimal.hpp"

#include <algorithm>
#include <cstddef>
#include <limits>
#include <stdexcept>
#include <utility>
#include <vector>

namespace oscope {

PageReplacementResult
Optimal::simulate(const std::vector<int>& reference_string, int frame_count) {
    if (frame_count <= 0) {
        throw std::invalid_argument("Frame count must be positive (> 0).");
    }

    for (int page : reference_string) {
        if (page < 0) {
            throw std::invalid_argument("Page number cannot be negative.");
        }
    }

    PageReplacementResult result;
    result.total_references = static_cast<int>(reference_string.size());

    if (reference_string.empty()) {
        return result;
    }

    // Allocate exactly frame_count frame slots, with -1 representing empty slots
    std::vector<int> current_frames(static_cast<std::size_t>(frame_count), -1);

    for (std::size_t time = 0; time < reference_string.size(); ++time) {
        int page = reference_string[time];
        PageReplacementStep step;
        step.page = page;

        // Check if page is currently resident in any frame slot
        auto it = std::find(current_frames.begin(), current_frames.end(), page);
        if (it != current_frames.end()) {
            // Page hit
            step.is_fault = false;
            step.evicted_page = std::nullopt;
            result.page_hits++;
        } else {
            // Page fault
            step.is_fault = true;
            result.page_faults++;

            // Look for the first available empty slot (-1)
            auto empty_it = std::find(current_frames.begin(), current_frames.end(), -1);
            if (empty_it != current_frames.end()) {
                *empty_it = page;
                step.evicted_page = std::nullopt;
            } else {
                // All slots are occupied; evict the page whose next reference is farthest in future
                std::size_t victim_slot = 0;
                std::size_t farthest_time = 0;

                for (std::size_t s = 0; s < static_cast<std::size_t>(frame_count); ++s) {
                    int resident_page = current_frames[s];
                    std::size_t next_use = std::numeric_limits<std::size_t>::max();

                    for (std::size_t future = time + 1; future < reference_string.size(); ++future) {
                        if (reference_string[future] == resident_page) {
                            next_use = future;
                            break;
                        }
                    }

                    if (next_use > farthest_time) {
                        farthest_time = next_use;
                        victim_slot = s;
                    }
                }

                int evicted = current_frames[victim_slot];
                current_frames[victim_slot] = page;
                step.evicted_page = evicted;
            }
        }

        step.frames = current_frames;
        result.steps.push_back(std::move(step));
    }

    if (result.total_references > 0) {
        result.fault_rate = static_cast<double>(result.page_faults) / result.total_references;
        result.hit_rate = static_cast<double>(result.page_hits) / result.total_references;
    }

    return result;
}

} // namespace oscope
