#include <gtest/gtest.h>

#include "oscope/paging/address_translation.hpp"

using namespace oscope::paging;

TEST(AddressTranslationTest, TranslatesMappedPagesCorrectlyPreservingOffset) {
    AddressTranslator translator(4096);
    translator.map_page(0, 5); // Page 0 -> Frame 5
    translator.map_page(1, 2); // Page 1 -> Frame 2
    translator.map_page(7, 10); // Page 7 -> Frame 10

    // Test VA 0: Page 0, offset 0 -> Frame 5, PA = 5 * 4096 = 20480
    auto res0 = translator.translate(0);
    EXPECT_FALSE(res0.page_fault);
    EXPECT_EQ(res0.page_number, 0u);
    EXPECT_EQ(res0.offset, 0u);
    EXPECT_EQ(res0.frame_number, 5);
    EXPECT_EQ(res0.physical_address, 20480u);

    // Test VA 4100: Page 1, offset 4 -> Frame 2, PA = 2 * 4096 + 4 = 8196
    auto res1 = translator.translate(4100);
    EXPECT_FALSE(res1.page_fault);
    EXPECT_EQ(res1.page_number, 1u);
    EXPECT_EQ(res1.offset, 4u);
    EXPECT_EQ(res1.frame_number, 2);
    EXPECT_EQ(res1.physical_address, 8196u);

    // Test VA 7 * 4096 + 1234 = 29906: Page 7, offset 1234 -> Frame 10, PA = 10 * 4096 + 1234 = 42194
    auto res2 = translator.translate(29906);
    EXPECT_FALSE(res2.page_fault);
    EXPECT_EQ(res2.page_number, 7u);
    EXPECT_EQ(res2.offset, 1234u);
    EXPECT_EQ(res2.frame_number, 10);
    EXPECT_EQ(res2.physical_address, 42194u);
}

TEST(AddressTranslationTest, ReportsPageFaultForUnmappedPages) {
    AddressTranslator translator(4096);
    translator.map_page(2, 4);

    // Page 3 is not mapped
    auto res = translator.translate(3 * 4096 + 50);
    EXPECT_TRUE(res.page_fault);
    EXPECT_EQ(res.page_number, 3u);
    EXPECT_EQ(res.offset, 50u);
    EXPECT_EQ(res.frame_number, -1);
    EXPECT_EQ(res.physical_address, 0u);
}

TEST(AddressTranslationTest, HandlesUnmappingAndPageTableClearing) {
    AddressTranslator translator(1024);
    translator.map_page(5, 1);
    EXPECT_FALSE(translator.translate(5 * 1024).page_fault);

    EXPECT_TRUE(translator.unmap_page(5));
    EXPECT_TRUE(translator.translate(5 * 1024).page_fault);
    EXPECT_FALSE(translator.unmap_page(99)); // unmapping non-existent page

    translator.map_page(1, 0);
    translator.map_page(2, 1);
    translator.clear_page_table();
    EXPECT_TRUE(translator.translate(1 * 1024).page_fault);
    EXPECT_TRUE(translator.translate(2 * 1024).page_fault);
}

TEST(AddressTranslationTest, ValidatesPageSizes) {
    AddressTranslator translator(4096);
    EXPECT_TRUE(translator.set_page_size(512));
    EXPECT_EQ(translator.page_size(), 512u);
    EXPECT_TRUE(translator.set_page_size(1024));
    EXPECT_EQ(translator.page_size(), 1024u);

    // Non-power of two or 0 must be rejected
    EXPECT_FALSE(translator.set_page_size(0));
    EXPECT_FALSE(translator.set_page_size(1000));
    EXPECT_FALSE(translator.set_page_size(300));
    EXPECT_EQ(translator.page_size(), 1024u);
}

TEST(AddressTranslationTest, DemandPagingSimulatesFIFOAllocationAndEviction) {
    // 3 frames, page size 4096
    // Sequence of virtual addresses corresponding to pages: 1, 2, 3, 4, 1, 2, 5, 1, 2, 3, 4, 5
    std::vector<int> pages = {1, 2, 3, 4, 1, 2, 5, 1, 2, 3, 4, 5};
    std::vector<uint64_t> vas;
    for (int p : pages) {
        vas.push_back(static_cast<uint64_t>(p) * 4096 + 10);
    }

    auto result = AddressTranslator::simulate_demand_paging(4096, 3, vas);
    EXPECT_EQ(result.total_accesses, 12);
    EXPECT_EQ(result.page_faults, 9);
    EXPECT_EQ(result.page_hits, 3);
    EXPECT_NEAR(result.fault_rate, 9.0 / 12.0, 1e-6);

    // Check first 3 steps allocate frames 0, 1, 2
    EXPECT_TRUE(result.steps[0].page_fault);
    EXPECT_EQ(result.steps[0].frame_number, 0);
    EXPECT_EQ(result.steps[0].victim_page, -1);

    EXPECT_TRUE(result.steps[1].page_fault);
    EXPECT_EQ(result.steps[1].frame_number, 1);

    EXPECT_TRUE(result.steps[2].page_fault);
    EXPECT_EQ(result.steps[2].frame_number, 2);

    // 4th step: Page 4 causes fault, evicts page 1 (in frame 0)
    EXPECT_TRUE(result.steps[3].page_fault);
    EXPECT_EQ(result.steps[3].victim_page, 1);
    EXPECT_EQ(result.steps[3].frame_number, 0);

    // 5th step: Page 1 causes fault, evicts page 2 (in frame 1)
    EXPECT_TRUE(result.steps[4].page_fault);
    EXPECT_EQ(result.steps[4].victim_page, 2);
    EXPECT_EQ(result.steps[4].frame_number, 1);
}

TEST(AddressTranslationTest, SimulatesThrashingCurveAcrossFrameCounts) {
    std::vector<int> pages = {1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4};
    auto thrash = AddressTranslator::simulate_thrashing(pages, 1, 4);

    EXPECT_EQ(thrash.points.size(), 4u);
    // Faults should decrease or stay same as frames increase
    for (size_t i = 1; i < thrash.points.size(); ++i) {
        EXPECT_LE(thrash.points[i].page_faults, thrash.points[i - 1].page_faults);
    }
    // At 4 frames, working set fits completely -> 4 initial faults, then 0 faults (total 4)
    EXPECT_EQ(thrash.points[3].page_faults, 4);
    EXPECT_GE(thrash.thrashing_threshold_frames, 1);
}
