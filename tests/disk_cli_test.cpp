#include <gtest/gtest.h>

#include <sstream>
#include <string>

#include "oscope/cli.hpp"

namespace {

TEST(DiskCLITest, EntersDiskMenuAndReturnsToMainMenu) {
    // 12 (Disk Scheduling), 8 (Return to Main Menu), 13 (Exit)
    std::istringstream in("12\n8\n13\n");
    std::ostringstream out;

    int exit_code = oscope::run_cli(in, out);

    EXPECT_EQ(exit_code, 0);
    const std::string s = out.str();
    EXPECT_NE(s.find("Disk Scheduling"), std::string::npos);
    EXPECT_NE(s.find("First-Come, First-Served (FCFS)"), std::string::npos);
    EXPECT_NE(s.find("Exiting OScope. Goodbye!"), std::string::npos);
}

TEST(DiskCLITest, RunsFCFSSchedulingViaCLI) {
    // 12 (Disk), 1 (FCFS), min 0, max 199, head 53, requests, 8 (Return), 13 (Exit)
    std::string input =
        "12\n"
        "1\n"
        "0\n"
        "199\n"
        "53\n"
        "98 183 37 122 14 124 65 67\n"
        "8\n"
        "13\n";

    std::istringstream in(input);
    std::ostringstream out;

    int exit_code = oscope::run_cli(in, out);

    EXPECT_EQ(exit_code, 0);
    const std::string s = out.str();
    EXPECT_NE(s.find("Disk Scheduling Result: First-Come, First-Served (FCFS)"), std::string::npos);
    EXPECT_NE(s.find("Total Head Movement:    640 cylinders"), std::string::npos);
}

TEST(DiskCLITest, RunsSCANSchedulingViaCLI) {
    // 12 (Disk), 3 (SCAN), min 0, max 199, head 53, dir 1 (Increasing), requests, 8, 13
    std::string input =
        "12\n"
        "3\n"
        "0\n"
        "199\n"
        "53\n"
        "1\n"
        "98 183 37 122 14 124 65 67\n"
        "8\n"
        "13\n";

    std::istringstream in(input);
    std::ostringstream out;

    int exit_code = oscope::run_cli(in, out);

    EXPECT_EQ(exit_code, 0);
    const std::string s = out.str();
    EXPECT_NE(s.find("SCAN (Elevator)"), std::string::npos);
    EXPECT_NE(s.find("Total Head Movement:    345 cylinders"), std::string::npos);
}

TEST(DiskCLITest, RunsCompareAllDiskAlgorithmsViaCLI) {
    // 12 (Disk), 7 (Compare All), min 0, max 199, head 53, dir 1 (Increasing), requests, 8, 13
    std::string input =
        "12\n"
        "7\n"
        "0\n"
        "199\n"
        "53\n"
        "1\n"
        "98 183 37 122 14 124 65 67\n"
        "8\n"
        "13\n";

    std::istringstream in(input);
    std::ostringstream out;

    int exit_code = oscope::run_cli(in, out);

    EXPECT_EQ(exit_code, 0);
    const std::string s = out.str();
    EXPECT_NE(s.find("Disk Scheduling Comparison"), std::string::npos);
    EXPECT_NE(s.find("C-SCAN"), std::string::npos);
    EXPECT_NE(s.find("C-LOOK"), std::string::npos);
    EXPECT_NE(s.find("640"), std::string::npos); // FCFS movement
    EXPECT_NE(s.find("236"), std::string::npos); // SSTF movement
}

TEST(DiskCLITest, RecoversFromInvalidSubmenuChoice) {
    // 12 (Disk), 0 (invalid), 99 (invalid), 8 (Return), 13 (Exit)
    std::istringstream in("12\n0\n99\n8\n13\n");
    std::ostringstream out;

    int exit_code = oscope::run_cli(in, out);

    EXPECT_EQ(exit_code, 0);
    const std::string s = out.str();
    EXPECT_NE(s.find("Error: Choice must be between 1 and 8."), std::string::npos);
}

TEST(DiskCLITest, HandlesEofAtDiskPrompt) {
    std::istringstream in("12\n"); // EOF after entering Disk menu
    std::ostringstream out;

    int exit_code = oscope::run_cli(in, out);

    EXPECT_EQ(exit_code, 0);
    EXPECT_NE(out.str().find("End of input reached. Exiting OScope."), std::string::npos);
}

TEST(DiskCLITest, RunsDiskViaCLIWithJsonFormat) {
    // In JSON mode: 12 (Disk), 1 (FCFS), min 0, max 199, head 53, requests, 8 (Return), 13 (Exit)
    std::string input =
        "12\n"
        "1\n"
        "0\n"
        "199\n"
        "53\n"
        "98 183 37 122 14 124 65 67\n"
        "8\n"
        "13\n";

    std::istringstream in(input);
    std::ostringstream out;

    int exit_code = oscope::run_cli(in, out, oscope::OutputFormat::Json);

    EXPECT_EQ(exit_code, 0);
    const std::string s = out.str();
    EXPECT_EQ(s.front(), '[');
    EXPECT_NE(s.find("\"category\": \"disk_scheduling\""), std::string::npos);
    EXPECT_NE(s.find("\"experiment\": \"disk_scheduling\""), std::string::npos);
    EXPECT_NE(s.find("\"total_head_movement\": 640"), std::string::npos);
}

} // namespace
