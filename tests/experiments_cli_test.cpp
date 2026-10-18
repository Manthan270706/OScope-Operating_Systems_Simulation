#include <gtest/gtest.h>

#include <sstream>
#include <string>

#include "oscope/cli.hpp"

namespace {

TEST(ExperimentsCLITest, EntersExperimentsMenuAndReturnsToMainMenu) {
    // 10 (Linux/POSIX Experiments), 5 (Return to Main Menu), 11 (Exit)
    std::istringstream in("10\n5\n11\n");
    std::ostringstream out;

    int exit_code = oscope::run_cli(in, out);

    EXPECT_EQ(exit_code, 0);
    const std::string s = out.str();
    EXPECT_NE(s.find("Linux/POSIX Experiments"), std::string::npos);
    EXPECT_NE(s.find("1. Process Creation"), std::string::npos);
    EXPECT_NE(s.find("2. Thread Creation"), std::string::npos);
    EXPECT_NE(s.find("3. Thread Synchronization"), std::string::npos);
    EXPECT_NE(s.find("4. Pipe-based IPC"), std::string::npos);
    EXPECT_NE(s.find("5. Return to Main Menu"), std::string::npos);
    EXPECT_NE(s.find("Exiting OScope. Goodbye!"), std::string::npos);
}

TEST(ExperimentsCLITest, RunsProcessCreationExperimentViaCLI) {
    // 10 (Experiments), 1 (Process Creation), 5 (Return), 11 (Exit)
    std::istringstream in("10\n1\n5\n11\n");
    std::ostringstream out;

    int exit_code = oscope::run_cli(in, out);

    EXPECT_EQ(exit_code, 0);
    const std::string s = out.str();
    EXPECT_NE(s.find("[Linux/POSIX Process Creation Experiment]"), std::string::npos);
    EXPECT_NE(s.find("=== Process Creation Experiment Result ==="), std::string::npos);
    EXPECT_NE(s.find("Status:                 SUCCESS"), std::string::npos);
    EXPECT_NE(s.find("Parent PID:"), std::string::npos);
    EXPECT_NE(s.find("Child PID:"), std::string::npos);
    EXPECT_NE(s.find("Normal exit (code 42)"), std::string::npos);
}

TEST(ExperimentsCLITest, RunsThreadCreationExperimentViaCLI) {
    // 10 (Experiments), 2 (Thread Creation), 5 (Return), 11 (Exit)
    std::istringstream in("10\n2\n5\n11\n");
    std::ostringstream out;

    int exit_code = oscope::run_cli(in, out);

    EXPECT_EQ(exit_code, 0);
    const std::string s = out.str();
    EXPECT_NE(s.find("[Linux/POSIX Thread Creation Experiment]"), std::string::npos);
    EXPECT_NE(s.find("=== Thread Creation Experiment Result ==="), std::string::npos);
    EXPECT_NE(s.find("Status:                 SUCCESS"), std::string::npos);
    EXPECT_NE(s.find("Requested Threads:      4"), std::string::npos);
    EXPECT_NE(s.find("Completed Threads:      4"), std::string::npos);
    EXPECT_NE(s.find("Worker Outputs:"), std::string::npos);
}

TEST(ExperimentsCLITest, RunsThreadSynchronizationExperimentViaCLI) {
    // 10 (Experiments), 3 (Thread Synchronization), 5 (Return), 11 (Exit)
    std::istringstream in("10\n3\n5\n11\n");
    std::ostringstream out;

    int exit_code = oscope::run_cli(in, out);

    EXPECT_EQ(exit_code, 0);
    const std::string s = out.str();
    EXPECT_NE(s.find("[Linux/POSIX Thread Synchronization Experiment]"), std::string::npos);
    EXPECT_NE(s.find("=== Thread Synchronization Experiment Result ==="), std::string::npos);
    EXPECT_NE(s.find("Status:                 SUCCESS"), std::string::npos);
    EXPECT_NE(s.find("Expected Counter:       40000"), std::string::npos);
    EXPECT_NE(s.find("Actual Counter:         40000"), std::string::npos);
    EXPECT_NE(s.find("PASSED (Counter exact match, no data race detected)"), std::string::npos);
}

TEST(ExperimentsCLITest, RunsPipeIpcExperimentViaCLI) {
    // 10 (Experiments), 4 (Pipe-based IPC), 5 (Return), 11 (Exit)
    std::istringstream in("10\n4\n5\n11\n");
    std::ostringstream out;

    int exit_code = oscope::run_cli(in, out);

    EXPECT_EQ(exit_code, 0);
    const std::string s = out.str();
    EXPECT_NE(s.find("[Linux/POSIX Pipe-based IPC Experiment]"), std::string::npos);
    EXPECT_NE(s.find("=== Pipe-based IPC Experiment Result ==="), std::string::npos);
    EXPECT_NE(s.find("Status:                 SUCCESS"), std::string::npos);
    EXPECT_NE(s.find("Direction:              Child -> Parent (POSIX pipe)"), std::string::npos);
    EXPECT_NE(s.find("Sent Message:           \"Hello from OScope child process via POSIX pipe!\""), std::string::npos);
    EXPECT_NE(s.find("Received Message:       \"Hello from OScope child process via POSIX pipe!\""), std::string::npos);
}

TEST(ExperimentsCLITest, RecoversFromInvalidSubmenuChoice) {
    // Choice: "bad", 0, 6, then 5 (Return), then 11 (Exit)
    std::istringstream in("10\nbad\n0\n6\n5\n11\n");
    std::ostringstream out;

    int exit_code = oscope::run_cli(in, out);

    EXPECT_EQ(exit_code, 0);
    const std::string s = out.str();
    EXPECT_NE(s.find("Error: Invalid numeric input."), std::string::npos);
    EXPECT_NE(s.find("Error: Choice must be between 1 and 5."), std::string::npos);
    EXPECT_NE(s.find("Exiting OScope. Goodbye!"), std::string::npos);
}

TEST(ExperimentsCLITest, HandlesEofAtExperimentsSubmenuPrompt) {
    // 10, then EOF immediately
    std::istringstream in("10\n");
    std::ostringstream out;

    int exit_code = oscope::run_cli(in, out);

    EXPECT_EQ(exit_code, 0);
    EXPECT_NE(out.str().find("End of input reached. Exiting OScope."), std::string::npos);
}

} // namespace
