#include <gtest/gtest.h>

#include "oscope/synchronization/petersons_algorithm.hpp"

using namespace oscope::synchronization;

TEST(PetersonsAlgorithmTest, MaintainsMutualExclusionAcrossMultipleRounds) {
    PetersonsAlgorithm algo;
    auto result = algo.simulate(5, 0); // 5 rounds with alternating start

    EXPECT_TRUE(result.mutual_exclusion_maintained);
    EXPECT_EQ(result.p0_critical_entries, 5);
    EXPECT_EQ(result.p1_critical_entries, 5);
    EXPECT_GT(result.total_steps, 0);

    // Verify invariant on every single trace step: both are never simultaneously in CS
    for (const auto& step : result.trace) {
        EXPECT_TRUE(step.mutual_exclusion_held);
        EXPECT_FALSE(step.p0_in_cs && step.p1_in_cs);
    }
}

TEST(PetersonsAlgorithmTest, HandlesUnequalInterleavingPatterns) {
    PetersonsAlgorithm algo;

    // Pattern 1: P0 always expresses interest first
    auto res1 = algo.simulate(3, 1);
    EXPECT_TRUE(res1.mutual_exclusion_maintained);
    EXPECT_EQ(res1.p0_critical_entries, 3);
    EXPECT_EQ(res1.p1_critical_entries, 3);

    // Pattern 2: P1 always expresses interest first
    auto res2 = algo.simulate(3, 2);
    EXPECT_TRUE(res2.mutual_exclusion_maintained);
    EXPECT_EQ(res2.p0_critical_entries, 3);
    EXPECT_EQ(res2.p1_critical_entries, 3);
}

TEST(PetersonsAlgorithmTest, ReturnsEducationalNotes) {
    auto notes = PetersonsAlgorithm::get_educational_notes();
    EXPECT_NE(notes.find("Mutual Exclusion"), std::string::npos);
    EXPECT_NE(notes.find("Bounded Waiting"), std::string::npos);
    EXPECT_NE(notes.find("memory barriers"), std::string::npos);
}
