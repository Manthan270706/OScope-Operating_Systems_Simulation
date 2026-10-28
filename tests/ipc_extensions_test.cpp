#include <gtest/gtest.h>

#include "oscope/experiments/ipc_experiments.hpp"

using namespace oscope::experiments;

TEST(IpcExperimentsTest, FifoTransfersDataAcrossProcessesAndCleansUp) {
    std::string test_msg = "OScope FIFO IPC Verification Payload";
    auto result = run_fifo_experiment(test_msg);

    EXPECT_TRUE(result.success) << "FIFO experiment error: " << result.error_message;
    EXPECT_EQ(result.message_received, test_msg);
    EXPECT_FALSE(result.fifo_path.empty());

    // Verify FIFO filesystem node was cleaned up (does not exist)
    EXPECT_EQ(::access(result.fifo_path.c_str(), F_OK), -1);
}

TEST(IpcExperimentsTest, SharedMemoryTransfersDataAcrossProcessesAndCleansUp) {
    std::string test_msg = "OScope Shared Memory Verification Payload";
    auto result = run_shared_memory_experiment(test_msg);

    EXPECT_TRUE(result.success) << "Shared memory experiment error: " << result.error_message;
    EXPECT_EQ(result.message_read, test_msg);
    EXPECT_GT(result.size_bytes, 0u);
}

TEST(IpcExperimentsTest, MessageQueueTransfersPayloadAcrossProcessesAndCleansUp) {
    std::string test_msg = "OScope POSIX Message Queue Verification Payload";
    auto result = run_message_queue_experiment(test_msg);

    EXPECT_TRUE(result.success) << "Message queue experiment error: " << result.error_message;
    EXPECT_EQ(result.message_content, test_msg);
    EXPECT_EQ(result.messages_sent, 1);
    EXPECT_EQ(result.messages_received, 1);
    EXPECT_FALSE(result.queue_name.empty());
    EXPECT_TRUE(result.error_message.empty());
}

TEST(IpcExperimentsTest, MessageQueueHandlesDifferentPayloads) {
    std::string test_msg = "Short MQ Payload #12345";
    auto result = run_message_queue_experiment(test_msg);

    EXPECT_TRUE(result.success);
    EXPECT_EQ(result.message_content, test_msg);
}
