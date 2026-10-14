#ifndef OSCOPE_CLI_HPP
#define OSCOPE_CLI_HPP

#include <iosfwd>
#include <optional>
#include <string>
#include <vector>

#include "oscope/memory/allocation_result.hpp"
#include "oscope/memory/memory_block.hpp"
#include "oscope/memory/memory_comparison.hpp"
#include "oscope/paging/page_replacement_comparison.hpp"
#include "oscope/paging/page_replacement_result.hpp"
#include "oscope/process.hpp"
#include "oscope/scheduling_comparison.hpp"
#include "oscope/scheduling_simulation_result.hpp"

namespace oscope {

enum class AlgorithmChoice {
    FCFS = 1,
    SJF = 2,
    SRTF = 3,
    Priority = 4,
    RoundRobin = 5,
    MLFQ = 6,
    CompareAll = 7,
    Paging = 8,
    MemoryAllocation = 9,
    Exit = 10
};

enum class PagingChoice {
    FIFO = 1,
    LRU = 2,
    Optimal = 3,
    CompareAll = 4,
    ReturnToMainMenu = 5
};

enum class MemoryChoice {
    FirstFit = 1,
    BestFit = 2,
    WorstFit = 3,
    CompareAll = 4,
    ReturnToMainMenu = 5
};

// Input parsing and validation utilities
bool read_int(std::istream& in, std::ostream& out, const std::string& prompt, int& value);
bool read_positive_int(std::istream& in, std::ostream& out, const std::string& prompt, int& value);
bool read_non_negative_int(std::istream& in, std::ostream& out, const std::string& prompt, int& value);
std::optional<std::vector<int>> read_reference_string(std::istream& in, std::ostream& out, const std::string& prompt);

// Process input reader
std::optional<std::vector<Process>> read_processes(std::istream& in, std::ostream& out, AlgorithmChoice choice);

// Menu rendering and selection
void print_main_menu(std::ostream& out);
void print_relevant_fields_explanation(std::ostream& out, AlgorithmChoice choice);
std::optional<AlgorithmChoice> read_menu_choice(std::istream& in, std::ostream& out);

void print_paging_menu(std::ostream& out);
std::optional<PagingChoice> read_paging_choice(std::istream& in, std::ostream& out);

void print_memory_menu(std::ostream& out);
std::optional<MemoryChoice> read_memory_choice(std::istream& in, std::ostream& out);

// CPU Scheduling results and metrics display
void display_execution_timeline(std::ostream& out, const SchedulingSimulationResult& result);
void display_process_metrics_table(std::ostream& out, const std::vector<Process>& processes, const SchedulingSimulationResult& result);
void display_average_metrics(std::ostream& out, const SchedulingSimulationResult& result);
void display_simulation_results(std::ostream& out, const std::vector<Process>& processes, const SchedulingSimulationResult& result);
void display_comparison_table(std::ostream& out, const std::vector<SchedulingComparisonEntry>& entries);

// Paging results and metrics display
void display_paging_steps(std::ostream& out, const PageReplacementResult& result, int frame_count);
void display_paging_metrics(std::ostream& out, const PageReplacementResult& result);
void display_paging_simulation_results(std::ostream& out, const PageReplacementResult& result, int frame_count);
void display_paging_comparison_table(std::ostream& out, const PageReplacementComparisonResult& result);

// Memory results and metrics display
void display_memory_blocks(std::ostream& out, const std::vector<MemoryBlock>& blocks);
void display_memory_metrics(std::ostream& out, const MemoryMetrics& metrics);
void display_memory_comparison_table(std::ostream& out, const MemoryComparisonResult& result);

// Interactive CLI entry points
bool run_paging_cli(std::istream& in, std::ostream& out);
bool run_memory_cli(std::istream& in, std::ostream& out);
int run_cli(std::istream& in, std::ostream& out);

} // namespace oscope

#endif // OSCOPE_CLI_HPP
