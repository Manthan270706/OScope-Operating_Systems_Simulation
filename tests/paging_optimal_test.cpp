#include <gtest/gtest.h>

#include <memory>
#include <stdexcept>
#include <vector>

#include "oscope/paging/optimal.hpp"
#include "oscope/paging/page_replacement_algorithm.hpp"
#include "oscope/paging/page_replacement_result.hpp"

// 1. Standard textbook example (Silberschatz Chapter 10)
// Reference string: 7, 0, 1, 2, 0, 3, 0, 4, 2, 3, 0, 3, 2, 1, 2, 0, 1, 7, 0, 1
// Frame count: 3 -> Page faults: 9, Page hits: 11
TEST(OScopePagingOptimalTest, MatchesSilberschatzTextbookExample) {
    oscope::Optimal optimal;
    const std::vector<int> ref = {
        7, 0, 1, 2, 0, 3, 0, 4, 2, 3, 0, 3, 2, 1, 2, 0, 1, 7, 0, 1
    };
    auto result = optimal.simulate(ref, 3);

    EXPECT_EQ(result.total_references, 20);
    EXPECT_EQ(result.page_faults, 9);
    EXPECT_EQ(result.page_hits, 11);
    EXPECT_DOUBLE_EQ(result.fault_rate, 9.0 / 20.0);
    EXPECT_DOUBLE_EQ(result.hit_rate, 11.0 / 20.0);
    ASSERT_EQ(result.steps.size(), 20);

    // Initial allocations (cold misses, no evictions)
    EXPECT_TRUE(result.steps[0].is_fault);
    EXPECT_EQ(result.steps[0].evicted_page, std::nullopt);
    EXPECT_EQ(result.steps[0].frames, (std::vector<int>{7, -1, -1}));

    EXPECT_TRUE(result.steps[1].is_fault);
    EXPECT_EQ(result.steps[1].evicted_page, std::nullopt);
    EXPECT_EQ(result.steps[1].frames, (std::vector<int>{7, 0, -1}));

    EXPECT_TRUE(result.steps[2].is_fault);
    EXPECT_EQ(result.steps[2].evicted_page, std::nullopt);
    EXPECT_EQ(result.steps[2].frames, (std::vector<int>{7, 0, 1}));

    // Step 3 (page 2): 7 is used at 17, 0 at 4, 1 at 13 -> 7 is farthest, evict 7
    EXPECT_TRUE(result.steps[3].is_fault);
    EXPECT_EQ(result.steps[3].evicted_page, 7);
    EXPECT_EQ(result.steps[3].frames, (std::vector<int>{2, 0, 1}));

    // Step 4 (page 0): hit
    EXPECT_FALSE(result.steps[4].is_fault);
    EXPECT_EQ(result.steps[4].evicted_page, std::nullopt);
    EXPECT_EQ(result.steps[4].frames, (std::vector<int>{2, 0, 1}));

    // Step 5 (page 3): 2 is used at 8, 0 at 6, 1 at 13 -> 1 is farthest, evict 1
    EXPECT_TRUE(result.steps[5].is_fault);
    EXPECT_EQ(result.steps[5].evicted_page, 1);
    EXPECT_EQ(result.steps[5].frames, (std::vector<int>{2, 0, 3}));
}

// 2. Empty reference string
TEST(OScopePagingOptimalTest, HandlesEmptyReferenceString) {
    oscope::Optimal optimal;
    auto result = optimal.simulate({}, 3);

    EXPECT_EQ(result.total_references, 0);
    EXPECT_EQ(result.page_faults, 0);
    EXPECT_EQ(result.page_hits, 0);
    EXPECT_DOUBLE_EQ(result.fault_rate, 0.0);
    EXPECT_DOUBLE_EQ(result.hit_rate, 0.0);
    EXPECT_TRUE(result.steps.empty());
}

// 3. Repeated references and all-hits behavior within frame capacity
TEST(OScopePagingOptimalTest, HandlesRepeatedReferencesAndAllHits) {
    oscope::Optimal optimal;
    const std::vector<int> ref = {1, 2, 1, 2, 1, 2};
    auto result = optimal.simulate(ref, 2);

    EXPECT_EQ(result.total_references, 6);
    EXPECT_EQ(result.page_faults, 2);
    EXPECT_EQ(result.page_hits, 4);
    EXPECT_DOUBLE_EQ(result.fault_rate, 2.0 / 6.0);
    EXPECT_DOUBLE_EQ(result.hit_rate, 4.0 / 6.0);
}

// 4. Eviction decision: evicts the page whose next reference is farthest in future
TEST(OScopePagingOptimalTest, EvictsPageFarthestInFuture) {
    oscope::Optimal optimal;
    // Resident: 1, 2, 3. Next page: 4.
    // Future uses: 2 at index 4, 1 at index 5, 3 at index 6.
    // 3 is farthest in future -> evicts 3 from slot 2.
    const std::vector<int> ref = {1, 2, 3, 4, 2, 1, 3};
    auto result = optimal.simulate(ref, 3);

    ASSERT_EQ(result.steps.size(), 7);
    EXPECT_EQ(result.steps[3].page, 4);
    EXPECT_TRUE(result.steps[3].is_fault);
    EXPECT_EQ(result.steps[3].evicted_page, 3);
    EXPECT_EQ(result.steps[3].frames, (std::vector<int>{1, 2, 4}));

    // Subsequent hits on 2 and 1
    EXPECT_FALSE(result.steps[4].is_fault);
    EXPECT_FALSE(result.steps[5].is_fault);
}

// 5. Eviction decision: prioritizes pages never referenced again
TEST(OScopePagingOptimalTest, PrioritizesPagesNeverReferencedAgain) {
    oscope::Optimal optimal;
    // Resident: 1, 2, 3. Next page: 4.
    // Future uses: 1 at index 4, 2 at index 5, 3 is never referenced again.
    // 3 must be evicted.
    const std::vector<int> ref = {1, 2, 3, 4, 1, 2};
    auto result = optimal.simulate(ref, 3);

    ASSERT_EQ(result.steps.size(), 6);
    EXPECT_EQ(result.steps[3].page, 4);
    EXPECT_TRUE(result.steps[3].is_fault);
    EXPECT_EQ(result.steps[3].evicted_page, 3);
    EXPECT_EQ(result.steps[3].frames, (std::vector<int>{1, 2, 4}));

    // References to 1 and 2 are hits
    EXPECT_FALSE(result.steps[4].is_fault);
    EXPECT_FALSE(result.steps[5].is_fault);
    EXPECT_EQ(result.page_faults, 4);
    EXPECT_EQ(result.page_hits, 2);
}

// 6. Fixed-size frame snapshots with -1 for empty slots
TEST(OScopePagingOptimalTest, FixedSizeFrameSnapshotsWithEmptySlots) {
    oscope::Optimal optimal;
    const std::vector<int> ref = {5, 6, 7, 8};
    auto result = optimal.simulate(ref, 3);

    ASSERT_EQ(result.steps.size(), 4);

    // Initial filling
    EXPECT_EQ(result.steps[0].frames, (std::vector<int>{5, -1, -1}));
    EXPECT_EQ(result.steps[0].frames.size(), 3);
    EXPECT_EQ(result.steps[0].evicted_page, std::nullopt);

    EXPECT_EQ(result.steps[1].frames, (std::vector<int>{5, 6, -1}));
    EXPECT_EQ(result.steps[1].frames.size(), 3);
    EXPECT_EQ(result.steps[1].evicted_page, std::nullopt);

    // Completely filled
    EXPECT_EQ(result.steps[2].frames, (std::vector<int>{5, 6, 7}));
    EXPECT_EQ(result.steps[2].frames.size(), 3);
    EXPECT_EQ(result.steps[2].evicted_page, std::nullopt);

    // Eviction: none of 5, 6, 7 are referenced again; slot 0 (5) is evicted
    EXPECT_EQ(result.steps[3].frames, (std::vector<int>{8, 6, 7}));
    EXPECT_EQ(result.steps[3].frames.size(), 3);
    EXPECT_EQ(result.steps[3].evicted_page, 5);
}

// 7. Invalid frame counts
TEST(OScopePagingOptimalTest, RejectsInvalidFrameCounts) {
    oscope::Optimal optimal;
    EXPECT_THROW(optimal.simulate({1, 2}, 0), std::invalid_argument);
    EXPECT_THROW(optimal.simulate({1, 2}, -1), std::invalid_argument);
    EXPECT_THROW(optimal.simulate({1, 2}, -5), std::invalid_argument);
}

// 8. Negative page numbers
TEST(OScopePagingOptimalTest, RejectsNegativePageNumbers) {
    oscope::Optimal optimal;
    EXPECT_THROW(optimal.simulate({1, -2, 3}, 3), std::invalid_argument);
    EXPECT_THROW(optimal.simulate({-1}, 2), std::invalid_argument);
}

// 9. Correct fault and hit rates
TEST(OScopePagingOptimalTest, ComputesCorrectRates) {
    oscope::Optimal optimal;

    // Zero references
    auto zero_res = optimal.simulate({}, 3);
    EXPECT_DOUBLE_EQ(zero_res.fault_rate, 0.0);
    EXPECT_DOUBLE_EQ(zero_res.hit_rate, 0.0);

    // 4 references: 3 faults, 1 hit
    auto res = optimal.simulate({1, 2, 1, 3}, 2);
    EXPECT_EQ(res.total_references, 4);
    EXPECT_EQ(res.page_faults, 3);
    EXPECT_EQ(res.page_hits, 1);
    EXPECT_DOUBLE_EQ(res.fault_rate, 0.75);
    EXPECT_DOUBLE_EQ(res.hit_rate, 0.25);
}

// 10. Polymorphic invocation through base interface
TEST(OScopePagingOptimalTest, PolymorphicInvocationThroughBasePointer) {
    std::unique_ptr<oscope::PageReplacementAlgorithm> algo = std::make_unique<oscope::Optimal>();
    auto result = algo->simulate({1, 2, 3, 2, 1}, 2);

    EXPECT_EQ(result.total_references, 5);
    EXPECT_GE(result.page_faults, 1);
    EXPECT_LE(result.page_faults, 5);
}
