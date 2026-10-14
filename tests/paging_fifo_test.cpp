#include <gtest/gtest.h>

#include <memory>
#include <stdexcept>
#include <vector>

#include "oscope/paging/fifo.hpp"
#include "oscope/paging/page_replacement_algorithm.hpp"
#include "oscope/paging/page_replacement_result.hpp"

// 1. Rejects non-positive frame count
TEST(OScopePagingFIFOTest, RejectsNonPositiveFrameCount) {
    oscope::FIFO fifo;
    EXPECT_THROW(fifo.simulate({1, 2, 3}, 0), std::invalid_argument);
    EXPECT_THROW(fifo.simulate({1, 2, 3}, -3), std::invalid_argument);
}

// 2. Rejects negative page numbers
TEST(OScopePagingFIFOTest, RejectsNegativePageNumbers) {
    oscope::FIFO fifo;
    EXPECT_THROW(fifo.simulate({1, -2, 3}, 3), std::invalid_argument);
}

// 3. Handles empty reference string cleanly
TEST(OScopePagingFIFOTest, HandlesEmptyReferenceString) {
    oscope::FIFO fifo;
    auto result = fifo.simulate({}, 3);

    EXPECT_EQ(result.total_references, 0);
    EXPECT_EQ(result.page_faults, 0);
    EXPECT_EQ(result.page_hits, 0);
    EXPECT_DOUBLE_EQ(result.fault_rate, 0.0);
    EXPECT_DOUBLE_EQ(result.hit_rate, 0.0);
    EXPECT_TRUE(result.steps.empty());
}

// 4. Single frame simulation
TEST(OScopePagingFIFOTest, SimulatesSingleFrameAccurately) {
    oscope::FIFO fifo;
    const std::vector<int> ref = {1, 1, 2, 1, 2};
    auto result = fifo.simulate(ref, 1);

    EXPECT_EQ(result.total_references, 5);
    EXPECT_EQ(result.page_faults, 4);
    EXPECT_EQ(result.page_hits, 1);

    // Step 0: page 1 fault
    EXPECT_EQ(result.steps[0].page, 1);
    EXPECT_TRUE(result.steps[0].is_fault);
    EXPECT_EQ(result.steps[0].evicted_page, std::nullopt);
    EXPECT_EQ(result.steps[0].frames, std::vector<int>{1});

    // Step 1: page 1 hit
    EXPECT_EQ(result.steps[1].page, 1);
    EXPECT_FALSE(result.steps[1].is_fault);
    EXPECT_EQ(result.steps[1].evicted_page, std::nullopt);
    EXPECT_EQ(result.steps[1].frames, std::vector<int>{1});

    // Step 2: page 2 fault (evicts 1)
    EXPECT_EQ(result.steps[2].page, 2);
    EXPECT_TRUE(result.steps[2].is_fault);
    EXPECT_EQ(result.steps[2].evicted_page, 1);
    EXPECT_EQ(result.steps[2].frames, std::vector<int>{2});
}

// 5. Standard textbook example (Silberschatz Chapter 10)
// Reference string: 7, 0, 1, 2, 0, 3, 0, 4, 2, 3, 0, 3, 2, 1, 2, 0, 1, 7, 0, 1
// Frame count: 3 -> Page faults: 15, Page hits: 5
TEST(OScopePagingFIFOTest, MatchesSilberschatzTextbookExample) {
    oscope::FIFO fifo;
    const std::vector<int> ref = {
        7, 0, 1, 2, 0, 3, 0, 4, 2, 3, 0, 3, 2, 1, 2, 0, 1, 7, 0, 1
    };
    auto result = fifo.simulate(ref, 3);

    EXPECT_EQ(result.total_references, 20);
    EXPECT_EQ(result.page_faults, 15);
    EXPECT_EQ(result.page_hits, 5);
    EXPECT_DOUBLE_EQ(result.fault_rate, 15.0 / 20.0);
    EXPECT_DOUBLE_EQ(result.hit_rate, 5.0 / 20.0);
    ASSERT_EQ(result.steps.size(), 20);

    // Initial 3 allocations (cold misses, no evictions)
    EXPECT_TRUE(result.steps[0].is_fault);
    EXPECT_EQ(result.steps[0].evicted_page, std::nullopt);
    EXPECT_EQ(result.steps[0].frames, (std::vector<int>{7, -1, -1}));

    EXPECT_TRUE(result.steps[1].is_fault);
    EXPECT_EQ(result.steps[1].evicted_page, std::nullopt);
    EXPECT_EQ(result.steps[1].frames, (std::vector<int>{7, 0, -1}));

    EXPECT_TRUE(result.steps[2].is_fault);
    EXPECT_EQ(result.steps[2].evicted_page, std::nullopt);
    EXPECT_EQ(result.steps[2].frames, (std::vector<int>{7, 0, 1}));

    // Step 3 (page 2): evicts 7
    EXPECT_TRUE(result.steps[3].is_fault);
    EXPECT_EQ(result.steps[3].evicted_page, 7);
    EXPECT_EQ(result.steps[3].frames, (std::vector<int>{2, 0, 1}));

    // Step 4 (page 0): hit
    EXPECT_FALSE(result.steps[4].is_fault);
    EXPECT_EQ(result.steps[4].evicted_page, std::nullopt);
    EXPECT_EQ(result.steps[4].frames, (std::vector<int>{2, 0, 1}));

    // Step 5 (page 3): evicts 0
    EXPECT_TRUE(result.steps[5].is_fault);
    EXPECT_EQ(result.steps[5].evicted_page, 0);
    EXPECT_EQ(result.steps[5].frames, (std::vector<int>{2, 3, 1}));
}

// 6. All hits within capacity
TEST(OScopePagingFIFOTest, HandlesAllHitsWithinCapacity) {
    oscope::FIFO fifo;
    const std::vector<int> ref = {1, 2, 1, 2, 1, 2};
    auto result = fifo.simulate(ref, 2);

    EXPECT_EQ(result.total_references, 6);
    EXPECT_EQ(result.page_faults, 2);
    EXPECT_EQ(result.page_hits, 4);
    EXPECT_DOUBLE_EQ(result.fault_rate, 2.0 / 6.0);
    EXPECT_DOUBLE_EQ(result.hit_rate, 4.0 / 6.0);
}

// 7. All faults with unique pages
TEST(OScopePagingFIFOTest, HandlesAllFaultsWithUniquePages) {
    oscope::FIFO fifo;
    const std::vector<int> ref = {1, 2, 3, 4, 5};
    auto result = fifo.simulate(ref, 2);

    EXPECT_EQ(result.total_references, 5);
    EXPECT_EQ(result.page_faults, 5);
    EXPECT_EQ(result.page_hits, 0);
    EXPECT_DOUBLE_EQ(result.fault_rate, 1.0);
    EXPECT_DOUBLE_EQ(result.hit_rate, 0.0);
}

// 8. Demonstrates Belady's Anomaly
// Reference string: 1, 2, 3, 4, 1, 2, 5, 1, 2, 3, 4, 5
// 3 frames: 9 page faults
// 4 frames: 10 page faults (more faults with more frames)
TEST(OScopePagingFIFOTest, DemonstratesBeladysAnomaly) {
    oscope::FIFO fifo;
    const std::vector<int> ref = {1, 2, 3, 4, 1, 2, 5, 1, 2, 3, 4, 5};

    auto result_3_frames = fifo.simulate(ref, 3);
    auto result_4_frames = fifo.simulate(ref, 4);

    EXPECT_EQ(result_3_frames.page_faults, 9);
    EXPECT_EQ(result_4_frames.page_faults, 10);
    EXPECT_GT(result_4_frames.page_faults, result_3_frames.page_faults);
}

// 9. Base class polymorphic invocation
TEST(OScopePagingFIFOTest, PolymorphicInvocationThroughBasePointer) {
    std::unique_ptr<oscope::PageReplacementAlgorithm> algo = std::make_unique<oscope::FIFO>();
    auto result = algo->simulate({1, 2, 3, 1}, 2);

    EXPECT_EQ(result.total_references, 4);
    EXPECT_EQ(result.page_faults, 4);
    EXPECT_EQ(result.page_hits, 0);
}

// 10. Frame snapshots have fixed size equal to frame_count with -1 for empty slots
TEST(OScopePagingFIFOTest, FixedSizeFrameSnapshotsWithEmptySlots) {
    oscope::FIFO fifo;
    const std::vector<int> ref = {5, 6, 7, 8};
    auto result = fifo.simulate(ref, 3);

    ASSERT_EQ(result.steps.size(), 4);

    // Initialization (during filling)
    EXPECT_EQ(result.steps[0].frames, (std::vector<int>{5, -1, -1}));
    EXPECT_EQ(result.steps[0].frames.size(), 3);
    EXPECT_EQ(result.steps[0].evicted_page, std::nullopt);

    EXPECT_EQ(result.steps[1].frames, (std::vector<int>{5, 6, -1}));
    EXPECT_EQ(result.steps[1].frames.size(), 3);
    EXPECT_EQ(result.steps[1].evicted_page, std::nullopt);

    // After filling frames completely
    EXPECT_EQ(result.steps[2].frames, (std::vector<int>{5, 6, 7}));
    EXPECT_EQ(result.steps[2].frames.size(), 3);
    EXPECT_EQ(result.steps[2].evicted_page, std::nullopt);

    // After eviction (FIFO evicts oldest page 5 from slot 0)
    EXPECT_EQ(result.steps[3].frames, (std::vector<int>{8, 6, 7}));
    EXPECT_EQ(result.steps[3].frames.size(), 3);
    EXPECT_EQ(result.steps[3].evicted_page, 5);
}
