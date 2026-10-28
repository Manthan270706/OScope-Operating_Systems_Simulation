#include "oscope/paging/address_translation.hpp"

#include <algorithm>
#include <cmath>
#include <stdexcept>

namespace oscope::paging {

namespace {

bool is_power_of_two(uint64_t x) noexcept {
    return x > 0 && (x & (x - 1)) == 0;
}

} // namespace

AddressTranslator::AddressTranslator(uint64_t page_size) {
    if (!set_page_size(page_size)) {
        page_size_ = 4096;
    }
}

bool AddressTranslator::set_page_size(uint64_t size) {
    if (size == 0 || !is_power_of_two(size)) {
        return false;
    }
    page_size_ = size;
    return true;
}

void AddressTranslator::map_page(uint64_t page_number, int frame_number, bool dirty) {
    PageTableEntry entry;
    entry.frame_number = frame_number;
    entry.valid = true;
    entry.dirty = dirty;
    entry.referenced = true;
    page_table_[page_number] = entry;
}

bool AddressTranslator::unmap_page(uint64_t page_number) {
    auto it = page_table_.find(page_number);
    if (it == page_table_.end()) {
        return false;
    }
    it->second.valid = false;
    it->second.frame_number = -1;
    return true;
}

void AddressTranslator::clear_page_table() noexcept {
    page_table_.clear();
}

std::optional<PageTableEntry> AddressTranslator::get_entry(uint64_t page_number) const {
    auto it = page_table_.find(page_number);
    if (it != page_table_.end()) {
        return it->second;
    }
    return std::nullopt;
}

TranslationResult AddressTranslator::translate(uint64_t virtual_address) const {
    TranslationResult result;
    result.virtual_address = virtual_address;
    result.page_number = virtual_address / page_size_;
    result.offset = virtual_address % page_size_;

    auto it = page_table_.find(result.page_number);
    if (it != page_table_.end() && it->second.valid && it->second.frame_number >= 0) {
        result.page_fault = false;
        result.frame_number = it->second.frame_number;
        result.physical_address = static_cast<uint64_t>(result.frame_number) * page_size_ + result.offset;
        result.message = "Address translated successfully.";
    } else {
        result.page_fault = true;
        result.frame_number = -1;
        result.physical_address = 0;
        result.message = "Page fault: page " + std::to_string(result.page_number) + " is not resident in memory.";
    }

    return result;
}

DemandPagingResult AddressTranslator::simulate_demand_paging(
    uint64_t page_size,
    int num_frames,
    const std::vector<uint64_t>& virtual_addresses) {

    DemandPagingResult result;
    if (page_size == 0 || !is_power_of_two(page_size)) {
        page_size = 4096;
    }
    if (num_frames <= 0) {
        num_frames = 1;
    }

    result.page_size = page_size;
    result.total_frames = num_frames;
    result.total_accesses = static_cast<int>(virtual_addresses.size());

    std::vector<int> frame_contents(static_cast<size_t>(num_frames), -1);
    std::deque<int> fifo_order; // tracks page numbers in FIFO order
    std::unordered_map<int, int> page_to_frame;

    for (uint64_t va : virtual_addresses) {
        DemandPagingStep step;
        step.virtual_address = va;
        step.page_number = va / page_size;
        step.offset = va % page_size;

        int page_num = static_cast<int>(step.page_number);

        auto it = page_to_frame.find(page_num);
        if (it != page_to_frame.end()) {
            // Hit
            step.page_fault = false;
            step.frame_number = it->second;
            step.physical_address = static_cast<uint64_t>(step.frame_number) * page_size + step.offset;
            step.victim_page = -1;
            result.page_hits++;
        } else {
            // Page fault
            step.page_fault = true;
            result.page_faults++;

            // Find an empty frame if available
            int allocated_frame = -1;
            for (int f = 0; f < num_frames; ++f) {
                if (frame_contents[static_cast<size_t>(f)] == -1) {
                    allocated_frame = f;
                    break;
                }
            }

            if (allocated_frame != -1) {
                // Free frame available
                frame_contents[static_cast<size_t>(allocated_frame)] = page_num;
                page_to_frame[page_num] = allocated_frame;
                fifo_order.push_back(page_num);

                step.frame_number = allocated_frame;
                step.victim_page = -1;
            } else {
                // Evict victim via FIFO
                int victim = fifo_order.front();
                fifo_order.pop_front();

                int victim_frame = page_to_frame[victim];
                page_to_frame.erase(victim);

                frame_contents[static_cast<size_t>(victim_frame)] = page_num;
                page_to_frame[page_num] = victim_frame;
                fifo_order.push_back(page_num);

                step.frame_number = victim_frame;
                step.victim_page = victim;
            }

            step.physical_address = static_cast<uint64_t>(step.frame_number) * page_size + step.offset;
        }

        step.frame_contents = frame_contents;
        result.steps.push_back(step);
    }

    if (result.total_accesses > 0) {
        result.fault_rate = static_cast<double>(result.page_faults) / static_cast<double>(result.total_accesses);
    }

    return result;
}

ThrashingSimulationResult AddressTranslator::simulate_thrashing(
    const std::vector<int>& page_references,
    int min_frames,
    int max_frames) {

    ThrashingSimulationResult result;
    result.reference_string = page_references;

    if (min_frames < 1) min_frames = 1;
    if (max_frames < min_frames) max_frames = min_frames;

    std::vector<uint64_t> addresses;
    addresses.reserve(page_references.size());
    for (int p : page_references) {
        addresses.push_back(static_cast<uint64_t>(p) * 4096);
    }

    int prev_faults = -1;
    int max_drop = -1;
    int threshold = min_frames;

    for (int f = min_frames; f <= max_frames; ++f) {
        DemandPagingResult dp = simulate_demand_paging(4096, f, addresses);
        ThrashingDataPoint pt;
        pt.frames = f;
        pt.page_faults = dp.page_faults;
        pt.fault_rate = dp.fault_rate;
        result.points.push_back(pt);

        if (prev_faults != -1) {
            int drop = prev_faults - dp.page_faults;
            if (drop > max_drop) {
                max_drop = drop;
                threshold = f;
            }
        }
        prev_faults = dp.page_faults;
    }

    result.thrashing_threshold_frames = threshold;
    return result;
}

} // namespace oscope::paging
