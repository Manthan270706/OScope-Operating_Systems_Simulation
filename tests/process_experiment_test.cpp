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

TEST(ProcessExperimentTest, ProcessExecReplacesImageAndCapturesOutput) {
    auto result = run_process_exec_experiment();

    EXPECT_TRUE(result.success) << "Exec experiment error: " << result.error_message;
    EXPECT_TRUE(result.image_replaced);
    EXPECT_GT(result.child_pid, 0);
    EXPECT_EQ(result.child_exit_code, 0);
    EXPECT_NE(result.captured_output.find("OScope Exec Process Replacement Verified"), std::string::npos);
    EXPECT_TRUE(result.error_message.empty());
}

TEST(ProcessExperimentTest, ProcessExecHandlesCustomExecutableAndArguments) {
    auto result = run_process_exec_experiment("/bin/echo", "TestingCustomEchoExec456");

    EXPECT_TRUE(result.success);
    EXPECT_TRUE(result.image_replaced);
    EXPECT_EQ(result.child_exit_code, 0);
    EXPECT_NE(result.captured_output.find("TestingCustomEchoExec456"), std::string::npos);
}

TEST(ProcessExperimentTest, ProcessExecHandlesNonExistentExecutableGracefully) {
    auto result = run_process_exec_experiment("/nonexistent_binary_xyz_oscope_999", "bad");

    EXPECT_FALSE(result.success);
    EXPECT_FALSE(result.image_replaced);
    EXPECT_EQ(result.child_exit_code, 127);
    EXPECT_FALSE(result.error_message.empty());
}

} // namespace
