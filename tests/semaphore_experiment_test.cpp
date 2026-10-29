#include <gtest/gtest.h>

#include <vector>
#include <thread>
#include <numeric>
#include <set>

#include "oscope/synchronization/semaphore_experiment.hpp"

namespace {

using namespace oscope::synchronization;

TEST(SemaphoreExperimentTest, BasicSemaphoreLifecycleAndOperations) {
    PosixSemaphore sem(1);
    EXPECT_TRUE(sem.is_valid());

    // Wait (decrement to 0)
    EXPECT_TRUE(sem.wait());

    // Post (increment to 1)
    EXPECT_TRUE(sem.post());

    // Wait again
    EXPECT_TRUE(sem.wait());
    EXPECT_TRUE(sem.post());
}

TEST(SemaphoreExperimentTest, MultiThreadedCountingSynchronization) {
    const std::size_t threads = 4;
    const std::size_t iters = 2500;
    auto result = run_semaphore_experiment(threads, iters);

    EXPECT_TRUE(result.success) << "Semaphore experiment error: " << result.error_message;
    EXPECT_EQ(result.num_threads, threads);
    EXPECT_EQ(result.iterations_per_thread, iters);
    EXPECT_EQ(result.threads_completed, threads);
    EXPECT_EQ(result.expected_counter, threads * iters);
    EXPECT_EQ(result.actual_counter, result.expected_counter);
    EXPECT_TRUE(result.error_message.empty());
}

TEST(SemaphoreExperimentTest, ZeroThreadsAndIterationsHandledCleanly) {
    auto r1 = run_semaphore_experiment(0, 1000);
    EXPECT_TRUE(r1.success);
    EXPECT_EQ(r1.num_threads, 0u);
    EXPECT_EQ(r1.actual_counter, 0u);

    auto r2 = run_semaphore_experiment(4, 0);
    EXPECT_TRUE(r2.success);
    EXPECT_EQ(r2.threads_completed, 4u);
    EXPECT_EQ(r2.actual_counter, 0u);
}

TEST(ProducerConsumerTest, BoundedBufferPreservesAllItemsWithoutLossOrDuplication) {
    const std::size_t buffer_cap = 5;
    const std::size_t total_items = 100;
    const std::size_t producers = 2;
    const std::size_t consumers = 2;

    auto result = run_producer_consumer_experiment(buffer_cap, total_items, producers, consumers);

    EXPECT_TRUE(result.success) << "Producer-Consumer error: " << result.error_message;
    EXPECT_EQ(result.buffer_capacity, buffer_cap);
    EXPECT_EQ(result.total_items, total_items);
    EXPECT_EQ(result.num_producers, producers);
    EXPECT_EQ(result.num_consumers, consumers);
    EXPECT_EQ(result.items_produced, total_items);
    EXPECT_EQ(result.items_consumed, total_items);
    EXPECT_TRUE(result.items_preserved);
    EXPECT_LE(result.max_buffer_occupancy_observed, buffer_cap);
    EXPECT_GT(result.max_buffer_occupancy_observed, 0u);
}

TEST(ProducerConsumerTest, SingleProducerSingleConsumerWorksCorrectly) {
    const std::size_t buffer_cap = 3;
    const std::size_t total_items = 50;

    auto result = run_producer_consumer_experiment(buffer_cap, total_items, 1, 1);

    EXPECT_TRUE(result.success);
    EXPECT_EQ(result.items_produced, total_items);
    EXPECT_EQ(result.items_consumed, total_items);
    EXPECT_TRUE(result.items_preserved);
    EXPECT_LE(result.max_buffer_occupancy_observed, buffer_cap);
}

TEST(ProducerConsumerTest, AsymmetricProducersAndConsumers) {
    // 3 producers, 1 consumer
    auto r1 = run_producer_consumer_experiment(4, 60, 3, 1);
    EXPECT_TRUE(r1.success);
    EXPECT_EQ(r1.items_produced, 60u);
    EXPECT_EQ(r1.items_consumed, 60u);
    EXPECT_TRUE(r1.items_preserved);

    // 1 producer, 4 consumers
    auto r2 = run_producer_consumer_experiment(4, 60, 1, 4);
    EXPECT_TRUE(r2.success);
    EXPECT_EQ(r2.items_produced, 60u);
    EXPECT_EQ(r2.items_consumed, 60u);
    EXPECT_TRUE(r2.items_preserved);
}

TEST(ProducerConsumerTest, SmallBufferHighContention) {
    // Buffer size 1: strict alternation / immediate blocking
    auto result = run_producer_consumer_experiment(1, 40, 4, 4);

    EXPECT_TRUE(result.success);
    EXPECT_EQ(result.items_produced, 40u);
    EXPECT_EQ(result.items_consumed, 40u);
    EXPECT_TRUE(result.items_preserved);
    EXPECT_LE(result.max_buffer_occupancy_observed, 1u);
}

} // namespace
