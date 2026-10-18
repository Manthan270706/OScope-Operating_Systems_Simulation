#include <gtest/gtest.h>

#include <unistd.h>
#include <string>

#include "oscope/experiments/pipe_ipc_experiment.hpp"

namespace {

using namespace oscope::experiments;

TEST(PipeIpcExperimentTest, DefaultMessageTransfersSuccessfully) {
    auto result = run_pipe_ipc_experiment();

    EXPECT_TRUE(result.is_success());
    EXPECT_EQ(result.status, PipeIpcStatus::Success);
    EXPECT_GT(result.parent_pid, 0);
    EXPECT_GT(result.child_pid, 0);
    EXPECT_NE(result.parent_pid, result.child_pid);
    EXPECT_EQ(result.parent_pid, ::getpid());
    EXPECT_TRUE(result.child_exited_normally);
    EXPECT_EQ(result.child_exit_code, kPipeChildSuccessExitCode);
    EXPECT_EQ(result.child_termination_signal, -1);
    EXPECT_EQ(result.sent_message, kDefaultPipeMessage);
    EXPECT_EQ(result.received_message, kDefaultPipeMessage);
    EXPECT_TRUE(result.error_message.empty());
}

TEST(PipeIpcExperimentTest, CustomAndLongMessagesTransferCorrectly) {
    const std::string long_msg(4096, 'A');
    auto r1 = run_pipe_ipc_experiment(long_msg);

    EXPECT_TRUE(r1.is_success());
    EXPECT_EQ(r1.received_message.size(), 4096);
    EXPECT_EQ(r1.received_message, long_msg);

    const std::string msg_with_newlines = "Line 1\nLine 2\nLine 3 with symbols: !@#$%^&*()_+";
    auto r2 = run_pipe_ipc_experiment(msg_with_newlines);

    EXPECT_TRUE(r2.is_success());
    EXPECT_EQ(r2.received_message, msg_with_newlines);
}

TEST(PipeIpcExperimentTest, EmptyMessageTransfersSafely) {
    auto result = run_pipe_ipc_experiment("");

    EXPECT_TRUE(result.is_success());
    EXPECT_EQ(result.sent_message, "");
    EXPECT_EQ(result.received_message, "");
    EXPECT_TRUE(result.child_exited_normally);
    EXPECT_EQ(result.child_exit_code, kPipeChildSuccessExitCode);
}

TEST(PipeIpcExperimentTest, SuccessiveRunsUseDistinctChildPids) {
    auto r1 = run_pipe_ipc_experiment("Run 1");
    auto r2 = run_pipe_ipc_experiment("Run 2");

    EXPECT_TRUE(r1.is_success());
    EXPECT_TRUE(r2.is_success());
    EXPECT_EQ(r1.parent_pid, r2.parent_pid);
    EXPECT_NE(r1.child_pid, r2.child_pid);
    EXPECT_EQ(r1.received_message, "Run 1");
    EXPECT_EQ(r2.received_message, "Run 2");
}

TEST(PipeIpcExperimentTest, DefaultResultStateRepresentsFailure) {
    PipeIpcExperimentResult default_res;
    EXPECT_FALSE(default_res.is_success());
    EXPECT_FALSE(default_res.child_exited_normally);
    EXPECT_EQ(default_res.child_exit_code, -1);
    EXPECT_EQ(default_res.child_termination_signal, -1);
    EXPECT_EQ(default_res.status, PipeIpcStatus::PipeCreationFailed);
}

} // namespace
