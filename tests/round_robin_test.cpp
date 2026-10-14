#include <gtest/gtest.h>

#include <cstddef>
#include <stdexcept>
#include <vector>

#include "oscope/execution_segment.hpp"
#include "oscope/process.hpp"
#include "oscope/scheduling/round_robin.hpp"
#include "oscope/scheduling_result.hpp"
#include "oscope/scheduling_simulation_result.hpp"

// 1. Empty input
TEST(OScopeRoundRobinTest, HandlesEmptyInput) {
    oscope::RoundRobin rr(3);
    const std::vector<oscope::Process> processes{};

    auto result = rr.schedule(processes);

    EXPECT_TRUE(result.process_results.empty());
    EXPECT_TRUE(result.timeline.empty());
}

// 2. One process requiring multiple time slices
TEST(OScopeRoundRobinTest, OneProcessRequiringMultipleTimeSlices) {
    oscope::RoundRobin rr(4);

    // P1 burst 10 with quantum 4 runs in slices: 0..4 (rem 6), 4..8 (rem 2), 8..10 (rem 0)
    const std::vector<oscope::Process> processes{
        {1, 0, 10, 0}
    };

    auto result = rr.schedule(processes);

    ASSERT_EQ(result.timeline.size(), 3);
    ASSERT_EQ(result.process_results.size(), 1);

    EXPECT_EQ(result.timeline[0].pid, 1);
    EXPECT_EQ(result.timeline[0].start_time, 0);
    EXPECT_EQ(result.timeline[0].end_time, 4);

    EXPECT_EQ(result.timeline[1].pid, 1);
    EXPECT_EQ(result.timeline[1].start_time, 4);
    EXPECT_EQ(result.timeline[1].end_time, 8);

    EXPECT_EQ(result.timeline[2].pid, 1);
    EXPECT_EQ(result.timeline[2].start_time, 8);
    EXPECT_EQ(result.timeline[2].end_time, 10);

    EXPECT_EQ(result.process_results[0].pid, 1);
    EXPECT_EQ(result.process_results[0].completion_time, 10);
    EXPECT_EQ(result.process_results[0].turnaround_time, 10);
    EXPECT_EQ(result.process_results[0].waiting_time, 0);
    EXPECT_EQ(result.process_results[0].response_time, 0);
}

// 3. Multiple processes sharing the CPU in FIFO order
TEST(OScopeRoundRobinTest, MultipleProcessesSharingCpuInFifoOrder) {
    oscope::RoundRobin rr(2);

    const std::vector<oscope::Process> processes{
        {1, 0, 5, 0},
        {2, 0, 5, 0}
    };

    auto result = rr.schedule(processes);

    ASSERT_EQ(result.timeline.size(), 6);
    ASSERT_EQ(result.process_results.size(), 2);

    // Timeline execution order
    EXPECT_EQ(result.timeline[0].pid, 1);
    EXPECT_EQ(result.timeline[0].start_time, 0);
    EXPECT_EQ(result.timeline[0].end_time, 2);

    EXPECT_EQ(result.timeline[1].pid, 2);
    EXPECT_EQ(result.timeline[1].start_time, 2);
    EXPECT_EQ(result.timeline[1].end_time, 4);

    EXPECT_EQ(result.timeline[2].pid, 1);
    EXPECT_EQ(result.timeline[2].start_time, 4);
    EXPECT_EQ(result.timeline[2].end_time, 6);

    EXPECT_EQ(result.timeline[3].pid, 2);
    EXPECT_EQ(result.timeline[3].start_time, 6);
    EXPECT_EQ(result.timeline[3].end_time, 8);

    EXPECT_EQ(result.timeline[4].pid, 1);
    EXPECT_EQ(result.timeline[4].start_time, 8);
    EXPECT_EQ(result.timeline[4].end_time, 9);

    EXPECT_EQ(result.timeline[5].pid, 2);
    EXPECT_EQ(result.timeline[5].start_time, 9);
    EXPECT_EQ(result.timeline[5].end_time, 10);

    // Completion metrics (P1 completes at 9, P2 at 10)
    EXPECT_EQ(result.process_results[0].pid, 1);
    EXPECT_EQ(result.process_results[0].completion_time, 9);
    EXPECT_EQ(result.process_results[0].turnaround_time, 9);
    EXPECT_EQ(result.process_results[0].waiting_time, 4);  // 9 - 5
    EXPECT_EQ(result.process_results[0].response_time, 0); // 0 - 0

    EXPECT_EQ(result.process_results[1].pid, 2);
    EXPECT_EQ(result.process_results[1].completion_time, 10);
    EXPECT_EQ(result.process_results[1].turnaround_time, 10);
    EXPECT_EQ(result.process_results[1].waiting_time, 5);  // 10 - 5
    EXPECT_EQ(result.process_results[1].response_time, 2); // 2 - 0
}

// 4. A process arriving while another process is executing
TEST(OScopeRoundRobinTest, ProcessArrivingWhileAnotherExecutes) {
    oscope::RoundRobin rr(4);

    // P1 arrives at 0 with burst 6.
    // P2 arrives at 2 with burst 3.
    // P1 runs 0..4 (rem 2). During this time P2 arrived at 2.
    // P2 is enqueued into the ready queue before P1 is re-enqueued.
    // Queue becomes [P2, P1].
    // P2 runs 4..7 (completes at 7).
    // P1 runs 7..9 (completes at 9).
    const std::vector<oscope::Process> processes{
        {1, 0, 6, 0},
        {2, 2, 3, 0}
    };

    auto result = rr.schedule(processes);

    ASSERT_EQ(result.timeline.size(), 3);
    ASSERT_EQ(result.process_results.size(), 2);

    EXPECT_EQ(result.timeline[0].pid, 1);
    EXPECT_EQ(result.timeline[0].start_time, 0);
    EXPECT_EQ(result.timeline[0].end_time, 4);

    EXPECT_EQ(result.timeline[1].pid, 2);
    EXPECT_EQ(result.timeline[1].start_time, 4);
    EXPECT_EQ(result.timeline[1].end_time, 7);

    EXPECT_EQ(result.timeline[2].pid, 1);
    EXPECT_EQ(result.timeline[2].start_time, 7);
    EXPECT_EQ(result.timeline[2].end_time, 9);

    EXPECT_EQ(result.process_results[0].pid, 2);
    EXPECT_EQ(result.process_results[0].completion_time, 7);
    EXPECT_EQ(result.process_results[0].turnaround_time, 5); // 7 - 2
    EXPECT_EQ(result.process_results[0].waiting_time, 2);    // 5 - 3
    EXPECT_EQ(result.process_results[0].response_time, 2);   // 4 - 2

    EXPECT_EQ(result.process_results[1].pid, 1);
    EXPECT_EQ(result.process_results[1].completion_time, 9);
    EXPECT_EQ(result.process_results[1].turnaround_time, 9); // 9 - 0
    EXPECT_EQ(result.process_results[1].waiting_time, 3);    // 9 - 6
    EXPECT_EQ(result.process_results[1].response_time, 0);   // 0 - 0
}

// 5. Multiple processes arriving at the same time
TEST(OScopeRoundRobinTest, MultipleProcessesArrivingAtTheSameTime) {
    oscope::RoundRobin rr(4);

    // P1 runs 0..4 and finishes.
    // P2 and P3 arrive at t=2.
    // At t=4, both are enqueued; relative input order is preserved (P2 then P3).
    const std::vector<oscope::Process> processes{
        {1, 0, 4, 0},
        {2, 2, 2, 0},
        {3, 2, 2, 0}
    };

    auto result = rr.schedule(processes);

    ASSERT_EQ(result.timeline.size(), 3);
    EXPECT_EQ(result.timeline[0].pid, 1);
    EXPECT_EQ(result.timeline[0].start_time, 0);
    EXPECT_EQ(result.timeline[0].end_time, 4);

    EXPECT_EQ(result.timeline[1].pid, 2);
    EXPECT_EQ(result.timeline[1].start_time, 4);
    EXPECT_EQ(result.timeline[1].end_time, 6);

    EXPECT_EQ(result.timeline[2].pid, 3);
    EXPECT_EQ(result.timeline[2].start_time, 6);
    EXPECT_EQ(result.timeline[2].end_time, 8);
}

// 6. Unsorted input and the stated arrival-order policy
TEST(OScopeRoundRobinTest, HandlesUnsortedInputPreservingArrivalPolicy) {
    oscope::RoundRobin rr(4);

    // Processes supplied in arbitrary order:
    // P3 arrives at 2, P1 arrives at 0, P2 arrives at 1.
    // While P1 runs 0..4: P2 (arr 1) arrives before P3 (arr 2).
    // Ascending arrival time dictates P2 is enqueued before P3.
    const std::vector<oscope::Process> processes{
        {3, 2, 2, 0},
        {1, 0, 4, 0},
        {2, 1, 2, 0}
    };

    auto result = rr.schedule(processes);

    ASSERT_EQ(result.timeline.size(), 3);
    EXPECT_EQ(result.timeline[0].pid, 1);
    EXPECT_EQ(result.timeline[0].start_time, 0);
    EXPECT_EQ(result.timeline[0].end_time, 4);

    EXPECT_EQ(result.timeline[1].pid, 2);
    EXPECT_EQ(result.timeline[1].start_time, 4);
    EXPECT_EQ(result.timeline[1].end_time, 6);

    EXPECT_EQ(result.timeline[2].pid, 3);
    EXPECT_EQ(result.timeline[2].start_time, 6);
    EXPECT_EQ(result.timeline[2].end_time, 8);
}

// 7. CPU idle time before the first arrival and between workloads
TEST(OScopeRoundRobinTest, HandlesIdleTimeBeforeFirstArrivalAndBetweenWorkloads) {
    oscope::RoundRobin rr(2);

    // Idle 0..3: P1 arrives at 3, burst 3 -> runs 3..5 (rem 1), 5..6 (completes at 6)
    // Idle 6..10: P2 arrives at 10, burst 2 -> runs 10..12 (completes at 12)
    const std::vector<oscope::Process> processes{
        {1, 3, 3, 0},
        {2, 10, 2, 0}
    };

    auto result = rr.schedule(processes);

    ASSERT_EQ(result.timeline.size(), 3);
    ASSERT_EQ(result.process_results.size(), 2);

    EXPECT_EQ(result.timeline[0].pid, 1);
    EXPECT_EQ(result.timeline[0].start_time, 3);
    EXPECT_EQ(result.timeline[0].end_time, 5);

    EXPECT_EQ(result.timeline[1].pid, 1);
    EXPECT_EQ(result.timeline[1].start_time, 5);
    EXPECT_EQ(result.timeline[1].end_time, 6);

    EXPECT_EQ(result.timeline[2].pid, 2);
    EXPECT_EQ(result.timeline[2].start_time, 10);
    EXPECT_EQ(result.timeline[2].end_time, 12);

    EXPECT_EQ(result.process_results[0].pid, 1);
    EXPECT_EQ(result.process_results[0].completion_time, 6);
    EXPECT_EQ(result.process_results[0].turnaround_time, 3);
    EXPECT_EQ(result.process_results[0].waiting_time, 0);
    EXPECT_EQ(result.process_results[0].response_time, 0);

    EXPECT_EQ(result.process_results[1].pid, 2);
    EXPECT_EQ(result.process_results[1].completion_time, 12);
    EXPECT_EQ(result.process_results[1].turnaround_time, 2);
    EXPECT_EQ(result.process_results[1].waiting_time, 0);
    EXPECT_EQ(result.process_results[1].response_time, 0);
}

// 8. Correct completion, turnaround, waiting, and response times
TEST(OScopeRoundRobinTest, CalculatesAllMetricsCorrectly) {
    oscope::RoundRobin rr(3);

    // Workload:
    // P1: arr 0, burst 7
    // P2: arr 2, burst 4
    // P3: arr 4, burst 1
    //
    // Timeline trace:
    // t=0..3: P1 runs (rem 4). P2 arrives at 2. Queue at t=3: [P2, P1]
    // t=3..6: P2 runs (rem 1). P3 arrives at 4. Queue at t=6: [P1, P3, P2]
    // t=6..9: P1 runs (rem 1). Queue at t=9: [P3, P2, P1]
    // t=9..10: P3 runs (rem 0). Completes at 10. Queue at t=10: [P2, P1]
    // t=10..11: P2 runs (rem 0). Completes at 11. Queue at t=11: [P1]
    // t=11..12: P1 runs (rem 0). Completes at 12.
    const std::vector<oscope::Process> processes{
        {1, 0, 7, 0},
        {2, 2, 4, 0},
        {3, 4, 1, 0}
    };

    auto result = rr.schedule(processes);

    ASSERT_EQ(result.timeline.size(), 6);
    ASSERT_EQ(result.process_results.size(), 3);

    // Metrics for P3 (completed at 10)
    EXPECT_EQ(result.process_results[0].pid, 3);
    EXPECT_EQ(result.process_results[0].completion_time, 10);
    EXPECT_EQ(result.process_results[0].turnaround_time, 6); // 10 - 4
    EXPECT_EQ(result.process_results[0].waiting_time, 5);    // 6 - 1
    EXPECT_EQ(result.process_results[0].response_time, 5);   // 9 - 4

    // Metrics for P2 (completed at 11)
    EXPECT_EQ(result.process_results[1].pid, 2);
    EXPECT_EQ(result.process_results[1].completion_time, 11);
    EXPECT_EQ(result.process_results[1].turnaround_time, 9); // 11 - 2
    EXPECT_EQ(result.process_results[1].waiting_time, 5);    // 9 - 4
    EXPECT_EQ(result.process_results[1].response_time, 1);   // 3 - 2

    // Metrics for P1 (completed at 12)
    EXPECT_EQ(result.process_results[2].pid, 1);
    EXPECT_EQ(result.process_results[2].completion_time, 12);
    EXPECT_EQ(result.process_results[2].turnaround_time, 12); // 12 - 0
    EXPECT_EQ(result.process_results[2].waiting_time, 5);     // 12 - 7
    EXPECT_EQ(result.process_results[2].response_time, 0);    // 0 - 0
}

// 9. Correct timeline slices and segment boundaries
TEST(OScopeRoundRobinTest, CorrectTimelineSlicesAndSegmentBoundaries) {
    oscope::RoundRobin rr(3);

    const std::vector<oscope::Process> processes{
        {1, 0, 5, 0},
        {2, 1, 2, 0}
    };

    // t=0..3: P1 runs (rem 2). P2 arrived at 1. Queue at 3: [P2, P1]
    // t=3..5: P2 runs (rem 0). Completes at 5. Queue: [P1]
    // t=5..7: P1 runs (rem 0). Completes at 7.
    auto result = rr.schedule(processes);

    ASSERT_EQ(result.timeline.size(), 3);

    EXPECT_EQ(result.timeline[0].pid, 1);
    EXPECT_EQ(result.timeline[0].start_time, 0);
    EXPECT_EQ(result.timeline[0].end_time, 3);

    EXPECT_EQ(result.timeline[1].pid, 2);
    EXPECT_EQ(result.timeline[1].start_time, 3);
    EXPECT_EQ(result.timeline[1].end_time, 5);

    EXPECT_EQ(result.timeline[2].pid, 1);
    EXPECT_EQ(result.timeline[2].start_time, 5);
    EXPECT_EQ(result.timeline[2].end_time, 7);
}

// 10. Input vector preservation
TEST(OScopeRoundRobinTest, PreservesCallerInputVector) {
    oscope::RoundRobin rr(2);

    std::vector<oscope::Process> processes{
        {2, 3, 4, 1},
        {1, 0, 5, 2},
        {3, 1, 2, 0}
    };

    const std::vector<oscope::Process> original_copy = processes;

    auto result = rr.schedule(processes);
    (void)result;

    ASSERT_EQ(processes.size(), original_copy.size());
    for (std::size_t i = 0; i < processes.size(); ++i) {
        EXPECT_EQ(processes[i].pid, original_copy[i].pid);
        EXPECT_EQ(processes[i].arrival_time, original_copy[i].arrival_time);
        EXPECT_EQ(processes[i].burst_time, original_copy[i].burst_time);
        EXPECT_EQ(processes[i].priority, original_copy[i].priority);
    }
}

// 11. Constructor rejects zero quantum
TEST(OScopeRoundRobinTest, ConstructorRejectsZeroQuantum) {
    EXPECT_THROW(oscope::RoundRobin(0), std::invalid_argument);
}

// 12. Constructor rejects negative quantum
TEST(OScopeRoundRobinTest, ConstructorRejectsNegativeQuantum) {
    EXPECT_THROW(oscope::RoundRobin(-4), std::invalid_argument);
}

// 13. A process whose burst is exactly equal to the quantum
TEST(OScopeRoundRobinTest, ProcessBurstExactlyEqualToQuantum) {
    oscope::RoundRobin rr(4);

    const std::vector<oscope::Process> processes{
        {1, 0, 4, 0}
    };

    auto result = rr.schedule(processes);

    ASSERT_EQ(result.timeline.size(), 1);
    EXPECT_EQ(result.timeline[0].pid, 1);
    EXPECT_EQ(result.timeline[0].start_time, 0);
    EXPECT_EQ(result.timeline[0].end_time, 4);

    ASSERT_EQ(result.process_results.size(), 1);
    EXPECT_EQ(result.process_results[0].completion_time, 4);
    EXPECT_EQ(result.process_results[0].turnaround_time, 4);
    EXPECT_EQ(result.process_results[0].waiting_time, 0);
    EXPECT_EQ(result.process_results[0].response_time, 0);
}

// 14. A process that completes in its final partial quantum
TEST(OScopeRoundRobinTest, ProcessCompletesInFinalPartialQuantum) {
    oscope::RoundRobin rr(3);

    // Burst 5: slice 1 is full quantum 3 (0..3, rem 2); slice 2 is partial quantum 2 (3..5, rem 0)
    const std::vector<oscope::Process> processes{
        {1, 0, 5, 0}
    };

    auto result = rr.schedule(processes);

    ASSERT_EQ(result.timeline.size(), 2);

    EXPECT_EQ(result.timeline[0].pid, 1);
    EXPECT_EQ(result.timeline[0].start_time, 0);
    EXPECT_EQ(result.timeline[0].end_time, 3);

    EXPECT_EQ(result.timeline[1].pid, 1);
    EXPECT_EQ(result.timeline[1].start_time, 3);
    EXPECT_EQ(result.timeline[1].end_time, 5);

    ASSERT_EQ(result.process_results.size(), 1);
    EXPECT_EQ(result.process_results[0].completion_time, 5);
    EXPECT_EQ(result.process_results[0].turnaround_time, 5);
    EXPECT_EQ(result.process_results[0].waiting_time, 0);
    EXPECT_EQ(result.process_results[0].response_time, 0);
}
