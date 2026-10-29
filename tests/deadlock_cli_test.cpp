#include <gtest/gtest.h>

#include <sstream>
#include <string>

#include "oscope/cli.hpp"

namespace {

TEST(DeadlockCLITest, EntersDeadlockMenuAndReturnsToMainMenu) {
    // 11 (Deadlock Management), 4 (Return to Main Menu), 13 (Exit)
    std::istringstream in("11\n4\n13\n");
    std::ostringstream out;

    int exit_code = oscope::run_cli(in, out);

    EXPECT_EQ(exit_code, 0);
    const std::string s = out.str();
    EXPECT_NE(s.find("Deadlock Management"), std::string::npos);
    EXPECT_NE(s.find("Banker's Safety Algorithm"), std::string::npos);
    EXPECT_NE(s.find("Exiting OScope. Goodbye!"), std::string::npos);
}

TEST(DeadlockCLITest, RunsSafetyAnalysisViaCLI) {
    // 11 (Deadlock)
    // 1 (Safety Analysis)
    // 3 processes, 2 resources
    // Available: 1 1
    // Allocation:
    // P0: 1 0
    // P1: 0 1
    // P2: 1 1
    // Max:
    // P0: 2 1
    // P1: 1 1
    // P2: 1 2
    // 4 (Return), 13 (Exit)
    std::string input =
        "11\n"
        "1\n"
        "3\n"
        "2\n"
        "1 1\n"
        "1 0\n"
        "0 1\n"
        "1 1\n"
        "2 1\n"
        "1 1\n"
        "1 2\n"
        "4\n"
        "13\n";

    std::istringstream in(input);
    std::ostringstream out;

    int exit_code = oscope::run_cli(in, out);

    EXPECT_EQ(exit_code, 0);
    const std::string s = out.str();
    EXPECT_NE(s.find("Banker's Safety Analysis"), std::string::npos);
    EXPECT_NE(s.find("SAFE"), std::string::npos);
    EXPECT_NE(s.find("Safe Execution Sequence:"), std::string::npos);
}

TEST(DeadlockCLITest, RunsResourceRequestViaCLI) {
    // 11 (Deadlock)
    // 2 (Resource Request)
    // 3 processes, 2 resources
    // Available: 2 2
    // Allocation: {1 0}, {0 1}, {1 1}
    // Max: {2 1}, {1 1}, {1 2}
    // Requesting process: 0
    // Requested resources: 1 0
    // 4 (Return), 13 (Exit)
    std::string input =
        "11\n"
        "2\n"
        "3\n"
        "2\n"
        "2 2\n"
        "1 0\n"
        "0 1\n"
        "1 1\n"
        "2 1\n"
        "1 1\n"
        "1 2\n"
        "0\n"
        "1 0\n"
        "4\n"
        "13\n";

    std::istringstream in(input);
    std::ostringstream out;

    int exit_code = oscope::run_cli(in, out);

    EXPECT_EQ(exit_code, 0);
    const std::string s = out.str();
    EXPECT_NE(s.find("Resource Request Simulation"), std::string::npos);
    EXPECT_NE(s.find("GRANTED"), std::string::npos);
}

TEST(DeadlockCLITest, RunsDeadlockDetectionViaCLI) {
    // 11 (Deadlock)
    // 3 (Detection)
    // 2 processes, 1 resource
    // Available: 0
    // Allocation: {1}, {1}
    // Request: {1}, {1}
    // 4 (Return), 13 (Exit)
    std::string input =
        "11\n"
        "3\n"
        "2\n"
        "1\n"
        "0\n"
        "1\n"
        "1\n"
        "1\n"
        "1\n"
        "4\n"
        "13\n";

    std::istringstream in(input);
    std::ostringstream out;

    int exit_code = oscope::run_cli(in, out);

    EXPECT_EQ(exit_code, 0);
    const std::string s = out.str();
    EXPECT_NE(s.find("Deadlock Detection Analysis"), std::string::npos);
    EXPECT_NE(s.find("DEADLOCK DETECTED"), std::string::npos);
}

TEST(DeadlockCLITest, RecoversFromInvalidSubmenuChoice) {
    // 11 (Deadlock), 0 (invalid), 99 (invalid), 4 (Return), 13 (Exit)
    std::istringstream in("11\n0\n99\n4\n13\n");
    std::ostringstream out;

    int exit_code = oscope::run_cli(in, out);

    EXPECT_EQ(exit_code, 0);
    const std::string s = out.str();
    EXPECT_NE(s.find("Error: Choice must be between 1 and 4."), std::string::npos);
}

TEST(DeadlockCLITest, HandlesEofAtDeadlockPrompt) {
    std::istringstream in("11\n"); // EOF after entering Deadlock menu
    std::ostringstream out;

    int exit_code = oscope::run_cli(in, out);

    EXPECT_EQ(exit_code, 0);
    EXPECT_NE(out.str().find("End of input reached. Exiting OScope."), std::string::npos);
}

TEST(DeadlockCLITest, RunsDeadlockViaCLIWithJsonFormat) {
    // In JSON mode: 11 (Deadlock), 1 (Safety), ... 4 (Return), 13 (Exit)
    std::string input =
        "11\n"
        "1\n"
        "3\n"
        "2\n"
        "1 1\n"
        "1 0\n"
        "0 1\n"
        "1 1\n"
        "2 1\n"
        "1 1\n"
        "1 2\n"
        "4\n"
        "13\n";

    std::istringstream in(input);
    std::ostringstream out;

    int exit_code = oscope::run_cli(in, out, oscope::OutputFormat::Json);

    EXPECT_EQ(exit_code, 0);
    const std::string s = out.str();
    EXPECT_EQ(s.front(), '[');
    EXPECT_NE(s.find("\"category\": \"deadlock_management\""), std::string::npos);
    EXPECT_NE(s.find("\"experiment\": \"bankers_safety\""), std::string::npos);
    EXPECT_NE(s.find("\"status\": \"success\""), std::string::npos);
}

} // namespace
