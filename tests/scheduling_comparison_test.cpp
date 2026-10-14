#include <gtest/gtest.h>

#include <memory>
#include <stdexcept>
#include <vector>

#include "oscope/process.hpp"
#include "oscope/scheduling/fcfs.hpp"
#include "oscope/scheduling/mlfq.hpp"
#include "oscope/scheduling/priority.hpp"
#include "oscope/scheduling/round_robin.hpp"
#include "oscope/scheduling/sjf.hpp"
#include "oscope/scheduling/srtf.hpp"
#include "oscope/scheduling_comparison.hpp"
#include "oscope/scheduling_metrics.hpp"
#include "oscope/scheduling_simulation_result.hpp"

// 1. Empty results without division by zero
TEST(OScopeMetricsTest, HandlesEmptyResultsWithoutDivisionByZero) {
    oscope::SchedulingSimulationResult empty_result;

    auto metrics = oscope::calculate_metrics(empty_result);

    EXPECT_DOUBLE_EQ(metrics.average_waiting_time, 0.0);
    EXPECT_DOUBLE_EQ(metrics.average_turnaround_time, 0.0);
    EXPECT_DOUBLE_EQ(metrics.average_response_time, 0.0);

    EXPECT_DOUBLE_EQ(oscope::calculate_average_waiting_time(empty_result), 0.0);
    EXPECT_DOUBLE_EQ(oscope::calculate_average_turnaround_time(empty_result), 0.0);
    EXPECT_DOUBLE_EQ(oscope::calculate_average_response_time(empty_result), 0.0);
}

// 2. Correct average calculations using known per-process metrics
TEST(OScopeMetricsTest, CalculatesCorrectAveragesForKnownMetrics) {
    oscope::SchedulingSimulationResult result;
    // Process 1: wait 2, tat 6, resp 1
    // Process 2: wait 4, tat 10, resp 3
    result.process_results.push_back({1, 6, 6, 2, 1});
    result.process_results.push_back({2, 11, 10, 4, 3});

    auto metrics = oscope::calculate_metrics(result);

    // Sums: wait=6, tat=16, resp=4. Count=2.
    // Expected averages: wait=3.0, tat=8.0, resp=2.0.
    EXPECT_DOUBLE_EQ(metrics.average_waiting_time, 3.0);
    EXPECT_DOUBLE_EQ(metrics.average_turnaround_time, 8.0);
    EXPECT_DOUBLE_EQ(metrics.average_response_time, 2.0);

    EXPECT_DOUBLE_EQ(oscope::calculate_average_waiting_time(result), 3.0);
    EXPECT_DOUBLE_EQ(oscope::calculate_average_turnaround_time(result), 8.0);
    EXPECT_DOUBLE_EQ(oscope::calculate_average_response_time(result), 2.0);
}

// 3. Fractional averages, confirming floating-point division
TEST(OScopeMetricsTest, ComputesFractionalAveragesWithFloatingPointDivision) {
    oscope::SchedulingSimulationResult result;
    // 3 processes:
    // P1: wait 0, tat 5, resp 0
    // P2: wait 4, tat 7, resp 4
    // P3: wait 6, tat 8, resp 6
    // Sums: wait = 10, tat = 20, resp = 10. Count = 3.
    // Averages: wait = 10/3 = 3.333..., tat = 20/3 = 6.666..., resp = 10/3 = 3.333...
    result.process_results.push_back({1, 5, 5, 0, 0});
    result.process_results.push_back({2, 8, 7, 4, 4});
    result.process_results.push_back({3, 10, 8, 6, 6});

    auto metrics = oscope::calculate_metrics(result);

    EXPECT_DOUBLE_EQ(metrics.average_waiting_time, 10.0 / 3.0);
    EXPECT_DOUBLE_EQ(metrics.average_turnaround_time, 20.0 / 3.0);
    EXPECT_DOUBLE_EQ(metrics.average_response_time, 10.0 / 3.0);
}

// 4. Comparison of at least two algorithms (FCFS vs SJF)
TEST(OScopeComparisonTest, ComparesMultipleAlgorithmsWithExecutionTimelines) {
    // Workload:
    // P1: arr 0, burst 8
    // P2: arr 1, burst 4
    // P3: arr 2, burst 2
    const std::vector<oscope::Process> processes{
        {1, 0, 8, 0},
        {2, 1, 4, 0},
        {3, 2, 2, 0}
    };

    oscope::FCFS fcfs;
    oscope::SJF sjf;

    oscope::SchedulingComparator comparator;
    comparator.add_algorithm("First-Come, First-Served", fcfs);
    comparator.add_algorithm("Shortest Job First", sjf);

    auto comparison = comparator.compare(processes);

    ASSERT_EQ(comparison.size(), 2);

    // Entry 0: FCFS
    EXPECT_EQ(comparison[0].algorithm_name, "First-Come, First-Served");
    ASSERT_EQ(comparison[0].simulation_result.timeline.size(), 3);
    EXPECT_EQ(comparison[0].simulation_result.timeline[0].pid, 1);
    EXPECT_EQ(comparison[0].simulation_result.timeline[1].pid, 2);
    EXPECT_EQ(comparison[0].simulation_result.timeline[2].pid, 3);
    // FCFS metrics: wait sum = 0 + 7 + 10 = 17, tat sum = 8 + 11 + 12 = 31, resp sum = 0 + 7 + 10 = 17
    EXPECT_DOUBLE_EQ(comparison[0].average_waiting_time(), 17.0 / 3.0);
    EXPECT_DOUBLE_EQ(comparison[0].average_turnaround_time(), 31.0 / 3.0);
    EXPECT_DOUBLE_EQ(comparison[0].average_response_time(), 17.0 / 3.0);

    // Entry 1: SJF
    EXPECT_EQ(comparison[1].algorithm_name, "Shortest Job First");
    ASSERT_EQ(comparison[1].simulation_result.timeline.size(), 3);
    EXPECT_EQ(comparison[1].simulation_result.timeline[0].pid, 1);
    EXPECT_EQ(comparison[1].simulation_result.timeline[1].pid, 3);
    EXPECT_EQ(comparison[1].simulation_result.timeline[2].pid, 2);
    // SJF metrics: wait sum = 0 + 6 + 9 = 15, tat sum = 8 + 8 + 13 = 29, resp sum = 0 + 6 + 9 = 15
    EXPECT_DOUBLE_EQ(comparison[1].average_waiting_time(), 15.0 / 3.0); // 5.0
    EXPECT_DOUBLE_EQ(comparison[1].average_turnaround_time(), 29.0 / 3.0);
    EXPECT_DOUBLE_EQ(comparison[1].average_response_time(), 15.0 / 3.0); // 5.0

    // SJF waiting time should be strictly lower than FCFS
    EXPECT_LT(comparison[1].average_waiting_time(), comparison[0].average_waiting_time());
}

// 5. Consistent results when algorithms are supplied in different orders
TEST(OScopeComparisonTest, ResultsAreConsistentRegardlessOfOrderSupplied) {
    const std::vector<oscope::Process> processes{
        {1, 0, 8, 0},
        {2, 1, 4, 0},
        {3, 2, 2, 0}
    };

    auto fcfs = std::make_shared<oscope::FCFS>();
    auto sjf = std::make_shared<oscope::SJF>();

    // Order 1: FCFS, then SJF
    auto order1 = oscope::SchedulingComparator::compare(processes, {
        {"FCFS", fcfs},
        {"SJF", sjf}
    });

    // Order 2: SJF, then FCFS
    auto order2 = oscope::SchedulingComparator::compare(processes, {
        {"SJF", sjf},
        {"FCFS", fcfs}
    });

    ASSERT_EQ(order1.size(), 2);
    ASSERT_EQ(order2.size(), 2);

    // Check order1
    EXPECT_EQ(order1[0].algorithm_name, "FCFS");
    EXPECT_EQ(order1[1].algorithm_name, "SJF");

    // Check order2
    EXPECT_EQ(order2[0].algorithm_name, "SJF");
    EXPECT_EQ(order2[1].algorithm_name, "FCFS");

    // Verify metrics for FCFS match across both orderings
    EXPECT_DOUBLE_EQ(order1[0].average_waiting_time(), order2[1].average_waiting_time());
    EXPECT_DOUBLE_EQ(order1[0].average_turnaround_time(), order2[1].average_turnaround_time());
    EXPECT_DOUBLE_EQ(order1[0].average_response_time(), order2[1].average_response_time());

    // Verify metrics for SJF match across both orderings
    EXPECT_DOUBLE_EQ(order1[1].average_waiting_time(), order2[0].average_waiting_time());
    EXPECT_DOUBLE_EQ(order1[1].average_turnaround_time(), order2[0].average_turnaround_time());
    EXPECT_DOUBLE_EQ(order1[1].average_response_time(), order2[0].average_response_time());
}

// 6. Comprehensive benchmark comparing all 6 scheduling algorithms
TEST(OScopeComparisonTest, ComparesAllSixAlgorithmsConsistently) {
    const std::vector<oscope::Process> processes{
        {1, 0, 6, 2},
        {2, 1, 4, 1},
        {3, 2, 2, 3}
    };

    oscope::FCFS fcfs;
    oscope::SJF sjf;
    oscope::SRTF srtf;
    oscope::Priority priority;
    oscope::RoundRobin rr(2);
    oscope::MLFQ mlfq(2, 4, 8);

    oscope::SchedulingComparator comparator;
    comparator.add_algorithm("FCFS", fcfs);
    comparator.add_algorithm("SJF", sjf);
    comparator.add_algorithm("SRTF", srtf);
    comparator.add_algorithm("Priority", priority);
    comparator.add_algorithm("Round Robin (q=2)", rr);
    comparator.add_algorithm("MLFQ (2,4,8)", mlfq);

    EXPECT_EQ(comparator.size(), 6);
    EXPECT_FALSE(comparator.empty());

    auto results = comparator.compare(processes);

    ASSERT_EQ(results.size(), 6);
    for (const auto& entry : results) {
        EXPECT_FALSE(entry.algorithm_name.empty());
        EXPECT_FALSE(entry.simulation_result.timeline.empty());
        EXPECT_EQ(entry.simulation_result.process_results.size(), 3);
        EXPECT_GE(entry.average_waiting_time(), 0.0);
        EXPECT_GE(entry.average_turnaround_time(), 0.0);
        EXPECT_GE(entry.average_response_time(), 0.0);
    }
}

// 7. Edge case: Handling empty workload in comparison
TEST(OScopeComparisonTest, HandlesEmptyWorkloadInComparison) {
    const std::vector<oscope::Process> empty_processes{};

    oscope::FCFS fcfs;
    oscope::SJF sjf;

    oscope::SchedulingComparator comparator;
    comparator.add_algorithm("FCFS", fcfs);
    comparator.add_algorithm("SJF", sjf);

    auto results = comparator.compare(empty_processes);

    ASSERT_EQ(results.size(), 2);
    for (const auto& entry : results) {
        EXPECT_TRUE(entry.simulation_result.timeline.empty());
        EXPECT_TRUE(entry.simulation_result.process_results.empty());
        EXPECT_DOUBLE_EQ(entry.average_waiting_time(), 0.0);
        EXPECT_DOUBLE_EQ(entry.average_turnaround_time(), 0.0);
        EXPECT_DOUBLE_EQ(entry.average_response_time(), 0.0);
    }
}

// 8. Edge case: Rejection of null algorithm pointers
TEST(OScopeComparisonTest, RejectsNullAlgorithmPointer) {
    oscope::SchedulingComparator comparator;
    std::shared_ptr<oscope::SchedulingAlgorithm> null_shared = nullptr;

    EXPECT_THROW(comparator.add_algorithm("Invalid", null_shared), std::invalid_argument);

    const std::vector<oscope::Process> processes{{1, 0, 5, 0}};
    const std::vector<std::pair<std::string, oscope::SchedulingAlgorithm*>> null_raw_algorithms{
        {"Invalid", nullptr}
    };
    EXPECT_THROW(
        oscope::SchedulingComparator::compare(processes, null_raw_algorithms),
        std::invalid_argument
    );

    const std::vector<std::pair<std::string, std::shared_ptr<oscope::SchedulingAlgorithm>>> null_shared_algorithms{
        {"Invalid", nullptr}
    };
    EXPECT_THROW(
        oscope::SchedulingComparator::compare(processes, null_shared_algorithms),
        std::invalid_argument
    );
}

// 9. Edge case: Clearing and resetting comparator
TEST(OScopeComparisonTest, ClearEmptiesRegisteredAlgorithms) {
    oscope::SchedulingComparator comparator;
    oscope::FCFS fcfs;
    comparator.add_algorithm("FCFS", fcfs);
    EXPECT_EQ(comparator.size(), 1);

    comparator.clear();
    EXPECT_EQ(comparator.size(), 0);
    EXPECT_TRUE(comparator.empty());

    const std::vector<oscope::Process> processes{{1, 0, 5, 0}};
    auto results = comparator.compare(processes);
    EXPECT_TRUE(results.empty());
}
