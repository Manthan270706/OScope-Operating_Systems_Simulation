#include "oscope/memory/memory_comparison.hpp"

#include <stdexcept>
#include <unordered_map>
#include <utility>
#include <vector>

#include "oscope/memory/allocation_strategy.hpp"
#include "oscope/memory/memory_manager.hpp"

namespace oscope::memory {

MemoryComparisonResult MemoryComparator::compare(
    std::size_t total_memory,
    const std::vector<MemoryOperation>& workload) const {
    if (total_memory == 0) {
        throw std::invalid_argument("Total memory size must be positive (> 0).");
    }

    MemoryComparisonResult result;
    result.total_memory = total_memory;
    result.workload = workload;

    // Evaluate strategies in deterministic order: First Fit, Best Fit, Worst Fit
    const std::vector<AllocationStrategy> strategies = {
        AllocationStrategy::FirstFit,
        AllocationStrategy::BestFit,
        AllocationStrategy::WorstFit
    };

    for (AllocationStrategy strategy : strategies) {
        MemoryComparisonEntry entry;
        entry.strategy = strategy;
        entry.strategy_name = std::string(to_string(strategy));

        // Independent, freshly initialized memory manager instance
        MemoryManager manager(total_memory, strategy);

        // Strategy-specific mapping: logical_request_id -> actual MemoryManager allocation_id
        std::unordered_map<int, int> active_allocations;

        for (const auto& op : workload) {
            if (op.type == MemoryOperationType::Allocate) {
                entry.allocation_requests_attempted++;

                // Validate positive logical request ID
                if (op.request_id <= 0) {
                    entry.failed_allocations++;
                    entry.allocation_results.push_back(AllocationResult{
                        false, std::nullopt, 0, 0, "Logical request ID must be positive (> 0)."
                    });
                    continue;
                }

                // Check for already-active logical request ID
                if (active_allocations.find(op.request_id) != active_allocations.end()) {
                    entry.failed_allocations++;
                    entry.allocation_results.push_back(AllocationResult{
                        false, std::nullopt, 0, 0, "Duplicate logical request ID."
                    });
                    continue;
                }

                // Attempt allocation in manager
                AllocationResult alloc_res = manager.allocate(op.size, strategy, op.process_id);
                entry.allocation_results.push_back(alloc_res);

                if (alloc_res.success) {
                    entry.successful_allocations++;
                    active_allocations[op.request_id] = alloc_res.allocation_id.value();
                } else {
                    entry.failed_allocations++;
                }
            } else if (op.type == MemoryOperationType::Deallocate) {
                // Resolve exclusively through strategy-specific active mapping
                auto it = active_allocations.find(op.request_id);
                if (it != active_allocations.end()) {
                    int actual_id = it->second;
                    bool freed = manager.deallocate(actual_id);
                    if (freed) {
                        active_allocations.erase(it);
                    }
                }
                // Unknown, failed, or repeated deallocations leave memory unchanged
                // and do not affect allocation statistics.
            }
        }

        entry.final_metrics = manager.calculate_metrics();
        entry.final_blocks = manager.blocks();

        if (entry.allocation_requests_attempted > 0) {
            entry.allocation_success_rate =
                static_cast<double>(entry.successful_allocations) /
                static_cast<double>(entry.allocation_requests_attempted);
        } else {
            entry.allocation_success_rate = 0.0;
        }

        result.entries.push_back(std::move(entry));
    }

    return result;
}

MemoryComparisonResult MemoryComparator::compare_all(
    std::size_t total_memory,
    const std::vector<MemoryOperation>& workload) {
    return MemoryComparator{}.compare(total_memory, workload);
}

} // namespace oscope::memory
