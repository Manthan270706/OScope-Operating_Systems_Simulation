#ifndef OSCOPE_MEMORY_MEMORY_COMPARISON_HPP
#define OSCOPE_MEMORY_MEMORY_COMPARISON_HPP

#include <cstddef>
#include <optional>
#include <string>
#include <vector>

#include "oscope/memory/allocation_result.hpp"
#include "oscope/memory/allocation_strategy.hpp"
#include "oscope/memory/memory_block.hpp"

namespace oscope::memory {

/**
 * @brief Types of operations supported within a memory comparison workload.
 */
enum class MemoryOperationType {
    Allocate,
    Deallocate
};

/**
 * @brief Represents a single memory operation in an evaluation workload.
 *
 * Each allocation operation requires an explicit, positive logical request ID.
 * Deallocation operations specify the logical request ID to free.
 */
struct MemoryOperation {
    MemoryOperationType type{MemoryOperationType::Allocate};
    int request_id{0};                           ///< Positive logical request identifier
    std::size_t size{0};                         ///< Bytes to allocate (for Allocate)
    std::optional<int> process_id{std::nullopt}; ///< Optional process ID metadata

    /**
     * @brief Factory for an allocation operation.
     * @param request_id Explicit positive logical request ID (> 0).
     * @param size Number of bytes requested (> 0).
     * @param process_id Optional associated process ID metadata.
     */
    static MemoryOperation alloc(int request_id, std::size_t size,
                                 std::optional<int> process_id = std::nullopt) {
        return MemoryOperation{MemoryOperationType::Allocate, request_id, size, process_id};
    }

    /**
     * @brief Factory for a deallocation operation.
     * @param request_id Logical request ID to free.
     */
    static MemoryOperation dealloc(int request_id) {
        return MemoryOperation{MemoryOperationType::Deallocate, request_id, 0, std::nullopt};
    }
};

/**
 * @brief Evaluation result for an individual memory allocation strategy.
 */
struct MemoryComparisonEntry {
    AllocationStrategy strategy{AllocationStrategy::FirstFit};
    std::string strategy_name;

    std::size_t allocation_requests_attempted{0};
    std::size_t successful_allocations{0};
    std::size_t failed_allocations{0};
    double allocation_success_rate{0.0}; ///< In range [0.0, 1.0]; 0.0 when attempted is 0

    MemoryMetrics final_metrics;
    std::vector<AllocationResult> allocation_results; ///< Outcomes of allocation requests
    std::vector<MemoryBlock> final_blocks;            ///< Final memory block layout

    std::size_t final_allocated_memory() const noexcept {
        return final_metrics.allocated_memory;
    }

    std::size_t final_free_memory() const noexcept {
        return final_metrics.free_memory;
    }

    std::size_t final_largest_free_block() const noexcept {
        return final_metrics.largest_free_block;
    }

    double final_external_fragmentation() const noexcept {
        return final_metrics.external_fragmentation;
    }
};

/**
 * @brief Aggregated comparison results across First Fit, Best Fit, and Worst Fit.
 */
struct MemoryComparisonResult {
    std::size_t total_memory{0};
    std::vector<MemoryOperation> workload;
    std::vector<MemoryComparisonEntry> entries;

    auto begin() noexcept { return entries.begin(); }
    auto end() noexcept { return entries.end(); }
    auto begin() const noexcept { return entries.begin(); }
    auto end() const noexcept { return entries.end(); }
    std::size_t size() const noexcept { return entries.size(); }
    bool empty() const noexcept { return entries.empty(); }
    const MemoryComparisonEntry& operator[](std::size_t idx) const { return entries[idx]; }
    MemoryComparisonEntry& operator[](std::size_t idx) { return entries[idx]; }

    const MemoryComparisonEntry* find(AllocationStrategy strategy) const {
        for (const auto& entry : entries) {
            if (entry.strategy == strategy) {
                return &entry;
            }
        }
        return nullptr;
    }

    const MemoryComparisonEntry* find(const std::string& name) const {
        for (const auto& entry : entries) {
            if (entry.strategy_name == name) {
                return &entry;
            }
        }
        return nullptr;
    }
};

/**
 * @brief Engine evaluating and comparing memory allocation strategies on the same workload.
 */
class MemoryComparator {
public:
    MemoryComparator() = default;

    /**
     * @brief Evaluates First Fit, Best Fit, and Worst Fit on the provided workload.
     *
     * Strategies are evaluated in deterministic order: First Fit, Best Fit, Worst Fit.
     * Each strategy runs with an independent, freshly initialized MemoryManager instance.
     *
     * @param total_memory Total memory capacity in bytes (> 0).
     * @param workload Sequence of allocation and deallocation operations.
     * @return MemoryComparisonResult containing entries for all three strategies.
     * @throws std::invalid_argument if total_memory == 0.
     */
    MemoryComparisonResult compare(std::size_t total_memory,
                                  const std::vector<MemoryOperation>& workload) const;

    /**
     * @brief Static convenience helper matching compare().
     */
    static MemoryComparisonResult compare_all(std::size_t total_memory,
                                              const std::vector<MemoryOperation>& workload);
};

using MemoryAllocationComparator = MemoryComparator;

} // namespace oscope::memory

namespace oscope {
    using oscope::memory::MemoryOperationType;
    using oscope::memory::MemoryOperation;
    using oscope::memory::MemoryComparisonEntry;
    using oscope::memory::MemoryComparisonResult;
    using oscope::memory::MemoryComparator;
    using oscope::memory::MemoryAllocationComparator;
}

#endif // OSCOPE_MEMORY_MEMORY_COMPARISON_HPP
