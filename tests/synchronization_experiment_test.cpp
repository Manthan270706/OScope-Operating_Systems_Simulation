#include <gtest/gtest.h>

#include <cstdint>
#include <limits>

#include "oscope/experiments/synchronization_experiment.hpp"

namespace {

using namespace oscope::experiments;

TEST(SynchronizationExperimentTest, DefaultParametersProduceExactMatch) {
    auto result = run_synchronization_experiment();

    EXPECT_TRUE(result.success);
    EXPECT_EQ(result.num_threads, kDefaultSyncThreadCount);
    EXPECT_EQ(result.iterations_per_thread, kDefaultIterationsPerThread);
    EXPECT_EQ(result.threads_completed, kDefaultSyncThreadCount);
    EXPECT_EQ(result.expected_counter, static_cast<std::uint64_t>(kDefaultSyncThreadCount) * kDefaultIterationsPerThread);
    EXPECT_EQ(result.actual_counter, result.expected_counter);
    EXPECT_TRUE(result.error_message.empty());
}

TEST(SynchronizationExperimentTest, VariousThreadAndIterationCountsSucceed) {
    const std::vector<std::pair<std::size_t, std::size_t>> configs = {
        {1, 5000},
        {2, 10000},
        {4, 25000},
        {8, 5000}
    };

    for (const auto& [threads, iters] : configs) {
        auto result = run_synchronization_experiment(threads, iters);

        EXPECT_TRUE(result.success);
        EXPECT_EQ(result.num_threads, threads);
        EXPECT_EQ(result.iterations_per_thread, iters);
        EXPECT_EQ(result.threads_completed, threads);
        EXPECT_EQ(result.expected_counter, static_cast<std::uint64_t>(threads) * iters);
        EXPECT_EQ(result.actual_counter, result.expected_counter);
    }
}

TEST(SynchronizationExperimentTest, ZeroThreadsHandledCleanly) {
    auto result = run_synchronization_experiment(0, 1000);

    EXPECT_TRUE(result.success);
    EXPECT_EQ(result.num_threads, 0);
    EXPECT_EQ(result.threads_completed, 0);
    EXPECT_EQ(result.expected_counter, 0);
    EXPECT_EQ(result.actual_counter, 0);
}

TEST(SynchronizationExperimentTest, ZeroIterationsHandledCleanly) {
    auto result = run_synchronization_experiment(4, 0);

    EXPECT_TRUE(result.success);
    EXPECT_EQ(result.num_threads, 4);
    EXPECT_EQ(result.threads_completed, 4);
    EXPECT_EQ(result.expected_counter, 0);
    EXPECT_EQ(result.actual_counter, 0);
}

TEST(SynchronizationExperimentTest, DetectsPotentialOverflowSafely) {
    std::size_t huge_iters = std::numeric_limits<std::uint64_t>::max();
    auto result = run_synchronization_experiment(2, huge_iters);

    EXPECT_FALSE(result.success);
    EXPECT_NE(result.error_message.find("overflow"), std::string::npos);
}

} // namespace
