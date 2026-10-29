#include <gtest/gtest.h>

#include "oscope/experiments/process_lifecycle_experiment.hpp"

using namespace oscope::experiments;

TEST(ProcessLifecycleExperimentTest, DemonstratesZombieProcessAndReaping) {
    auto result = run_zombie_demonstration();

    EXPECT_GT(result.child_pid, 0);
    EXPECT_TRUE(result.reaped_successfully);
    // On Linux/WSL, state 'Z' is observed before waitpid
    EXPECT_TRUE(result.zombie_observed);
    EXPECT_EQ(result.observed_state, 'Z');
}

TEST(ProcessLifecycleExperimentTest, DemonstratesOrphanReparenting) {
    auto result = run_orphan_demonstration();

    EXPECT_GT(result.initial_parent_pid, 0);
    EXPECT_GT(result.adopted_parent_pid, 0);
    EXPECT_NE(result.initial_parent_pid, result.adopted_parent_pid);
    EXPECT_TRUE(result.reparented_to_init_or_subreaper);
}
