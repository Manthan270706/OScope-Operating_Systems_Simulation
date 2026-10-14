#include <gtest/gtest.h>

#include <cstddef>
#include <limits>
#include <optional>
#include <stdexcept>
#include <vector>

#include "oscope/memory/allocation_result.hpp"
#include "oscope/memory/memory_block.hpp"
#include "oscope/memory/memory_manager.hpp"

using oscope::memory::AllocationResult;
using oscope::memory::AllocationStrategy;
using oscope::memory::MemoryBlock;
using oscope::memory::MemoryManager;
using oscope::memory::MemoryMetrics;
using oscope::memory::to_string;

namespace oscope::memory::testing {
struct MemoryManagerTestAccess {
    static void set_next_allocation_id(MemoryManager& manager, int id) noexcept {
        manager.next_allocation_id_ = id;
    }
    static bool are_ids_exhausted(const MemoryManager& manager) noexcept {
        return manager.ids_exhausted_;
    }
};
}

// 1. Initial memory state and metrics
TEST(OScopeMemoryAllocationTest, InitialStateAndMetrics) {
    MemoryManager manager(1000);

    EXPECT_EQ(manager.total_memory(), 1000);
    const auto& blocks = manager.blocks();
    ASSERT_EQ(blocks.size(), 1);

    EXPECT_EQ(blocks[0].start_address, 0);
    EXPECT_EQ(blocks[0].size, 1000);
    EXPECT_FALSE(blocks[0].is_allocated);
    EXPECT_EQ(blocks[0].allocation_id, std::nullopt);
    EXPECT_EQ(blocks[0].process_id, std::nullopt);

    MemoryMetrics metrics = manager.calculate_metrics();
    EXPECT_EQ(metrics.total_memory, 1000);
    EXPECT_EQ(metrics.allocated_memory, 0);
    EXPECT_EQ(metrics.free_memory, 1000);
    EXPECT_EQ(metrics.largest_free_block, 1000);
    EXPECT_DOUBLE_EQ(metrics.external_fragmentation, 0.0);
}

// 2. First Fit selecting the first suitable hole
TEST(OScopeMemoryAllocationTest, FirstFitSelectsFirstSuitableHole) {
    // Layout: 1000 total. Allocate three 200 blocks (id 1, 2, 3), then a 400 block (id 4).
    // Deallocate id 1 (at [0, 200)) and id 3 (at [400, 600)).
    // Holes are: [0, 200) of size 200, [400, 600) of size 200.
    // An allocation of size 150 must select the first suitable hole at address 0.
    MemoryManager manager(1000);

    auto a1 = manager.allocate(200);
    auto a2 = manager.allocate(200);
    auto a3 = manager.allocate(200);
    auto a4 = manager.allocate(400);

    ASSERT_TRUE(a1.success && a2.success && a3.success && a4.success);

    EXPECT_TRUE(manager.deallocate(a1.allocation_id.value()));
    EXPECT_TRUE(manager.deallocate(a3.allocation_id.value()));

    // First Fit request of size 150
    auto result = manager.allocate(150, 42);
    ASSERT_TRUE(result.success);
    EXPECT_EQ(result.start_address, 0);
    EXPECT_EQ(result.size, 150);

    const auto& blocks = manager.blocks();
    // Expected layout:
    // 0: allocated (150)
    // 1: free (50) [150 -> 200]
    // 2: allocated a2 (200) [200 -> 400]
    // 3: free (200) [400 -> 600]
    // 4: allocated a4 (400) [600 -> 1000]
    ASSERT_EQ(blocks.size(), 5);
    EXPECT_EQ(blocks[0].start_address, 0);
    EXPECT_EQ(blocks[0].size, 150);
    EXPECT_TRUE(blocks[0].is_allocated);
    EXPECT_EQ(blocks[0].process_id, 42);

    EXPECT_EQ(blocks[1].start_address, 150);
    EXPECT_EQ(blocks[1].size, 50);
    EXPECT_FALSE(blocks[1].is_allocated);
}

// 3. Exact-fit allocation without creating zero-sized block
TEST(OScopeMemoryAllocationTest, ExactFitAllocationAvoidsZeroSizedBlock) {
    MemoryManager manager(500);

    auto result = manager.allocate(500, 10);
    ASSERT_TRUE(result.success);
    EXPECT_EQ(result.start_address, 0);
    EXPECT_EQ(result.size, 500);

    const auto& blocks = manager.blocks();
    ASSERT_EQ(blocks.size(), 1);
    EXPECT_TRUE(blocks[0].is_allocated);
    EXPECT_EQ(blocks[0].size, 500);
    EXPECT_EQ(blocks[0].start_address, 0);

    MemoryMetrics metrics = manager.calculate_metrics();
    EXPECT_EQ(metrics.allocated_memory, 500);
    EXPECT_EQ(metrics.free_memory, 0);
    EXPECT_EQ(metrics.largest_free_block, 0);
    EXPECT_DOUBLE_EQ(metrics.external_fragmentation, 0.0);
}

// 4. Block splitting
TEST(OScopeMemoryAllocationTest, BlockSplittingPreservesContiguity) {
    MemoryManager manager(1000);

    auto r1 = manager.allocate(300);
    ASSERT_TRUE(r1.success);
    EXPECT_EQ(r1.start_address, 0);
    EXPECT_EQ(r1.size, 300);

    const auto& blocks = manager.blocks();
    ASSERT_EQ(blocks.size(), 2);

    // Allocated block
    EXPECT_TRUE(blocks[0].is_allocated);
    EXPECT_EQ(blocks[0].start_address, 0);
    EXPECT_EQ(blocks[0].size, 300);

    // Free remainder
    EXPECT_FALSE(blocks[1].is_allocated);
    EXPECT_EQ(blocks[1].start_address, 300);
    EXPECT_EQ(blocks[1].size, 700);

    EXPECT_EQ(blocks[0].size + blocks[1].size, 1000);
}

// 5. Failed allocation leaves state unchanged
TEST(OScopeMemoryAllocationTest, FailedAllocationLeavesStateUnchanged) {
    MemoryManager manager(500);
    auto a1 = manager.allocate(300);
    ASSERT_TRUE(a1.success);

    auto state_before = manager.blocks();
    auto metrics_before = manager.calculate_metrics();

    // Request more than available contiguous memory (only 200 available)
    auto failed_res = manager.allocate(250);
    EXPECT_FALSE(failed_res.success);
    EXPECT_EQ(failed_res.allocation_id, std::nullopt);
    EXPECT_FALSE(failed_res.error_message.empty());

    const auto& state_after = manager.blocks();
    ASSERT_EQ(state_before.size(), state_after.size());
    for (std::size_t i = 0; i < state_before.size(); ++i) {
        EXPECT_EQ(state_before[i].start_address, state_after[i].start_address);
        EXPECT_EQ(state_before[i].size, state_after[i].size);
        EXPECT_EQ(state_before[i].is_allocated, state_after[i].is_allocated);
        EXPECT_EQ(state_before[i].allocation_id, state_after[i].allocation_id);
    }

    auto metrics_after = manager.calculate_metrics();
    EXPECT_EQ(metrics_before.allocated_memory, metrics_after.allocated_memory);
    EXPECT_EQ(metrics_before.free_memory, metrics_after.free_memory);
    EXPECT_DOUBLE_EQ(metrics_before.external_fragmentation, metrics_after.external_fragmentation);
}

// 6. Deallocation and left-side coalescing
TEST(OScopeMemoryAllocationTest, DeallocationWithLeftSideCoalescing) {
    MemoryManager manager(1000);
    auto a1 = manager.allocate(200);
    auto a2 = manager.allocate(300);
    auto a3 = manager.allocate(500);

    // Deallocate a1: block [0, 200) becomes free
    EXPECT_TRUE(manager.deallocate(a1.allocation_id.value()));

    // Now deallocate a2: block [200, 500) merges with left neighbor [0, 200) -> [0, 500)
    EXPECT_TRUE(manager.deallocate(a2.allocation_id.value()));

    const auto& blocks = manager.blocks();
    ASSERT_EQ(blocks.size(), 2);

    EXPECT_FALSE(blocks[0].is_allocated);
    EXPECT_EQ(blocks[0].start_address, 0);
    EXPECT_EQ(blocks[0].size, 500);

    EXPECT_TRUE(blocks[1].is_allocated);
    EXPECT_EQ(blocks[1].start_address, 500);
    EXPECT_EQ(blocks[1].size, 500);
}

// 7. Right-side coalescing
TEST(OScopeMemoryAllocationTest, DeallocationWithRightSideCoalescing) {
    MemoryManager manager(1000);
    auto a1 = manager.allocate(200);
    auto a2 = manager.allocate(300);
    auto a3 = manager.allocate(500);

    // Deallocate a3: block [500, 1000) becomes free
    EXPECT_TRUE(manager.deallocate(a3.allocation_id.value()));

    // Now deallocate a2: block [200, 500) merges with right neighbor [500, 1000) -> [200, 1000)
    EXPECT_TRUE(manager.deallocate(a2.allocation_id.value()));

    const auto& blocks = manager.blocks();
    ASSERT_EQ(blocks.size(), 2);

    EXPECT_TRUE(blocks[0].is_allocated);
    EXPECT_EQ(blocks[0].start_address, 0);
    EXPECT_EQ(blocks[0].size, 200);

    EXPECT_FALSE(blocks[1].is_allocated);
    EXPECT_EQ(blocks[1].start_address, 200);
    EXPECT_EQ(blocks[1].size, 800);
}

// 8. Coalescing both neighboring free blocks (sandwich merge)
TEST(OScopeMemoryAllocationTest, DeallocationWithBothSidesCoalescing) {
    MemoryManager manager(1000);
    auto a1 = manager.allocate(200);
    auto a2 = manager.allocate(300);
    auto a3 = manager.allocate(500);

    // Free a1 (left) and a3 (right), leaving a2 in the middle
    EXPECT_TRUE(manager.deallocate(a1.allocation_id.value()));
    EXPECT_TRUE(manager.deallocate(a3.allocation_id.value()));

    ASSERT_EQ(manager.blocks().size(), 3);

    // Deallocate a2: merges left [0, 200), a2 [200, 500), and right [500, 1000)
    EXPECT_TRUE(manager.deallocate(a2.allocation_id.value()));

    const auto& blocks = manager.blocks();
    ASSERT_EQ(blocks.size(), 1);
    EXPECT_FALSE(blocks[0].is_allocated);
    EXPECT_EQ(blocks[0].start_address, 0);
    EXPECT_EQ(blocks[0].size, 1000);

    MemoryMetrics metrics = manager.calculate_metrics();
    EXPECT_EQ(metrics.allocated_memory, 0);
    EXPECT_EQ(metrics.free_memory, 1000);
    EXPECT_DOUBLE_EQ(metrics.external_fragmentation, 0.0);
}

// 9. Unknown and repeated deallocation
TEST(OScopeMemoryAllocationTest, UnknownAndRepeatedDeallocationRejected) {
    MemoryManager manager(1000);
    auto a1 = manager.allocate(200);
    ASSERT_TRUE(a1.success);

    // Non-existent ID
    EXPECT_FALSE(manager.deallocate(999));
    EXPECT_FALSE(manager.deallocate(-1));
    EXPECT_FALSE(manager.deallocate(0));

    // Valid deallocation
    EXPECT_TRUE(manager.deallocate(a1.allocation_id.value()));

    // Repeated deallocation of same ID
    EXPECT_FALSE(manager.deallocate(a1.allocation_id.value()));

    // Memory layout remains intact
    ASSERT_EQ(manager.blocks().size(), 1);
    EXPECT_FALSE(manager.blocks()[0].is_allocated);
    EXPECT_EQ(manager.blocks()[0].size, 1000);
}

// 10. Invalid sizes and overflow-sensitive cases
TEST(OScopeMemoryAllocationTest, HandlesInvalidSizesAndOverflowSafely) {
    // Zero-sized memory pool constructor rejection
    EXPECT_THROW(MemoryManager(0), std::invalid_argument);

    MemoryManager manager(1000);

    // Zero-sized allocation request
    auto r_zero = manager.allocate(0);
    EXPECT_FALSE(r_zero.success);
    EXPECT_FALSE(r_zero.error_message.empty());

    // Allocation larger than total memory pool
    auto r_large = manager.allocate(1001);
    EXPECT_FALSE(r_large.success);

    // Allocation near size_t max
    auto r_overflow = manager.allocate(std::numeric_limits<std::size_t>::max());
    EXPECT_FALSE(r_overflow.success);

    // Layout should be unchanged
    ASSERT_EQ(manager.blocks().size(), 1);
    EXPECT_EQ(manager.blocks()[0].size, 1000);
}

// 11. Metrics and external fragmentation calculations
TEST(OScopeMemoryAllocationTest, CalculatesExternalFragmentationCorrectly) {
    // Total 1000. Allocate 5 blocks of 200: a1, a2, a3, a4, a5
    // Free a2 (200 at 200) and a4 (200 at 600).
    // Total free memory = 400. Largest free block = 200.
    // External fragmentation = 1.0 - (200 / 400) = 0.50.
    MemoryManager manager(1000);

    auto a1 = manager.allocate(200);
    auto a2 = manager.allocate(200);
    auto a3 = manager.allocate(200);
    auto a4 = manager.allocate(200);
    auto a5 = manager.allocate(200);

    EXPECT_TRUE(manager.deallocate(a2.allocation_id.value()));
    EXPECT_TRUE(manager.deallocate(a4.allocation_id.value()));

    MemoryMetrics m = manager.calculate_metrics();
    EXPECT_EQ(m.total_memory, 1000);
    EXPECT_EQ(m.allocated_memory, 600);
    EXPECT_EQ(m.free_memory, 400);
    EXPECT_EQ(m.largest_free_block, 200);
    EXPECT_DOUBLE_EQ(m.external_fragmentation, 0.50);

    // Now deallocate a3: merges a2(200), a3(200), a4(200) into 600
    EXPECT_TRUE(manager.deallocate(a3.allocation_id.value()));
    MemoryMetrics m2 = manager.calculate_metrics();
    EXPECT_EQ(m2.allocated_memory, 400);
    EXPECT_EQ(m2.free_memory, 600);
    EXPECT_EQ(m2.largest_free_block, 600);
    EXPECT_DOUBLE_EQ(m2.external_fragmentation, 0.0);
}

// 12. Reset behavior and allocation-ID uniqueness
TEST(OScopeMemoryAllocationTest, ResetBehaviorAndIdUniqueness) {
    MemoryManager manager(500);

    auto a1 = manager.allocate(100);
    auto a2 = manager.allocate(100);
    ASSERT_TRUE(a1.success && a2.success);
    EXPECT_EQ(a1.allocation_id.value(), 1);
    EXPECT_EQ(a2.allocation_id.value(), 2);

    manager.reset();

    // After reset: 1 free block spanning entire memory
    EXPECT_EQ(manager.blocks().size(), 1);
    EXPECT_FALSE(manager.blocks()[0].is_allocated);
    EXPECT_EQ(manager.blocks()[0].size, 500);

    // New allocation IDs must NOT reuse previous IDs
    auto a3 = manager.allocate(100);
    ASSERT_TRUE(a3.success);
    EXPECT_GT(a3.allocation_id.value(), a2.allocation_id.value());
    EXPECT_EQ(a3.allocation_id.value(), 3);
}

// 13. Ability to allocate using maximum positive int ID
TEST(OScopeMemoryAllocationTest, AllocatesUsingMaxIntIdAndDeallocatesSuccessfully) {
    MemoryManager manager(1000);

    // Fast-forward next allocation ID to INT_MAX using minimal test seam
    const int max_id = std::numeric_limits<int>::max();
    oscope::memory::testing::MemoryManagerTestAccess::set_next_allocation_id(manager, max_id);

    auto result = manager.allocate(200, 99);
    ASSERT_TRUE(result.success);
    ASSERT_TRUE(result.allocation_id.has_value());
    EXPECT_EQ(result.allocation_id.value(), max_id);
    EXPECT_EQ(result.start_address, 0);
    EXPECT_EQ(result.size, 200);

    EXPECT_TRUE(oscope::memory::testing::MemoryManagerTestAccess::are_ids_exhausted(manager));

    // Deallocation using INT_MAX must succeed and coalesce
    EXPECT_TRUE(manager.deallocate(max_id));
    ASSERT_EQ(manager.blocks().size(), 1);
    EXPECT_FALSE(manager.blocks()[0].is_allocated);
    EXPECT_EQ(manager.blocks()[0].size, 1000);
}

// 14. Allocation fails cleanly when allocation IDs are exhausted
TEST(OScopeMemoryAllocationTest, RejectsAllocationsWhenAllocationIdsAreExhausted) {
    MemoryManager manager(1000);

    // Set to INT_MAX and exhaust the final ID
    const int max_id = std::numeric_limits<int>::max();
    oscope::memory::testing::MemoryManagerTestAccess::set_next_allocation_id(manager, max_id);

    auto r1 = manager.allocate(200);
    ASSERT_TRUE(r1.success);
    EXPECT_EQ(r1.allocation_id.value(), max_id);

    // Record memory block layout before failed allocation attempt
    auto layout_before = manager.blocks();
    ASSERT_EQ(layout_before.size(), 2);

    // Subsequent allocation must fail cleanly without mutating blocks or ID state
    auto r2 = manager.allocate(100);
    EXPECT_FALSE(r2.success);
    EXPECT_EQ(r2.allocation_id, std::nullopt);
    EXPECT_EQ(r2.error_message, "Allocation ID capacity exhausted.");

    // Verify memory blocks remain completely unchanged
    const auto& layout_after = manager.blocks();
    ASSERT_EQ(layout_before.size(), layout_after.size());
    for (std::size_t i = 0; i < layout_before.size(); ++i) {
        EXPECT_EQ(layout_before[i].start_address, layout_after[i].start_address);
        EXPECT_EQ(layout_before[i].size, layout_after[i].size);
        EXPECT_EQ(layout_before[i].is_allocated, layout_after[i].is_allocated);
        EXPECT_EQ(layout_before[i].allocation_id, layout_after[i].allocation_id);
    }

    // Deallocate the active allocation
    EXPECT_TRUE(manager.deallocate(max_id));

    // Even though memory is now 100% free, no previously issued IDs may be reused
    auto r3 = manager.allocate(100);
    EXPECT_FALSE(r3.success);
    EXPECT_EQ(r3.error_message, "Allocation ID capacity exhausted.");

    // Resetting the manager also does not allow ID reuse
    manager.reset();
    EXPECT_EQ(manager.blocks().size(), 1);
    EXPECT_FALSE(manager.blocks()[0].is_allocated);
    EXPECT_EQ(manager.blocks()[0].size, 1000);

    auto r4 = manager.allocate(100);
    EXPECT_FALSE(r4.success);
    EXPECT_EQ(r4.error_message, "Allocation ID capacity exhausted.");
}

// 15. Best Fit chooses the smallest suitable hole
TEST(OScopeMemoryAllocationTest, BestFitSelectsSmallestSuitableHole) {
    MemoryManager manager(1000);

    // Create holes of sizes: 100 [0, 100), 300 [150, 450), 200 [500, 700), 250 [750, 1000)
    auto h1 = manager.allocate(100);
    auto s1 = manager.allocate(50);
    auto h2 = manager.allocate(300);
    auto s2 = manager.allocate(50);
    auto h3 = manager.allocate(200);
    auto s3 = manager.allocate(50);

    EXPECT_TRUE(manager.deallocate(h1.allocation_id.value()));
    EXPECT_TRUE(manager.deallocate(h2.allocation_id.value()));
    EXPECT_TRUE(manager.deallocate(h3.allocation_id.value()));

    // Request 180: eligible holes are 300 (at 150), 200 (at 500), 250 (at 750).
    // Best Fit must select the smallest suitable hole: size 200 at start_address 500.
    auto result = manager.allocate(180, AllocationStrategy::BestFit);
    ASSERT_TRUE(result.success);
    EXPECT_EQ(result.start_address, 500);
    EXPECT_EQ(result.size, 180);

    // Verify block at 500 was split into [500, 680) allocated and [680, 700) free (size 20)
    const auto& blocks = manager.blocks();
    bool found_allocated = false;
    bool found_remainder = false;
    for (const auto& b : blocks) {
        if (b.start_address == 500 && b.size == 180 && b.is_allocated) {
            found_allocated = true;
        }
        if (b.start_address == 680 && b.size == 20 && !b.is_allocated) {
            found_remainder = true;
        }
    }
    EXPECT_TRUE(found_allocated);
    EXPECT_TRUE(found_remainder);

    // Also test constructor-configured BestFit strategy
    MemoryManager bf_mgr(500, AllocationStrategy::BestFit);
    EXPECT_EQ(bf_mgr.strategy(), AllocationStrategy::BestFit);
}

// 16. Worst Fit chooses the largest suitable hole
TEST(OScopeMemoryAllocationTest, WorstFitSelectsLargestSuitableHole) {
    MemoryManager manager(1000);

    // Create holes of sizes: 100 [0, 100), 300 [150, 450), 200 [500, 700), 250 [750, 1000)
    auto h1 = manager.allocate(100);
    auto s1 = manager.allocate(50);
    auto h2 = manager.allocate(300);
    auto s2 = manager.allocate(50);
    auto h3 = manager.allocate(200);
    auto s3 = manager.allocate(50);

    EXPECT_TRUE(manager.deallocate(h1.allocation_id.value()));
    EXPECT_TRUE(manager.deallocate(h2.allocation_id.value()));
    EXPECT_TRUE(manager.deallocate(h3.allocation_id.value()));

    // Request 180: eligible holes are 300 (at 150), 200 (at 500), 250 (at 750).
    // Worst Fit must select the largest suitable hole: size 300 at start_address 150.
    auto result = manager.allocate(180, AllocationStrategy::WorstFit);
    ASSERT_TRUE(result.success);
    EXPECT_EQ(result.start_address, 150);
    EXPECT_EQ(result.size, 180);

    // Verify block at 150 was split into [150, 330) allocated and [330, 450) free (size 120)
    const auto& blocks = manager.blocks();
    bool found_allocated = false;
    bool found_remainder = false;
    for (const auto& b : blocks) {
        if (b.start_address == 150 && b.size == 180 && b.is_allocated) {
            found_allocated = true;
        }
        if (b.start_address == 330 && b.size == 120 && !b.is_allocated) {
            found_remainder = true;
        }
    }
    EXPECT_TRUE(found_allocated);
    EXPECT_TRUE(found_remainder);

    // Also test constructor-configured WorstFit strategy
    MemoryManager wf_mgr(500, AllocationStrategy::WorstFit);
    EXPECT_EQ(wf_mgr.strategy(), AllocationStrategy::WorstFit);
}

// 17. Both Best Fit and Worst Fit handle exact fits without splitting or zero-sized blocks
TEST(OScopeMemoryAllocationTest, BestFitAndWorstFitExactFits) {
    MemoryManager manager(1000);

    // Create holes: 100 [0, 100), 200 [150, 350), 300 [400, 700), tail [750, 1000) (size 250)
    auto h1 = manager.allocate(100);
    auto s1 = manager.allocate(50);
    auto h2 = manager.allocate(200);
    auto s2 = manager.allocate(50);
    auto h3 = manager.allocate(300);
    auto s3 = manager.allocate(50);

    EXPECT_TRUE(manager.deallocate(h1.allocation_id.value()));
    EXPECT_TRUE(manager.deallocate(h2.allocation_id.value()));
    EXPECT_TRUE(manager.deallocate(h3.allocation_id.value()));

    // Best Fit exact fit: request size 200. Eligible are 200, 300, 250.
    // Smallest is 200 at 150 (exact fit).
    auto r_bf = manager.allocate(200, AllocationStrategy::BestFit);
    ASSERT_TRUE(r_bf.success);
    EXPECT_EQ(r_bf.start_address, 150);
    EXPECT_EQ(r_bf.size, 200);

    // Confirm no zero-sized blocks exist
    for (const auto& b : manager.blocks()) {
        EXPECT_GT(b.size, 0);
    }

    // Worst Fit exact fit: request size 300. Eligible are 300 (at 400) and 250 (at 750).
    // Largest is 300 at 400 (exact fit).
    auto r_wf = manager.allocate(300, AllocationStrategy::WorstFit);
    ASSERT_TRUE(r_wf.success);
    EXPECT_EQ(r_wf.start_address, 400);
    EXPECT_EQ(r_wf.size, 300);

    for (const auto& b : manager.blocks()) {
        EXPECT_GT(b.size, 0);
    }
}

// 18. Both Best Fit and Worst Fit handle no suitable hole cleanly without state mutation
TEST(OScopeMemoryAllocationTest, BestFitAndWorstFitNoSuitableHole) {
    MemoryManager manager(1000);

    // Allocate partitions such that free holes are small: 100, 150, 150 (total free = 400)
    auto h1 = manager.allocate(100);
    auto s1 = manager.allocate(200);
    auto h2 = manager.allocate(150);
    auto s2 = manager.allocate(200);
    auto h3 = manager.allocate(150);
    auto s3 = manager.allocate(200);

    EXPECT_TRUE(manager.deallocate(h1.allocation_id.value()));
    EXPECT_TRUE(manager.deallocate(h2.allocation_id.value()));
    EXPECT_TRUE(manager.deallocate(h3.allocation_id.value()));

    auto blocks_before = manager.blocks();

    // Request 250 (exceeds any single hole size of 150)
    auto r_bf = manager.allocate(250, AllocationStrategy::BestFit);
    EXPECT_FALSE(r_bf.success);
    EXPECT_EQ(r_bf.allocation_id, std::nullopt);
    EXPECT_EQ(r_bf.error_message, "Insufficient contiguous free memory.");

    auto r_wf = manager.allocate(250, AllocationStrategy::WorstFit);
    EXPECT_FALSE(r_wf.success);
    EXPECT_EQ(r_wf.allocation_id, std::nullopt);
    EXPECT_EQ(r_wf.error_message, "Insufficient contiguous free memory.");

    // Memory block state must be identical
    const auto& blocks_after = manager.blocks();
    ASSERT_EQ(blocks_before.size(), blocks_after.size());
    for (std::size_t i = 0; i < blocks_before.size(); ++i) {
        EXPECT_EQ(blocks_before[i].start_address, blocks_after[i].start_address);
        EXPECT_EQ(blocks_before[i].size, blocks_after[i].size);
        EXPECT_EQ(blocks_before[i].is_allocated, blocks_after[i].is_allocated);
        EXPECT_EQ(blocks_before[i].allocation_id, blocks_after[i].allocation_id);
    }

    // Verify allocation ID counter was not consumed
    auto r_success = manager.allocate(100, AllocationStrategy::BestFit);
    ASSERT_TRUE(r_success.success);
    EXPECT_EQ(r_success.allocation_id.value(), 7);
}

// 19. Tie-breaking between equal-sized holes selects earliest block in memory order
TEST(OScopeMemoryAllocationTest, TieBreakingSelectsEarliestBlockInMemoryOrder) {
    MemoryManager manager(1000);

    // Three equal free holes of size 200 at addresses 0, 300, 600
    auto h1 = manager.allocate(200); // [0, 200)
    auto s1 = manager.allocate(100); // [200, 300)
    auto h2 = manager.allocate(200); // [300, 500)
    auto s2 = manager.allocate(100); // [500, 600)
    auto h3 = manager.allocate(200); // [600, 800)
    auto s3 = manager.allocate(200); // [800, 1000)

    EXPECT_TRUE(manager.deallocate(h1.allocation_id.value()));
    EXPECT_TRUE(manager.deallocate(h2.allocation_id.value()));
    EXPECT_TRUE(manager.deallocate(h3.allocation_id.value()));

    // Best Fit tie-breaking: request 150. All holes are size 200.
    // Earliest block is at address 0.
    auto r_bf = manager.allocate(150, AllocationStrategy::BestFit);
    ASSERT_TRUE(r_bf.success);
    EXPECT_EQ(r_bf.start_address, 0);

    // Deallocate and restore hole at address 0
    EXPECT_TRUE(manager.deallocate(r_bf.allocation_id.value()));
    ASSERT_EQ(manager.blocks()[0].size, 200);
    EXPECT_FALSE(manager.blocks()[0].is_allocated);

    // Worst Fit tie-breaking: request 150. All holes are size 200.
    // Earliest block is at address 0.
    auto r_wf = manager.allocate(150, AllocationStrategy::WorstFit);
    ASSERT_TRUE(r_wf.success);
    EXPECT_EQ(r_wf.start_address, 0);
}

// 20. Block splitting and subsequent coalescing with Best Fit and Worst Fit
TEST(OScopeMemoryAllocationTest, SplittingAndSubsequentCoalescingWithDifferentStrategies) {
    MemoryManager manager(1000);

    // Setup: [0, 400) free, [400, 600) allocated, [600, 1000) free
    auto h1 = manager.allocate(400);
    auto s1 = manager.allocate(200);
    EXPECT_TRUE(manager.deallocate(h1.allocation_id.value()));

    // Best Fit: allocate 250.
    // Eligible holes are 400 (at 0) and 400 (at 600).
    // Earliest is at 0, splits into [0, 250) allocated and [250, 400) free (size 150).
    auto r_bf = manager.allocate(250, AllocationStrategy::BestFit);
    ASSERT_TRUE(r_bf.success);
    EXPECT_EQ(r_bf.start_address, 0);
    EXPECT_EQ(r_bf.size, 250);

    // Deallocate the best fit block: should coalesce with right neighbor [250, 400) -> [0, 400)
    EXPECT_TRUE(manager.deallocate(r_bf.allocation_id.value()));
    ASSERT_EQ(manager.blocks().size(), 3);
    EXPECT_EQ(manager.blocks()[0].start_address, 0);
    EXPECT_EQ(manager.blocks()[0].size, 400);
    EXPECT_FALSE(manager.blocks()[0].is_allocated);

    // Free the separator s1: coalesces [0, 400), [400, 600), and [600, 1000) into single 1000 block
    EXPECT_TRUE(manager.deallocate(s1.allocation_id.value()));
    ASSERT_EQ(manager.blocks().size(), 1);
    EXPECT_EQ(manager.blocks()[0].size, 1000);
    EXPECT_FALSE(manager.blocks()[0].is_allocated);
}

// 21. First Fit remains the default and behaves as before
TEST(OScopeMemoryAllocationTest, FirstFitRemainsDefaultAndBehavesAsBefore) {
    MemoryManager manager(1000);

    // Manager defaults to FirstFit
    EXPECT_EQ(manager.strategy(), AllocationStrategy::FirstFit);

    // Create holes: 100 [0, 100), 300 [150, 450), 200 [500, 700), 250 [750, 1000)
    auto h1 = manager.allocate(100);
    auto s1 = manager.allocate(50);
    auto h2 = manager.allocate(300);
    auto s2 = manager.allocate(50);
    auto h3 = manager.allocate(200);
    auto s3 = manager.allocate(50);

    EXPECT_TRUE(manager.deallocate(h1.allocation_id.value()));
    EXPECT_TRUE(manager.deallocate(h2.allocation_id.value()));
    EXPECT_TRUE(manager.deallocate(h3.allocation_id.value()));

    // Request 180 without specifying strategy: uses FirstFit default.
    // First suitable hole in memory order is 300 at address 150 (even though 200 is smaller).
    auto r1 = manager.allocate(180);
    ASSERT_TRUE(r1.success);
    EXPECT_EQ(r1.start_address, 150);
    EXPECT_EQ(r1.size, 180);

    // Switch strategy to BestFit on the instance
    manager.set_strategy(AllocationStrategy::BestFit);
    EXPECT_EQ(manager.strategy(), AllocationStrategy::BestFit);

    // Now request 180 without specifying strategy: uses instance BestFit.
    // Eligible holes are 200 (at 500) and 250 (at 750). Smallest is 200 at 500.
    auto r2 = manager.allocate(180);
    ASSERT_TRUE(r2.success);
    EXPECT_EQ(r2.start_address, 500);

    // Switch to WorstFit
    manager.set_strategy(AllocationStrategy::WorstFit);
    EXPECT_EQ(manager.strategy(), AllocationStrategy::WorstFit);

    // Verify to_string helper
    EXPECT_EQ(to_string(AllocationStrategy::FirstFit), "First Fit");
    EXPECT_EQ(to_string(AllocationStrategy::BestFit), "Best Fit");
    EXPECT_EQ(to_string(AllocationStrategy::WorstFit), "Worst Fit");
}

// 22. Allocate overloads accept process ID and strategy in any order
TEST(OScopeMemoryAllocationTest, AllocateOverloadsAcceptBothProcessIdAndStrategyOrder) {
    MemoryManager manager(1000);

    // (size, strategy, process_id)
    auto r1 = manager.allocate(100, AllocationStrategy::BestFit, 10);
    ASSERT_TRUE(r1.success);
    EXPECT_EQ(manager.blocks()[0].process_id, 10);

    // (size, process_id, strategy)
    auto r2 = manager.allocate(100, 20, AllocationStrategy::WorstFit);
    ASSERT_TRUE(r2.success);
    EXPECT_EQ(manager.blocks()[1].process_id, 20);

    // (size, strategy)
    auto r3 = manager.allocate(100, AllocationStrategy::FirstFit);
    ASSERT_TRUE(r3.success);
    EXPECT_EQ(manager.blocks()[2].process_id, std::nullopt);

    // (size, process_id)
    auto r4 = manager.allocate(100, 30);
    ASSERT_TRUE(r4.success);
    EXPECT_EQ(manager.blocks()[3].process_id, 30);

    // (size)
    auto r5 = manager.allocate(100);
    ASSERT_TRUE(r5.success);
    EXPECT_EQ(manager.blocks()[4].process_id, std::nullopt);
}

