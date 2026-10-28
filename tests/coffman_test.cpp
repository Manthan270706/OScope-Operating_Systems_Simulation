#include <gtest/gtest.h>

#include "oscope/deadlock/coffman_conditions.hpp"

using namespace oscope::deadlock;

TEST(CoffmanConditionsTest, DeadlockRequiresAllFourConditions) {
    // When all four conditions hold, deadlock is possible
    auto all_active = CoffmanEvaluator::evaluate(true, true, true, true);
    EXPECT_TRUE(all_active.deadlock_possible);
    EXPECT_NE(all_active.summary.find("DEADLOCK VULNERABLE"), std::string::npos);

    // If any single condition is false, deadlock is impossible
    EXPECT_FALSE(CoffmanEvaluator::evaluate(false, true, true, true).deadlock_possible);
    EXPECT_FALSE(CoffmanEvaluator::evaluate(true, false, true, true).deadlock_possible);
    EXPECT_FALSE(CoffmanEvaluator::evaluate(true, true, false, true).deadlock_possible);
    EXPECT_FALSE(CoffmanEvaluator::evaluate(true, true, true, false).deadlock_possible);
}

TEST(CoffmanConditionsTest, PreventionStrategiesBreakConditions) {
    auto p1 = CoffmanEvaluator::demonstrate_prevention(PreventionStrategy::SpoolingOrSharing);
    EXPECT_FALSE(p1.mutual_exclusion);
    EXPECT_FALSE(p1.deadlock_possible);

    auto p2 = CoffmanEvaluator::demonstrate_prevention(PreventionStrategy::AllOrNothingAllocation);
    EXPECT_FALSE(p2.hold_and_wait);
    EXPECT_FALSE(p2.deadlock_possible);

    auto p3 = CoffmanEvaluator::demonstrate_prevention(PreventionStrategy::ResourcePreemption);
    EXPECT_FALSE(p3.no_preemption);
    EXPECT_FALSE(p3.deadlock_possible);

    auto p4 = CoffmanEvaluator::demonstrate_prevention(PreventionStrategy::HierarchicalOrdering);
    EXPECT_FALSE(p4.circular_wait);
    EXPECT_FALSE(p4.deadlock_possible);
}
