#include <gtest/gtest.h>

#include <memory>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

#include "oscope/paging/fifo.hpp"
#include "oscope/paging/lru.hpp"
#include "oscope/paging/optimal.hpp"
#include "oscope/paging/page_replacement_comparison.hpp"

// 1. Correct comparison of all three algorithms with default initialization
TEST(OScopePagingComparisonTest, InitializesWithDefaultAlgorithmsAndCompares) {
    oscope::PageReplacementComparator comparator;

    EXPECT_EQ(comparator.size(), 3);
    EXPECT_FALSE(comparator.empty());

    const std::vector<int> ref = {1, 2, 3, 4, 1, 2};
    const int frame_count = 3;

    auto result = comparator.compare(ref, frame_count);

    EXPECT_EQ(result.size(), 3);
    EXPECT_FALSE(result.empty());
    EXPECT_EQ(result.reference_string, ref);
    EXPECT_EQ(result.frame_count, frame_count);

    EXPECT_NE(result.find("FIFO"), nullptr);
    EXPECT_NE(result.find("LRU"), nullptr);
    EXPECT_NE(result.find("Optimal"), nullptr);
    EXPECT_EQ(result.find("NonExistent"), nullptr);

    EXPECT_EQ(result[0].algorithm_name, "FIFO");
    EXPECT_EQ(result[1].algorithm_name, "LRU");
    EXPECT_EQ(result[2].algorithm_name, "Optimal");
}

// 2. Identical input and frame count supplied to each algorithm
TEST(OScopePagingComparisonTest, SuppliesIdenticalInputAndFrameCountToAllAlgorithms) {
    const std::vector<int> ref = {2, 3, 2, 1, 5, 2, 4, 5, 3, 2, 5, 2};
    const int frame_count = 3;

    auto result = oscope::PageReplacementComparator::compare_all(ref, frame_count);

    ASSERT_EQ(result.size(), 3);
    EXPECT_EQ(result.reference_string, ref);
    EXPECT_EQ(result.frame_count, frame_count);

    for (const auto& entry : result) {
        EXPECT_EQ(entry.total_references(), static_cast<int>(ref.size()));
        EXPECT_EQ(entry.steps().size(), ref.size());

        for (std::size_t i = 0; i < ref.size(); ++i) {
            EXPECT_EQ(entry.steps()[i].page, ref[i]);
            EXPECT_EQ(entry.steps()[i].frames.size(), static_cast<std::size_t>(frame_count));
        }

        // Faults + hits must equal total references
        EXPECT_EQ(entry.page_faults() + entry.page_hits(), entry.total_references());
        EXPECT_DOUBLE_EQ(entry.fault_rate() + entry.hit_rate(), 1.0);
    }
}

// 3. Known textbook reference string and expected fault counts (Silberschatz Chapter 10)
// Reference string: 7, 0, 1, 2, 0, 3, 0, 4, 2, 3, 0, 3, 2, 1, 2, 0, 1, 7, 0, 1
// Frame count: 3
// Expected:
// FIFO:    15 faults, 5 hits
// LRU:     12 faults, 8 hits
// Optimal:  9 faults, 11 hits
TEST(OScopePagingComparisonTest, MatchesTextbookExpectedFaultCounts) {
    const std::vector<int> ref = {
        7, 0, 1, 2, 0, 3, 0, 4, 2, 3, 0, 3, 2, 1, 2, 0, 1, 7, 0, 1
    };
    const int frame_count = 3;

    auto result = oscope::PageReplacementComparator::compare_all(ref, frame_count);

    ASSERT_EQ(result.size(), 3);

    const auto* fifo_entry = result.find("FIFO");
    const auto* lru_entry = result.find("LRU");
    const auto* opt_entry = result.find("Optimal");

    ASSERT_NE(fifo_entry, nullptr);
    ASSERT_NE(lru_entry, nullptr);
    ASSERT_NE(opt_entry, nullptr);

    // FIFO checks
    EXPECT_EQ(fifo_entry->total_references(), 20);
    EXPECT_EQ(fifo_entry->page_faults(), 15);
    EXPECT_EQ(fifo_entry->page_hits(), 5);
    EXPECT_DOUBLE_EQ(fifo_entry->fault_rate(), 15.0 / 20.0);
    EXPECT_DOUBLE_EQ(fifo_entry->hit_rate(), 5.0 / 20.0);

    // LRU checks
    EXPECT_EQ(lru_entry->total_references(), 20);
    EXPECT_EQ(lru_entry->page_faults(), 12);
    EXPECT_EQ(lru_entry->page_hits(), 8);
    EXPECT_DOUBLE_EQ(lru_entry->fault_rate(), 12.0 / 20.0);
    EXPECT_DOUBLE_EQ(lru_entry->hit_rate(), 8.0 / 20.0);

    // Optimal checks
    EXPECT_EQ(opt_entry->total_references(), 20);
    EXPECT_EQ(opt_entry->page_faults(), 9);
    EXPECT_EQ(opt_entry->page_hits(), 11);
    EXPECT_DOUBLE_EQ(opt_entry->fault_rate(), 9.0 / 20.0);
    EXPECT_DOUBLE_EQ(opt_entry->hit_rate(), 11.0 / 20.0);

    // Optimal has strictly fewest faults, FIFO has most faults
    EXPECT_LT(opt_entry->page_faults(), lru_entry->page_faults());
    EXPECT_LT(lru_entry->page_faults(), fifo_entry->page_faults());
}

// 4. Empty reference string handling
TEST(OScopePagingComparisonTest, HandlesEmptyReferenceString) {
    oscope::PageReplacementComparator comparator;
    auto result = comparator.compare({}, 4);

    EXPECT_EQ(result.size(), 3);
    EXPECT_TRUE(result.reference_string.empty());
    EXPECT_EQ(result.frame_count, 4);

    for (const auto& entry : result) {
        EXPECT_EQ(entry.total_references(), 0);
        EXPECT_EQ(entry.page_faults(), 0);
        EXPECT_EQ(entry.page_hits(), 0);
        EXPECT_DOUBLE_EQ(entry.fault_rate(), 0.0);
        EXPECT_DOUBLE_EQ(entry.hit_rate(), 0.0);
        EXPECT_TRUE(entry.steps().empty());
    }
}

// 5. Invalid frame count rejection
TEST(OScopePagingComparisonTest, RejectsInvalidFrameCount) {
    oscope::PageReplacementComparator comparator;
    const std::vector<int> ref = {1, 2, 3};

    EXPECT_THROW(comparator.compare(ref, 0), std::invalid_argument);
    EXPECT_THROW(comparator.compare(ref, -1), std::invalid_argument);
    EXPECT_THROW(comparator.compare(ref, -10), std::invalid_argument);

    EXPECT_THROW(oscope::PageReplacementComparator::compare_all(ref, 0), std::invalid_argument);
    EXPECT_THROW(oscope::PageReplacementComparator::compare_all(ref, -1), std::invalid_argument);
}

// 6. Negative page number rejection
TEST(OScopePagingComparisonTest, RejectsNegativePageNumbers) {
    oscope::PageReplacementComparator comparator;

    EXPECT_THROW(comparator.compare({1, -2, 3}, 3), std::invalid_argument);
    EXPECT_THROW(comparator.compare({-1}, 2), std::invalid_argument);
    EXPECT_THROW(comparator.compare({0, 1, 2, -5}, 3), std::invalid_argument);

    EXPECT_THROW(oscope::PageReplacementComparator::compare_all({-3, 0}, 2), std::invalid_argument);
}

// 7. Retention of individual reference-step history and frame snapshots
TEST(OScopePagingComparisonTest, RetainsStepHistoryAndFrameSnapshotsForEveryAlgorithm) {
    // Workload where FIFO, LRU, and Optimal make distinct eviction choices at step 4 (page 4):
    // Sequence: 1, 2, 3, 1, 4, 2, 1, 3 with 3 frames
    // Step 0: 1 -> [1, -1, -1]
    // Step 1: 2 -> [1, 2, -1]
    // Step 2: 3 -> [1, 2, 3]
    // Step 3: 1 -> [1, 2, 3] (hit)
    // Step 4: 4 -> eviction!
    //   FIFO:    evicts page 1 (oldest loaded) -> [4, 2, 3]
    //   LRU:     evicts page 2 (least recently used) -> [1, 4, 3]
    //   Optimal: future is 2, 1, 3. Farthest is 3 -> evicts 3 -> [1, 2, 4]
    const std::vector<int> ref = {1, 2, 3, 1, 4, 2, 1, 3};
    const int frame_count = 3;

    auto result = oscope::PageReplacementComparator::compare_all(ref, frame_count);

    ASSERT_EQ(result.size(), 3);

    const auto* fifo_entry = result.find("FIFO");
    const auto* lru_entry = result.find("LRU");
    const auto* opt_entry = result.find("Optimal");

    ASSERT_NE(fifo_entry, nullptr);
    ASSERT_NE(lru_entry, nullptr);
    ASSERT_NE(opt_entry, nullptr);

    // Verify all steps are preserved
    ASSERT_EQ(fifo_entry->steps().size(), 8);
    ASSERT_EQ(lru_entry->steps().size(), 8);
    ASSERT_EQ(opt_entry->steps().size(), 8);

    // Verify Step 3 is a hit on page 1 for all 3 algorithms
    EXPECT_FALSE(fifo_entry->steps()[3].is_fault);
    EXPECT_EQ(fifo_entry->steps()[3].page, 1);
    EXPECT_EQ(fifo_entry->steps()[3].evicted_page, std::nullopt);

    EXPECT_FALSE(lru_entry->steps()[3].is_fault);
    EXPECT_EQ(lru_entry->steps()[3].page, 1);
    EXPECT_EQ(lru_entry->steps()[3].evicted_page, std::nullopt);

    EXPECT_FALSE(opt_entry->steps()[3].is_fault);
    EXPECT_EQ(opt_entry->steps()[3].page, 1);
    EXPECT_EQ(opt_entry->steps()[3].evicted_page, std::nullopt);

    // Verify distinct Step 4 eviction decisions and frame snapshots
    // FIFO evicts 1
    EXPECT_TRUE(fifo_entry->steps()[4].is_fault);
    EXPECT_EQ(fifo_entry->steps()[4].page, 4);
    EXPECT_EQ(fifo_entry->steps()[4].evicted_page, 1);
    EXPECT_EQ(fifo_entry->steps()[4].frames, (std::vector<int>{4, 2, 3}));

    // LRU evicts 2
    EXPECT_TRUE(lru_entry->steps()[4].is_fault);
    EXPECT_EQ(lru_entry->steps()[4].page, 4);
    EXPECT_EQ(lru_entry->steps()[4].evicted_page, 2);
    EXPECT_EQ(lru_entry->steps()[4].frames, (std::vector<int>{1, 4, 3}));

    // Optimal evicts 3
    EXPECT_TRUE(opt_entry->steps()[4].is_fault);
    EXPECT_EQ(opt_entry->steps()[4].page, 4);
    EXPECT_EQ(opt_entry->steps()[4].evicted_page, 3);
    EXPECT_EQ(opt_entry->steps()[4].frames, (std::vector<int>{1, 2, 4}));
}

// 8. Custom algorithm registration, clear, size, and empty
TEST(OScopePagingComparisonTest, SupportsCustomAlgorithmRegistrationAndClear) {
    oscope::PageReplacementComparator comparator;
    comparator.clear();

    EXPECT_EQ(comparator.size(), 0);
    EXPECT_TRUE(comparator.empty());

    auto fifo = std::make_shared<oscope::FIFO>();
    oscope::LRU lru;

    comparator.add_algorithm("Custom-FIFO", fifo);
    comparator.add_algorithm("Custom-LRU", lru);

    EXPECT_EQ(comparator.size(), 2);
    EXPECT_FALSE(comparator.empty());

    const std::vector<int> ref = {1, 2, 1, 3};
    auto result = comparator.compare(ref, 2);

    ASSERT_EQ(result.size(), 2);
    EXPECT_EQ(result[0].algorithm_name, "Custom-FIFO");
    EXPECT_EQ(result[1].algorithm_name, "Custom-LRU");
}

// 9. Null algorithm pointer rejection
TEST(OScopePagingComparisonTest, RejectsNullAlgorithmPointers) {
    oscope::PageReplacementComparator comparator;
    std::shared_ptr<oscope::PageReplacementAlgorithm> null_shared = nullptr;

    EXPECT_THROW(comparator.add_algorithm("NullAlgo", null_shared), std::invalid_argument);

    const std::vector<int> ref = {1, 2};
    const std::vector<std::pair<std::string, oscope::PageReplacementAlgorithm*>> null_raw_list = {
        {"NullRaw", nullptr}
    };
    EXPECT_THROW(
        oscope::PageReplacementComparator::compare(ref, 2, null_raw_list),
        std::invalid_argument
    );

    const std::vector<std::pair<std::string, std::shared_ptr<oscope::PageReplacementAlgorithm>>> null_shared_list = {
        {"NullShared", nullptr}
    };
    EXPECT_THROW(
        oscope::PageReplacementComparator::compare(ref, 2, null_shared_list),
        std::invalid_argument
    );
}

// 10. Namespace alias support
TEST(OScopePagingComparisonTest, SupportsPagingNamespaceAliases) {
    oscope::paging::PageReplacementComparator comparator;
    oscope::paging::PageReplacementComparisonResult result =
        comparator.compare({1, 2, 1}, 2);

    ASSERT_EQ(result.size(), 3);
    for (const oscope::paging::PageReplacementComparisonEntry& entry : result) {
        EXPECT_EQ(entry.total_references(), 3);
    }
}
