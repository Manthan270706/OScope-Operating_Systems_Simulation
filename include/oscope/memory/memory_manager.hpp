#ifndef OSCOPE_MEMORY_MEMORY_MANAGER_HPP
#define OSCOPE_MEMORY_MEMORY_MANAGER_HPP

#include <cstddef>
#include <optional>
#include <vector>

#include "oscope/memory/allocation_result.hpp"
#include "oscope/memory/allocation_strategy.hpp"
#include "oscope/memory/memory_block.hpp"

namespace oscope::memory {

namespace testing {
struct MemoryManagerTestAccess;
}

/**
 * @brief Dynamic-partition memory manager supporting First Fit, Best Fit, and Worst Fit
 * allocation, block splitting, coalescing, and metrics tracking.
 */
class MemoryManager {
public:
    friend struct testing::MemoryManagerTestAccess;

    /**
     * @brief Initializes a contiguous memory pool of the specified total size.
     * @param total_memory Total capacity in bytes. Must be > 0.
     * @param default_strategy Default allocation strategy (defaults to FirstFit).
     * @throws std::invalid_argument if total_memory is 0.
     */
    explicit MemoryManager(std::size_t total_memory,
                           AllocationStrategy default_strategy = AllocationStrategy::FirstFit);

    /**
     * @brief Allocates a contiguous block using the instance's default strategy.
     *
     * Finds a suitable free block according to the manager's current strategy. If the free
     * block is larger than the requested size, it is split into an allocated block
     * and a free remainder. Exact fits do not create zero-sized blocks.
     *
     * @param size Size to allocate. Must be > 0.
     * @param process_id Optional associated process ID metadata.
     * @return AllocationResult containing allocation details on success or failure info.
     */
    AllocationResult allocate(std::size_t size, std::optional<int> process_id = std::nullopt);

    /**
     * @brief Allocates a contiguous block using an explicitly specified strategy.
     *
     * @param size Size to allocate. Must be > 0.
     * @param strategy The allocation strategy (FirstFit, BestFit, or WorstFit).
     * @param process_id Optional associated process ID metadata.
     * @return AllocationResult containing allocation details on success or failure info.
     */
    AllocationResult allocate(std::size_t size, AllocationStrategy strategy,
                              std::optional<int> process_id = std::nullopt);

    /**
     * @brief Allocates a contiguous block with process ID and an explicitly specified strategy.
     *
     * @param size Size to allocate. Must be > 0.
     * @param process_id Optional associated process ID metadata.
     * @param strategy The allocation strategy (FirstFit, BestFit, or WorstFit).
     * @return AllocationResult containing allocation details on success or failure info.
     */
    AllocationResult allocate(std::size_t size, std::optional<int> process_id,
                              AllocationStrategy strategy);

    /**
     * @brief Returns the default allocation strategy of this manager.
     */
    AllocationStrategy strategy() const noexcept;

    /**
     * @brief Updates the default allocation strategy of this manager.
     */
    void set_strategy(AllocationStrategy strategy) noexcept;

    /**
     * @brief Deallocates a block by its allocation ID and coalesces adjacent free blocks.
     *
     * Merges immediately preceding and succeeding free blocks to eliminate external fragmentation.
     * Unknown IDs or attempts to deallocate already-freed blocks are rejected without changing state.
     *
     * @param allocation_id The ID of the allocation to free.
     * @return true if successfully found and deallocated, false otherwise.
     */
    bool deallocate(int allocation_id);

    /**
     * @brief Returns a read-only snapshot of all memory blocks (both allocated and free).
     */
    const std::vector<MemoryBlock>& blocks() const noexcept;

    /**
     * @brief Calculates current allocation metrics and external fragmentation.
     */
    MemoryMetrics calculate_metrics() const noexcept;

    /**
     * @brief Returns the total capacity of the memory pool.
     */
    std::size_t total_memory() const noexcept;

    /**
     * @brief Resets the memory pool back to a single initial free block.
     *
     * Allocation IDs continue incrementing to maintain global uniqueness.
     * The configured default allocation strategy is preserved.
     */
    void reset();

private:
    /**
     * @brief Finds a free block according to the specified allocation strategy.
     *
     * @param size Requested allocation size.
     * @param strategy Strategy to apply.
     * @return Index of the chosen block in blocks_, or std::nullopt if no block fits.
     */
    std::optional<std::size_t> find_block(std::size_t size, AllocationStrategy strategy) const;

    std::size_t total_memory_{0};
    AllocationStrategy strategy_{AllocationStrategy::FirstFit};
    int next_allocation_id_{1};
    bool ids_exhausted_{false};
    std::vector<MemoryBlock> blocks_;
};

} // namespace oscope::memory

namespace oscope {
    using oscope::memory::MemoryManager;
}

#endif // OSCOPE_MEMORY_MEMORY_MANAGER_HPP
