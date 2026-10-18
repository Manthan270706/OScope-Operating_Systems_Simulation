#include <gtest/gtest.h>

#include "oscope/experiments/thread_experiment.hpp"

namespace {

using namespace oscope::experiments;

TEST(ThreadExperimentTest, DefaultThreadCountExecutesAndJoinsAllWorkers) {
    auto result = run_thread_experiment();

    EXPECT_TRUE(result.success);
    EXPECT_EQ(result.requested_threads, kDefaultThreadExperimentCount);
    EXPECT_EQ(result.started_threads, kDefaultThreadExperimentCount);
    EXPECT_EQ(result.completed_threads, kDefaultThreadExperimentCount);
    EXPECT_EQ(result.worker_results.size(), kDefaultThreadExperimentCount);
    EXPECT_TRUE(result.error_message.empty());

    for (std::size_t i = 0; i < kDefaultThreadExperimentCount; ++i) {
        EXPECT_EQ(result.worker_results[i], static_cast<int>((i + 1) * 100));
    }
}

TEST(ThreadExperimentTest, CustomThreadCountsExecuteDeterministically) {
    for (std::size_t count : {1, 2, 5, 8}) {
        auto result = run_thread_experiment(count);

        EXPECT_TRUE(result.success);
        EXPECT_EQ(result.requested_threads, count);
        EXPECT_EQ(result.started_threads, count);
        EXPECT_EQ(result.completed_threads, count);
        EXPECT_EQ(result.worker_results.size(), count);

        for (std::size_t i = 0; i < count; ++i) {
            EXPECT_EQ(result.worker_results[i], static_cast<int>((i + 1) * 100));
        }
    }
}

TEST(ThreadExperimentTest, ZeroThreadsHandledCleanly) {
    auto result = run_thread_experiment(0);

    EXPECT_TRUE(result.success);
    EXPECT_EQ(result.requested_threads, 0);
    EXPECT_EQ(result.started_threads, 0);
    EXPECT_EQ(result.completed_threads, 0);
    EXPECT_TRUE(result.worker_results.empty());
}

TEST(ThreadExperimentTest, RejectsUnusuallyLargeThreadCount) {
    const std::size_t excess_count = kMaxSupportedThreads + 1;
    auto result = run_thread_experiment(excess_count);

    EXPECT_FALSE(result.success);
    EXPECT_EQ(result.requested_threads, excess_count);
    EXPECT_EQ(result.started_threads, 0);
    EXPECT_EQ(result.completed_threads, 0);
    EXPECT_TRUE(result.worker_results.empty());
    EXPECT_FALSE(result.error_message.empty());
    EXPECT_NE(result.error_message.find("exceeds maximum supported limit"), std::string::npos);
}

TEST(ThreadExperimentTest, RejectsExtremeThreadCountWithoutCrashing) {
    const std::size_t extreme_count = std::numeric_limits<std::size_t>::max();
    auto result = run_thread_experiment(extreme_count);

    EXPECT_FALSE(result.success);
    EXPECT_EQ(result.requested_threads, extreme_count);
    EXPECT_EQ(result.started_threads, 0);
    EXPECT_EQ(result.completed_threads, 0);
    EXPECT_TRUE(result.worker_results.empty());
    EXPECT_FALSE(result.error_message.empty());
}

} // namespace
