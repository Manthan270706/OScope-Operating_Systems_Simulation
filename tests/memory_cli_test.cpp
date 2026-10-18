#include <gtest/gtest.h>

#include <iomanip>
#include <sstream>
#include <string>
#include <vector>

#include "oscope/cli.hpp"
#include "oscope/memory/allocation_result.hpp"
#include "oscope/memory/allocation_strategy.hpp"
#include "oscope/memory/memory_block.hpp"
#include "oscope/memory/memory_comparison.hpp"

// 1. Navigation: Enter Memory Allocation menu and return cleanly to main menu
TEST(OScopeMemoryCLITest, EntersMemoryMenuAndReturnsToMainMenu) {
    // 9 (Memory Allocation), 5 (Return to main menu), 11 (Exit)
    std::istringstream in("9\n5\n11\n");
    std::ostringstream out;

    int exit_code = oscope::run_cli(in, out);

    EXPECT_EQ(exit_code, 0);
    const std::string s = out.str();
    EXPECT_NE(s.find("Memory Allocation"), std::string::npos);
    EXPECT_NE(s.find("1. First Fit"), std::string::npos);
    EXPECT_NE(s.find("2. Best Fit"), std::string::npos);
    EXPECT_NE(s.find("3. Worst Fit"), std::string::npos);
    EXPECT_NE(s.find("4. Compare all three strategies"), std::string::npos);
    EXPECT_NE(s.find("5. Return to main menu"), std::string::npos);
    EXPECT_NE(s.find("Exiting OScope. Goodbye!"), std::string::npos);
}

// 2. Individual strategy: Successful allocation and deallocation
TEST(OScopeMemoryCLITest, IndividualStrategySuccessfulAllocationAndDeallocation) {
    // 9 (Memory Allocation)
    // 1 (First Fit)
    // 1000 (total memory size in bytes)
    // 2 (number of operations)
    // Op 1: 1 (Allocate), Req ID 1, Size 200, PID 42
    // Op 2: 2 (Deallocate), Req ID 1
    // 5 (Return to main menu)
    // 11 (Exit)
    std::istringstream in("9\n1\n1000\n2\n1\n1\n200\n42\n2\n1\n5\n11\n");
    std::ostringstream out;

    int exit_code = oscope::run_cli(in, out);

    EXPECT_EQ(exit_code, 0);
    const std::string s = out.str();
    EXPECT_NE(s.find("[First Fit Memory Allocation]"), std::string::npos);
    EXPECT_NE(s.find("Allocation successful: Request ID 1 allocated at address 0 (200 bytes, Internal ID: 1)"), std::string::npos);
    EXPECT_NE(s.find("Deallocation successful: Request ID 1 (Internal ID: 1) freed."), std::string::npos);
    EXPECT_NE(s.find("=== Memory Block Layout ==="), std::string::npos);
    EXPECT_NE(s.find("=== Memory Allocation Metrics ==="), std::string::npos);
    EXPECT_NE(s.find("Total Memory:           1000 bytes"), std::string::npos);
    EXPECT_NE(s.find("Allocated Memory:       0 bytes"), std::string::npos);
    EXPECT_NE(s.find("Free Memory:            1000 bytes"), std::string::npos);
    EXPECT_NE(s.find("Largest Free Block:     1000 bytes"), std::string::npos);
    EXPECT_NE(s.find("External Fragmentation: 0.00% (0.00)"), std::string::npos);
}

// 3. Individual strategy: Best Fit and Worst Fit can be selected and executed
TEST(OScopeMemoryCLITest, IndividualBestFitAndWorstFitExecuteCorrectly) {
    // Best Fit: 500 bytes, 1 op (Alloc Req 1, 120 B, PID none)
    std::istringstream in_best("9\n2\n500\n1\n1\n1\n120\n-1\n5\n11\n");
    std::ostringstream out_best;
    EXPECT_EQ(oscope::run_cli(in_best, out_best), 0);
    const std::string s_best = out_best.str();
    EXPECT_NE(s_best.find("[Best Fit Memory Allocation]"), std::string::npos);
    EXPECT_NE(s_best.find("Allocated Memory:       120 bytes"), std::string::npos);
    EXPECT_NE(s_best.find("Free Memory:            380 bytes"), std::string::npos);

    // Worst Fit: 600 bytes, 1 op (Alloc Req 1, 250 B, PID none)
    std::istringstream in_worst("9\n3\n600\n1\n1\n1\n250\n-1\n5\n11\n");
    std::ostringstream out_worst;
    EXPECT_EQ(oscope::run_cli(in_worst, out_worst), 0);
    const std::string s_worst = out_worst.str();
    EXPECT_NE(s_worst.find("[Worst Fit Memory Allocation]"), std::string::npos);
    EXPECT_NE(s_worst.find("Allocated Memory:       250 bytes"), std::string::npos);
    EXPECT_NE(s_worst.find("Free Memory:            350 bytes"), std::string::npos);
}

// 4. Comparison mode with distinguishable results across strategies
TEST(OScopeMemoryCLITest, ComparisonModeProducesDistinguishableResults) {
    // Workload where Worst Fit fails on request 6, while First Fit and Best Fit succeed:
    // Total memory: 700 bytes
    // Op 1: Alloc Req 1, size 100
    // Op 2: Alloc Req 2, size 200
    // Op 3: Alloc Req 3, size 100
    // Op 4: Alloc Req 4, size 300
    // Op 5: Dealloc Req 2 (leaves free [100, 300) size 200)
    // Op 6: Dealloc Req 4 (leaves free [400, 700) size 300)
    // Op 7: Alloc Req 5, size 150 (First/Best take from 200 leaving 50; Worst takes from 300 leaving 150)
    // Op 8: Alloc Req 6, size 250 (First/Best have 300 block and succeed; Worst has max 200 block and fails)
    std::string input =
        "9\n4\n700\n8\n"
        "1\n1\n100\n-1\n"
        "1\n2\n200\n-1\n"
        "1\n3\n100\n-1\n"
        "1\n4\n300\n-1\n"
        "2\n2\n"
        "2\n4\n"
        "1\n5\n150\n-1\n"
        "1\n6\n250\n-1\n"
        "5\n11\n";

    std::istringstream in(input);
    std::ostringstream out;

    int exit_code = oscope::run_cli(in, out);

    EXPECT_EQ(exit_code, 0);
    const std::string s = out.str();
    EXPECT_NE(s.find("Comparison completed successfully across 3 memory allocation strategies."), std::string::npos);
    EXPECT_NE(s.find("=== Memory Allocation Strategy Comparison ==="), std::string::npos);
    EXPECT_NE(s.find("Total Memory: 700 bytes | Total Workload Operations: 8"), std::string::npos);
    EXPECT_NE(s.find("First Fit"), std::string::npos);
    EXPECT_NE(s.find("Best Fit"), std::string::npos);
    EXPECT_NE(s.find("Worst Fit"), std::string::npos);

    // First Fit and Best Fit have 100% success rate (6/6 successes, 0 failures)
    // Worst Fit has 5 successes and 1 failure (83.33% success rate)
    EXPECT_NE(s.find("100.00%"), std::string::npos);
    EXPECT_NE(s.find("83.33%"), std::string::npos);
}

// 5. Input validation and recovery from malformed numeric and operation type inputs
TEST(OScopeMemoryCLITest, RecoversFromInvalidNumericAndOperationTypeInputs) {
    // Menu choice: "bad", 0, 6, then 1 (First Fit)
    // Total memory: "xyz", -50, 0, then 1000
    // Operation count: "bad", -2, then 1
    // Operation type: "bad", 0, 3, then 1 (Allocate)
    // Logical Request ID: "abc", 0, -1, then 1
    // Size: "xyz", 0, -20, then 200
    // Process ID: "invalid", then 10
    // 5, 10
    std::string input =
        "9\n"
        "bad\n0\n6\n1\n"
        "xyz\n-50\n0\n1000\n"
        "bad\n-2\n1\n"
        "bad\n0\n3\n1\n"
        "abc\n0\n-1\n1\n"
        "xyz\n0\n-20\n200\n"
        "invalid\n10\n"
        "5\n11\n";

    std::istringstream in(input);
    std::ostringstream out;

    int exit_code = oscope::run_cli(in, out);

    EXPECT_EQ(exit_code, 0);
    const std::string s = out.str();
    EXPECT_NE(s.find("Error: Choice must be between 1 and 5."), std::string::npos);
    EXPECT_NE(s.find("Error: Value must be a positive integer (> 0)."), std::string::npos);
    EXPECT_NE(s.find("Error: Value must be non-negative (>= 0)."), std::string::npos);
    EXPECT_NE(s.find("Error: Invalid operation type. Please enter 1 for Allocate or 2 for Deallocate."), std::string::npos);
    EXPECT_NE(s.find("Error: Invalid numeric input."), std::string::npos);
    EXPECT_NE(s.find("Allocation successful: Request ID 1 allocated at address 0 (200 bytes, Internal ID: 1)"), std::string::npos);
}

// 6. Rejection of duplicate active logical request IDs and out-of-memory allocations
TEST(OScopeMemoryCLITest, RejectionOfDuplicateActiveLogicalIdsAndOom) {
    // Total memory: 500
    // 3 operations:
    // Op 1: Alloc Req 1, size 200 -> succeeds
    // Op 2: Alloc Req 1, size 100 -> duplicate active logical request ID -> fails
    // Op 3: Alloc Req 2, size 400 -> insufficient memory (only 300 free) -> fails
    std::string input =
        "9\n1\n500\n3\n"
        "1\n1\n200\n-1\n"
        "1\n1\n100\n-1\n"
        "1\n2\n400\n-1\n"
        "5\n11\n";

    std::istringstream in(input);
    std::ostringstream out;

    int exit_code = oscope::run_cli(in, out);

    EXPECT_EQ(exit_code, 0);
    const std::string s = out.str();
    EXPECT_NE(s.find("Allocation successful: Request ID 1 allocated at address 0 (200 bytes, Internal ID: 1)"), std::string::npos);
    EXPECT_NE(s.find("Allocation failed: Duplicate active logical request ID 1."), std::string::npos);
    EXPECT_NE(s.find("Allocation failed for request ID 2:"), std::string::npos);
    // State remains preserved: only the 200 byte block is allocated
    EXPECT_NE(s.find("Allocated Memory:       200 bytes"), std::string::npos);
    EXPECT_NE(s.find("Free Memory:            300 bytes"), std::string::npos);
}

// 7. Unknown and repeated deallocation behavior
TEST(OScopeMemoryCLITest, UnknownAndRepeatedDeallocationBehavior) {
    // Total memory: 500
    // 4 operations:
    // Op 1: Alloc Req 1, size 100
    // Op 2: Dealloc Req 99 (unknown) -> clear failure message, state unchanged
    // Op 3: Dealloc Req 1 -> succeeds, freed
    // Op 4: Dealloc Req 1 (repeated) -> clear failure message
    std::string input =
        "9\n1\n500\n4\n"
        "1\n1\n100\n-1\n"
        "2\n99\n"
        "2\n1\n"
        "2\n1\n"
        "5\n11\n";

    std::istringstream in(input);
    std::ostringstream out;

    int exit_code = oscope::run_cli(in, out);

    EXPECT_EQ(exit_code, 0);
    const std::string s = out.str();
    EXPECT_NE(s.find("Allocation successful: Request ID 1 allocated at address 0 (100 bytes, Internal ID: 1)"), std::string::npos);
    EXPECT_NE(s.find("Deallocation failed: Request ID 99 is not active."), std::string::npos);
    EXPECT_NE(s.find("Deallocation successful: Request ID 1 (Internal ID: 1) freed."), std::string::npos);
    EXPECT_NE(s.find("Deallocation failed: Request ID 1 is not active."), std::string::npos);
    EXPECT_NE(s.find("Allocated Memory:       0 bytes"), std::string::npos);
    EXPECT_NE(s.find("Free Memory:            500 bytes"), std::string::npos);
}

// 8. Empty workload in individual and comparison modes
TEST(OScopeMemoryCLITest, HandlesEmptyWorkloadCleanly) {
    // Individual mode with 0 operations
    std::istringstream in_ind("9\n1\n400\n0\n5\n11\n");
    std::ostringstream out_ind;
    EXPECT_EQ(oscope::run_cli(in_ind, out_ind), 0);
    const std::string s_ind = out_ind.str();
    EXPECT_NE(s_ind.find("Total Memory:           400 bytes"), std::string::npos);
    EXPECT_NE(s_ind.find("Allocated Memory:       0 bytes"), std::string::npos);
    EXPECT_NE(s_ind.find("Free Memory:            400 bytes"), std::string::npos);
    EXPECT_NE(s_ind.find("Largest Free Block:     400 bytes"), std::string::npos);
    EXPECT_NE(s_ind.find("External Fragmentation: 0.00% (0.00)"), std::string::npos);

    // Comparison mode with 0 operations
    std::istringstream in_comp("9\n4\n400\n0\n5\n11\n");
    std::ostringstream out_comp;
    EXPECT_EQ(oscope::run_cli(in_comp, out_comp), 0);
    const std::string s_comp = out_comp.str();
    EXPECT_NE(s_comp.find("Comparison completed successfully across 3 memory allocation strategies."), std::string::npos);
    EXPECT_NE(s_comp.find("Total Memory: 400 bytes | Total Workload Operations: 0"), std::string::npos);
}

// 9. Graceful EOF handling at various memory input prompts
TEST(OScopeMemoryCLITest, HandlesEofAtVariousMemoryInputPrompts) {
    // EOF at memory menu prompt
    {
        std::istringstream in("9\n");
        std::ostringstream out;
        EXPECT_EQ(oscope::run_cli(in, out), 0);
        EXPECT_NE(out.str().find("End of input reached. Exiting OScope."), std::string::npos);
    }
    // EOF at total memory prompt
    {
        std::istringstream in("9\n1\n");
        std::ostringstream out;
        EXPECT_EQ(oscope::run_cli(in, out), 0);
        EXPECT_NE(out.str().find("End of input reached. Exiting OScope."), std::string::npos);
    }
    // EOF at operation count prompt
    {
        std::istringstream in("9\n1\n500\n");
        std::ostringstream out;
        EXPECT_EQ(oscope::run_cli(in, out), 0);
        EXPECT_NE(out.str().find("End of input reached. Exiting OScope."), std::string::npos);
    }
    // EOF at operation type prompt
    {
        std::istringstream in("9\n1\n500\n1\n");
        std::ostringstream out;
        EXPECT_EQ(oscope::run_cli(in, out), 0);
        EXPECT_NE(out.str().find("End of input reached. Exiting OScope."), std::string::npos);
    }
    // EOF at request ID prompt
    {
        std::istringstream in("9\n1\n500\n1\n1\n");
        std::ostringstream out;
        EXPECT_EQ(oscope::run_cli(in, out), 0);
        EXPECT_NE(out.str().find("End of input reached. Exiting OScope."), std::string::npos);
    }
    // EOF at allocation size prompt
    {
        std::istringstream in("9\n1\n500\n1\n1\n1\n");
        std::ostringstream out;
        EXPECT_EQ(oscope::run_cli(in, out), 0);
        EXPECT_NE(out.str().find("End of input reached. Exiting OScope."), std::string::npos);
    }
    // EOF at process ID prompt
    {
        std::istringstream in("9\n1\n500\n1\n1\n1\n100");
        std::ostringstream out;
        EXPECT_EQ(oscope::run_cli(in, out), 0);
        EXPECT_NE(out.str().find("End of input reached. Exiting OScope."), std::string::npos);
    }
    // EOF at deallocation request ID prompt
    {
        std::istringstream in("9\n1\n500\n1\n2\n");
        std::ostringstream out;
        EXPECT_EQ(oscope::run_cli(in, out), 0);
        EXPECT_NE(out.str().find("End of input reached. Exiting OScope."), std::string::npos);
    }
}

// 10. Existing scheduling and paging CLI behaviors remain unaffected
TEST(OScopeMemoryCLITest, ExistingSchedulingAndPagingBehaviorsUnaffected) {
    // Run FCFS (Option 1) -> 1 process -> Exit with Option 11
    {
        std::istringstream in("1\n1\n1\n0\n5\n0\n11\n");
        std::ostringstream out;
        EXPECT_EQ(oscope::run_cli(in, out), 0);
        const std::string s = out.str();
        EXPECT_NE(s.find("Simulation completed successfully."), std::string::npos);
        EXPECT_NE(s.find("=== Execution Timeline ==="), std::string::npos);
    }

    // Run Paging FIFO (Option 8 -> Option 1 -> frames 3 -> ref string "1 2 3" -> 5 -> 11)
    {
        std::istringstream in("8\n1\n3\n1 2 3\n5\n11\n");
        std::ostringstream out;
        EXPECT_EQ(oscope::run_cli(in, out), 0);
        const std::string s = out.str();
        EXPECT_NE(s.find("[FIFO Page Replacement Simulation]"), std::string::npos);
        EXPECT_NE(s.find("=== Page Replacement Step-by-Step Execution ==="), std::string::npos);
        EXPECT_NE(s.find("Exiting OScope. Goodbye!"), std::string::npos);
    }
}

// 11. Unit tests for display_memory_blocks, display_memory_metrics, display_memory_comparison_table
TEST(OScopeMemoryCLITest, DirectDisplayFunctionsFormatAndPreserveStreamState) {
    // Test display_memory_blocks with empty list
    {
        std::ostringstream out;
        std::vector<oscope::MemoryBlock> empty_blocks;
        oscope::display_memory_blocks(out, empty_blocks);
        EXPECT_NE(out.str().find("No memory blocks available."), std::string::npos);
    }

    // Test display_memory_blocks with allocated and free blocks
    {
        std::ostringstream out;
        std::vector<oscope::MemoryBlock> blocks = {
            {1, 0, 200, true, 42},
            {std::nullopt, 200, 300, false, std::nullopt}
        };
        oscope::display_memory_blocks(out, blocks);
        const std::string s = out.str();
        EXPECT_NE(s.find("=== Memory Block Layout ==="), std::string::npos);
        EXPECT_NE(s.find("Allocated"), std::string::npos);
        EXPECT_NE(s.find("Free"), std::string::npos);
        EXPECT_NE(s.find("42"), std::string::npos);
    }

    // Test display_memory_metrics and check stream state preservation
    {
        std::ostringstream out;
        out << std::setprecision(6);
        const auto orig_flags = out.flags();
        const auto orig_prec = out.precision();

        oscope::MemoryMetrics metrics{1000, 400, 600, 400, 0.333333};
        oscope::display_memory_metrics(out, metrics);

        EXPECT_EQ(out.flags(), orig_flags);
        EXPECT_EQ(out.precision(), orig_prec);

        const std::string s = out.str();
        EXPECT_NE(s.find("Total Memory:           1000 bytes"), std::string::npos);
        EXPECT_NE(s.find("Allocated Memory:       400 bytes"), std::string::npos);
        EXPECT_NE(s.find("Free Memory:            600 bytes"), std::string::npos);
        EXPECT_NE(s.find("Largest Free Block:     400 bytes"), std::string::npos);
        EXPECT_NE(s.find("External Fragmentation: 33.33% (0.33)"), std::string::npos);
    }

    // Test display_memory_comparison_table with empty and populated result
    {
        std::ostringstream out_empty;
        oscope::MemoryComparisonResult empty_result;
        oscope::display_memory_comparison_table(out_empty, empty_result);
        EXPECT_NE(out_empty.str().find("No comparison results available"), std::string::npos);

        std::ostringstream out_pop;
        out_pop << std::setprecision(5);
        const auto orig_flags = out_pop.flags();
        const auto orig_prec = out_pop.precision();

        oscope::MemoryComparisonResult result;
        result.total_memory = 500;
        result.workload = {oscope::MemoryOperation::alloc(1, 200)};

        oscope::MemoryComparisonEntry entry;
        entry.strategy = oscope::memory::AllocationStrategy::FirstFit;
        entry.strategy_name = "First Fit";
        entry.allocation_requests_attempted = 1;
        entry.successful_allocations = 1;
        entry.failed_allocations = 0;
        entry.allocation_success_rate = 1.0;
        entry.final_metrics = {500, 200, 300, 300, 0.0};

        result.entries.push_back(entry);

        oscope::display_memory_comparison_table(out_pop, result);

        EXPECT_EQ(out_pop.flags(), orig_flags);
        EXPECT_EQ(out_pop.precision(), orig_prec);

        const std::string s = out_pop.str();
        EXPECT_NE(s.find("=== Memory Allocation Strategy Comparison ==="), std::string::npos);
        EXPECT_NE(s.find("First Fit"), std::string::npos);
        EXPECT_NE(s.find("100.00%"), std::string::npos);
    }
}
