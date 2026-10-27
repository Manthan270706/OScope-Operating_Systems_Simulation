#include <gtest/gtest.h>

#include <sstream>
#include <string>
#include <vector>

#include "oscope/cli.hpp"
#include "oscope/paging/page_replacement_comparison.hpp"
#include "oscope/paging/page_replacement_result.hpp"

// 1. Navigation: Enter Paging menu and return cleanly to main menu
TEST(OScopePagingCLITest, EntersPagingMenuAndReturnsToMainMenu) {
    // 8 (Paging), 5 (Return to main menu), 13 (Exit)
    std::istringstream in("8\n5\n13\n");
    std::ostringstream out;

    int exit_code = oscope::run_cli(in, out);

    EXPECT_EQ(exit_code, 0);
    const std::string s = out.str();
    EXPECT_NE(s.find("Page Replacement"), std::string::npos);
    EXPECT_NE(s.find("1. Run FIFO"), std::string::npos);
    EXPECT_NE(s.find("2. Run LRU"), std::string::npos);
    EXPECT_NE(s.find("3. Run Optimal"), std::string::npos);
    EXPECT_NE(s.find("4. Compare FIFO, LRU, and Optimal"), std::string::npos);
    EXPECT_NE(s.find("5. Return to main menu"), std::string::npos);
    EXPECT_NE(s.find("Exiting OScope. Goodbye!"), std::string::npos);
}

// 2. Interactive FIFO page replacement simulation
TEST(OScopePagingCLITest, RunsFifoSimulationSuccessfully) {
    // 8 (Paging)
    // 1 (FIFO)
    // 3 (frames)
    // 7 0 1 2 0 3 0 4 2 3 0 3 2 1 2 0 1 7 0 1 (textbook string)
    // 5 (Return to main menu)
    // 13 (Exit)
    std::istringstream in("8\n1\n3\n7 0 1 2 0 3 0 4 2 3 0 3 2 1 2 0 1 7 0 1\n5\n13\n");
    std::ostringstream out;

    int exit_code = oscope::run_cli(in, out);

    EXPECT_EQ(exit_code, 0);
    const std::string s = out.str();
    EXPECT_NE(s.find("[FIFO Page Replacement Simulation]"), std::string::npos);
    EXPECT_NE(s.find("Simulation completed successfully with 20 reference(s) across 3 frame(s)."), std::string::npos);
    EXPECT_NE(s.find("=== Page Replacement Step-by-Step Execution ==="), std::string::npos);
    EXPECT_NE(s.find("Step"), std::string::npos);
    EXPECT_NE(s.find("Page"), std::string::npos);
    EXPECT_NE(s.find("Result"), std::string::npos);
    EXPECT_NE(s.find("Evicted"), std::string::npos);
    EXPECT_NE(s.find("Frames"), std::string::npos);

    // Initial step checking
    EXPECT_NE(s.find("Fault"), std::string::npos);
    EXPECT_NE(s.find("Hit"), std::string::npos);
    EXPECT_NE(s.find("[7, -1, -1]"), std::string::npos);

    // Aggregate metrics
    EXPECT_NE(s.find("=== Page Replacement Metrics ==="), std::string::npos);
    EXPECT_NE(s.find("Total Page References: 20"), std::string::npos);
    EXPECT_NE(s.find("Page Faults:           15"), std::string::npos);
    EXPECT_NE(s.find("Page Hits:             5"), std::string::npos);
    EXPECT_NE(s.find("Page-Fault Rate:       75.00%"), std::string::npos);
    EXPECT_NE(s.find("Page-Hit Rate:         25.00%"), std::string::npos);
}

// 3. Interactive LRU page replacement simulation
TEST(OScopePagingCLITest, RunsLruSimulationSuccessfully) {
    // 8 (Paging)
    // 2 (LRU)
    // 3 (frames)
    // 7 0 1 2 0 3 0 4 2 3 0 3 2 1 2 0 1 7 0 1
    // 5 (Return to main menu)
    // 13 (Exit)
    std::istringstream in("8\n2\n3\n7 0 1 2 0 3 0 4 2 3 0 3 2 1 2 0 1 7 0 1\n5\n13\n");
    std::ostringstream out;

    int exit_code = oscope::run_cli(in, out);

    EXPECT_EQ(exit_code, 0);
    const std::string s = out.str();
    EXPECT_NE(s.find("[LRU Page Replacement Simulation]"), std::string::npos);
    EXPECT_NE(s.find("Total Page References: 20"), std::string::npos);
    EXPECT_NE(s.find("Page Faults:           12"), std::string::npos);
    EXPECT_NE(s.find("Page Hits:             8"), std::string::npos);
    EXPECT_NE(s.find("Page-Fault Rate:       60.00%"), std::string::npos);
    EXPECT_NE(s.find("Page-Hit Rate:         40.00%"), std::string::npos);
}

// 4. Interactive Optimal page replacement simulation
TEST(OScopePagingCLITest, RunsOptimalSimulationSuccessfully) {
    // 8 (Paging)
    // 3 (Optimal)
    // 3 (frames)
    // 7 0 1 2 0 3 0 4 2 3 0 3 2 1 2 0 1 7 0 1
    // 5 (Return to main menu)
    // 13 (Exit)
    std::istringstream in("8\n3\n3\n7 0 1 2 0 3 0 4 2 3 0 3 2 1 2 0 1 7 0 1\n5\n13\n");
    std::ostringstream out;

    int exit_code = oscope::run_cli(in, out);

    EXPECT_EQ(exit_code, 0);
    const std::string s = out.str();
    EXPECT_NE(s.find("[Optimal Page Replacement Simulation]"), std::string::npos);
    EXPECT_NE(s.find("Total Page References: 20"), std::string::npos);
    EXPECT_NE(s.find("Page Faults:           9"), std::string::npos);
    EXPECT_NE(s.find("Page Hits:             11"), std::string::npos);
    EXPECT_NE(s.find("Page-Fault Rate:       45.00%"), std::string::npos);
    EXPECT_NE(s.find("Page-Hit Rate:         55.00%"), std::string::npos);
}

// 5. Interactive Page Replacement comparison
TEST(OScopePagingCLITest, RunsPageReplacementComparisonSuccessfully) {
    // 8 (Paging)
    // 4 (Compare FIFO, LRU, and Optimal)
    // 3 (frames)
    // 7 0 1 2 0 3 0 4 2 3 0 3 2 1 2 0 1 7 0 1
    // 5 (Return to main menu)
    // 13 (Exit)
    std::istringstream in("8\n4\n3\n7 0 1 2 0 3 0 4 2 3 0 3 2 1 2 0 1 7 0 1\n5\n13\n");
    std::ostringstream out;

    int exit_code = oscope::run_cli(in, out);

    EXPECT_EQ(exit_code, 0);
    const std::string s = out.str();
    EXPECT_NE(s.find("Comparison completed successfully across 3 page replacement algorithm(s)."), std::string::npos);
    EXPECT_NE(s.find("=== Page Replacement Algorithm Comparison ==="), std::string::npos);
    EXPECT_NE(s.find("Frame Count: 3 | Total References: 20"), std::string::npos);
    EXPECT_NE(s.find("FIFO"), std::string::npos);
    EXPECT_NE(s.find("LRU"), std::string::npos);
    EXPECT_NE(s.find("Optimal"), std::string::npos);
    EXPECT_NE(s.find("75.00%"), std::string::npos);
    EXPECT_NE(s.find("60.00%"), std::string::npos);
    EXPECT_NE(s.find("45.00%"), std::string::npos);
}

// 6. Handle empty reference string in interactive simulation
TEST(OScopePagingCLITest, HandlesEmptyReferenceString) {
    // 8 (Paging), 1 (FIFO), 3 (frames), empty line for reference string, 5, 13
    std::istringstream in("8\n1\n3\n\n5\n13\n");
    std::ostringstream out;

    int exit_code = oscope::run_cli(in, out);

    EXPECT_EQ(exit_code, 0);
    const std::string s = out.str();
    EXPECT_NE(s.find("No page references recorded (reference string is empty)."), std::string::npos);
    EXPECT_NE(s.find("Total Page References: 0"), std::string::npos);
    EXPECT_NE(s.find("Page Faults:           0"), std::string::npos);
    EXPECT_NE(s.find("Page Hits:             0"), std::string::npos);
}

// 7. Input validation: Rejection of nonpositive or invalid frame counts
TEST(OScopePagingCLITest, RejectsInvalidFrameCountsAndRecovers) {
    // 8 (Paging), 1 (FIFO)
    // Frame count: 0 (rejected), -2 (rejected), "bad" (rejected), 3 (accepted)
    // ref: 1 2 3
    // 5, 13
    std::istringstream in("8\n1\n0\n-2\nbad\n3\n1 2 3\n5\n13\n");
    std::ostringstream out;

    int exit_code = oscope::run_cli(in, out);

    EXPECT_EQ(exit_code, 0);
    const std::string s = out.str();
    EXPECT_NE(s.find("Error: Value must be a positive integer (> 0)."), std::string::npos);
    EXPECT_NE(s.find("Error: Invalid numeric input."), std::string::npos);
    EXPECT_NE(s.find("Simulation completed successfully with 3 reference(s) across 3 frame(s)."), std::string::npos);
}

// 8. Input validation: Rejection of negative page numbers
TEST(OScopePagingCLITest, RejectsNegativePageNumbersAndRecovers) {
    // 8 (Paging), 1 (FIFO), 2 (frames)
    // Ref: "1 -4 2" (rejected), then "1 4 2" (accepted)
    // 5, 13
    std::istringstream in("8\n1\n2\n1 -4 2\n1 4 2\n5\n13\n");
    std::ostringstream out;

    int exit_code = oscope::run_cli(in, out);

    EXPECT_EQ(exit_code, 0);
    const std::string s = out.str();
    EXPECT_NE(s.find("Error: Negative page number (-4) detected. Page numbers must be non-negative (>= 0)."), std::string::npos);
    EXPECT_NE(s.find("Simulation completed successfully with 3 reference(s) across 2 frame(s)."), std::string::npos);
}

// 9. Input validation: Rejection of malformed / non-numeric reference string tokens
TEST(OScopePagingCLITest, RejectsMalformedReferenceStringTokensAndRecovers) {
    // 8 (Paging), 1 (FIFO), 2 (frames)
    // Ref: "1 abc 2" (rejected), "1 2a 3" (rejected), then "1 2 3" (accepted)
    // 5, 13
    std::istringstream in("8\n1\n2\n1 abc 2\n1 2a 3\n1 2 3\n5\n13\n");
    std::ostringstream out;

    int exit_code = oscope::run_cli(in, out);

    EXPECT_EQ(exit_code, 0);
    const std::string s = out.str();
    EXPECT_NE(s.find("Error: Invalid numeric input in token 'abc'."), std::string::npos);
    EXPECT_NE(s.find("Error: Trailing non-numeric characters in token '2a'."), std::string::npos);
    EXPECT_NE(s.find("Simulation completed successfully with 3 reference(s) across 2 frame(s)."), std::string::npos);
}

// 10. Input validation: Out-of-range and invalid paging menu choices
TEST(OScopePagingCLITest, RejectsInvalidPagingMenuChoiceAndRecovers) {
    // 8 (Paging)
    // Choice: 0 (rejected), 6 (rejected), "xyz" (rejected), 5 (return)
    // 13 (Exit)
    std::istringstream in("8\n0\n6\nxyz\n5\n13\n");
    std::ostringstream out;

    int exit_code = oscope::run_cli(in, out);

    EXPECT_EQ(exit_code, 0);
    const std::string s = out.str();
    EXPECT_NE(s.find("Error: Choice must be between 1 and 5."), std::string::npos);
    EXPECT_NE(s.find("Error: Invalid numeric input."), std::string::npos);
    EXPECT_NE(s.find("Exiting OScope. Goodbye!"), std::string::npos);
}

// 11. Graceful EOF handling at paging menu prompt
TEST(OScopePagingCLITest, HandlesEofAtPagingMenuPrompt) {
    // 8 (Paging), then EOF immediately
    std::istringstream in("8\n");
    std::ostringstream out;

    int exit_code = oscope::run_cli(in, out);

    EXPECT_EQ(exit_code, 0);
    EXPECT_NE(out.str().find("End of input reached. Exiting OScope."), std::string::npos);
}

// 12. Graceful EOF handling during frame count input
TEST(OScopePagingCLITest, HandlesEofDuringFrameCountInput) {
    // 8 (Paging), 1 (FIFO), then EOF
    std::istringstream in("8\n1\n");
    std::ostringstream out;

    int exit_code = oscope::run_cli(in, out);

    EXPECT_EQ(exit_code, 0);
    EXPECT_NE(out.str().find("End of input reached. Exiting OScope."), std::string::npos);
}

// 13. Graceful EOF handling during reference string input
TEST(OScopePagingCLITest, HandlesEofDuringReferenceStringInput) {
    // 8 (Paging), 1 (FIFO), 3 (frames), then EOF without newline
    std::istringstream in("8\n1\n3");
    std::ostringstream out;

    int exit_code = oscope::run_cli(in, out);

    EXPECT_EQ(exit_code, 0);
    EXPECT_NE(out.str().find("End of input reached. Exiting OScope."), std::string::npos);
}

// 14. Unit testing for display_paging_steps
TEST(OScopePagingCLITest, DisplayPagingStepsFormattedProperly) {
    oscope::PageReplacementResult result;
    result.total_references = 3;
    result.page_faults = 2;
    result.page_hits = 1;

    oscope::PageReplacementStep s1;
    s1.page = 7;
    s1.is_fault = true;
    s1.evicted_page = std::nullopt;
    s1.frames = {7, -1, -1};

    oscope::PageReplacementStep s2;
    s2.page = 7;
    s2.is_fault = false;
    s2.evicted_page = std::nullopt;
    s2.frames = {7, -1, -1};

    oscope::PageReplacementStep s3;
    s3.page = 2;
    s3.is_fault = true;
    s3.evicted_page = 7;
    s3.frames = {2, -1, -1};

    result.steps = {s1, s2, s3};

    std::ostringstream out;
    oscope::display_paging_steps(out, result, 3);

    const std::string s = out.str();
    EXPECT_NE(s.find("=== Page Replacement Step-by-Step Execution ==="), std::string::npos);
    EXPECT_NE(s.find("Fault"), std::string::npos);
    EXPECT_NE(s.find("Hit"), std::string::npos);
    EXPECT_NE(s.find("None"), std::string::npos);
    EXPECT_NE(s.find("7"), std::string::npos);
    EXPECT_NE(s.find("[7, -1, -1]"), std::string::npos);
    EXPECT_NE(s.find("[2, -1, -1]"), std::string::npos);
}

// 15. Unit testing for display_paging_metrics formatting and stream preservation
TEST(OScopePagingCLITest, DisplayPagingMetricsPreservesStreamState) {
    oscope::PageReplacementResult result;
    result.total_references = 10;
    result.page_faults = 6;
    result.page_hits = 4;
    result.fault_rate = 0.6;
    result.hit_rate = 0.4;

    std::ostringstream out;
    out.precision(6);
    auto initial_flags = out.flags();

    oscope::display_paging_metrics(out, result);

    const std::string s = out.str();
    EXPECT_NE(s.find("=== Page Replacement Metrics ==="), std::string::npos);
    EXPECT_NE(s.find("Total Page References: 10"), std::string::npos);
    EXPECT_NE(s.find("Page Faults:           6"), std::string::npos);
    EXPECT_NE(s.find("Page Hits:             4"), std::string::npos);
    EXPECT_NE(s.find("Page-Fault Rate:       60.00% (0.60)"), std::string::npos);
    EXPECT_NE(s.find("Page-Hit Rate:         40.00% (0.40)"), std::string::npos);

    EXPECT_EQ(out.precision(), 6);
    EXPECT_EQ(out.flags(), initial_flags);
}

// 16. Unit testing for display_paging_comparison_table
TEST(OScopePagingCLITest, DisplayPagingComparisonTableFormattedProperly) {
    oscope::PageReplacementComparisonResult result;
    result.frame_count = 3;
    result.reference_string = {1, 2, 3};

    oscope::PageReplacementResult res_fifo;
    res_fifo.total_references = 3;
    res_fifo.page_faults = 3;
    res_fifo.page_hits = 0;
    res_fifo.fault_rate = 1.0;
    res_fifo.hit_rate = 0.0;

    oscope::PageReplacementResult res_opt;
    res_opt.total_references = 3;
    res_opt.page_faults = 3;
    res_opt.page_hits = 0;
    res_opt.fault_rate = 1.0;
    res_opt.hit_rate = 0.0;

    result.entries = {
        {"FIFO", res_fifo},
        {"Optimal", res_opt}
    };

    std::ostringstream out;
    out.precision(6);
    auto initial_flags = out.flags();

    oscope::display_paging_comparison_table(out, result);

    const std::string s = out.str();
    EXPECT_NE(s.find("=== Page Replacement Algorithm Comparison ==="), std::string::npos);
    EXPECT_NE(s.find("Frame Count: 3 | Total References: 3"), std::string::npos);
    EXPECT_NE(s.find("FIFO"), std::string::npos);
    EXPECT_NE(s.find("Optimal"), std::string::npos);
    EXPECT_NE(s.find("100.00%"), std::string::npos);

    EXPECT_EQ(out.precision(), 6);
    EXPECT_EQ(out.flags(), initial_flags);
}
