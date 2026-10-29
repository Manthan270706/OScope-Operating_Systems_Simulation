#include <gtest/gtest.h>

#include <cstddef>
#include <vector>

#include "oscope/execution_segment.hpp"
#include "oscope/process.hpp"
#include "oscope/scheduling/srtf.hpp"
#include "oscope/scheduling_result.hpp"
#include "oscope/scheduling_simulation_result.hpp"

// 1. Empty input
TEST(OScopeSRTFTest, HandlesEmptyInput) {
    oscope::SRTF srtf;
    const std::vector<oscope::Process> processes{};

    auto result = srtf.schedule(processes);

    EXPECT_TRUE(result.process_results.empty());
    EXPECT_TRUE(result.timeline.empty());
}

// 2. A workload that demonstrates actual preemption
TEST(OScopeSRTFTest, PreemptsRunningProcessWhenShorterProcessArrives) {
    oscope::SRTF srtf;

    // P1 arrives at 0 with burst 8.
    // P2 arrives at 2 with burst 2.
    // At t=2, P1 has remaining time 6. Since 2 < 6, P2 strictly preempts P1.
    // P2 finishes at t=4. P1 resumes and finishes at t=10.
    const std::vector<oscope::Process> processes{
        {1, 0, 8, 0},
        {2, 2, 2, 0}
    };

    auto result = srtf.schedule(processes);

    ASSERT_EQ(result.timeline.size(), 3);
    ASSERT_EQ(result.process_results.size(), 2);

    // Timeline segments
    EXPECT_EQ(result.timeline[0].pid, 1);
    EXPECT_EQ(result.timeline[0].start_time, 0);
    EXPECT_EQ(result.timeline[0].end_time, 2);

    EXPECT_EQ(result.timeline[1].pid, 2);
    EXPECT_EQ(result.timeline[1].start_time, 2);
    EXPECT_EQ(result.timeline[1].end_time, 4);

    EXPECT_EQ(result.timeline[2].pid, 1);
    EXPECT_EQ(result.timeline[2].start_time, 4);
    EXPECT_EQ(result.timeline[2].end_time, 10);

    // Process results (in completion order: P2 completes at 4, P1 completes at 10)
    EXPECT_EQ(result.process_results[0].pid, 2);
    EXPECT_EQ(result.process_results[0].completion_time, 4);
    EXPECT_EQ(result.process_results[0].turnaround_time, 2); // 4 - 2
    EXPECT_EQ(result.process_results[0].waiting_time, 0);    // 2 - 2
    EXPECT_EQ(result.process_results[0].response_time, 0);   // 2 - 2

    EXPECT_EQ(result.process_results[1].pid, 1);
    EXPECT_EQ(result.process_results[1].completion_time, 10);
    EXPECT_EQ(result.process_results[1].turnaround_time, 10); // 10 - 0
    EXPECT_EQ(result.process_results[1].waiting_time, 2);     // 10 - 8
    EXPECT_EQ(result.process_results[1].response_time, 0);    // 0 - 0
}

// 3. Multiple preemptions and process resumption
TEST(OScopeSRTFTest, HandlesMultiplePreemptionsAndResumptions) {
    oscope::SRTF srtf;

    // P1: arrives 0, burst 12
    // P2: arrives 2, burst 4  (at t=2, P1 rem 10; 4 < 10 -> P2 preempts P1)
    // P3: arrives 3, burst 1  (at t=3, P2 rem 3; 1 < 3 -> P3 preempts P2)
    // Sequence:
    // t=0..2: P1 runs (rem becomes 10)
    // t=2..3: P2 runs (rem becomes 3)
    // t=3..4: P3 runs and completes at 4
    // t=4..7: P2 resumes (rem 3) and completes at 7
    // t=7..17: P1 resumes (rem 10) and completes at 17
    const std::vector<oscope::Process> processes{
        {1, 0, 12, 0},
        {2, 2, 4, 0},
        {3, 3, 1, 0}
    };

    auto result = srtf.schedule(processes);

    ASSERT_EQ(result.timeline.size(), 5);
    ASSERT_EQ(result.process_results.size(), 3);

    EXPECT_EQ(result.timeline[0].pid, 1);
    EXPECT_EQ(result.timeline[0].start_time, 0);
    EXPECT_EQ(result.timeline[0].end_time, 2);

    EXPECT_EQ(result.timeline[1].pid, 2);
    EXPECT_EQ(result.timeline[1].start_time, 2);
    EXPECT_EQ(result.timeline[1].end_time, 3);

    EXPECT_EQ(result.timeline[2].pid, 3);
    EXPECT_EQ(result.timeline[2].start_time, 3);
    EXPECT_EQ(result.timeline[2].end_time, 4);

    EXPECT_EQ(result.timeline[3].pid, 2);
    EXPECT_EQ(result.timeline[3].start_time, 4);
    EXPECT_EQ(result.timeline[3].end_time, 7);

    EXPECT_EQ(result.timeline[4].pid, 1);
    EXPECT_EQ(result.timeline[4].start_time, 7);
    EXPECT_EQ(result.timeline[4].end_time, 17);

    // Completion order: P3 (4), P2 (7), P1 (17)
    EXPECT_EQ(result.process_results[0].pid, 3);
    EXPECT_EQ(result.process_results[0].completion_time, 4);
    EXPECT_EQ(result.process_results[0].turnaround_time, 1); // 4 - 3
    EXPECT_EQ(result.process_results[0].waiting_time, 0);
    EXPECT_EQ(result.process_results[0].response_time, 0);

    EXPECT_EQ(result.process_results[1].pid, 2);
    EXPECT_EQ(result.process_results[1].completion_time, 7);
    EXPECT_EQ(result.process_results[1].turnaround_time, 5); // 7 - 2
    EXPECT_EQ(result.process_results[1].waiting_time, 1);    // 5 - 4
    EXPECT_EQ(result.process_results[1].response_time, 0);   // 2 - 2

    EXPECT_EQ(result.process_results[2].pid, 1);
    EXPECT_EQ(result.process_results[2].completion_time, 17);
    EXPECT_EQ(result.process_results[2].turnaround_time, 17); // 17 - 0
    EXPECT_EQ(result.process_results[2].waiting_time, 5);     // 17 - 12
    EXPECT_EQ(result.process_results[2].response_time, 0);    // 0 - 0
}

// 4. Unsorted input
TEST(OScopeSRTFTest, HandlesProcessesSuppliedInUnsortedOrder) {
    oscope::SRTF srtf;

    // Supplied out of arrival order
    const std::vector<oscope::Process> processes{
        {2, 2, 2, 0},
        {3, 5, 1, 0},
        {1, 0, 8, 0}
    };

    auto result = srtf.schedule(processes);

    ASSERT_EQ(result.timeline.size(), 5);
    ASSERT_EQ(result.process_results.size(), 3);

    // 0..2: P1 runs (rem becomes 6)
    // 2..4: P2 preempts and completes at 4
    // 4..5: P1 resumes (rem becomes 5)
    // 5..6: P3 preempts and completes at 6
    // 6..11: P1 resumes and completes at 11
    EXPECT_EQ(result.timeline[0].pid, 1);
    EXPECT_EQ(result.timeline[0].start_time, 0);
    EXPECT_EQ(result.timeline[0].end_time, 2);

    EXPECT_EQ(result.timeline[1].pid, 2);
    EXPECT_EQ(result.timeline[1].start_time, 2);
    EXPECT_EQ(result.timeline[1].end_time, 4);

    EXPECT_EQ(result.timeline[2].pid, 1);
    EXPECT_EQ(result.timeline[2].start_time, 4);
    EXPECT_EQ(result.timeline[2].end_time, 5);

    EXPECT_EQ(result.timeline[3].pid, 3);
    EXPECT_EQ(result.timeline[3].start_time, 5);
    EXPECT_EQ(result.timeline[3].end_time, 6);

    EXPECT_EQ(result.timeline[4].pid, 1);
    EXPECT_EQ(result.timeline[4].start_time, 6);
    EXPECT_EQ(result.timeline[4].end_time, 11);

    // Process results: P2 at 4, P3 at 6, P1 at 11
    EXPECT_EQ(result.process_results[0].pid, 2);
    EXPECT_EQ(result.process_results[0].completion_time, 4);
    EXPECT_EQ(result.process_results[1].pid, 3);
    EXPECT_EQ(result.process_results[1].completion_time, 6);
    EXPECT_EQ(result.process_results[2].pid, 1);
    EXPECT_EQ(result.process_results[2].completion_time, 11);
}

// 5. CPU idle time before the first arrival and between workloads
TEST(OScopeSRTFTest, HandlesIdleTimeBeforeFirstArrivalAndBetweenWorkloads) {
    oscope::SRTF srtf;

    // Idle 0..3
    // P1 arrives at 3, burst 4. (P1 runs 3..4, rem becomes 3)
    // P2 arrives at 4, burst 1. (1 < 3 -> P2 preempts P1, runs 4..5)
    // P1 resumes 5..8 and completes at 8.
    // Idle 8..12
    // P3 arrives at 12, burst 2. (runs 12..14)
    const std::vector<oscope::Process> processes{
        {1, 3, 4, 0},
        {2, 4, 1, 0},
        {3, 12, 2, 0}
    };

    auto result = srtf.schedule(processes);

    ASSERT_EQ(result.timeline.size(), 4);
    ASSERT_EQ(result.process_results.size(), 3);

    EXPECT_EQ(result.timeline[0].pid, 1);
    EXPECT_EQ(result.timeline[0].start_time, 3);
    EXPECT_EQ(result.timeline[0].end_time, 4);

    EXPECT_EQ(result.timeline[1].pid, 2);
    EXPECT_EQ(result.timeline[1].start_time, 4);
    EXPECT_EQ(result.timeline[1].end_time, 5);

    EXPECT_EQ(result.timeline[2].pid, 1);
    EXPECT_EQ(result.timeline[2].start_time, 5);
    EXPECT_EQ(result.timeline[2].end_time, 8);

    EXPECT_EQ(result.timeline[3].pid, 3);
    EXPECT_EQ(result.timeline[3].start_time, 12);
    EXPECT_EQ(result.timeline[3].end_time, 14);

    // Metrics
    EXPECT_EQ(result.process_results[0].pid, 2);
    EXPECT_EQ(result.process_results[0].completion_time, 5);
    EXPECT_EQ(result.process_results[0].turnaround_time, 1);
    EXPECT_EQ(result.process_results[0].waiting_time, 0);
    EXPECT_EQ(result.process_results[0].response_time, 0);

    EXPECT_EQ(result.process_results[1].pid, 1);
    EXPECT_EQ(result.process_results[1].completion_time, 8);
    EXPECT_EQ(result.process_results[1].turnaround_time, 5); // 8 - 3
    EXPECT_EQ(result.process_results[1].waiting_time, 1);    // 5 - 4
    EXPECT_EQ(result.process_results[1].response_time, 0);   // 3 - 3

    EXPECT_EQ(result.process_results[2].pid, 3);
    EXPECT_EQ(result.process_results[2].completion_time, 14);
    EXPECT_EQ(result.process_results[2].turnaround_time, 2);
    EXPECT_EQ(result.process_results[2].waiting_time, 0);
    EXPECT_EQ(result.process_results[2].response_time, 0);
}

// 6. Equal remaining times and deterministic tie behavior
TEST(OScopeSRTFTest, BreaksTiesByEarlierArrivalTimeThenLowerPidWithoutPreemptingTies) {
    oscope::SRTF srtf;

    // Case A: A running process is NOT preempted when a newly arrived process ties its remaining time
    // P1 arrives at 0, burst 6.
    // P2 arrives at 3, burst 3.
    // At t=3, P1 remaining is 3. P2 remaining is 3.
    // Because remaining times are tied, P1 is NOT preempted.
    const std::vector<oscope::Process> processes_tie_no_preempt{
        {1, 0, 6, 0},
        {2, 3, 3, 0}
    };

    auto result_a = srtf.schedule(processes_tie_no_preempt);
    ASSERT_EQ(result_a.timeline.size(), 2);
    EXPECT_EQ(result_a.timeline[0].pid, 1);
    EXPECT_EQ(result_a.timeline[0].start_time, 0);
    EXPECT_EQ(result_a.timeline[0].end_time, 6);
    EXPECT_EQ(result_a.timeline[1].pid, 2);
    EXPECT_EQ(result_a.timeline[1].start_time, 6);
    EXPECT_EQ(result_a.timeline[1].end_time, 9);

    // Case B: Ready selection with equal remaining time breaks ties by earlier arrival time
    const std::vector<oscope::Process> processes_arrival_tie{
        {1, 1, 4, 0},
        {2, 2, 4, 0}
    };
    // At t=2, P1 has run 1..2 (rem 3). But if idle at start until both arrive (e.g. at 2):
    // Here P1 arrives at 1, starts at 1, at 2 has rem 3 < P2's 4.
    // To test pure ready selection tie-breaking by arrival time:
    // P0 runs 0..2. At t=2, P1 (arr 0, burst 3) and P2 (arr 1, burst 3) are ready.
    const std::vector<oscope::Process> processes_arrival_ready_tie{
        {0, 0, 2, 0},
        {1, 0, 3, 0},
        {2, 1, 3, 0}
    };
    // P0 arrives 0, burst 2. P1 arrives 0, burst 3. P0 runs 0..2.
    // At t=2, P1 (rem 3, arr 0) and P2 (rem 3, arr 1) are ready.
    // P1 arrived earlier (0 < 1), so P1 must be chosen over P2.
    auto result_b = srtf.schedule(processes_arrival_ready_tie);
    ASSERT_EQ(result_b.timeline.size(), 3);
    EXPECT_EQ(result_b.timeline[0].pid, 0);
    EXPECT_EQ(result_b.timeline[0].start_time, 0);
    EXPECT_EQ(result_b.timeline[0].end_time, 2);

    EXPECT_EQ(result_b.timeline[1].pid, 1);
    EXPECT_EQ(result_b.timeline[1].start_time, 2);
    EXPECT_EQ(result_b.timeline[1].end_time, 5);

    EXPECT_EQ(result_b.timeline[2].pid, 2);
    EXPECT_EQ(result_b.timeline[2].start_time, 5);
    EXPECT_EQ(result_b.timeline[2].end_time, 8);

    // Case C: Equal remaining time AND equal arrival time breaks ties by lower PID
    const std::vector<oscope::Process> processes_pid_tie{
        {20, 0, 3, 0},
        {10, 0, 3, 0},
        {5, 0, 3, 0}
    };

    auto result_c = srtf.schedule(processes_pid_tie);
    ASSERT_EQ(result_c.timeline.size(), 3);
    EXPECT_EQ(result_c.timeline[0].pid, 5);
    EXPECT_EQ(result_c.timeline[0].start_time, 0);
    EXPECT_EQ(result_c.timeline[0].end_time, 3);

    EXPECT_EQ(result_c.timeline[1].pid, 10);
    EXPECT_EQ(result_c.timeline[1].start_time, 3);
    EXPECT_EQ(result_c.timeline[1].end_time, 6);

    EXPECT_EQ(result_c.timeline[2].pid, 20);
    EXPECT_EQ(result_c.timeline[2].start_time, 6);
    EXPECT_EQ(result_c.timeline[2].end_time, 9);
}

// 7. Completion, turnaround, waiting, and response time correctness
TEST(OScopeSRTFTest, CalculatesAllMetricsCorrectlyWithPreemptions) {
    oscope::SRTF srtf;

    // Workload:
    // P1: arr 0, burst 9
    // P2: arr 1, burst 4
    // P3: arr 2, burst 2
    // P4: arr 3, burst 1
    //
    // Timeline trace:
    // t=0: P1 starts (rem 9)
    // t=1: P2 arrives (rem 4). P1 rem is 8. 4 < 8 -> P2 preempts P1.
    //      Segment 0: PID 1, 0..1
    // t=1: P2 starts (rem 4)
    // t=2: P3 arrives (rem 2). P2 rem is 3. 2 < 3 -> P3 preempts P2.
    //      Segment 1: PID 2, 1..2
    // t=2: P3 starts (rem 2)
    // t=3: P4 arrives (rem 1). P3 rem is 1. 1 < 1 is false -> no preemption.
    //      P3 continues!
    // t=4: P3 completes at 4.
    //      Segment 2: PID 3, 2..4
    // t=4: Ready: P4 (rem 1), P2 (rem 3), P1 (rem 8).
    //      P4 selected. Runs 4..5 and completes.
    //      Segment 3: PID 4, 4..5
    // t=5: Ready: P2 (rem 3), P1 (rem 8).
    //      P2 selected. Runs 5..8 and completes.
    //      Segment 4: PID 2, 5..8
    // t=8: Ready: P1 (rem 8).
    //      P1 selected. Runs 8..16 and completes.
    //      Segment 5: PID 1, 8..16
    const std::vector<oscope::Process> processes{
        {1, 0, 9, 0},
        {2, 1, 4, 0},
        {3, 2, 2, 0},
        {4, 3, 1, 0}
    };

    auto result = srtf.schedule(processes);

    ASSERT_EQ(result.timeline.size(), 6);
    ASSERT_EQ(result.process_results.size(), 4);

    // Verify timeline
    EXPECT_EQ(result.timeline[0].pid, 1);
    EXPECT_EQ(result.timeline[0].start_time, 0);
    EXPECT_EQ(result.timeline[0].end_time, 1);

    EXPECT_EQ(result.timeline[1].pid, 2);
    EXPECT_EQ(result.timeline[1].start_time, 1);
    EXPECT_EQ(result.timeline[1].end_time, 2);

    EXPECT_EQ(result.timeline[2].pid, 3);
    EXPECT_EQ(result.timeline[2].start_time, 2);
    EXPECT_EQ(result.timeline[2].end_time, 4);

    EXPECT_EQ(result.timeline[3].pid, 4);
    EXPECT_EQ(result.timeline[3].start_time, 4);
    EXPECT_EQ(result.timeline[3].end_time, 5);

    EXPECT_EQ(result.timeline[4].pid, 2);
    EXPECT_EQ(result.timeline[4].start_time, 5);
    EXPECT_EQ(result.timeline[4].end_time, 8);

    EXPECT_EQ(result.timeline[5].pid, 1);
    EXPECT_EQ(result.timeline[5].start_time, 8);
    EXPECT_EQ(result.timeline[5].end_time, 16);

    // Metrics for P3 (completed first at 4)
    EXPECT_EQ(result.process_results[0].pid, 3);
    EXPECT_EQ(result.process_results[0].completion_time, 4);
    EXPECT_EQ(result.process_results[0].turnaround_time, 2);  // 4 - 2
    EXPECT_EQ(result.process_results[0].waiting_time, 0);     // 2 - 2
    EXPECT_EQ(result.process_results[0].response_time, 0);    // 2 - 2

    // Metrics for P4 (completed second at 5)
    EXPECT_EQ(result.process_results[1].pid, 4);
    EXPECT_EQ(result.process_results[1].completion_time, 5);
    EXPECT_EQ(result.process_results[1].turnaround_time, 2);  // 5 - 3
    EXPECT_EQ(result.process_results[1].waiting_time, 1);     // 2 - 1
    EXPECT_EQ(result.process_results[1].response_time, 1);    // first start 4 - 3 = 1

    // Metrics for P2 (completed third at 8)
    EXPECT_EQ(result.process_results[2].pid, 2);
    EXPECT_EQ(result.process_results[2].completion_time, 8);
    EXPECT_EQ(result.process_results[2].turnaround_time, 7);  // 8 - 1
    EXPECT_EQ(result.process_results[2].waiting_time, 3);     // 7 - 4
    EXPECT_EQ(result.process_results[2].response_time, 0);    // first start 1 - 1 = 0

    // Metrics for P1 (completed fourth at 16)
    EXPECT_EQ(result.process_results[3].pid, 1);
    EXPECT_EQ(result.process_results[3].completion_time, 16);
    EXPECT_EQ(result.process_results[3].turnaround_time, 16); // 16 - 0
    EXPECT_EQ(result.process_results[3].waiting_time, 7);     // 16 - 9
    EXPECT_EQ(result.process_results[3].response_time, 0);    // first start 0 - 0 = 0
}

// 8. Input preservation
TEST(OScopeSRTFTest, PreservesCallerInputVector) {
    oscope::SRTF srtf;

    std::vector<oscope::Process> processes{
        {2, 3, 4, 1},
        {1, 0, 5, 2},
        {3, 1, 2, 0}
    };

    const std::vector<oscope::Process> original_copy = processes;

    auto result = srtf.schedule(processes);
    (void)result;

    ASSERT_EQ(processes.size(), original_copy.size());
    for (std::size_t i = 0; i < processes.size(); ++i) {
        EXPECT_EQ(processes[i].pid, original_copy[i].pid);
        EXPECT_EQ(processes[i].arrival_time, original_copy[i].arrival_time);
        EXPECT_EQ(processes[i].burst_time, original_copy[i].burst_time);
        EXPECT_EQ(processes[i].priority, original_copy[i].priority);
    }
}

// 9. Timeline segments correctly split at preemption boundaries without unnecessary adjacent duplicates
TEST(OScopeSRTFTest, CorrectlySplitsSegmentsAtPreemptionBoundariesWithoutAdjacentDuplicates) {
    oscope::SRTF srtf;

    // P1: arrives 0, burst 10
    // P2: arrives 2, burst 20 (longer than P1's remaining 8 -> does not preempt)
    // P3: arrives 4, burst 2  (shorter than P1's remaining 6 -> preempts!)
    // Sequence:
    // 0..4: P1 runs continuously (must be a single segment 0..4, not split at 2)
    // 4..6: P3 runs and completes at 6
    // 6..12: P1 resumes and completes at 12
    // 12..32: P2 runs and completes at 32
    const std::vector<oscope::Process> processes{
        {1, 0, 10, 0},
        {2, 2, 20, 0},
        {3, 4, 2, 0}
    };

    auto result = srtf.schedule(processes);

    ASSERT_EQ(result.timeline.size(), 4);

    EXPECT_EQ(result.timeline[0].pid, 1);
    EXPECT_EQ(result.timeline[0].start_time, 0);
    EXPECT_EQ(result.timeline[0].end_time, 4);

    EXPECT_EQ(result.timeline[1].pid, 3);
    EXPECT_EQ(result.timeline[1].start_time, 4);
    EXPECT_EQ(result.timeline[1].end_time, 6);

    EXPECT_EQ(result.timeline[2].pid, 1);
    EXPECT_EQ(result.timeline[2].start_time, 6);
    EXPECT_EQ(result.timeline[2].end_time, 12);

    EXPECT_EQ(result.timeline[3].pid, 2);
    EXPECT_EQ(result.timeline[3].start_time, 12);
    EXPECT_EQ(result.timeline[3].end_time, 32);
}

// 10. A single process with no preemption
TEST(OScopeSRTFTest, HandlesSingleProcessWithoutPreemption) {
    oscope::SRTF srtf;

    const std::vector<oscope::Process> processes{
        {1, 5, 7, 0}
    };

    auto result = srtf.schedule(processes);

    ASSERT_EQ(result.timeline.size(), 1);
    ASSERT_EQ(result.process_results.size(), 1);

    EXPECT_EQ(result.timeline[0].pid, 1);
    EXPECT_EQ(result.timeline[0].start_time, 5);
    EXPECT_EQ(result.timeline[0].end_time, 12);

    EXPECT_EQ(result.process_results[0].pid, 1);
    EXPECT_EQ(result.process_results[0].completion_time, 12);
    EXPECT_EQ(result.process_results[0].turnaround_time, 7);
    EXPECT_EQ(result.process_results[0].waiting_time, 0);
    EXPECT_EQ(result.process_results[0].response_time, 0);
}
