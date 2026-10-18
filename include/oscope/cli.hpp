#ifndef OSCOPE_CLI_HPP
#define OSCOPE_CLI_HPP

#include <iosfwd>
#include <optional>
#include <string>
#include <vector>

#include "oscope/experiments/pipe_ipc_experiment.hpp"
#include "oscope/experiments/process_experiment.hpp"
#include "oscope/experiments/synchronization_experiment.hpp"
#include "oscope/experiments/thread_experiment.hpp"
#include "oscope/reporting/json_value.hpp"
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
    LinuxExperiments = 10,
    Exit = 11
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

enum class ExperimentChoice {
    ProcessCreation = 1,
    ThreadCreation = 2,
    ThreadSynchronization = 3,
    PipeIpc = 4,
    ReturnToMainMenu = 5
};

enum class OutputFormat {
    HumanReadable,
    Json
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

void print_experiments_menu(std::ostream& out);
std::optional<ExperimentChoice> read_experiment_choice(std::istream& in, std::ostream& out);

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

// Linux/POSIX Experiments results display
void display_process_experiment_result(std::ostream& out, const experiments::ProcessExperimentResult& result, OutputFormat format = OutputFormat::HumanReadable);
void display_thread_experiment_result(std::ostream& out, const experiments::ThreadExperimentResult& result, OutputFormat format = OutputFormat::HumanReadable);
void display_synchronization_experiment_result(std::ostream& out, const experiments::SynchronizationExperimentResult& result, OutputFormat format = OutputFormat::HumanReadable);
void display_pipe_ipc_experiment_result(std::ostream& out, const experiments::PipeIpcExperimentResult& result, OutputFormat format = OutputFormat::HumanReadable);

// Interactive CLI entry points
bool run_paging_cli(std::istream& in, std::ostream& out);
bool run_memory_cli(std::istream& in, std::ostream& out);
bool run_experiments_cli(
    std::istream& in,
    std::ostream& out,
    OutputFormat format = OutputFormat::HumanReadable,
    std::vector<reporting::JsonValue>* json_accumulator = nullptr);
int run_cli(std::istream& in, std::ostream& out, OutputFormat format = OutputFormat::HumanReadable);

} // namespace oscope

#endif // OSCOPE_CLI_HPP
