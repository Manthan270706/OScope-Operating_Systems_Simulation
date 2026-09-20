#include <gtest/gtest.h>

#include "oscope/process.hpp"
#include "oscope/scheduling_result.hpp"
#include "oscope/execution_segment.hpp"
#include "oscope/scheduling_simulation_result.hpp"

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
