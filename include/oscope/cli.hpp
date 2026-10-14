#ifndef OSCOPE_CLI_HPP
#define OSCOPE_CLI_HPP

#include <iosfwd>
#include <optional>
#include <string>
#include <vector>

#include "oscope/process.hpp"
#include "oscope/scheduling_simulation_result.hpp"

namespace oscope {

enum class AlgorithmChoice {
    FCFS = 1,
    SJF = 2,
    SRTF = 3,
    Priority = 4,
    RoundRobin = 5,
    MLFQ = 6,
    Exit = 7
};

// Input parsing and validation utilities
bool read_int(std::istream& in, std::ostream& out, const std::string& prompt, int& value);
bool read_positive_int(std::istream& in, std::ostream& out, const std::string& prompt, int& value);
bool read_non_negative_int(std::istream& in, std::ostream& out, const std::string& prompt, int& value);

// Process input reader
std::optional<std::vector<Process>> read_processes(std::istream& in, std::ostream& out, AlgorithmChoice choice);

// Menu rendering and selection
void print_main_menu(std::ostream& out);
void print_relevant_fields_explanation(std::ostream& out, AlgorithmChoice choice);
std::optional<AlgorithmChoice> read_menu_choice(std::istream& in, std::ostream& out);

// Results and metrics display
void display_execution_timeline(std::ostream& out, const SchedulingSimulationResult& result);
void display_process_metrics_table(std::ostream& out, const std::vector<Process>& processes, const SchedulingSimulationResult& result);
void display_average_metrics(std::ostream& out, const SchedulingSimulationResult& result);
void display_simulation_results(std::ostream& out, const std::vector<Process>& processes, const SchedulingSimulationResult& result);

// Interactive CLI main entry point
int run_cli(std::istream& in, std::ostream& out);

} // namespace oscope

#endif // OSCOPE_CLI_HPP
