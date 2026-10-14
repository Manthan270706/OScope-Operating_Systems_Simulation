#include "oscope/memory/memory_manager.hpp"

#include <cstddef>
#include <limits>
#include <stdexcept>
#include <utility>

namespace oscope::memory {

MemoryManager::MemoryManager(std::size_t total_memory, AllocationStrategy default_strategy)
    : total_memory_(total_memory), strategy_(default_strategy) {
    if (total_memory == 0) {
        throw std::invalid_argument("Total memory size must be positive (> 0).");
    }
    reset();
}

AllocationStrategy MemoryManager::strategy() const noexcept {
    return strategy_;
}

void MemoryManager::set_strategy(AllocationStrategy strategy) noexcept {
    strategy_ = strategy;
}

void MemoryManager::reset() {
    blocks_.clear();
    MemoryBlock initial_block;
    initial_block.allocation_id = std::nullopt;
    initial_block.start_address = 0;
    initial_block.size = total_memory_;
    initial_block.is_allocated = false;
    initial_block.process_id = std::nullopt;
    blocks_.push_back(initial_block);
}

std::optional<std::size_t> MemoryManager::find_block(std::size_t size,
                                                     AllocationStrategy strategy) const {
    std::optional<std::size_t> chosen_idx = std::nullopt;

    for (std::size_t i = 0; i < blocks_.size(); ++i) {
        if (blocks_[i].is_allocated || blocks_[i].size < size) {
            continue;
        }

        switch (strategy) {
            case AllocationStrategy::FirstFit:
                return i;

            case AllocationStrategy::BestFit:
                if (!chosen_idx.has_value() || blocks_[i].size < blocks_[*chosen_idx].size) {
                    chosen_idx = i;
                }
                break;

            case AllocationStrategy::WorstFit:
                if (!chosen_idx.has_value() || blocks_[i].size > blocks_[*chosen_idx].size) {
                    chosen_idx = i;
                }
                break;
        }
    }

    return chosen_idx;
}

AllocationResult MemoryManager::allocate(std::size_t size, std::optional<int> process_id) {
    return allocate(size, strategy_, process_id);
}

AllocationResult MemoryManager::allocate(std::size_t size, std::optional<int> process_id,
                                         AllocationStrategy strategy) {
    return allocate(size, strategy, process_id);
}

AllocationResult MemoryManager::allocate(std::size_t size, AllocationStrategy strategy,
                                         std::optional<int> process_id) {
    if (size == 0) {
        return AllocationResult{false, std::nullopt, 0, 0, "Allocation size must be positive (> 0)."};
    }

    if (size > total_memory_) {
        return AllocationResult{false, std::nullopt, 0, 0, "Requested size exceeds total memory capacity."};
    }

    if (ids_exhausted_) {
        return AllocationResult{false, std::nullopt, 0, 0, "Allocation ID capacity exhausted."};
    }

    auto target_idx = find_block(size, strategy);
    if (!target_idx.has_value()) {
        return AllocationResult{false, std::nullopt, 0, 0, "Insufficient contiguous free memory."};
    }

    std::size_t i = *target_idx;
    std::size_t start = blocks_[i].start_address;
    std::size_t avail = blocks_[i].size;
    int alloc_id = next_allocation_id_;

    if (next_allocation_id_ == std::numeric_limits<int>::max()) {
        ids_exhausted_ = true;
    } else {
        ++next_allocation_id_;
    }

    if (avail == size) {
        // Exact fit: do not split, avoid creating a zero-sized block
        blocks_[i].is_allocated = true;
        blocks_[i].allocation_id = alloc_id;
        blocks_[i].process_id = process_id;
    } else {
        // Split block into allocated portion and free remainder
        blocks_[i].size = size;
        blocks_[i].is_allocated = true;
        blocks_[i].allocation_id = alloc_id;
        blocks_[i].process_id = process_id;

        MemoryBlock remainder;
        remainder.allocation_id = std::nullopt;
        remainder.start_address = start + size;
        remainder.size = avail - size;
        remainder.is_allocated = false;
        remainder.process_id = std::nullopt;

        blocks_.insert(blocks_.begin() + static_cast<std::ptrdiff_t>(i + 1), remainder);
    }

    return AllocationResult{true, alloc_id, start, size, ""};
}

bool MemoryManager::deallocate(int allocation_id) {
    if (allocation_id <= 0) {
        return false;
    }

    std::size_t target_idx = blocks_.size();
    for (std::size_t i = 0; i < blocks_.size(); ++i) {
        if (blocks_[i].is_allocated && blocks_[i].allocation_id == allocation_id) {
            target_idx = i;
            break;
        }
    }

    if (target_idx == blocks_.size()) {
        return false;
    }

    blocks_[target_idx].is_allocated = false;
    blocks_[target_idx].allocation_id = std::nullopt;
    blocks_[target_idx].process_id = std::nullopt;

    // Left-side coalescing
    if (target_idx > 0 && !blocks_[target_idx - 1].is_allocated) {
        blocks_[target_idx - 1].size += blocks_[target_idx].size;
        blocks_.erase(blocks_.begin() + static_cast<std::ptrdiff_t>(target_idx));
        --target_idx;
    }

    // Right-side coalescing
    if (target_idx + 1 < blocks_.size() && !blocks_[target_idx + 1].is_allocated) {
        blocks_[target_idx].size += blocks_[target_idx + 1].size;
        blocks_.erase(blocks_.begin() + static_cast<std::ptrdiff_t>(target_idx + 1));
    }

    return true;
}

const std::vector<MemoryBlock>& MemoryManager::blocks() const noexcept {
    return blocks_;
}

MemoryMetrics MemoryManager::calculate_metrics() const noexcept {
    MemoryMetrics metrics;
    metrics.total_memory = total_memory_;

    for (const auto& b : blocks_) {
        if (b.is_allocated) {
            metrics.allocated_memory += b.size;
        } else {
            metrics.free_memory += b.size;
            if (b.size > metrics.largest_free_block) {
                metrics.largest_free_block = b.size;
            }
        }
    }

    if (metrics.free_memory == 0 || metrics.allocated_memory == 0) {
        metrics.external_fragmentation = 0.0;
    } else {
        metrics.external_fragmentation = 1.0 - (static_cast<double>(metrics.largest_free_block) /
                                               static_cast<double>(metrics.free_memory));
    }

    return metrics;
}

std::size_t MemoryManager::total_memory() const noexcept {
    return total_memory_;
}

} // namespace oscope::memory
