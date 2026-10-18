#include <gtest/gtest.h>

#include <unistd.h>

#include "oscope/experiments/process_experiment.hpp"

namespace {

using namespace oscope::experiments;

TEST(ProcessExperimentTest, SuccessfulForkAndWaitReapsChild) {
    auto result = run_process_experiment();

    EXPECT_TRUE(result.is_success());
    EXPECT_EQ(result.status, ProcessExperimentStatus::Success);
    EXPECT_GT(result.parent_pid, 0);
    EXPECT_GT(result.child_pid, 0);
    EXPECT_NE(result.parent_pid, result.child_pid);
    EXPECT_EQ(result.parent_pid, ::getpid());
    EXPECT_TRUE(result.exited_normally);
    EXPECT_EQ(result.exit_code, kExpectedChildExitCode);
    EXPECT_EQ(result.termination_signal, -1);
    EXPECT_FALSE(result.message.empty());
}

TEST(ProcessExperimentTest, RepeatedRunsSucceedAndYieldDistinctChildPids) {
    auto r1 = run_process_experiment();
    auto r2 = run_process_experiment();

    EXPECT_TRUE(r1.is_success());
    EXPECT_TRUE(r2.is_success());
    EXPECT_EQ(r1.parent_pid, r2.parent_pid);
    EXPECT_NE(r1.child_pid, r2.child_pid);
    EXPECT_EQ(r1.exit_code, kExpectedChildExitCode);
    EXPECT_EQ(r2.exit_code, kExpectedChildExitCode);
}

TEST(ProcessExperimentTest, ResultReportsConsistentExitDetails) {
    auto result = run_process_experiment();

    EXPECT_TRUE(result.exited_normally);
    EXPECT_EQ(result.exit_code, 42);
    EXPECT_NE(result.message.find("42"), std::string::npos);
}

} // namespace
