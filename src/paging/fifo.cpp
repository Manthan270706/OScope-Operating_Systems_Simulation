#include "oscope/paging/fifo.hpp"

#include <algorithm>
#include <cstddef>
#include <stdexcept>
#include <utility>

namespace oscope {

PageReplacementResult
FIFO::simulate(const std::vector<int>& reference_string, int frame_count) {
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
    std::size_t victim_idx = 0;

    for (int page : reference_string) {
        PageReplacementStep step;
        step.page = page;

        auto it = std::find(current_frames.begin(), current_frames.end(), page);
        if (it != current_frames.end()) {
            // Page hit: frames remain unchanged, FIFO order is not modified
            step.is_fault = false;
            step.evicted_page = std::nullopt;
            result.page_hits++;
        } else {
            // Page fault: page is not currently in any physical frame
            step.is_fault = true;
            result.page_faults++;

            // Look for the first available empty slot (-1)
            auto empty_it = std::find(current_frames.begin(), current_frames.end(), -1);
            if (empty_it != current_frames.end()) {
                // Fill first available empty slot without advancing victim pointer
                *empty_it = page;
                step.evicted_page = std::nullopt;
            } else {
                // All frames are occupied; evict the oldest resident page (FIFO order)
                int evicted = current_frames[victim_idx];
                current_frames[victim_idx] = page;
                victim_idx = (victim_idx + 1) % static_cast<std::size_t>(frame_count);
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
