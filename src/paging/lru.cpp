#include "oscope/paging/lru.hpp"

#include <algorithm>
#include <cstddef>
#include <stdexcept>
#include <utility>
#include <vector>

namespace oscope {

PageReplacementResult
LRU::simulate(const std::vector<int>& reference_string, int frame_count) {
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
    // Track the last-referenced access timestamp for each frame slot
    std::vector<std::size_t> last_used_time(static_cast<std::size_t>(frame_count), 0);

    for (std::size_t time = 0; time < reference_string.size(); ++time) {
        int page = reference_string[time];
        PageReplacementStep step;
        step.page = page;

        // Check if page is currently resident in any frame slot
        auto it = std::find(current_frames.begin(), current_frames.end(), page);
        if (it != current_frames.end()) {
            // Page hit: update last-used timestamp for this frame slot
            std::size_t slot = static_cast<std::size_t>(std::distance(current_frames.begin(), it));
            last_used_time[slot] = time;
            step.is_fault = false;
            step.evicted_page = std::nullopt;
            result.page_hits++;
        } else {
            // Page fault: page is not resident
            step.is_fault = true;
            result.page_faults++;

            // Look for an available frame slot (-1)
            auto empty_it = std::find(current_frames.begin(), current_frames.end(), -1);
            if (empty_it != current_frames.end()) {
                // Load page into first available slot without eviction
                std::size_t slot = static_cast<std::size_t>(std::distance(current_frames.begin(), empty_it));
                current_frames[slot] = page;
                last_used_time[slot] = time;
                step.evicted_page = std::nullopt;
            } else {
                // All slots full; evict the page whose most recent reference is the oldest
                std::size_t lru_slot = 0;
                std::size_t min_time = last_used_time[0];
                for (std::size_t s = 1; s < static_cast<std::size_t>(frame_count); ++s) {
                    if (last_used_time[s] < min_time) {
                        min_time = last_used_time[s];
                        lru_slot = s;
                    }
                }

                int evicted = current_frames[lru_slot];
                current_frames[lru_slot] = page;
                last_used_time[lru_slot] = time;
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
