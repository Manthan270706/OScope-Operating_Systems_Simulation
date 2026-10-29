#include <gtest/gtest.h>

#include <cstddef>
#include <vector>

#include "oscope/execution_segment.hpp"
#include "oscope/process.hpp"
#include "oscope/scheduling/fcfs.hpp"
#include "oscope/scheduling/sjf.hpp"
#include "oscope/scheduling_result.hpp"
#include "oscope/scheduling_simulation_result.hpp"

TEST(OScopeSJFTest, HandlesEmptyInput) {
    oscope::SJF sjf;
    const std::vector<oscope::Process> processes{};

    auto result = sjf.schedule(processes);

    EXPECT_TRUE(result.process_results.empty());
    EXPECT_TRUE(result.timeline.empty());
}

TEST(OScopeSJFTest, ProducesDifferentExecutionOrderFromFCFS) {
    oscope::SJF sjf;
    oscope::FCFS fcfs;

    // Process 1 arrives at 0 with long burst (8).
    // Processes 2 and 3 arrive while P1 is running, with P3 having shorter burst than P2.
    // FCFS order: P1, P2, P3.
    // SJF order: P1, P3, P2.
    const std::vector<oscope::Process> processes{
        {1, 0, 8, 0},
        {2, 1, 4, 0},
        {3, 2, 2, 0}
    };

    auto fcfs_result = fcfs.schedule(processes);
    auto sjf_result = sjf.schedule(processes);

    ASSERT_EQ(fcfs_result.timeline.size(), 3);
    ASSERT_EQ(sjf_result.timeline.size(), 3);

    // Verify FCFS timeline order: P1, P2, P3
    EXPECT_EQ(fcfs_result.timeline[0].pid, 1);
    EXPECT_EQ(fcfs_result.timeline[1].pid, 2);
    EXPECT_EQ(fcfs_result.timeline[2].pid, 3);

    // Verify SJF timeline order: P1, P3, P2
    EXPECT_EQ(sjf_result.timeline[0].pid, 1);
    EXPECT_EQ(sjf_result.timeline[1].pid, 3);
    EXPECT_EQ(sjf_result.timeline[2].pid, 2);

    // Explicitly verify orders differ
    EXPECT_NE(sjf_result.timeline[1].pid, fcfs_result.timeline[1].pid);
    EXPECT_NE(sjf_result.timeline[2].pid, fcfs_result.timeline[2].pid);

    // Exact timeline verification for SJF
    EXPECT_EQ(sjf_result.timeline[0].start_time, 0);
    EXPECT_EQ(sjf_result.timeline[0].end_time, 8);

    EXPECT_EQ(sjf_result.timeline[1].start_time, 8);
    EXPECT_EQ(sjf_result.timeline[1].end_time, 10);

    EXPECT_EQ(sjf_result.timeline[2].start_time, 10);
    EXPECT_EQ(sjf_result.timeline[2].end_time, 14);
}

TEST(OScopeSJFTest, HandlesProcessesSuppliedInUnsortedOrder) {
    oscope::SJF sjf;

    // Supplied out of arrival order and out of PID order
    const std::vector<oscope::Process> processes{
        {3, 2, 2, 0},
        {1, 0, 8, 0},
        {2, 1, 4, 0}
    };

    auto result = sjf.schedule(processes);

    ASSERT_EQ(result.timeline.size(), 3);
    ASSERT_EQ(result.process_results.size(), 3);

    // At t=0, only P1 has arrived.
    EXPECT_EQ(result.timeline[0].pid, 1);
    EXPECT_EQ(result.timeline[0].start_time, 0);
    EXPECT_EQ(result.timeline[0].end_time, 8);

    // At t=8, P3 (burst 2) and P2 (burst 4) are available -> P3 selected.
    EXPECT_EQ(result.timeline[1].pid, 3);
    EXPECT_EQ(result.timeline[1].start_time, 8);
    EXPECT_EQ(result.timeline[1].end_time, 10);

    // At t=10, P2 is scheduled.
    EXPECT_EQ(result.timeline[2].pid, 2);
    EXPECT_EQ(result.timeline[2].start_time, 10);
    EXPECT_EQ(result.timeline[2].end_time, 14);

    EXPECT_EQ(result.process_results[0].pid, 1);
    EXPECT_EQ(result.process_results[0].completion_time, 8);
    EXPECT_EQ(result.process_results[1].pid, 3);
    EXPECT_EQ(result.process_results[1].completion_time, 10);
    EXPECT_EQ(result.process_results[2].pid, 2);
    EXPECT_EQ(result.process_results[2].completion_time, 14);
}

TEST(OScopeSJFTest, DoesNotPreemptRunningProcessWhenShorterProcessArrives) {
    oscope::SJF sjf;

    // P1 arrives at 0 with burst 10.
    // P2 arrives at 3 with short burst 2.
    // In non-preemptive SJF, P1 must execute until completion at 10 without being interrupted.
    const std::vector<oscope::Process> processes{
        {1, 0, 10, 0},
        {2, 3, 2, 0}
    };

    auto result = sjf.schedule(processes);

    ASSERT_EQ(result.timeline.size(), 2);
    ASSERT_EQ(result.process_results.size(), 2);

    EXPECT_EQ(result.timeline[0].pid, 1);
    EXPECT_EQ(result.timeline[0].start_time, 0);
    EXPECT_EQ(result.timeline[0].end_time, 10);

    EXPECT_EQ(result.timeline[1].pid, 2);
    EXPECT_EQ(result.timeline[1].start_time, 10);
    EXPECT_EQ(result.timeline[1].end_time, 12);

    EXPECT_EQ(result.process_results[0].pid, 1);
    EXPECT_EQ(result.process_results[0].completion_time, 10);
    EXPECT_EQ(result.process_results[0].turnaround_time, 10);
    EXPECT_EQ(result.process_results[0].waiting_time, 0);
    EXPECT_EQ(result.process_results[0].response_time, 0);

    EXPECT_EQ(result.process_results[1].pid, 2);
    EXPECT_EQ(result.process_results[1].completion_time, 12);
    EXPECT_EQ(result.process_results[1].turnaround_time, 9);
    EXPECT_EQ(result.process_results[1].waiting_time, 7);
    EXPECT_EQ(result.process_results[1].response_time, 7);
}

TEST(OScopeSJFTest, HandlesIdleTimeBeforeFirstArrivalAndBetweenWorkloads) {
    oscope::SJF sjf;

    // Idle from 0 to 4. P1 runs from 4 to 7.
    // Idle from 7 to 11. P2 runs from 11 to 13.
    const std::vector<oscope::Process> processes{
        {1, 4, 3, 0},
        {2, 11, 2, 0}
    };

    auto result = sjf.schedule(processes);

    ASSERT_EQ(result.timeline.size(), 2);
    ASSERT_EQ(result.process_results.size(), 2);

    // Segment 1 (starts at 4 after initial idle)
    EXPECT_EQ(result.timeline[0].pid, 1);
    EXPECT_EQ(result.timeline[0].start_time, 4);
    EXPECT_EQ(result.timeline[0].end_time, 7);

    // Segment 2 (starts at 11 after intermediate idle)
    EXPECT_EQ(result.timeline[1].pid, 2);
    EXPECT_EQ(result.timeline[1].start_time, 11);
    EXPECT_EQ(result.timeline[1].end_time, 13);

    EXPECT_EQ(result.process_results[0].pid, 1);
    EXPECT_EQ(result.process_results[0].completion_time, 7);
    EXPECT_EQ(result.process_results[0].turnaround_time, 3);
    EXPECT_EQ(result.process_results[0].waiting_time, 0);
    EXPECT_EQ(result.process_results[0].response_time, 0);

    EXPECT_EQ(result.process_results[1].pid, 2);
    EXPECT_EQ(result.process_results[1].completion_time, 13);
    EXPECT_EQ(result.process_results[1].turnaround_time, 2);
    EXPECT_EQ(result.process_results[1].waiting_time, 0);
    EXPECT_EQ(result.process_results[1].response_time, 0);
}

TEST(OScopeSJFTest, BreaksTiesByEarlierArrivalTimeThenLowerPid) {
    oscope::SJF sjf;

    // Case A: Equal burst time (5), different arrival times (P2 arrived at 1, P1 arrived at 2).
    // Both are available at t=2. P2 must be selected over P1 due to earlier arrival time.
    const std::vector<oscope::Process> processes_arrival_tie{
        {1, 2, 5, 0},
        {2, 1, 5, 0}
    };

    auto result_arrival = sjf.schedule(processes_arrival_tie);
    ASSERT_EQ(result_arrival.timeline.size(), 2);
    EXPECT_EQ(result_arrival.timeline[0].pid, 2);
    EXPECT_EQ(result_arrival.timeline[0].start_time, 1);
    EXPECT_EQ(result_arrival.timeline[0].end_time, 6);
    EXPECT_EQ(result_arrival.timeline[1].pid, 1);
    EXPECT_EQ(result_arrival.timeline[1].start_time, 6);
    EXPECT_EQ(result_arrival.timeline[1].end_time, 11);

    // Case B: Equal burst time (4) AND equal arrival time (0).
    // P3 (pid 20), P1 (pid 10), P2 (pid 5)
    // Must be selected in order of lower PID: 5 (P2), then 10 (P1), then 20 (P3).
    const std::vector<oscope::Process> processes_pid_tie{
        {20, 0, 4, 0},
        {10, 0, 4, 0},
        {5, 0, 4, 0}
    };

    auto result_pid = sjf.schedule(processes_pid_tie);
    ASSERT_EQ(result_pid.timeline.size(), 3);
    EXPECT_EQ(result_pid.timeline[0].pid, 5);
    EXPECT_EQ(result_pid.timeline[0].start_time, 0);
    EXPECT_EQ(result_pid.timeline[0].end_time, 4);

    EXPECT_EQ(result_pid.timeline[1].pid, 10);
    EXPECT_EQ(result_pid.timeline[1].start_time, 4);
    EXPECT_EQ(result_pid.timeline[1].end_time, 8);

    EXPECT_EQ(result_pid.timeline[2].pid, 20);
    EXPECT_EQ(result_pid.timeline[2].start_time, 8);
    EXPECT_EQ(result_pid.timeline[2].end_time, 12);
}

TEST(OScopeSJFTest, CalculatesAllMetricsCorrectly) {
    oscope::SJF sjf;

    // Multi-process workload:
    // P1: arrival 1, burst 6
    // P2: arrival 1, burst 8
    // P3: arrival 2, burst 3
    // P4: arrival 4, burst 4
    //
    // Timeline trace:
    // t=0..1: Idle
    // t=1: P1 (burst 6) vs P2 (burst 8) -> P1 runs (1..7)
    // t=7: P2 (burst 8), P3 (burst 3), P4 (burst 4) available -> P3 runs (7..10)
    // t=10: P2 (burst 8), P4 (burst 4) available -> P4 runs (10..14)
    // t=14: P2 (burst 8) runs (14..22)
    const std::vector<oscope::Process> processes{
        {1, 1, 6, 0},
        {2, 1, 8, 0},
        {3, 2, 3, 0},
        {4, 4, 4, 0}
    };

    auto result = sjf.schedule(processes);

    ASSERT_EQ(result.process_results.size(), 4);
    ASSERT_EQ(result.timeline.size(), 4);

    // P1 results
    EXPECT_EQ(result.process_results[0].pid, 1);
    EXPECT_EQ(result.process_results[0].completion_time, 7);
    EXPECT_EQ(result.process_results[0].turnaround_time, 6);   // 7 - 1
    EXPECT_EQ(result.process_results[0].waiting_time, 0);      // 6 - 6
    EXPECT_EQ(result.process_results[0].response_time, 0);     // 1 - 1

    // P3 results
    EXPECT_EQ(result.process_results[1].pid, 3);
    EXPECT_EQ(result.process_results[1].completion_time, 10);
    EXPECT_EQ(result.process_results[1].turnaround_time, 8);   // 10 - 2
    EXPECT_EQ(result.process_results[1].waiting_time, 5);      // 8 - 3
    EXPECT_EQ(result.process_results[1].response_time, 5);     // 7 - 2

    // P4 results
    EXPECT_EQ(result.process_results[2].pid, 4);
    EXPECT_EQ(result.process_results[2].completion_time, 14);
    EXPECT_EQ(result.process_results[2].turnaround_time, 10);  // 14 - 4
    EXPECT_EQ(result.process_results[2].waiting_time, 6);      // 10 - 4
    EXPECT_EQ(result.process_results[2].response_time, 6);     // 10 - 4

    // P2 results
    EXPECT_EQ(result.process_results[3].pid, 2);
    EXPECT_EQ(result.process_results[3].completion_time, 22);
    EXPECT_EQ(result.process_results[3].turnaround_time, 21);  // 22 - 1
    EXPECT_EQ(result.process_results[3].waiting_time, 13);     // 21 - 8
    EXPECT_EQ(result.process_results[3].response_time, 13);    // 14 - 1

    // Timeline segments
    EXPECT_EQ(result.timeline[0].pid, 1);
    EXPECT_EQ(result.timeline[0].start_time, 1);
    EXPECT_EQ(result.timeline[0].end_time, 7);

    EXPECT_EQ(result.timeline[1].pid, 3);
    EXPECT_EQ(result.timeline[1].start_time, 7);
    EXPECT_EQ(result.timeline[1].end_time, 10);

    EXPECT_EQ(result.timeline[2].pid, 4);
    EXPECT_EQ(result.timeline[2].start_time, 10);
    EXPECT_EQ(result.timeline[2].end_time, 14);

    EXPECT_EQ(result.timeline[3].pid, 2);
    EXPECT_EQ(result.timeline[3].start_time, 14);
    EXPECT_EQ(result.timeline[3].end_time, 22);
}

TEST(OScopeSJFTest, CallerInputVectorRemainsUnchanged) {
    oscope::SJF sjf;

    std::vector<oscope::Process> processes{
        {3, 2, 2, 1},
        {1, 0, 8, 2},
        {2, 1, 4, 3}
    };

    const std::vector<oscope::Process> original_copy = processes;

    auto result = sjf.schedule(processes);
    (void)result;

    ASSERT_EQ(processes.size(), original_copy.size());
    for (std::size_t i = 0; i < processes.size(); ++i) {
        EXPECT_EQ(processes[i].pid, original_copy[i].pid);
        EXPECT_EQ(processes[i].arrival_time, original_copy[i].arrival_time);
        EXPECT_EQ(processes[i].burst_time, original_copy[i].burst_time);
        EXPECT_EQ(processes[i].priority, original_copy[i].priority);
    }
}
