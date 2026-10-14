#include <gtest/gtest.h>

#include <memory>
#include <stdexcept>
#include <vector>

#include "oscope/paging/lru.hpp"
#include "oscope/paging/page_replacement_algorithm.hpp"
#include "oscope/paging/page_replacement_result.hpp"

// 1. Known reference string [7, 0, 1, 2, 0, 3, 0, 4, 2, 3, 0, 3, 2, 1, 2, 0, 1, 7, 0, 1] with 3 frames
// Exactly 12 faults and 8 hits for LRU
TEST(OScopePagingLRUTest, MatchesSilberschatzTextbookExample) {
    oscope::LRU lru;
    const std::vector<int> ref = {
        7, 0, 1, 2, 0, 3, 0, 4, 2, 3, 0, 3, 2, 1, 2, 0, 1, 7, 0, 1
    };
    auto result = lru.simulate(ref, 3);

    EXPECT_EQ(result.total_references, 20);
    EXPECT_EQ(result.page_faults, 12);
    EXPECT_EQ(result.page_hits, 8);
    EXPECT_DOUBLE_EQ(result.fault_rate, 12.0 / 20.0);
    EXPECT_DOUBLE_EQ(result.hit_rate, 8.0 / 20.0);
    ASSERT_EQ(result.steps.size(), 20);
}

// 2. Empty reference string
TEST(OScopePagingLRUTest, HandlesEmptyReferenceString) {
    oscope::LRU lru;
    auto result = lru.simulate({}, 3);

    EXPECT_EQ(result.total_references, 0);
    EXPECT_EQ(result.page_faults, 0);
    EXPECT_EQ(result.page_hits, 0);
    EXPECT_DOUBLE_EQ(result.fault_rate, 0.0);
    EXPECT_DOUBLE_EQ(result.hit_rate, 0.0);
    EXPECT_TRUE(result.steps.empty());
}

// 3. Repeated references and all-hits behavior within frame capacity
TEST(OScopePagingLRUTest, HandlesRepeatedReferencesAndAllHitsWithinCapacity) {
    oscope::LRU lru;
    const std::vector<int> ref = {1, 2, 1, 2, 1, 2, 1};
    auto result = lru.simulate(ref, 2);

    EXPECT_EQ(result.total_references, 7);
    EXPECT_EQ(result.page_faults, 2);
    EXPECT_EQ(result.page_hits, 5);
    EXPECT_DOUBLE_EQ(result.fault_rate, 2.0 / 7.0);
    EXPECT_DOUBLE_EQ(result.hit_rate, 5.0 / 7.0);
}

// 4. Sequence that distinguishes LRU from FIFO
// Reference: 1, 2, 3, 1, 4 with 3 frames
// - Step 0 (1): fault, frames [1, -1, -1]
// - Step 1 (2): fault, frames [1, 2, -1]
// - Step 2 (3): fault, frames [1, 2, 3]
// - Step 3 (1): hit! Updates last-used time for 1. (Resident: 1, 2, 3; LRU is 2)
// - Step 4 (4): fault. Under FIFO, 1 would be evicted (oldest arrival).
//   Under LRU, 2 is evicted (oldest reference).
TEST(OScopePagingLRUTest, DistinguishesLRUFromFIFO) {
    oscope::LRU lru;
    const std::vector<int> ref = {1, 2, 3, 1, 4};
    auto result = lru.simulate(ref, 3);

    ASSERT_EQ(result.steps.size(), 5);
    // Step 3 was a hit on 1
    EXPECT_EQ(result.steps[3].page, 1);
    EXPECT_FALSE(result.steps[3].is_fault);
    EXPECT_EQ(result.steps[3].evicted_page, std::nullopt);

    // Step 4 evicts 2 (not 1)
    EXPECT_EQ(result.steps[4].page, 4);
    EXPECT_TRUE(result.steps[4].is_fault);
    EXPECT_EQ(result.steps[4].evicted_page, 2);
    EXPECT_EQ(result.steps[4].frames, (std::vector<int>{1, 4, 3}));
}

// 5. Correct frame snapshots and evicted-page reporting (exact frame_count with -1 for empty slots)
TEST(OScopePagingLRUTest, CorrectFrameSnapshotsAndEvictedPageReporting) {
    oscope::LRU lru;
    const std::vector<int> ref = {5, 6, 7, 8};
    auto result = lru.simulate(ref, 3);

    ASSERT_EQ(result.steps.size(), 4);

    // Step 0: slot 0 filled, slots 1 and 2 are -1
    EXPECT_EQ(result.steps[0].frames, (std::vector<int>{5, -1, -1}));
    EXPECT_TRUE(result.steps[0].is_fault);
    EXPECT_EQ(result.steps[0].evicted_page, std::nullopt);

    // Step 1: slots 0 and 1 filled, slot 2 is -1
    EXPECT_EQ(result.steps[1].frames, (std::vector<int>{5, 6, -1}));
    EXPECT_TRUE(result.steps[1].is_fault);
    EXPECT_EQ(result.steps[1].evicted_page, std::nullopt);

    // Step 2: all 3 slots filled
    EXPECT_EQ(result.steps[2].frames, (std::vector<int>{5, 6, 7}));
    EXPECT_TRUE(result.steps[2].is_fault);
    EXPECT_EQ(result.steps[2].evicted_page, std::nullopt);

    // Step 3: page 8 causes fault; 5 is LRU -> evicts 5 from slot 0
    EXPECT_EQ(result.steps[3].frames, (std::vector<int>{8, 6, 7}));
    EXPECT_TRUE(result.steps[3].is_fault);
    EXPECT_EQ(result.steps[3].evicted_page, 5);
}

// 6. Invalid zero and negative frame counts
TEST(OScopePagingLRUTest, RejectsInvalidFrameCounts) {
    oscope::LRU lru;
    EXPECT_THROW(lru.simulate({1, 2}, 0), std::invalid_argument);
    EXPECT_THROW(lru.simulate({1, 2}, -1), std::invalid_argument);
    EXPECT_THROW(lru.simulate({1, 2}, -10), std::invalid_argument);
}

// 7. Negative page numbers
TEST(OScopePagingLRUTest, RejectsNegativePageNumbers) {
    oscope::LRU lru;
    EXPECT_THROW(lru.simulate({1, -2, 3}, 3), std::invalid_argument);
    EXPECT_THROW(lru.simulate({-1}, 2), std::invalid_argument);
}

// 8. Correct fault and hit rates, including zero references
TEST(OScopePagingLRUTest, ComputesCorrectRates) {
    oscope::LRU lru;

    // Zero references
    auto zero_res = lru.simulate({}, 4);
    EXPECT_DOUBLE_EQ(zero_res.fault_rate, 0.0);
    EXPECT_DOUBLE_EQ(zero_res.hit_rate, 0.0);

    // 4 references: 3 faults, 1 hit
    auto res = lru.simulate({1, 2, 1, 3}, 2);
    EXPECT_EQ(res.total_references, 4);
    EXPECT_EQ(res.page_faults, 3);
    EXPECT_EQ(res.page_hits, 1);
    EXPECT_DOUBLE_EQ(res.fault_rate, 0.75);
    EXPECT_DOUBLE_EQ(res.hit_rate, 0.25);
}

// 9. Polymorphic invocation through base interface
TEST(OScopePagingLRUTest, PolymorphicInvocationThroughBasePointer) {
    std::unique_ptr<oscope::PageReplacementAlgorithm> algo = std::make_unique<oscope::LRU>();
    auto result = algo->simulate({1, 2, 3, 2, 1}, 2);

    EXPECT_EQ(result.total_references, 5);
    EXPECT_GE(result.page_faults, 1);
    EXPECT_LE(result.page_faults, 5);
}
