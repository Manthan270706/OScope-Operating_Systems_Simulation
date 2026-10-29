#include <gtest/gtest.h>

#include <cstddef>
#include <stdexcept>
#include <vector>

#include "oscope/execution_segment.hpp"
#include "oscope/process.hpp"
#include "oscope/scheduling/mlfq.hpp"
#include "oscope/scheduling_result.hpp"
#include "oscope/scheduling_simulation_result.hpp"

// 1. Empty input
TEST(OScopeMLFQTest, HandlesEmptyInput) {
    oscope::MLFQ mlfq(2, 4, 8);
    const std::vector<oscope::Process> processes{};

    auto result = mlfq.schedule(processes);

    EXPECT_TRUE(result.process_results.empty());
    EXPECT_TRUE(result.timeline.empty());
}

// 2. Single-process completion within Q0
TEST(OScopeMLFQTest, SingleProcessCompletesWithinQ0) {
    oscope::MLFQ mlfq(4, 8, 16);

    const std::vector<oscope::Process> processes{
        {1, 0, 3, 0}
    };

    auto result = mlfq.schedule(processes);

    ASSERT_EQ(result.timeline.size(), 1);
    ASSERT_EQ(result.process_results.size(), 1);

    EXPECT_EQ(result.timeline[0].pid, 1);
    EXPECT_EQ(result.timeline[0].start_time, 0);
    EXPECT_EQ(result.timeline[0].end_time, 3);

    EXPECT_EQ(result.process_results[0].pid, 1);
    EXPECT_EQ(result.process_results[0].completion_time, 3);
    EXPECT_EQ(result.process_results[0].turnaround_time, 3);
    EXPECT_EQ(result.process_results[0].waiting_time, 0);
    EXPECT_EQ(result.process_results[0].response_time, 0);
}

// 3. Correct queue demotion after exhausting a quantum (Q0 -> Q1 -> Q2)
TEST(OScopeMLFQTest, QueueDemotionAcrossAllQueues) {
    oscope::MLFQ mlfq(2, 4, 8);

    // P1 burst 10:
    // Q0 (quantum 2): runs 0..2 (rem 8), exhausts Q0 -> demoted to Q1
    // Q1 (quantum 4): runs 2..6 (rem 4), exhausts Q1 -> demoted to Q2
    // Q2 (quantum 8): runs 6..10 (rem 0), completes at 10
    const std::vector<oscope::Process> processes{
        {1, 0, 10, 0}
    };

    auto result = mlfq.schedule(processes);

    ASSERT_EQ(result.timeline.size(), 3);
    ASSERT_EQ(result.process_results.size(), 1);

    EXPECT_EQ(result.timeline[0].pid, 1);
    EXPECT_EQ(result.timeline[0].start_time, 0);
    EXPECT_EQ(result.timeline[0].end_time, 2);

    EXPECT_EQ(result.timeline[1].pid, 1);
    EXPECT_EQ(result.timeline[1].start_time, 2);
    EXPECT_EQ(result.timeline[1].end_time, 6);

    EXPECT_EQ(result.timeline[2].pid, 1);
    EXPECT_EQ(result.timeline[2].start_time, 6);
    EXPECT_EQ(result.timeline[2].end_time, 10);

    EXPECT_EQ(result.process_results[0].pid, 1);
    EXPECT_EQ(result.process_results[0].completion_time, 10);
    EXPECT_EQ(result.process_results[0].turnaround_time, 10);
    EXPECT_EQ(result.process_results[0].waiting_time, 0);
    EXPECT_EQ(result.process_results[0].response_time, 0);
}

// 4. Requeuing at Q2 after exhausting Q2 quantum
TEST(OScopeMLFQTest, RequeuesAtTailOfQ2) {
    oscope::MLFQ mlfq(2, 3, 4);

    // Two processes with burst 11 each:
    // t=0..2: P1 in Q0 (rem 9) -> demoted to Q1
    // t=2..4: P2 in Q0 (rem 9) -> demoted to Q1
    // t=4..7: P1 in Q1 (rem 6) -> demoted to Q2
    // t=7..10: P2 in Q1 (rem 6) -> demoted to Q2
    // Both in Q2 (quantum 4):
    // t=10..14: P1 in Q2 (rem 2) -> requeued at tail of Q2
    // t=14..18: P2 in Q2 (rem 2) -> requeued at tail of Q2
    // t=18..20: P1 in Q2 (rem 0) -> completes at 20
    // t=20..22: P2 in Q2 (rem 0) -> completes at 22
    const std::vector<oscope::Process> processes{
        {1, 0, 11, 0},
        {2, 0, 11, 0}
    };

    auto result = mlfq.schedule(processes);

    ASSERT_EQ(result.timeline.size(), 8);
    ASSERT_EQ(result.process_results.size(), 2);

    EXPECT_EQ(result.timeline[0].pid, 1);
    EXPECT_EQ(result.timeline[0].start_time, 0);
    EXPECT_EQ(result.timeline[0].end_time, 2);

    EXPECT_EQ(result.timeline[1].pid, 2);
    EXPECT_EQ(result.timeline[1].start_time, 2);
    EXPECT_EQ(result.timeline[1].end_time, 4);

    EXPECT_EQ(result.timeline[2].pid, 1);
    EXPECT_EQ(result.timeline[2].start_time, 4);
    EXPECT_EQ(result.timeline[2].end_time, 7);

    EXPECT_EQ(result.timeline[3].pid, 2);
    EXPECT_EQ(result.timeline[3].start_time, 7);
    EXPECT_EQ(result.timeline[3].end_time, 10);

    EXPECT_EQ(result.timeline[4].pid, 1);
    EXPECT_EQ(result.timeline[4].start_time, 10);
    EXPECT_EQ(result.timeline[4].end_time, 14);

    EXPECT_EQ(result.timeline[5].pid, 2);
    EXPECT_EQ(result.timeline[5].start_time, 14);
    EXPECT_EQ(result.timeline[5].end_time, 18);

    EXPECT_EQ(result.timeline[6].pid, 1);
    EXPECT_EQ(result.timeline[6].start_time, 18);
    EXPECT_EQ(result.timeline[6].end_time, 20);

    EXPECT_EQ(result.timeline[7].pid, 2);
    EXPECT_EQ(result.timeline[7].start_time, 20);
    EXPECT_EQ(result.timeline[7].end_time, 22);

    EXPECT_EQ(result.process_results[0].pid, 1);
    EXPECT_EQ(result.process_results[0].completion_time, 20);
    EXPECT_EQ(result.process_results[0].turnaround_time, 20);
    EXPECT_EQ(result.process_results[0].waiting_time, 9);  // 20 - 11
    EXPECT_EQ(result.process_results[0].response_time, 0);

    EXPECT_EQ(result.process_results[1].pid, 2);
    EXPECT_EQ(result.process_results[1].completion_time, 22);
    EXPECT_EQ(result.process_results[1].turnaround_time, 22);
    EXPECT_EQ(result.process_results[1].waiting_time, 11); // 22 - 11
    EXPECT_EQ(result.process_results[1].response_time, 2); // 2 - 0
}

// 5. Preemption by a newly arrived higher-priority process
TEST(OScopeMLFQTest, PreemptsLowerQueueWhenNewProcessArrives) {
    oscope::MLFQ mlfq(2, 6, 12);

    // P1: arrives 0, burst 8
    // P2: arrives 3, burst 2
    // t=0..2: P1 in Q0 (rem 6) -> demoted to Q1 (allotment 6)
    // t=2..3: P1 in Q1 (rem 5). At t=3, P2 arrives in Q0 -> preemption!
    //         P1 returns to front of Q1 with remaining allotment 5
    // t=3..5: P2 in Q0 (rem 0) -> completes at 5
    // t=5..10: P1 resumes in Q1 with remaining allotment 5 (rem 0) -> completes at 10
    const std::vector<oscope::Process> processes{
        {1, 0, 8, 0},
        {2, 3, 2, 0}
    };

    auto result = mlfq.schedule(processes);

    ASSERT_EQ(result.timeline.size(), 4);
    ASSERT_EQ(result.process_results.size(), 2);

    EXPECT_EQ(result.timeline[0].pid, 1);
    EXPECT_EQ(result.timeline[0].start_time, 0);
    EXPECT_EQ(result.timeline[0].end_time, 2);

    EXPECT_EQ(result.timeline[1].pid, 1);
    EXPECT_EQ(result.timeline[1].start_time, 2);
    EXPECT_EQ(result.timeline[1].end_time, 3);

    EXPECT_EQ(result.timeline[2].pid, 2);
    EXPECT_EQ(result.timeline[2].start_time, 3);
    EXPECT_EQ(result.timeline[2].end_time, 5);

    EXPECT_EQ(result.timeline[3].pid, 1);
    EXPECT_EQ(result.timeline[3].start_time, 5);
    EXPECT_EQ(result.timeline[3].end_time, 10);

    EXPECT_EQ(result.process_results[0].pid, 2);
    EXPECT_EQ(result.process_results[0].completion_time, 5);
    EXPECT_EQ(result.process_results[0].turnaround_time, 2); // 5 - 3
    EXPECT_EQ(result.process_results[0].waiting_time, 0);
    EXPECT_EQ(result.process_results[0].response_time, 0);

    EXPECT_EQ(result.process_results[1].pid, 1);
    EXPECT_EQ(result.process_results[1].completion_time, 10);
    EXPECT_EQ(result.process_results[1].turnaround_time, 10); // 10 - 0
    EXPECT_EQ(result.process_results[1].waiting_time, 2);     // 10 - 8
    EXPECT_EQ(result.process_results[1].response_time, 0);
}

// 6. Preserving remaining quantum after preemption with demotion after full consumption
TEST(OScopeMLFQTest, PreservesRemainingQuantumAfterPreemption) {
    oscope::MLFQ mlfq(2, 4, 8);

    // P1: arrives 0, burst 8
    // P2: arrives 3, burst 1
    // t=0..2: P1 in Q0 (rem 6) -> demoted to Q1 (allotment 4)
    // t=2..3: P1 in Q1 (rem 5). At t=3, P2 arrives in Q0 -> preemption!
    //         P1 returns to front of Q1 with remaining allotment 3
    // t=3..4: P2 in Q0 (rem 0) -> completes at 4
    // t=4..7: P1 resumes in Q1 with remaining allotment 3 (runs 3 units, rem burst 2).
    //         Full quantum of 4 consumed in Q1 (1 + 3 = 4) -> demoted to Q2!
    // t=7..9: P1 runs in Q2 (rem 0) -> completes at 9
    const std::vector<oscope::Process> processes{
        {1, 0, 8, 0},
        {2, 3, 1, 0}
    };

    auto result = mlfq.schedule(processes);

    ASSERT_EQ(result.timeline.size(), 5);
    ASSERT_EQ(result.process_results.size(), 2);

    EXPECT_EQ(result.timeline[0].pid, 1);
    EXPECT_EQ(result.timeline[0].start_time, 0);
    EXPECT_EQ(result.timeline[0].end_time, 2);

    EXPECT_EQ(result.timeline[1].pid, 1);
    EXPECT_EQ(result.timeline[1].start_time, 2);
    EXPECT_EQ(result.timeline[1].end_time, 3);

    EXPECT_EQ(result.timeline[2].pid, 2);
    EXPECT_EQ(result.timeline[2].start_time, 3);
    EXPECT_EQ(result.timeline[2].end_time, 4);

    EXPECT_EQ(result.timeline[3].pid, 1);
    EXPECT_EQ(result.timeline[3].start_time, 4);
    EXPECT_EQ(result.timeline[3].end_time, 7);

    EXPECT_EQ(result.timeline[4].pid, 1);
    EXPECT_EQ(result.timeline[4].start_time, 7);
    EXPECT_EQ(result.timeline[4].end_time, 9);

    EXPECT_EQ(result.process_results[0].pid, 2);
    EXPECT_EQ(result.process_results[0].completion_time, 4);
    EXPECT_EQ(result.process_results[0].turnaround_time, 1);
    EXPECT_EQ(result.process_results[0].waiting_time, 0);
    EXPECT_EQ(result.process_results[0].response_time, 0);

    EXPECT_EQ(result.process_results[1].pid, 1);
    EXPECT_EQ(result.process_results[1].completion_time, 9);
    EXPECT_EQ(result.process_results[1].turnaround_time, 9);
    EXPECT_EQ(result.process_results[1].waiting_time, 1);
    EXPECT_EQ(result.process_results[1].response_time, 0);
}

// 7. Same-time arrival ordering
TEST(OScopeMLFQTest, SameTimeArrivalPreservesOriginalInputOrder) {
    oscope::MLFQ mlfq(3, 6, 12);

    const std::vector<oscope::Process> processes{
        {1, 0, 3, 0},
        {2, 0, 3, 0},
        {3, 0, 3, 0}
    };

    auto result = mlfq.schedule(processes);

    ASSERT_EQ(result.timeline.size(), 3);
    EXPECT_EQ(result.timeline[0].pid, 1);
    EXPECT_EQ(result.timeline[0].start_time, 0);
    EXPECT_EQ(result.timeline[0].end_time, 3);

    EXPECT_EQ(result.timeline[1].pid, 2);
    EXPECT_EQ(result.timeline[1].start_time, 3);
    EXPECT_EQ(result.timeline[1].end_time, 6);

    EXPECT_EQ(result.timeline[2].pid, 3);
    EXPECT_EQ(result.timeline[2].start_time, 6);
    EXPECT_EQ(result.timeline[2].end_time, 9);
}

// 8. Completion exactly at quantum expiration
TEST(OScopeMLFQTest, CompletionExactlyAtQuantumExpiration) {
    oscope::MLFQ mlfq(4, 8, 16);

    const std::vector<oscope::Process> processes{
        {1, 0, 4, 0}
    };

    auto result = mlfq.schedule(processes);

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

// 9. Invalid quantum values
TEST(OScopeMLFQTest, ConstructorRejectsInvalidQuanta) {
    EXPECT_THROW(oscope::MLFQ(0, 4, 8), std::invalid_argument);
    EXPECT_THROW(oscope::MLFQ(4, 0, 8), std::invalid_argument);
    EXPECT_THROW(oscope::MLFQ(4, 8, 0), std::invalid_argument);

    EXPECT_THROW(oscope::MLFQ(-1, 4, 8), std::invalid_argument);
    EXPECT_THROW(oscope::MLFQ(4, -2, 8), std::invalid_argument);
    EXPECT_THROW(oscope::MLFQ(4, 8, -3), std::invalid_argument);
}

// 10. Correct completion, turnaround, waiting, and response times
TEST(OScopeMLFQTest, CalculatesAllMetricsCorrectly) {
    oscope::MLFQ mlfq(2, 4, 8);

    // Multi-process trace:
    // P1: arr 0, burst 6
    // P2: arr 1, burst 3
    // P3: arr 5, burst 2
    //
    // t=0..2: P1 in Q0 (rem 4). P2 arrives at 1. P1 demoted to Q1 at t=2.
    // t=2..4: P2 in Q0 (rem 1). P2 demoted to Q1 at t=4. Q1=[P1, P2].
    // t=4..5: P1 in Q1 (allotment 4, runs 1 unit, rem burst 3, rem allotment 3).
    //         At t=5, P3 arrives in Q0 -> P1 preempted! Q0=[P3], Q1=[P1, P2].
    // t=5..7: P3 in Q0 (rem 0) -> completes at 7.
    // t=7..10: P1 in Q1 (uses remaining allotment 3, rem 0) -> completes at 10.
    // t=10..11: P2 in Q1 (rem 0) -> completes at 11.
    const std::vector<oscope::Process> processes{
        {1, 0, 6, 0},
        {2, 1, 3, 0},
        {3, 5, 2, 0}
    };

    auto result = mlfq.schedule(processes);

    ASSERT_EQ(result.timeline.size(), 6);
    ASSERT_EQ(result.process_results.size(), 3);

    // Timeline segments
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
    EXPECT_EQ(result.timeline[3].end_time, 7);

    EXPECT_EQ(result.timeline[4].pid, 1);
    EXPECT_EQ(result.timeline[4].start_time, 7);
    EXPECT_EQ(result.timeline[4].end_time, 10);

    EXPECT_EQ(result.timeline[5].pid, 2);
    EXPECT_EQ(result.timeline[5].start_time, 10);
    EXPECT_EQ(result.timeline[5].end_time, 11);

    // Metrics for P3 (completed at 7)
    EXPECT_EQ(result.process_results[0].pid, 3);
    EXPECT_EQ(result.process_results[0].completion_time, 7);
    EXPECT_EQ(result.process_results[0].turnaround_time, 2);  // 7 - 5
    EXPECT_EQ(result.process_results[0].waiting_time, 0);     // 2 - 2
    EXPECT_EQ(result.process_results[0].response_time, 0);    // 5 - 5

    // Metrics for P1 (completed at 10)
    EXPECT_EQ(result.process_results[1].pid, 1);
    EXPECT_EQ(result.process_results[1].completion_time, 10);
    EXPECT_EQ(result.process_results[1].turnaround_time, 10); // 10 - 0
    EXPECT_EQ(result.process_results[1].waiting_time, 4);     // 10 - 6
    EXPECT_EQ(result.process_results[1].response_time, 0);    // 0 - 0

    // Metrics for P2 (completed at 11)
    EXPECT_EQ(result.process_results[2].pid, 2);
    EXPECT_EQ(result.process_results[2].completion_time, 11);
    EXPECT_EQ(result.process_results[2].turnaround_time, 10); // 11 - 1
    EXPECT_EQ(result.process_results[2].waiting_time, 7);     // 10 - 3
    EXPECT_EQ(result.process_results[2].response_time, 1);    // 2 - 1
}

// 11. CPU idle time before first arrival and between workloads
TEST(OScopeMLFQTest, HandlesIdleTimeBeforeFirstArrivalAndBetweenWorkloads) {
    oscope::MLFQ mlfq(2, 4, 8);

    // Idle 0..3: P1 arrives at 3, burst 3 -> runs 3..5 in Q0 (rem 1), 5..6 in Q1 (completes at 6)
    // Idle 6..10: P2 arrives at 10, burst 2 -> runs 10..12 in Q0 (completes at 12)
    const std::vector<oscope::Process> processes{
        {1, 3, 3, 0},
        {2, 10, 2, 0}
    };

    auto result = mlfq.schedule(processes);

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

// 12. Input vector preservation
TEST(OScopeMLFQTest, PreservesCallerInputVector) {
    oscope::MLFQ mlfq(2, 4, 8);

    std::vector<oscope::Process> processes{
        {2, 3, 4, 1},
        {1, 0, 5, 2},
        {3, 1, 2, 0}
    };

    const std::vector<oscope::Process> original_copy = processes;

    auto result = mlfq.schedule(processes);
    (void)result;

    ASSERT_EQ(processes.size(), original_copy.size());
    for (std::size_t i = 0; i < processes.size(); ++i) {
        EXPECT_EQ(processes[i].pid, original_copy[i].pid);
        EXPECT_EQ(processes[i].arrival_time, original_copy[i].arrival_time);
        EXPECT_EQ(processes[i].burst_time, original_copy[i].burst_time);
        EXPECT_EQ(processes[i].priority, original_copy[i].priority);
    }
}
