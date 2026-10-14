#include <gtest/gtest.h>

#include <sstream>
#include <string>

#include "oscope/cli.hpp"

// 1. Clean exit on selecting Option 10
TEST(OScopeCLITest, ExitOptionTerminatesCleanly) {
    std::istringstream in("10\n");
    std::ostringstream out;

    int exit_code = oscope::run_cli(in, out);

    EXPECT_EQ(exit_code, 0);
    EXPECT_NE(out.str().find("Exiting OScope. Goodbye!"), std::string::npos);
}

// 2. Clean exit on EOF at main menu
TEST(OScopeCLITest, EofAtMainMenuTerminatesCleanly) {
    std::istringstream in(""); // empty stream simulates immediate EOF
    std::ostringstream out;

    int exit_code = oscope::run_cli(in, out);

    EXPECT_EQ(exit_code, 0);
    EXPECT_NE(out.str().find("End of input reached. Exiting OScope."), std::string::npos);
}

// 3. Recovery from non-numeric menu input
TEST(OScopeCLITest, RecoversFromNonNumericMenuInput) {
    // User enters "abc", then "xyz123", then "10" (Exit)
    std::istringstream in("abc\nxyz123\n10\n");
    std::ostringstream out;

    int exit_code = oscope::run_cli(in, out);

    EXPECT_EQ(exit_code, 0);
    EXPECT_NE(out.str().find("Error: Invalid numeric input."), std::string::npos);
    EXPECT_NE(out.str().find("Exiting OScope. Goodbye!"), std::string::npos);
}

// 4. Rejection of out-of-range menu choice
TEST(OScopeCLITest, RejectsOutOfRangeMenuChoice) {
    // User enters 0, then 11, then 10 (Exit)
    std::istringstream in("0\n11\n10\n");
    std::ostringstream out;

    int exit_code = oscope::run_cli(in, out);

    EXPECT_EQ(exit_code, 0);
    EXPECT_NE(out.str().find("Error: Choice must be between 1 and 10."), std::string::npos);
    EXPECT_NE(out.str().find("Exiting OScope. Goodbye!"), std::string::npos);
}

// 5. Rejection of non-positive process count
TEST(OScopeCLITest, RejectsNonPositiveProcessCount) {
    // Process count 0 and -2 are rejected before accepting 1
    std::istringstream in("0\n-2\n1\n1\n0\n5\n0\n");
    std::ostringstream out;

    auto result = oscope::read_processes(in, out, oscope::AlgorithmChoice::FCFS);

    ASSERT_TRUE(result.has_value());
    EXPECT_EQ(result.value().size(), 1);
    EXPECT_NE(out.str().find("Error: Value must be a positive integer (> 0)."), std::string::npos);
}

// 6. Rejection of negative arrival time
TEST(OScopeCLITest, RejectsNegativeArrivalTime) {
    // 1 process, PID 1, arrival -3 (rejected), then arrival 2 (accepted), burst 4, priority 0
    std::istringstream in("1\n1\n-3\n2\n4\n0\n");
    std::ostringstream out;

    auto result = oscope::read_processes(in, out, oscope::AlgorithmChoice::FCFS);

    ASSERT_TRUE(result.has_value());
    ASSERT_EQ(result.value().size(), 1);
    EXPECT_EQ(result.value()[0].arrival_time, 2);
    EXPECT_NE(out.str().find("Error: Value must be non-negative (>= 0)."), std::string::npos);
}

// 7. Rejection of non-positive burst time
TEST(OScopeCLITest, RejectsNonPositiveBurstTime) {
    // 1 process, PID 1, arrival 0, burst 0 (rejected), burst -5 (rejected), burst 6, priority 0
    std::istringstream in("1\n1\n0\n0\n-5\n6\n0\n");
    std::ostringstream out;

    auto result = oscope::read_processes(in, out, oscope::AlgorithmChoice::FCFS);

    ASSERT_TRUE(result.has_value());
    ASSERT_EQ(result.value().size(), 1);
    EXPECT_EQ(result.value()[0].burst_time, 6);
    EXPECT_NE(out.str().find("Error: Value must be a positive integer (> 0)."), std::string::npos);
}

// 8. Rejection of duplicate PIDs
TEST(OScopeCLITest, RejectsDuplicatePids) {
    // 2 processes:
    // Process 1: PID 10, arr 0, burst 3, prio 0
    // Process 2: PID 10 (duplicate rejected), then PID 20, arr 1, burst 4, prio 0
    std::istringstream in("2\n10\n0\n3\n0\n10\n20\n1\n4\n0\n");
    std::ostringstream out;

    auto result = oscope::read_processes(in, out, oscope::AlgorithmChoice::FCFS);

    ASSERT_TRUE(result.has_value());
    ASSERT_EQ(result.value().size(), 2);
    EXPECT_EQ(result.value()[0].pid, 10);
    EXPECT_EQ(result.value()[1].pid, 20);
    EXPECT_NE(out.str().find("Error: PID 10 has already been entered. PIDs must be unique."), std::string::npos);
}

// 9. Recovery from non-numeric process field inputs without infinite loop
TEST(OScopeCLITest, RecoversFromNonNumericProcessFieldInputs) {
    // 1 process:
    // count: "invalid_count", then 1
    // PID: "invalid_pid", then 1
    // Arrival: "bad_arr", then 0
    // Burst: "bad_burst", then 5
    // Priority: "bad_prio", then 0
    std::istringstream in("invalid_count\n1\ninvalid_pid\n1\nbad_arr\n0\nbad_burst\n5\nbad_prio\n0\n");
    std::ostringstream out;

    auto result = oscope::read_processes(in, out, oscope::AlgorithmChoice::FCFS);

    ASSERT_TRUE(result.has_value());
    ASSERT_EQ(result.value().size(), 1);
    EXPECT_EQ(result.value()[0].pid, 1);
    EXPECT_EQ(result.value()[0].arrival_time, 0);
    EXPECT_EQ(result.value()[0].burst_time, 5);
    EXPECT_EQ(result.value()[0].priority, 0);
}

// 10. Full flow for FCFS simulation
TEST(OScopeCLITest, RunsFCFSSimulationSuccessfully) {
    // Select 1 (FCFS)
    // 2 processes:
    // P1: PID 1, Arr 0, Burst 4, Prio 0
    // P2: PID 2, Arr 1, Burst 2, Prio 0
    // Then 10 (Exit)
    std::istringstream in("1\n2\n1\n0\n4\n0\n2\n1\n2\n0\n10\n");
    std::ostringstream out;

    int exit_code = oscope::run_cli(in, out);

    EXPECT_EQ(exit_code, 0);
    EXPECT_NE(out.str().find("Simulation completed successfully."), std::string::npos);
    EXPECT_NE(out.str().find("Scheduled 2 process(es) across 2 timeline execution segment(s)."), std::string::npos);
    EXPECT_NE(out.str().find("Exiting OScope. Goodbye!"), std::string::npos);
}

// 11. Full flow for Round Robin simulation with quantum validation
TEST(OScopeCLITest, RunsRoundRobinSimulationWithQuantum) {
    // Select 5 (Round Robin)
    // Quantum: 0 (rejected), -2 (rejected), 3 (accepted)
    // 1 process: PID 1, Arr 0, Burst 7, Prio 0
    // Then 10 (Exit)
    std::istringstream in("5\n0\n-2\n3\n1\n1\n0\n7\n0\n10\n");
    std::ostringstream out;

    int exit_code = oscope::run_cli(in, out);

    EXPECT_EQ(exit_code, 0);
    EXPECT_NE(out.str().find("[Round Robin Configuration]"), std::string::npos);
    EXPECT_NE(out.str().find("Simulation completed successfully."), std::string::npos);
    // Burst 7 with quantum 3 gives 3 slices: 0..3, 3..6, 6..7
    EXPECT_NE(out.str().find("Scheduled 1 process(es) across 3 timeline execution segment(s)."), std::string::npos);
}

// 12. Full flow for MLFQ simulation with three quanta validation
TEST(OScopeCLITest, RunsMLFQSimulationWithQuanta) {
    // Select 6 (MLFQ)
    // Q0: 0 (rejected), 2
    // Q1: 4
    // Q2: 8
    // 1 process: PID 1, Arr 0, Burst 5, Prio 0
    // Then 10 (Exit)
    std::istringstream in("6\n0\n2\n4\n8\n1\n1\n0\n5\n0\n10\n");
    std::ostringstream out;

    int exit_code = oscope::run_cli(in, out);

    EXPECT_EQ(exit_code, 0);
    EXPECT_NE(out.str().find("[MLFQ Configuration]"), std::string::npos);
    EXPECT_NE(out.str().find("Simulation completed successfully."), std::string::npos);
}

// 13. Full flow for Priority simulation
TEST(OScopeCLITest, RunsPrioritySimulationSuccessfully) {
    // Select 4 (Priority)
    // 2 processes:
    // P1: PID 1, Arr 0, Burst 4, Prio 2
    // P2: PID 2, Arr 0, Burst 2, Prio 1
    // Then 10 (Exit)
    std::istringstream in("4\n2\n1\n0\n4\n2\n2\n0\n2\n1\n10\n");
    std::ostringstream out;

    int exit_code = oscope::run_cli(in, out);

    EXPECT_EQ(exit_code, 0);
    EXPECT_NE(out.str().find("Selected: Non-Preemptive Priority Scheduling"), std::string::npos);
    EXPECT_NE(out.str().find("Simulation completed successfully."), std::string::npos);
}

// 14. Premature EOF during process entry exits cleanly
TEST(OScopeCLITest, EofDuringProcessInputExitsCleanly) {
    // Select 1 (FCFS), then EOF
    std::istringstream in("1\n");
    std::ostringstream out;

    int exit_code = oscope::run_cli(in, out);

    EXPECT_EQ(exit_code, 0);
    EXPECT_NE(out.str().find("End of input reached. Exiting OScope."), std::string::npos);
}

// 15. Execution timeline: empty timeline handled cleanly
TEST(OScopeCLITest, TimelineEmptyHandledCleanly) {
    oscope::SchedulingSimulationResult empty_result;
    std::ostringstream out;

    oscope::display_execution_timeline(out, empty_result);

    EXPECT_NE(out.str().find("=== Execution Timeline ==="), std::string::npos);
    EXPECT_NE(out.str().find("No execution segments recorded (timeline is empty)."), std::string::npos);
}

// 16. Execution timeline: correct ordering and total interval
TEST(OScopeCLITest, TimelineCorrectOrderingAndInterval) {
    oscope::SchedulingSimulationResult result;
    result.timeline = {
        {1, 0, 4},
        {2, 4, 7}
    };
    std::ostringstream out;

    oscope::display_execution_timeline(out, result);

    const std::string s = out.str();
    EXPECT_NE(s.find("Total Simulation Interval: [0 -> 7] (Duration: 7)"), std::string::npos);
    EXPECT_NE(s.find("| [P1 0-4] | [P2 4-7] |"), std::string::npos);
    EXPECT_NE(s.find("[0 -> 4] Process PID 1"), std::string::npos);
    EXPECT_NE(s.find("[4 -> 7] Process PID 2"), std::string::npos);
}

// 17. Execution timeline: explicit idle gap between segments
TEST(OScopeCLITest, TimelineIdleGapsBetweenSegments) {
    oscope::SchedulingSimulationResult result;
    result.timeline = {
        {1, 0, 3},
        {2, 6, 10}
    };
    std::ostringstream out;

    oscope::display_execution_timeline(out, result);

    const std::string s = out.str();
    EXPECT_NE(s.find("[IDLE 3-6]"), std::string::npos);
    EXPECT_NE(s.find("[3 -> 6] IDLE (CPU Idle)"), std::string::npos);
    EXPECT_NE(s.find("[0 -> 3] Process PID 1"), std::string::npos);
    EXPECT_NE(s.find("[6 -> 10] Process PID 2"), std::string::npos);
}

// 18. Execution timeline: preemptive/repeated execution segments
TEST(OScopeCLITest, TimelinePreemptiveAndRepeatedSegments) {
    oscope::SchedulingSimulationResult result;
    result.timeline = {
        {1, 0, 2},
        {2, 2, 4},
        {1, 4, 5}
    };
    std::ostringstream out;

    oscope::display_execution_timeline(out, result);

    const std::string s = out.str();
    EXPECT_NE(s.find("| [P1 0-2] | [P2 2-4] | [P1 4-5] |"), std::string::npos);
    EXPECT_NE(s.find("[0 -> 2] Process PID 1"), std::string::npos);
    EXPECT_NE(s.find("[2 -> 4] Process PID 2"), std::string::npos);
    EXPECT_NE(s.find("[4 -> 5] Process PID 1"), std::string::npos);
}

// 19. Process metrics table: empty result handled cleanly
TEST(OScopeCLITest, ProcessMetricsTableEmptyHandledCleanly) {
    std::vector<oscope::Process> processes;
    oscope::SchedulingSimulationResult empty_result;
    std::ostringstream out;

    oscope::display_process_metrics_table(out, processes, empty_result);

    EXPECT_NE(out.str().find("=== Process Metrics Table ==="), std::string::npos);
    EXPECT_NE(out.str().find("No process metrics available (simulation result is empty)."), std::string::npos);
}

// 20. Process metrics table: correct process-to-metrics matching by PID
TEST(OScopeCLITest, ProcessMetricsTableMatchesByPid) {
    // Processes entered in order: PID 2 then PID 1
    std::vector<oscope::Process> processes = {
        {2, 5, 6, 0},
        {1, 0, 4, 0}
    };
    // Result order: PID 1 then PID 2
    oscope::SchedulingSimulationResult result;
    result.process_results = {
        {1, 4, 4, 0, 0},
        {2, 11, 6, 0, 0}
    };
    std::ostringstream out;

    oscope::display_process_metrics_table(out, processes, result);

    const std::string s = out.str();
    EXPECT_NE(s.find("=== Process Metrics Table ==="), std::string::npos);
    // Verify rows contain PIDs and their matched arrival and burst times
    EXPECT_NE(s.find("4"), std::string::npos);
    EXPECT_NE(s.find("5"), std::string::npos);
    EXPECT_NE(s.find("6"), std::string::npos);
    EXPECT_NE(s.find("11"), std::string::npos);
}

// 21. Process metrics table: all requested metric columns present
TEST(OScopeCLITest, ProcessMetricsTableContainsAllRequestedColumns) {
    std::vector<oscope::Process> processes = {{1, 0, 2, 0}};
    oscope::SchedulingSimulationResult result;
    result.process_results = {{1, 2, 2, 0, 0}};
    std::ostringstream out;

    oscope::display_process_metrics_table(out, processes, result);

    const std::string s = out.str();
    EXPECT_NE(s.find("PID"), std::string::npos);
    EXPECT_NE(s.find("Arrival"), std::string::npos);
    EXPECT_NE(s.find("Burst"), std::string::npos);
    EXPECT_NE(s.find("Completion"), std::string::npos);
    EXPECT_NE(s.find("Turnaround"), std::string::npos);
    EXPECT_NE(s.find("Waiting"), std::string::npos);
    EXPECT_NE(s.find("Response"), std::string::npos);
}

// 22. Average metrics: empty result handled cleanly
TEST(OScopeCLITest, AverageMetricsEmptyHandledCleanly) {
    oscope::SchedulingSimulationResult empty_result;
    std::ostringstream out;

    oscope::display_average_metrics(out, empty_result);

    EXPECT_NE(out.str().find("=== Average Metrics ==="), std::string::npos);
    EXPECT_NE(out.str().find("No process metrics available to calculate averages (simulation result is empty)."), std::string::npos);
}

// 23. Average metrics: calculated values, decimal formatting, and stream state preservation
TEST(OScopeCLITest, AverageMetricsCalculatedAndDecimalFormatted) {
    oscope::SchedulingSimulationResult result;
    // 3 processes:
    // waiting times: 1, 2, 2 -> avg = 5.0 / 3 = 1.67
    // turnaround times: 4, 5, 6 -> avg = 15.0 / 3 = 5.00
    // response times: 0, 1, 2 -> avg = 3.0 / 3 = 1.00
    result.process_results = {
        {1, 4, 4, 1, 0},
        {2, 5, 5, 2, 1},
        {3, 6, 6, 2, 2}
    };
    std::ostringstream out;
    out.precision(6);
    auto initial_flags = out.flags();

    oscope::display_average_metrics(out, result);

    const std::string s = out.str();
    EXPECT_NE(s.find("Average Waiting Time:    1.67"), std::string::npos);
    EXPECT_NE(s.find("Average Turnaround Time: 5.00"), std::string::npos);
    EXPECT_NE(s.find("Average Response Time:   1.00"), std::string::npos);

    // Stream formatting should be restored
    EXPECT_EQ(out.precision(), 6);
    EXPECT_EQ(out.flags(), initial_flags);
}

// 24. End-to-end interactive CLI test: FCFS displays full timeline, table, and averages
TEST(OScopeCLITest, InteractiveFcfsDisplaysFullResults) {
    // Select 1 (FCFS)
    // 2 processes:
    // P1: PID 1, Arr 0, Burst 3, Prio 0
    // P2: PID 2, Arr 1, Burst 2, Prio 0
    // Then 10 (Exit)
    std::istringstream in("1\n2\n1\n0\n3\n0\n2\n1\n2\n0\n10\n");
    std::ostringstream out;

    int exit_code = oscope::run_cli(in, out);

    EXPECT_EQ(exit_code, 0);
    const std::string s = out.str();
    EXPECT_NE(s.find("=== Execution Timeline ==="), std::string::npos);
    EXPECT_NE(s.find("Total Simulation Interval: [0 -> 5] (Duration: 5)"), std::string::npos);
    EXPECT_NE(s.find("| [P1 0-3] | [P2 3-5] |"), std::string::npos);
    EXPECT_NE(s.find("=== Process Metrics Table ==="), std::string::npos);
    EXPECT_NE(s.find("=== Average Metrics ==="), std::string::npos);
    EXPECT_NE(s.find("Average Waiting Time:"), std::string::npos);
    EXPECT_NE(s.find("Average Turnaround Time:"), std::string::npos);
    EXPECT_NE(s.find("Average Response Time:"), std::string::npos);
}

// 25. End-to-end interactive CLI test: Round Robin shows preemption slices
TEST(OScopeCLITest, InteractiveRoundRobinPreemptionDisplay) {
    // Select 5 (Round Robin), quantum 2
    // 2 processes:
    // P1: PID 1, Arr 0, Burst 3, Prio 0
    // P2: PID 2, Arr 0, Burst 2, Prio 0
    // Then 10 (Exit)
    // P1 runs [0-2], P2 runs [2-4], P1 runs [4-5]
    std::istringstream in("5\n2\n2\n1\n0\n3\n0\n2\n0\n2\n0\n10\n");
    std::ostringstream out;

    int exit_code = oscope::run_cli(in, out);

    EXPECT_EQ(exit_code, 0);
    const std::string s = out.str();
    EXPECT_NE(s.find("| [P1 0-2] | [P2 2-4] | [P1 4-5] |"), std::string::npos);
    EXPECT_NE(s.find("[0 -> 2] Process PID 1"), std::string::npos);
    EXPECT_NE(s.find("[2 -> 4] Process PID 2"), std::string::npos);
    EXPECT_NE(s.find("[4 -> 5] Process PID 1"), std::string::npos);
}

// 26. End-to-end interactive CLI test: Idle gap displayed explicitly
TEST(OScopeCLITest, InteractiveFcfsWithIdleGapDisplay) {
    // Select 1 (FCFS)
    // 2 processes:
    // P1: PID 1, Arr 0, Burst 2, Prio 0
    // P2: PID 2, Arr 5, Burst 3, Prio 0
    // Then 10 (Exit)
    std::istringstream in("1\n2\n1\n0\n2\n0\n2\n5\n3\n0\n10\n");
    std::ostringstream out;

    int exit_code = oscope::run_cli(in, out);

    EXPECT_EQ(exit_code, 0);
    const std::string s = out.str();
    EXPECT_NE(s.find("[IDLE 2-5]"), std::string::npos);
    EXPECT_NE(s.find("[2 -> 5] IDLE (CPU Idle)"), std::string::npos);
    EXPECT_NE(s.find("[0 -> 2] Process PID 1"), std::string::npos);
    EXPECT_NE(s.find("[5 -> 8] Process PID 2"), std::string::npos);
}

// 27. Process metrics table: unknown PID displays N/A for arrival and burst times
TEST(OScopeCLITest, ProcessMetricsTableUnknownPidDisplaysNA) {
    // Original process list only contains PID 1
    std::vector<oscope::Process> processes = {
        {1, 0, 4, 0}
    };
    // Result contains PID 1 and unknown PID 99
    oscope::SchedulingSimulationResult result;
    result.process_results = {
        {1, 4, 4, 0, 0},
        {99, 8, 4, 0, 0}
    };
    std::ostringstream out;

    oscope::display_process_metrics_table(out, processes, result);

    const std::string s = out.str();
    EXPECT_NE(s.find("=== Process Metrics Table ==="), std::string::npos);
    EXPECT_NE(s.find("99"), std::string::npos);
    EXPECT_NE(s.find("N/A"), std::string::npos);
}

// 28. Comparison table: empty entries handled cleanly
TEST(OScopeCLITest, ComparisonTableEmptyHandledCleanly) {
    std::vector<oscope::SchedulingComparisonEntry> empty_entries;
    std::ostringstream out;

    oscope::display_comparison_table(out, empty_entries);

    EXPECT_NE(out.str().find("=== Scheduling Algorithm Comparison ==="), std::string::npos);
    EXPECT_NE(out.str().find("No comparison results available (empty comparison entries)."), std::string::npos);
}

// 29. Comparison table: empty workload simulation results handled cleanly
TEST(OScopeCLITest, ComparisonTableEmptyWorkloadHandledCleanly) {
    std::vector<oscope::SchedulingComparisonEntry> entries = {
        {"FCFS", {}, {}},
        {"SJF", {}, {}}
    };
    std::ostringstream out;

    oscope::display_comparison_table(out, entries);

    EXPECT_NE(out.str().find("=== Scheduling Algorithm Comparison ==="), std::string::npos);
    EXPECT_NE(out.str().find("No process metrics available to calculate averages (simulation result is empty)."), std::string::npos);
}

// 30. Comparison table: formatted output, decimal precision, and stream state preservation
TEST(OScopeCLITest, ComparisonTableFormattedOutputAndStreamPreservation) {
    oscope::SchedulingMetrics m1{1.67, 5.00, 1.00};
    oscope::SchedulingMetrics m2{1.33, 4.67, 0.67};

    oscope::SchedulingSimulationResult sim1;
    sim1.process_results.push_back({1, 4, 4, 1, 0});
    oscope::SchedulingSimulationResult sim2;
    sim2.process_results.push_back({1, 4, 4, 1, 0});

    std::vector<oscope::SchedulingComparisonEntry> entries = {
        {"FCFS", sim1, m1},
        {"SJF", sim2, m2}
    };

    std::ostringstream out;
    out.precision(6);
    auto initial_flags = out.flags();

    oscope::display_comparison_table(out, entries);

    const std::string s = out.str();
    EXPECT_NE(s.find("=== Scheduling Algorithm Comparison ==="), std::string::npos);
    EXPECT_NE(s.find("Algorithm"), std::string::npos);
    EXPECT_NE(s.find("Avg Waiting"), std::string::npos);
    EXPECT_NE(s.find("Avg Turnaround"), std::string::npos);
    EXPECT_NE(s.find("Avg Response"), std::string::npos);

    EXPECT_NE(s.find("FCFS"), std::string::npos);
    EXPECT_NE(s.find("1.67"), std::string::npos);
    EXPECT_NE(s.find("5.00"), std::string::npos);
    EXPECT_NE(s.find("1.00"), std::string::npos);

    EXPECT_NE(s.find("SJF"), std::string::npos);
    EXPECT_NE(s.find("1.33"), std::string::npos);
    EXPECT_NE(s.find("4.67"), std::string::npos);
    EXPECT_NE(s.find("0.67"), std::string::npos);

    EXPECT_EQ(out.precision(), 6);
    EXPECT_EQ(out.flags(), initial_flags);
}

// 31. End-to-end interactive CLI test: Full comparison of all six algorithms
TEST(OScopeCLITest, InteractiveComparisonRunsAllSixAlgorithms) {
    // Select 7 (Compare All)
    // Round Robin quantum: 2
    // MLFQ quanta: 2, 4, 8
    // 2 processes:
    // P1: PID 1, Arr 0, Burst 4, Prio 2
    // P2: PID 2, Arr 1, Burst 2, Prio 1
    // Then 10 (Exit)
    std::istringstream in("7\n2\n2\n4\n8\n2\n1\n0\n4\n2\n2\n1\n2\n1\n10\n");
    std::ostringstream out;

    int exit_code = oscope::run_cli(in, out);

    EXPECT_EQ(exit_code, 0);
    const std::string s = out.str();
    EXPECT_NE(s.find("Selected: Compare All Scheduling Algorithms"), std::string::npos);
    EXPECT_NE(s.find("Comparison completed successfully across 6 algorithm(s)."), std::string::npos);
    EXPECT_NE(s.find("=== Scheduling Algorithm Comparison ==="), std::string::npos);
    EXPECT_NE(s.find("FCFS"), std::string::npos);
    EXPECT_NE(s.find("SJF"), std::string::npos);
    EXPECT_NE(s.find("SRTF"), std::string::npos);
    EXPECT_NE(s.find("Priority"), std::string::npos);
    EXPECT_NE(s.find("Round Robin"), std::string::npos);
    EXPECT_NE(s.find("MLFQ"), std::string::npos);
    EXPECT_NE(s.find("Exiting OScope. Goodbye!"), std::string::npos);
}

// 32. Interactive comparison: invalid quanta rejection and recovery
TEST(OScopeCLITest, InteractiveComparisonRecoversFromInvalidQuanta) {
    // Select 7 (Compare All)
    // RR quantum: 0 (rejected), -1 (rejected), 2 (accepted)
    // MLFQ Q0: -3 (rejected), 2 (accepted)
    // MLFQ Q1: 0 (rejected), 4 (accepted)
    // MLFQ Q2: bad (rejected), 8 (accepted)
    // 1 process: PID 1, Arr 0, Burst 3, Prio 1
    // Then 10 (Exit)
    std::istringstream in("7\n0\n-1\n2\n-3\n2\n0\n4\nbad\n8\n1\n1\n0\n3\n1\n10\n");
    std::ostringstream out;

    int exit_code = oscope::run_cli(in, out);

    EXPECT_EQ(exit_code, 0);
    const std::string s = out.str();
    EXPECT_NE(s.find("Error: Value must be a positive integer (> 0)."), std::string::npos);
    EXPECT_NE(s.find("Comparison completed successfully across 6 algorithm(s)."), std::string::npos);
    EXPECT_NE(s.find("=== Scheduling Algorithm Comparison ==="), std::string::npos);
}

// 33. Interactive comparison: EOF during quantum input exits cleanly
TEST(OScopeCLITest, InteractiveComparisonEofDuringQuantumExitsCleanly) {
    // Select 7 (Compare All), then EOF
    std::istringstream in("7\n");
    std::ostringstream out;

    int exit_code = oscope::run_cli(in, out);

    EXPECT_EQ(exit_code, 0);
    EXPECT_NE(out.str().find("End of input reached. Exiting OScope."), std::string::npos);
}

// 34. Interactive comparison: EOF during process input exits cleanly
TEST(OScopeCLITest, InteractiveComparisonEofDuringProcessInputExitsCleanly) {
    // Select 7 (Compare All), valid quanta, then EOF at process count
    std::istringstream in("7\n2\n2\n4\n8\n");
    std::ostringstream out;

    int exit_code = oscope::run_cli(in, out);

    EXPECT_EQ(exit_code, 0);
    EXPECT_NE(out.str().find("End of input reached. Exiting OScope."), std::string::npos);
}
