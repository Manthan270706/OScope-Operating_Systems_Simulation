#include <gtest/gtest.h>

#include <sstream>
#include <string>

#include "oscope/cli.hpp"

// 1. Clean exit on selecting Option 7
TEST(OScopeCLITest, ExitOptionTerminatesCleanly) {
    std::istringstream in("7\n");
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
    // User enters "abc", then "xyz123", then "7" (Exit)
    std::istringstream in("abc\nxyz123\n7\n");
    std::ostringstream out;

    int exit_code = oscope::run_cli(in, out);

    EXPECT_EQ(exit_code, 0);
    EXPECT_NE(out.str().find("Error: Invalid numeric input."), std::string::npos);
    EXPECT_NE(out.str().find("Exiting OScope. Goodbye!"), std::string::npos);
}

// 4. Rejection of out-of-range menu choice
TEST(OScopeCLITest, RejectsOutOfRangeMenuChoice) {
    // User enters 0, then 8, then 7 (Exit)
    std::istringstream in("0\n8\n7\n");
    std::ostringstream out;

    int exit_code = oscope::run_cli(in, out);

    EXPECT_EQ(exit_code, 0);
    EXPECT_NE(out.str().find("Error: Choice must be between 1 and 7."), std::string::npos);
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
    // Then 7 (Exit)
    std::istringstream in("1\n2\n1\n0\n4\n0\n2\n1\n2\n0\n7\n");
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
    // Then 7 (Exit)
    std::istringstream in("5\n0\n-2\n3\n1\n1\n0\n7\n0\n7\n");
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
    // Then 7 (Exit)
    std::istringstream in("6\n0\n2\n4\n8\n1\n1\n0\n5\n0\n7\n");
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
    // Then 7 (Exit)
    std::istringstream in("4\n2\n1\n0\n4\n2\n2\n0\n2\n1\n7\n");
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
