#include <gtest/gtest.h>

#include <cstddef>
#include <vector>

#include "oscope/execution_segment.hpp"
#include "oscope/process.hpp"
#include "oscope/scheduling/fcfs.hpp"
#include "oscope/scheduling/priority.hpp"
#include "oscope/scheduling_result.hpp"
#include "oscope/scheduling_simulation_result.hpp"

// 1. Empty input
TEST(OScopePriorityTest, HandlesEmptyInput) {
    oscope::Priority priority_sched;
    const std::vector<oscope::Process> processes{};

    auto result = priority_sched.schedule(processes);

    EXPECT_TRUE(result.process_results.empty());
    EXPECT_TRUE(result.timeline.empty());
}

// 2. Priority selection differs from FCFS when multiple processes are ready
TEST(OScopePriorityTest, DiffersFromFCFSWhenMultipleProcessesReady) {
    oscope::Priority priority_sched;
    oscope::FCFS fcfs;

    // P1 runs 0..5. During this time, P2 (arrival 1, prio 4) and P3 (arrival 2, prio 1) arrive.
    // FCFS will run P1, then P2, then P3.
    // Priority scheduling will run P1, then P3 (prio 1 outranks 4), then P2.
    const std::vector<oscope::Process> processes{
        {1, 0, 5, 5},
        {2, 1, 3, 4},
        {3, 2, 3, 1}
    };

    auto fcfs_result = fcfs.schedule(processes);
    auto priority_result = priority_sched.schedule(processes);

    ASSERT_EQ(fcfs_result.timeline.size(), 3);
    ASSERT_EQ(priority_result.timeline.size(), 3);

    // FCFS order: P1, P2, P3
    EXPECT_EQ(fcfs_result.timeline[0].pid, 1);
    EXPECT_EQ(fcfs_result.timeline[1].pid, 2);
    EXPECT_EQ(fcfs_result.timeline[2].pid, 3);

    // Priority order: P1, P3, P2
    EXPECT_EQ(priority_result.timeline[0].pid, 1);
    EXPECT_EQ(priority_result.timeline[1].pid, 3);
    EXPECT_EQ(priority_result.timeline[2].pid, 2);

    EXPECT_NE(priority_result.timeline[1].pid, fcfs_result.timeline[1].pid);
    EXPECT_NE(priority_result.timeline[2].pid, fcfs_result.timeline[2].pid);

    EXPECT_EQ(priority_result.timeline[0].start_time, 0);
    EXPECT_EQ(priority_result.timeline[0].end_time, 5);

    EXPECT_EQ(priority_result.timeline[1].start_time, 5);
    EXPECT_EQ(priority_result.timeline[1].end_time, 8);

    EXPECT_EQ(priority_result.timeline[2].start_time, 8);
    EXPECT_EQ(priority_result.timeline[2].end_time, 11);
}

// 3. Lower numeric priority value wins
TEST(OScopePriorityTest, LowerNumericPriorityWins) {
    oscope::Priority priority_sched;

    // All arrive at t=0 with priorities 5, 2, 8.
    // P2 (priority 2) outranks P1 (priority 5) and P3 (priority 8).
    const std::vector<oscope::Process> processes{
        {1, 0, 4, 5},
        {2, 0, 4, 2},
        {3, 0, 4, 8}
    };

    auto result = priority_sched.schedule(processes);

    ASSERT_EQ(result.timeline.size(), 3);
    EXPECT_EQ(result.timeline[0].pid, 2);
    EXPECT_EQ(result.timeline[0].start_time, 0);
    EXPECT_EQ(result.timeline[0].end_time, 4);

    EXPECT_EQ(result.timeline[1].pid, 1);
    EXPECT_EQ(result.timeline[1].start_time, 4);
    EXPECT_EQ(result.timeline[1].end_time, 8);

    EXPECT_EQ(result.timeline[2].pid, 3);
    EXPECT_EQ(result.timeline[2].start_time, 8);
    EXPECT_EQ(result.timeline[2].end_time, 12);
}

// 4. Processes supplied in unsorted input order
TEST(OScopePriorityTest, HandlesProcessesSuppliedInUnsortedOrder) {
    oscope::Priority priority_sched;

    const std::vector<oscope::Process> processes{
        {3, 2, 3, 1},
        {1, 0, 5, 5},
        {2, 1, 3, 3}
    };

    auto result = priority_sched.schedule(processes);

    ASSERT_EQ(result.timeline.size(), 3);
    ASSERT_EQ(result.process_results.size(), 3);

    // At t=0, only P1 is ready -> P1 runs 0..5
    EXPECT_EQ(result.timeline[0].pid, 1);
    EXPECT_EQ(result.timeline[0].start_time, 0);
    EXPECT_EQ(result.timeline[0].end_time, 5);

    // At t=5, P3 (prio 1) and P2 (prio 3) are ready -> P3 runs 5..8
    EXPECT_EQ(result.timeline[1].pid, 3);
    EXPECT_EQ(result.timeline[1].start_time, 5);
    EXPECT_EQ(result.timeline[1].end_time, 8);

    // At t=8, P2 runs 8..11
    EXPECT_EQ(result.timeline[2].pid, 2);
    EXPECT_EQ(result.timeline[2].start_time, 8);
    EXPECT_EQ(result.timeline[2].end_time, 11);

    EXPECT_EQ(result.process_results[0].pid, 1);
    EXPECT_EQ(result.process_results[0].completion_time, 5);
    EXPECT_EQ(result.process_results[1].pid, 3);
    EXPECT_EQ(result.process_results[1].completion_time, 8);
    EXPECT_EQ(result.process_results[2].pid, 2);
    EXPECT_EQ(result.process_results[2].completion_time, 11);
}

// 5. A process arriving while another runs does not preempt it
TEST(OScopePriorityTest, DoesNotPreemptRunningProcessWhenHigherPriorityArrives) {
    oscope::Priority priority_sched;

    // P1 (priority 10) starts at t=0 and runs for 8 units.
    // P2 (priority 1) arrives at t=2.
    // Since non-preemptive, P1 must run to completion at t=8 before P2 runs.
    const std::vector<oscope::Process> processes{
        {1, 0, 8, 10},
        {2, 2, 2, 1}
    };

    auto result = priority_sched.schedule(processes);

    ASSERT_EQ(result.timeline.size(), 2);
    ASSERT_EQ(result.process_results.size(), 2);

    EXPECT_EQ(result.timeline[0].pid, 1);
    EXPECT_EQ(result.timeline[0].start_time, 0);
    EXPECT_EQ(result.timeline[0].end_time, 8);

    EXPECT_EQ(result.timeline[1].pid, 2);
    EXPECT_EQ(result.timeline[1].start_time, 8);
    EXPECT_EQ(result.timeline[1].end_time, 10);

    EXPECT_EQ(result.process_results[0].pid, 1);
    EXPECT_EQ(result.process_results[0].completion_time, 8);
    EXPECT_EQ(result.process_results[0].turnaround_time, 8);
    EXPECT_EQ(result.process_results[0].waiting_time, 0);
    EXPECT_EQ(result.process_results[0].response_time, 0);

    EXPECT_EQ(result.process_results[1].pid, 2);
    EXPECT_EQ(result.process_results[1].completion_time, 10);
    EXPECT_EQ(result.process_results[1].turnaround_time, 8); // 10 - 2
    EXPECT_EQ(result.process_results[1].waiting_time, 6);    // 8 - 2
    EXPECT_EQ(result.process_results[1].response_time, 6);   // 8 - 2
}

// 6. CPU idle time before the first arrival and between workloads
TEST(OScopePriorityTest, HandlesIdleTimeBeforeFirstArrivalAndBetweenWorkloads) {
    oscope::Priority priority_sched;

    // Idle 0..4, P1 runs 4..7
    // Idle 7..10, P2 runs 10..12
    const std::vector<oscope::Process> processes{
        {1, 4, 3, 2},
        {2, 10, 2, 1}
    };

    auto result = priority_sched.schedule(processes);

    ASSERT_EQ(result.timeline.size(), 2);
    ASSERT_EQ(result.process_results.size(), 2);

    EXPECT_EQ(result.timeline[0].pid, 1);
    EXPECT_EQ(result.timeline[0].start_time, 4);
    EXPECT_EQ(result.timeline[0].end_time, 7);

    EXPECT_EQ(result.timeline[1].pid, 2);
    EXPECT_EQ(result.timeline[1].start_time, 10);
    EXPECT_EQ(result.timeline[1].end_time, 12);

    EXPECT_EQ(result.process_results[0].pid, 1);
    EXPECT_EQ(result.process_results[0].completion_time, 7);
    EXPECT_EQ(result.process_results[0].turnaround_time, 3);
    EXPECT_EQ(result.process_results[0].waiting_time, 0);
    EXPECT_EQ(result.process_results[0].response_time, 0);

    EXPECT_EQ(result.process_results[1].pid, 2);
    EXPECT_EQ(result.process_results[1].completion_time, 12);
    EXPECT_EQ(result.process_results[1].turnaround_time, 2);
    EXPECT_EQ(result.process_results[1].waiting_time, 0);
    EXPECT_EQ(result.process_results[1].response_time, 0);
}

// 7. Equal-priority tie-breaking by arrival time and then PID
TEST(OScopePriorityTest, BreaksTiesByEarlierArrivalTimeThenLowerPid) {
    oscope::Priority priority_sched;

    // Case A: Equal priority (2), different arrival time (P2 at 1, P1 at 2).
    // P0 runs 0..3 (priority 1).
    // At t=3, both P1 and P2 are ready with priority 2. P2 arrived earlier (1 < 2).
    const std::vector<oscope::Process> processes_arrival_tie{
        {0, 0, 3, 1},
        {1, 2, 4, 2},
        {2, 1, 4, 2}
    };

    auto result_arrival = priority_sched.schedule(processes_arrival_tie);
    ASSERT_EQ(result_arrival.timeline.size(), 3);
    EXPECT_EQ(result_arrival.timeline[0].pid, 0);
    EXPECT_EQ(result_arrival.timeline[0].start_time, 0);
    EXPECT_EQ(result_arrival.timeline[0].end_time, 3);

    EXPECT_EQ(result_arrival.timeline[1].pid, 2);
    EXPECT_EQ(result_arrival.timeline[1].start_time, 3);
    EXPECT_EQ(result_arrival.timeline[1].end_time, 7);

    EXPECT_EQ(result_arrival.timeline[2].pid, 1);
    EXPECT_EQ(result_arrival.timeline[2].start_time, 7);
    EXPECT_EQ(result_arrival.timeline[2].end_time, 11);

    // Case B: Equal priority (2) AND equal arrival time (0).
    // Chosen by lower PID: P5, then P10, then P20.
    const std::vector<oscope::Process> processes_pid_tie{
        {20, 0, 3, 2},
        {10, 0, 3, 2},
        {5, 0, 3, 2}
    };

    auto result_pid = priority_sched.schedule(processes_pid_tie);
    ASSERT_EQ(result_pid.timeline.size(), 3);
    EXPECT_EQ(result_pid.timeline[0].pid, 5);
    EXPECT_EQ(result_pid.timeline[0].start_time, 0);
    EXPECT_EQ(result_pid.timeline[0].end_time, 3);

    EXPECT_EQ(result_pid.timeline[1].pid, 10);
    EXPECT_EQ(result_pid.timeline[1].start_time, 3);
    EXPECT_EQ(result_pid.timeline[1].end_time, 6);

    EXPECT_EQ(result_pid.timeline[2].pid, 20);
    EXPECT_EQ(result_pid.timeline[2].start_time, 6);
    EXPECT_EQ(result_pid.timeline[2].end_time, 9);
}

// 8. Correct completion, turnaround, waiting, and response metrics
TEST(OScopePriorityTest, CalculatesAllMetricsCorrectly) {
    oscope::Priority priority_sched;

    // Workload:
    // P1: arr 1, burst 6, prio 3
    // P2: arr 1, burst 8, prio 4
    // P3: arr 2, burst 3, prio 1
    // P4: arr 4, burst 4, prio 2
    //
    // Timeline trace:
    // t=0..1: Idle
    // t=1: P1 (prio 3) vs P2 (prio 4) -> P1 runs 1..7
    // t=7: Ready: P3 (prio 1), P4 (prio 2), P2 (prio 4) -> P3 runs 7..10
    // t=10: Ready: P4 (prio 2), P2 (prio 4) -> P4 runs 10..14
    // t=14: Ready: P2 (prio 4) -> P2 runs 14..22
    const std::vector<oscope::Process> processes{
        {1, 1, 6, 3},
        {2, 1, 8, 4},
        {3, 2, 3, 1},
        {4, 4, 4, 2}
    };

    auto result = priority_sched.schedule(processes);

    ASSERT_EQ(result.timeline.size(), 4);
    ASSERT_EQ(result.process_results.size(), 4);

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

    // Metrics for P1
    EXPECT_EQ(result.process_results[0].pid, 1);
    EXPECT_EQ(result.process_results[0].completion_time, 7);
    EXPECT_EQ(result.process_results[0].turnaround_time, 6);   // 7 - 1
    EXPECT_EQ(result.process_results[0].waiting_time, 0);      // 6 - 6
    EXPECT_EQ(result.process_results[0].response_time, 0);     // 1 - 1

    // Metrics for P3
    EXPECT_EQ(result.process_results[1].pid, 3);
    EXPECT_EQ(result.process_results[1].completion_time, 10);
    EXPECT_EQ(result.process_results[1].turnaround_time, 8);   // 10 - 2
    EXPECT_EQ(result.process_results[1].waiting_time, 5);      // 8 - 3
    EXPECT_EQ(result.process_results[1].response_time, 5);     // 7 - 2

    // Metrics for P4
    EXPECT_EQ(result.process_results[2].pid, 4);
    EXPECT_EQ(result.process_results[2].completion_time, 14);
    EXPECT_EQ(result.process_results[2].turnaround_time, 10);  // 14 - 4
    EXPECT_EQ(result.process_results[2].waiting_time, 6);      // 10 - 4
    EXPECT_EQ(result.process_results[2].response_time, 6);     // 10 - 4

    // Metrics for P2
    EXPECT_EQ(result.process_results[3].pid, 2);
    EXPECT_EQ(result.process_results[3].completion_time, 22);
    EXPECT_EQ(result.process_results[3].turnaround_time, 21);  // 22 - 1
    EXPECT_EQ(result.process_results[3].waiting_time, 13);     // 21 - 8
    EXPECT_EQ(result.process_results[3].response_time, 13);    // 14 - 1
}

// 9. Input vector remains unchanged
TEST(OScopePriorityTest, PreservesCallerInputVector) {
    oscope::Priority priority_sched;

    std::vector<oscope::Process> processes{
        {3, 2, 3, 1},
        {1, 0, 5, 5},
        {2, 1, 3, 3}
    };

    const std::vector<oscope::Process> original_copy = processes;

    auto result = priority_sched.schedule(processes);
    (void)result;

    ASSERT_EQ(processes.size(), original_copy.size());
    for (std::size_t i = 0; i < processes.size(); ++i) {
        EXPECT_EQ(processes[i].pid, original_copy[i].pid);
        EXPECT_EQ(processes[i].arrival_time, original_copy[i].arrival_time);
        EXPECT_EQ(processes[i].burst_time, original_copy[i].burst_time);
        EXPECT_EQ(processes[i].priority, original_copy[i].priority);
    }
}

// 10. A single process
TEST(OScopePriorityTest, HandlesSingleProcess) {
    oscope::Priority priority_sched;

    const std::vector<oscope::Process> processes{
        {1, 3, 5, 1}
    };

    auto result = priority_sched.schedule(processes);

    ASSERT_EQ(result.timeline.size(), 1);
    ASSERT_EQ(result.process_results.size(), 1);

    EXPECT_EQ(result.timeline[0].pid, 1);
    EXPECT_EQ(result.timeline[0].start_time, 3);
    EXPECT_EQ(result.timeline[0].end_time, 8);

    EXPECT_EQ(result.process_results[0].pid, 1);
    EXPECT_EQ(result.process_results[0].completion_time, 8);
    EXPECT_EQ(result.process_results[0].turnaround_time, 5);
    EXPECT_EQ(result.process_results[0].waiting_time, 0);
    EXPECT_EQ(result.process_results[0].response_time, 0);
}
