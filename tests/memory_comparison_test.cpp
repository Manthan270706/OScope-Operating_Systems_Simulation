#include <gtest/gtest.h>

#include <cstddef>
#include <optional>
#include <stdexcept>
#include <vector>

#include "oscope/memory/allocation_result.hpp"
#include "oscope/memory/allocation_strategy.hpp"
#include "oscope/memory/memory_block.hpp"
#include "oscope/memory/memory_comparison.hpp"

using oscope::memory::AllocationResult;
using oscope::memory::AllocationStrategy;
using oscope::memory::MemoryBlock;
using oscope::memory::MemoryComparisonEntry;
using oscope::memory::MemoryComparisonResult;
using oscope::memory::MemoryComparator;
using oscope::memory::MemoryMetrics;
using oscope::memory::MemoryOperation;
using oscope::memory::MemoryOperationType;

// 1. Zero total memory throws std::invalid_argument
TEST(OScopeMemoryComparisonTest, ZeroTotalMemoryThrowsInvalidArgument) {
    MemoryComparator comparator;
    EXPECT_THROW(comparator.compare(0, {}), std::invalid_argument);
    EXPECT_THROW(MemoryComparator::compare_all(0, {}), std::invalid_argument);
}

// 2. Empty workload returns three correctly initialized entries
TEST(OScopeMemoryComparisonTest, EmptyWorkloadReturnsThreeInitializedEntries) {
    auto result = MemoryComparator::compare_all(1000, {});

    EXPECT_EQ(result.total_memory, 1000);
    EXPECT_TRUE(result.workload.empty());
    ASSERT_EQ(result.size(), 3);

    for (std::size_t i = 0; i < 3; ++i) {
        const auto& entry = result[i];
        EXPECT_EQ(entry.allocation_requests_attempted, 0);
        EXPECT_EQ(entry.successful_allocations, 0);
        EXPECT_EQ(entry.failed_allocations, 0);
        EXPECT_DOUBLE_EQ(entry.allocation_success_rate, 0.0);
        EXPECT_TRUE(entry.allocation_results.empty());

        EXPECT_EQ(entry.final_allocated_memory(), 0);
        EXPECT_EQ(entry.final_free_memory(), 1000);
        EXPECT_EQ(entry.final_largest_free_block(), 1000);
        EXPECT_DOUBLE_EQ(entry.final_external_fragmentation(), 0.0);

        ASSERT_EQ(entry.final_blocks.size(), 1);
        EXPECT_FALSE(entry.final_blocks[0].is_allocated);
        EXPECT_EQ(entry.final_blocks[0].start_address, 0);
        EXPECT_EQ(entry.final_blocks[0].size, 1000);
    }
}

// 3. Deterministic strategy order: First Fit, Best Fit, Worst Fit
TEST(OScopeMemoryComparisonTest, PreservesDeterministicStrategyOrder) {
    auto result = MemoryComparator::compare_all(1000, {});

    ASSERT_EQ(result.size(), 3);
    EXPECT_EQ(result[0].strategy, AllocationStrategy::FirstFit);
    EXPECT_EQ(result[0].strategy_name, "First Fit");

    EXPECT_EQ(result[1].strategy, AllocationStrategy::BestFit);
    EXPECT_EQ(result[1].strategy_name, "Best Fit");

    EXPECT_EQ(result[2].strategy, AllocationStrategy::WorstFit);
    EXPECT_EQ(result[2].strategy_name, "Worst Fit");

    // Lookup by strategy and name
    EXPECT_NE(result.find(AllocationStrategy::FirstFit), nullptr);
    EXPECT_NE(result.find(AllocationStrategy::BestFit), nullptr);
    EXPECT_NE(result.find(AllocationStrategy::WorstFit), nullptr);
    EXPECT_NE(result.find("First Fit"), nullptr);
    EXPECT_NE(result.find("Best Fit"), nullptr);
    EXPECT_NE(result.find("Worst Fit"), nullptr);
    EXPECT_EQ(result.find("NonExistent"), nullptr);
}

// 4. Duplicate active logical IDs fail without modifying existing mapping or memory
TEST(OScopeMemoryComparisonTest, DuplicateActiveLogicalIdFailsAndPreservesOriginalAllocation) {
    std::vector<MemoryOperation> workload = {
        MemoryOperation::alloc(1, 200, 10), // Req 1: size 200, pid 10
        MemoryOperation::alloc(1, 300, 20), // Duplicate active logical ID 1 -> must fail
        MemoryOperation::alloc(2, 100, 30), // Req 2: size 100
        MemoryOperation::dealloc(1)         // Dealloc logical ID 1 -> must free the 200 block!
    };

    auto result = MemoryComparator::compare_all(1000, workload);

    for (const auto& entry : result) {
        EXPECT_EQ(entry.allocation_requests_attempted, 3);
        EXPECT_EQ(entry.successful_allocations, 2);
        EXPECT_EQ(entry.failed_allocations, 1);
        EXPECT_DOUBLE_EQ(entry.allocation_success_rate, 2.0 / 3.0);

        ASSERT_EQ(entry.allocation_results.size(), 3);
        EXPECT_TRUE(entry.allocation_results[0].success);
        EXPECT_EQ(entry.allocation_results[0].size, 200);

        EXPECT_FALSE(entry.allocation_results[1].success);
        EXPECT_EQ(entry.allocation_results[1].error_message, "Duplicate logical request ID.");

        EXPECT_TRUE(entry.allocation_results[2].success);
        EXPECT_EQ(entry.allocation_results[2].size, 100);

        // After dealloc(1), the original 200 block was freed
        // Remaining allocated memory should be only Req 2 (size 100)
        EXPECT_EQ(entry.final_allocated_memory(), 100);
        EXPECT_EQ(entry.final_free_memory(), 900);
    }
}

// 5. Logical ID reuse is permitted after successful deallocation
TEST(OScopeMemoryComparisonTest, LogicalIdMayBeReusedAfterSuccessfulDeallocation) {
    std::vector<MemoryOperation> workload = {
        MemoryOperation::alloc(1, 200), // Req 1: 200
        MemoryOperation::dealloc(1),    // Deallocate Req 1 -> ID 1 is no longer active
        MemoryOperation::alloc(1, 350)  // Reusing ID 1 now succeeds!
    };

    auto result = MemoryComparator::compare_all(1000, workload);

    for (const auto& entry : result) {
        EXPECT_EQ(entry.allocation_requests_attempted, 2);
        EXPECT_EQ(entry.successful_allocations, 2);
        EXPECT_EQ(entry.failed_allocations, 0);
        EXPECT_DOUBLE_EQ(entry.allocation_success_rate, 1.0);

        ASSERT_EQ(entry.allocation_results.size(), 2);
        EXPECT_TRUE(entry.allocation_results[0].success);
        EXPECT_EQ(entry.allocation_results[0].size, 200);

        EXPECT_TRUE(entry.allocation_results[1].success);
        EXPECT_EQ(entry.allocation_results[1].size, 350);

        EXPECT_EQ(entry.final_allocated_memory(), 350);
        EXPECT_EQ(entry.final_free_memory(), 650);
    }
}

// 6. Deallocation of a request that failed under a strategy leaves that strategy unaffected
TEST(OScopeMemoryComparisonTest, HandlesDeallocationWhenAllocationFailedUnderStrategy) {
    // Workload based on the discriminating sequence:
    // Reqs 1..5 set up holes [0, 300), [350, 550), [600, 1000) separated by Reqs 2 (50) and 4 (50).
    // Req 6 (180) and Req 7 (250) are placed differently by each strategy.
    // Req 8 (350) SUCCEEDS under Best Fit (in [600, 1000)), but FAILS under First Fit and Worst Fit.
    // Finally, dealloc(8) is attempted.
    std::vector<MemoryOperation> workload = {
        MemoryOperation::alloc(1, 300),
        MemoryOperation::alloc(2, 50),
        MemoryOperation::alloc(3, 200),
        MemoryOperation::alloc(4, 50),
        MemoryOperation::alloc(5, 400),
        MemoryOperation::dealloc(1),
        MemoryOperation::dealloc(3),
        MemoryOperation::dealloc(5),
        MemoryOperation::alloc(6, 180),
        MemoryOperation::alloc(7, 250),
        MemoryOperation::alloc(8, 350), // Succeeds under Best Fit; fails under First Fit and Worst Fit
        MemoryOperation::dealloc(8)     // Deallocate logical request 8
    };

    auto result = MemoryComparator::compare_all(1000, workload);

    const auto* ff = result.find(AllocationStrategy::FirstFit);
    const auto* bf = result.find(AllocationStrategy::BestFit);
    const auto* wf = result.find(AllocationStrategy::WorstFit);

    ASSERT_NE(ff, nullptr);
    ASSERT_NE(bf, nullptr);
    ASSERT_NE(wf, nullptr);

    // 1. Verify allocation outcome of request 8 before deallocation
    EXPECT_FALSE(ff->allocation_results[7].success);
    EXPECT_TRUE(bf->allocation_results[7].success);
    EXPECT_FALSE(wf->allocation_results[7].success);

    // 2. Allocation attempt, success, and failure counters are unchanged by deallocation
    EXPECT_EQ(ff->allocation_requests_attempted, 8);
    EXPECT_EQ(ff->successful_allocations, 7);
    EXPECT_EQ(ff->failed_allocations, 1);
    EXPECT_DOUBLE_EQ(ff->allocation_success_rate, 0.875);

    EXPECT_EQ(bf->allocation_requests_attempted, 8);
    EXPECT_EQ(bf->successful_allocations, 8);
    EXPECT_EQ(bf->failed_allocations, 0);
    EXPECT_DOUBLE_EQ(bf->allocation_success_rate, 1.0);

    EXPECT_EQ(wf->allocation_requests_attempted, 8);
    EXPECT_EQ(wf->successful_allocations, 7);
    EXPECT_EQ(wf->failed_allocations, 1);
    EXPECT_DOUBLE_EQ(wf->allocation_success_rate, 0.875);

    // 3. Best Fit frees its successful request 8 allocation:
    // Prior to dealloc(8), Best Fit had 880 allocated.
    // After dealloc(8), allocated drops by 350 to 530, restoring [600, 1000) as a 400-byte hole.
    EXPECT_EQ(bf->final_allocated_memory(), 530);
    EXPECT_EQ(bf->final_free_memory(), 470);
    EXPECT_EQ(bf->final_largest_free_block(), 400);
    EXPECT_DOUBLE_EQ(bf->final_external_fragmentation(), 1.0 - (400.0 / 470.0));

    // Confirm request 8 is no longer allocated and hole [600, 1000) is restored in Best Fit layout
    bool bf_req8_found = false;
    bool bf_restored_hole_found = false;
    for (const auto& b : bf->final_blocks) {
        if (b.is_allocated && b.size == 350) {
            bf_req8_found = true;
        }
        if (!b.is_allocated && b.start_address == 600 && b.size == 400) {
            bf_restored_hole_found = true;
        }
    }
    EXPECT_FALSE(bf_req8_found);
    EXPECT_TRUE(bf_restored_hole_found);

    // 4. First Fit and Worst Fit leave all their allocations untouched:
    // Request 8 never succeeded under FF or WF, so dealloc(8) was a safe no-op.
    EXPECT_EQ(ff->final_allocated_memory(), 530);
    EXPECT_EQ(ff->final_free_memory(), 470);
    EXPECT_EQ(ff->final_largest_free_block(), 200);

    EXPECT_EQ(wf->final_allocated_memory(), 530);
    EXPECT_EQ(wf->final_free_memory(), 470);
    EXPECT_EQ(wf->final_largest_free_block(), 220);

    // 5. Memory layout consistency for all three strategies (allocated + free == total)
    for (const auto& entry : result) {
        EXPECT_EQ(entry.final_allocated_memory() + entry.final_free_memory(), 1000);
        std::size_t sum_sizes = 0;
        for (const auto& b : entry.final_blocks) {
            EXPECT_GT(b.size, 0);
            sum_sizes += b.size;
        }
        EXPECT_EQ(sum_sizes, 1000);
    }
}

// 7. Unknown, non-positive, and repeated deallocations do not affect memory or statistics
TEST(OScopeMemoryComparisonTest, UnknownAndRepeatedDeallocationsHandledSafely) {
    std::vector<MemoryOperation> workload = {
        MemoryOperation::alloc(1, 250),
        MemoryOperation::dealloc(999),  // Unknown ID
        MemoryOperation::dealloc(-5),   // Non-positive ID
        MemoryOperation::dealloc(1),    // Valid deallocation
        MemoryOperation::dealloc(1)     // Repeated deallocation
    };

    auto result = MemoryComparator::compare_all(1000, workload);

    for (const auto& entry : result) {
        // Only 1 allocation attempted and succeeded; deallocations do not increment failures
        EXPECT_EQ(entry.allocation_requests_attempted, 1);
        EXPECT_EQ(entry.successful_allocations, 1);
        EXPECT_EQ(entry.failed_allocations, 0);
        EXPECT_DOUBLE_EQ(entry.allocation_success_rate, 1.0);

        EXPECT_EQ(entry.final_allocated_memory(), 0);
        EXPECT_EQ(entry.final_free_memory(), 1000);
        EXPECT_EQ(entry.final_largest_free_block(), 1000);
    }
}

// 8. Strict logical ID isolation prevents accidental freeing of other requests
TEST(OScopeMemoryComparisonTest, PreventsAccidentalFreeingOfOtherAllocations) {
    std::vector<MemoryOperation> workload = {
        MemoryOperation::alloc(1, 200),
        MemoryOperation::alloc(2, 300),
        MemoryOperation::dealloc(1),   // Free request 1 only
        MemoryOperation::dealloc(1)    // Repeated free of 1 must not free request 2
    };

    auto result = MemoryComparator::compare_all(1000, workload);

    for (const auto& entry : result) {
        EXPECT_EQ(entry.final_allocated_memory(), 300);
        EXPECT_EQ(entry.final_free_memory(), 700);

        // Only request 2 remains in memory
        bool found_req2 = false;
        for (const auto& b : entry.final_blocks) {
            if (b.is_allocated && b.size == 300) {
                found_req2 = true;
            }
        }
        EXPECT_TRUE(found_req2);
    }
}

// 9. Equivalent initial memory and workload isolation across strategies
TEST(OScopeMemoryComparisonTest, WorkloadIsolationAcrossStrategies) {
    // Workload where strategies will diverge:
    // Create holes: 300 (at 0), 200 (at 350), 400 (at 600)
    std::vector<MemoryOperation> workload = {
        MemoryOperation::alloc(1, 300),
        MemoryOperation::alloc(2, 50),
        MemoryOperation::alloc(3, 200),
        MemoryOperation::alloc(4, 50),
        MemoryOperation::alloc(5, 400),
        MemoryOperation::dealloc(1),
        MemoryOperation::dealloc(3),
        MemoryOperation::dealloc(5),
        MemoryOperation::alloc(6, 180) // FF picks hole 0, BF picks hole 350, WF picks hole 600
    };

    auto result = MemoryComparator::compare_all(1000, workload);

    const auto* ff = result.find(AllocationStrategy::FirstFit);
    const auto* bf = result.find(AllocationStrategy::BestFit);
    const auto* wf = result.find(AllocationStrategy::WorstFit);

    ASSERT_NE(ff, nullptr);
    ASSERT_NE(bf, nullptr);
    ASSERT_NE(wf, nullptr);

    // Each strategy placed Request 6 at a different address independently:
    EXPECT_EQ(ff->allocation_results[5].start_address, 0);
    EXPECT_EQ(bf->allocation_results[5].start_address, 350);
    EXPECT_EQ(wf->allocation_results[5].start_address, 600);

    // Separators (Req 2 and Req 4) remain untouched in all strategies
    for (const auto& entry : result) {
        EXPECT_EQ(entry.final_allocated_memory(), 50 + 50 + 180); // 280
        EXPECT_EQ(entry.final_free_memory(), 720);
    }
}

// 10. Correct allocation attempt/success/failure counts and success rates
TEST(OScopeMemoryComparisonTest, CountsAttemptsSuccessesFailuresAndRatesCorrectly) {
    std::vector<MemoryOperation> workload = {
        MemoryOperation::alloc(1, 200),   // Success
        MemoryOperation::alloc(2, 0),     // Failure: zero size
        MemoryOperation::alloc(3, 5000),  // Failure: capacity exceeded
        MemoryOperation::alloc(-4, 100),  // Failure: negative logical ID
        MemoryOperation::alloc(5, 300)    // Success
    };

    auto result = MemoryComparator::compare_all(1000, workload);

    for (const auto& entry : result) {
        EXPECT_EQ(entry.allocation_requests_attempted, 5);
        EXPECT_EQ(entry.successful_allocations, 2);
        EXPECT_EQ(entry.failed_allocations, 3);
        EXPECT_DOUBLE_EQ(entry.allocation_success_rate, 2.0 / 5.0);

        EXPECT_TRUE(entry.allocation_results[0].success);
        EXPECT_FALSE(entry.allocation_results[1].success);
        EXPECT_FALSE(entry.allocation_results[2].success);
        EXPECT_FALSE(entry.allocation_results[3].success);
        EXPECT_TRUE(entry.allocation_results[4].success);
    }
}

// 11. Final metrics and memory layout consistency (allocated + free == total)
TEST(OScopeMemoryComparisonTest, FinalMetricsAndMemoryLayoutConsistency) {
    std::vector<MemoryOperation> workload = {
        MemoryOperation::alloc(1, 150),
        MemoryOperation::alloc(2, 250),
        MemoryOperation::alloc(3, 350),
        MemoryOperation::dealloc(2)
    };

    auto result = MemoryComparator::compare_all(1000, workload);

    for (const auto& entry : result) {
        EXPECT_EQ(entry.final_allocated_memory() + entry.final_free_memory(), 1000);
        EXPECT_EQ(entry.final_metrics.total_memory, 1000);

        std::size_t sum_blocks = 0;
        for (const auto& b : entry.final_blocks) {
            EXPECT_GT(b.size, 0);
            sum_blocks += b.size;
        }
        EXPECT_EQ(sum_blocks, 1000);
    }
}

// 12. Full discriminating workload with exact placement addresses, outcomes, and metrics
TEST(OScopeMemoryComparisonTest, ExecutesFullDiscriminatingWorkloadAccurately) {
    // Exact 11-step sequence:
    // 1. Allocate req 1: 300
    // 2. Allocate req 2: 50
    // 3. Allocate req 3: 200
    // 4. Allocate req 4: 50
    // 5. Allocate req 5: 400
    // 6. Deallocate req 1, 3, 5
    // 7. Allocate req 6: 180
    // 8. Allocate req 7: 250
    // 9. Allocate req 8: 350
    std::vector<MemoryOperation> workload = {
        MemoryOperation::alloc(1, 300),
        MemoryOperation::alloc(2, 50),
        MemoryOperation::alloc(3, 200),
        MemoryOperation::alloc(4, 50),
        MemoryOperation::alloc(5, 400),
        MemoryOperation::dealloc(1),
        MemoryOperation::dealloc(3),
        MemoryOperation::dealloc(5),
        MemoryOperation::alloc(6, 180),
        MemoryOperation::alloc(7, 250),
        MemoryOperation::alloc(8, 350)
    };

    auto result = MemoryComparator::compare_all(1000, workload);

    const auto* ff = result.find(AllocationStrategy::FirstFit);
    const auto* bf = result.find(AllocationStrategy::BestFit);
    const auto* wf = result.find(AllocationStrategy::WorstFit);

    ASSERT_NE(ff, nullptr);
    ASSERT_NE(bf, nullptr);
    ASSERT_NE(wf, nullptr);

    // --- Placement of Request 6 (180 bytes) ---
    // First Fit: address 0 (Hole A, 300)
    EXPECT_TRUE(ff->allocation_results[5].success);
    EXPECT_EQ(ff->allocation_results[5].start_address, 0);

    // Best Fit: address 350 (Hole B, 200)
    EXPECT_TRUE(bf->allocation_results[5].success);
    EXPECT_EQ(bf->allocation_results[5].start_address, 350);

    // Worst Fit: address 600 (Hole C, 400)
    EXPECT_TRUE(wf->allocation_results[5].success);
    EXPECT_EQ(wf->allocation_results[5].start_address, 600);

    // --- Placement of Request 7 (250 bytes) ---
    // First Fit: address 600 (Hole C, 400)
    EXPECT_TRUE(ff->allocation_results[6].success);
    EXPECT_EQ(ff->allocation_results[6].start_address, 600);

    // Best Fit: address 0 (Hole A, 300)
    EXPECT_TRUE(bf->allocation_results[6].success);
    EXPECT_EQ(bf->allocation_results[6].start_address, 0);

    // Worst Fit: address 0 (Hole A, 300)
    EXPECT_TRUE(wf->allocation_results[6].success);
    EXPECT_EQ(wf->allocation_results[6].start_address, 0);

    // --- Outcome of Request 8 (350 bytes) ---
    // First Fit: FAILS (free holes: 120, 200, 150 -> max block is 200)
    EXPECT_FALSE(ff->allocation_results[7].success);
    EXPECT_EQ(ff->allocation_results[7].error_message, "Insufficient contiguous free memory.");

    // Best Fit: SUCCEEDS at address 600 (free holes: 50, 20, 400 -> fits in 400)
    EXPECT_TRUE(bf->allocation_results[7].success);
    EXPECT_EQ(bf->allocation_results[7].start_address, 600);

    // Worst Fit: FAILS (free holes: 50, 200, 220 -> max block is 220)
    EXPECT_FALSE(wf->allocation_results[7].success);
    EXPECT_EQ(wf->allocation_results[7].error_message, "Insufficient contiguous free memory.");

    // --- Allocation Statistics ---
    // First Fit: 7 successes out of 8 attempts; rate 0.875
    EXPECT_EQ(ff->allocation_requests_attempted, 8);
    EXPECT_EQ(ff->successful_allocations, 7);
    EXPECT_EQ(ff->failed_allocations, 1);
    EXPECT_DOUBLE_EQ(ff->allocation_success_rate, 0.875);

    // Best Fit: 8 successes out of 8 attempts; rate 1.0
    EXPECT_EQ(bf->allocation_requests_attempted, 8);
    EXPECT_EQ(bf->successful_allocations, 8);
    EXPECT_EQ(bf->failed_allocations, 0);
    EXPECT_DOUBLE_EQ(bf->allocation_success_rate, 1.0);

    // Worst Fit: 7 successes out of 8 attempts; rate 0.875
    EXPECT_EQ(wf->allocation_requests_attempted, 8);
    EXPECT_EQ(wf->successful_allocations, 7);
    EXPECT_EQ(wf->failed_allocations, 1);
    EXPECT_DOUBLE_EQ(wf->allocation_success_rate, 0.875);

    // --- Final Metrics ---
    // First Fit: allocated 530, free 470, largest 200
    EXPECT_EQ(ff->final_allocated_memory(), 530);
    EXPECT_EQ(ff->final_free_memory(), 470);
    EXPECT_EQ(ff->final_largest_free_block(), 200);
    EXPECT_DOUBLE_EQ(ff->final_external_fragmentation(), 1.0 - (200.0 / 470.0));
    EXPECT_EQ(ff->final_allocated_memory() + ff->final_free_memory(), 1000);

    // Best Fit: allocated 880, free 120, largest 50
    EXPECT_EQ(bf->final_allocated_memory(), 880);
    EXPECT_EQ(bf->final_free_memory(), 120);
    EXPECT_EQ(bf->final_largest_free_block(), 50);
    EXPECT_DOUBLE_EQ(bf->final_external_fragmentation(), 1.0 - (50.0 / 120.0));
    EXPECT_EQ(bf->final_allocated_memory() + bf->final_free_memory(), 1000);

    // Worst Fit: allocated 530, free 470, largest 220
    EXPECT_EQ(wf->final_allocated_memory(), 530);
    EXPECT_EQ(wf->final_free_memory(), 470);
    EXPECT_EQ(wf->final_largest_free_block(), 220);
    EXPECT_DOUBLE_EQ(wf->final_external_fragmentation(), 1.0 - (220.0 / 470.0));
    EXPECT_EQ(wf->final_allocated_memory() + wf->final_free_memory(), 1000);
}
