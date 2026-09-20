#include <gtest/gtest.h>

#include "oscope/process.hpp"
#include "oscope/scheduling_result.hpp"
#include "oscope/execution_segment.hpp"
#include "oscope/scheduling_simulation_result.hpp"
#include "oscope/scheduling_algorithm.hpp"
#include "oscope/scheduling/fcfs.hpp"

TEST(OScopeProcessTest, CreatesProcess) {
    oscope::Process process{1, 0, 5, 2};

    EXPECT_EQ(process.pid, 1);
    EXPECT_EQ(process.arrival_time, 0);
    EXPECT_EQ(process.burst_time, 5);
    EXPECT_EQ(process.priority, 2);
}

TEST(OScopeSchedulingResultTest, CreatesSchedulingResult) {
    oscope::SchedulingResult result{1, 5, 5, 0, 0};

    EXPECT_EQ(result.pid, 1);
    EXPECT_EQ(result.completion_time, 5);
    EXPECT_EQ(result.turnaround_time, 5);
    EXPECT_EQ(result.waiting_time, 0);
    EXPECT_EQ(result.response_time, 0);
}

TEST(OScopeExecutionSegmentTest, CreatesExecutionSegment) {
    oscope::ExecutionSegment segment{1, 0, 5};

    EXPECT_EQ(segment.pid, 1);
    EXPECT_EQ(segment.start_time, 0);
    EXPECT_EQ(segment.end_time, 5);
}

TEST(OScopeSchedulingSimulationResultTest, CreatesSimulationResult) {
    oscope::SchedulingSimulationResult simulation;

    simulation.process_results.push_back({1, 5, 5, 0, 0});
    simulation.timeline.push_back({1, 0, 5});

    ASSERT_EQ(simulation.process_results.size(), 1);
    ASSERT_EQ(simulation.timeline.size(), 1);

    EXPECT_EQ(simulation.process_results[0].pid, 1);
    EXPECT_EQ(simulation.timeline[0].pid, 1);
    EXPECT_EQ(simulation.timeline[0].start_time, 0);
    EXPECT_EQ(simulation.timeline[0].end_time, 5);
}

class TestSchedulingAlgorithm : public oscope::SchedulingAlgorithm {
public:
    oscope::SchedulingSimulationResult
    schedule(const std::vector<oscope::Process>& processes) override {
        return {};
    }
};

TEST(OScopeSchedulingAlgorithmTest, CanBeImplemented) {
    TestSchedulingAlgorithm algorithm;

    std::vector<oscope::Process> processes{
        {1, 0, 5, 2}
    };

    auto result = algorithm.schedule(processes);

    EXPECT_TRUE(result.process_results.empty());
    EXPECT_TRUE(result.timeline.empty());
}

TEST(OScopeFCFSTest, SchedulesProcessesInArrivalOrder) {
    oscope::FCFS fcfs;

    std::vector<oscope::Process> processes{
        {1, 0, 5, 2},
        {2, 1, 3, 1},
        {3, 2, 2, 3}
    };

    auto result = fcfs.schedule(processes);

    ASSERT_EQ(result.process_results.size(), 3);
    ASSERT_EQ(result.timeline.size(), 3);

    EXPECT_EQ(result.process_results[0].pid, 1);
    EXPECT_EQ(result.process_results[0].completion_time, 5);
    EXPECT_EQ(result.process_results[0].turnaround_time, 5);
    EXPECT_EQ(result.process_results[0].waiting_time, 0);
    EXPECT_EQ(result.process_results[0].response_time, 0);

    EXPECT_EQ(result.process_results[1].pid, 2);
    EXPECT_EQ(result.process_results[1].completion_time, 8);
    EXPECT_EQ(result.process_results[1].turnaround_time, 7);
    EXPECT_EQ(result.process_results[1].waiting_time, 4);
    EXPECT_EQ(result.process_results[1].response_time, 4);

    EXPECT_EQ(result.process_results[2].pid, 3);
    EXPECT_EQ(result.process_results[2].completion_time, 10);
    EXPECT_EQ(result.process_results[2].turnaround_time, 8);
    EXPECT_EQ(result.process_results[2].waiting_time, 6);
    EXPECT_EQ(result.process_results[2].response_time, 6);

    EXPECT_EQ(result.timeline[0].pid, 1);
    EXPECT_EQ(result.timeline[0].start_time, 0);
    EXPECT_EQ(result.timeline[0].end_time, 5);

    EXPECT_EQ(result.timeline[1].pid, 2);
    EXPECT_EQ(result.timeline[1].start_time, 5);
    EXPECT_EQ(result.timeline[1].end_time, 8);

    EXPECT_EQ(result.timeline[2].pid, 3);
    EXPECT_EQ(result.timeline[2].start_time, 8);
    EXPECT_EQ(result.timeline[2].end_time, 10);
}
