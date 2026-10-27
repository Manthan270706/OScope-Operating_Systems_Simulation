#include "oscope/cli.hpp"
#include "oscope/reporting/experiment_reporter.hpp"

#include <iomanip>
#include <iostream>
#include <limits>
#include <memory>
#include <sstream>
#include <string>
#include <unordered_map>
#include <unordered_set>
#include <vector>
#include "oscope/memory/allocation_strategy.hpp"
#include "oscope/memory/memory_comparison.hpp"
#include "oscope/memory/memory_manager.hpp"
#include "oscope/paging/fifo.hpp"
#include "oscope/paging/lru.hpp"
#include "oscope/paging/optimal.hpp"
#include "oscope/paging/page_replacement_comparison.hpp"
#include "oscope/paging/page_replacement_result.hpp"
#include "oscope/scheduling_metrics.hpp"
#include "oscope/scheduling/fcfs.hpp"
#include "oscope/scheduling/mlfq.hpp"
#include "oscope/scheduling/priority.hpp"
#include "oscope/scheduling/round_robin.hpp"
#include "oscope/scheduling/sjf.hpp"
#include "oscope/scheduling/srtf.hpp"

namespace oscope {

bool read_int(std::istream& in, std::ostream& out, const std::string& prompt, int& value) {
    std::string line;
    while (true) {
        out << prompt;
        if (!std::getline(in, line)) {
            return false;
        }

        const auto start = line.find_first_not_of(" \t\r\n");
        if (start == std::string::npos) {
            out << "Error: Input cannot be empty. Please enter an integer.\n";
            continue;
        }
        const auto end = line.find_last_not_of(" \t\r\n");
        const std::string trimmed = line.substr(start, end - start + 1);

        try {
            std::size_t pos = 0;
            long val = std::stol(trimmed, &pos);
            if (pos != trimmed.size()) {
                out << "Error: Trailing non-numeric characters detected. Please enter a valid integer.\n";
                continue;
            }
            if (val < std::numeric_limits<int>::min() || val > std::numeric_limits<int>::max()) {
                out << "Error: Number is out of integer range.\n";
                continue;
            }
            value = static_cast<int>(val);
            return true;
        } catch (const std::invalid_argument&) {
            out << "Error: Invalid numeric input. Please enter an integer.\n";
        } catch (const std::out_of_range&) {
            out << "Error: Number is out of integer range.\n";
        }
    }
}

bool read_positive_int(std::istream& in, std::ostream& out, const std::string& prompt, int& value) {
    while (true) {
        if (!read_int(in, out, prompt, value)) {
            return false;
        }
        if (value <= 0) {
            out << "Error: Value must be a positive integer (> 0).\n";
            continue;
        }
        return true;
    }
}

bool read_non_negative_int(std::istream& in, std::ostream& out, const std::string& prompt, int& value) {
    while (true) {
        if (!read_int(in, out, prompt, value)) {
            return false;
        }
        if (value < 0) {
            out << "Error: Value must be non-negative (>= 0).\n";
            continue;
        }
        return true;
    }
}

std::optional<std::vector<int>> read_reference_string(std::istream& in, std::ostream& out, const std::string& prompt) {
    std::string line;
    while (true) {
        out << prompt;
        if (!std::getline(in, line)) {
            return std::nullopt;
        }

        const auto start = line.find_first_not_of(" \t\r\n");
        if (start == std::string::npos) {
            // Empty reference string is valid
            return std::vector<int>{};
        }
        const auto end = line.find_last_not_of(" \t\r\n");
        const std::string trimmed = line.substr(start, end - start + 1);

        std::istringstream iss(trimmed);
        std::string token;
        std::vector<int> pages;
        bool valid = true;

        while (iss >> token) {
            try {
                std::size_t pos = 0;
                long val = std::stol(token, &pos);
                if (pos != token.size()) {
                    out << "Error: Trailing non-numeric characters in token '" << token
                        << "'. Page numbers must be valid integers.\n";
                    valid = false;
                    break;
                }
                if (val < 0) {
                    out << "Error: Negative page number (" << val
                        << ") detected. Page numbers must be non-negative (>= 0).\n";
                    valid = false;
                    break;
                }
                if (val > std::numeric_limits<int>::max()) {
                    out << "Error: Page number " << val << " exceeds maximum integer range.\n";
                    valid = false;
                    break;
                }
                pages.push_back(static_cast<int>(val));
            } catch (const std::invalid_argument&) {
                out << "Error: Invalid numeric input in token '" << token
                    << "'. Page numbers must be non-negative integers.\n";
                valid = false;
                break;
            } catch (const std::out_of_range&) {
                out << "Error: Page number out of integer range in token '" << token << "'.\n";
                valid = false;
                break;
            }
        }

        if (valid) {
            return pages;
        }
    }
}

void print_relevant_fields_explanation(std::ostream& out, AlgorithmChoice choice) {
    out << "\n[Algorithm Information]\n";
    switch (choice) {
        case AlgorithmChoice::FCFS:
            out << "Selected: First-Come, First-Served (FCFS)\n"
                << "Relevant fields: PID, Arrival Time, Burst Time. (Priority is ignored).\n";
            break;
        case AlgorithmChoice::SJF:
            out << "Selected: Shortest Job First (SJF - Non-Preemptive)\n"
                << "Relevant fields: PID, Arrival Time, Burst Time. (Priority is ignored).\n";
            break;
        case AlgorithmChoice::SRTF:
            out << "Selected: Shortest Remaining Time First (SRTF - Preemptive)\n"
                << "Relevant fields: PID, Arrival Time, Burst Time. (Priority is ignored).\n";
            break;
        case AlgorithmChoice::Priority:
            out << "Selected: Non-Preemptive Priority Scheduling\n"
                << "Relevant fields: PID, Arrival Time, Burst Time, Priority (Lower numeric value = higher priority).\n";
            break;
        case AlgorithmChoice::RoundRobin:
            out << "Selected: Round Robin (RR)\n"
                << "Relevant fields: PID, Arrival Time, Burst Time. (Priority is ignored).\n";
            break;
        case AlgorithmChoice::MLFQ:
            out << "Selected: Multilevel Feedback Queue (MLFQ)\n"
                << "Relevant fields: PID, Arrival Time, Burst Time. (Priority is ignored).\n";
            break;
        case AlgorithmChoice::CompareAll:
            out << "Selected: Compare All Scheduling Algorithms\n"
                << "Relevant fields: PID, Arrival Time, Burst Time, Priority (Used by Priority scheduling).\n";
            break;
        case AlgorithmChoice::Paging:
        case AlgorithmChoice::Exit:
            break;
    }
    out << "\n";
}

std::optional<std::vector<Process>> read_processes(std::istream& in, std::ostream& out, AlgorithmChoice choice) {
    print_relevant_fields_explanation(out, choice);

    int count = 0;
    if (!read_positive_int(in, out, "Enter number of processes: ", count)) {
        return std::nullopt;
    }

    std::vector<Process> processes;
    processes.reserve(count);
    std::unordered_set<int> seen_pids;

    for (int i = 1; i <= count; ++i) {
        out << "\n--- Process " << i << " of " << count << " ---\n";

        int pid = 0;
        while (true) {
            if (!read_int(in, out, "  PID: ", pid)) {
                return std::nullopt;
            }
            if (seen_pids.find(pid) != seen_pids.end()) {
                out << "Error: PID " << pid << " has already been entered. PIDs must be unique.\n";
                continue;
            }
            seen_pids.insert(pid);
            break;
        }

        int arrival_time = 0;
        if (!read_non_negative_int(in, out, "  Arrival Time: ", arrival_time)) {
            return std::nullopt;
        }

        int burst_time = 0;
        if (!read_positive_int(in, out, "  Burst Time: ", burst_time)) {
            return std::nullopt;
        }

        int priority = 0;
        if (choice == AlgorithmChoice::Priority || choice == AlgorithmChoice::CompareAll) {
            if (!read_int(in, out, "  Priority (lower numeric value = higher priority): ", priority)) {
                return std::nullopt;
            }
        } else {
            if (!read_int(in, out, "  Priority (ignored for this algorithm, enter integer, e.g. 0): ", priority)) {
                return std::nullopt;
            }
        }

        processes.push_back({pid, arrival_time, burst_time, priority});
    }

    return processes;
}

void print_main_menu(std::ostream& out) {
    out << "\n========================================\n"
        << "                OScope                  \n"
        << "  CPU Scheduling & Paging Platform      \n"
        << "========================================\n"
        << "1. Run FCFS\n"
        << "2. Run SJF\n"
        << "3. Run SRTF\n"
        << "4. Run non-preemptive Priority\n"
        << "5. Run Round Robin\n"
        << "6. Run MLFQ\n"
        << "7. Compare all scheduling algorithms\n"
        << "8. Page replacement (Paging)\n"
        << "9. Memory Allocation (Dynamic Partitioning)\n"
        << "10. Linux/POSIX Experiments\n"
        << "11. Deadlock Management\n"
        << "12. Disk Scheduling\n"
        << "13. Exit\n"
        << "========================================\n";
}

std::optional<AlgorithmChoice> read_menu_choice(std::istream& in, std::ostream& out) {
    int choice_val = 0;
    while (true) {
        if (!read_int(in, out, "Enter your choice (1-13): ", choice_val)) {
            return std::nullopt;
        }
        if (choice_val < 1 || choice_val > 13) {
            out << "Error: Choice must be between 1 and 13.\n";
            continue;
        }
        return static_cast<AlgorithmChoice>(choice_val);
    }
}

void print_paging_menu(std::ostream& out) {
    out << "\n========================================\n"
        << "            Page Replacement            \n"
        << "========================================\n"
        << "1. Run FIFO\n"
        << "2. Run LRU\n"
        << "3. Run Optimal\n"
        << "4. Compare FIFO, LRU, and Optimal\n"
        << "5. Return to main menu\n"
        << "========================================\n";
}

std::optional<PagingChoice> read_paging_choice(std::istream& in, std::ostream& out) {
    int choice_val = 0;
    while (true) {
        if (!read_int(in, out, "Enter your choice (1-5): ", choice_val)) {
            return std::nullopt;
        }
        if (choice_val < 1 || choice_val > 5) {
            out << "Error: Choice must be between 1 and 5.\n";
            continue;
        }
        return static_cast<PagingChoice>(choice_val);
    }
}

bool run_paging_cli(std::istream& in, std::ostream& out) {
    while (true) {
        print_paging_menu(out);

        auto choice_opt = read_paging_choice(in, out);
        if (!choice_opt.has_value()) {
            return false;
        }

        PagingChoice choice = choice_opt.value();
        if (choice == PagingChoice::ReturnToMainMenu) {
            return true;
        }

        int frame_count = 0;
        if (!read_positive_int(in, out, "Enter number of frames: ", frame_count)) {
            return false;
        }

        auto ref_opt = read_reference_string(
            in, out, "Enter page-reference string (space-separated, empty line allowed): ");
        if (!ref_opt.has_value()) {
            return false;
        }

        const auto& ref_string = ref_opt.value();

        if (choice == PagingChoice::CompareAll) {
            try {
                auto comp_result = PageReplacementComparator::compare_all(ref_string, frame_count);
                out << "\nComparison completed successfully across "
                    << comp_result.size() << " page replacement algorithm(s).\n";
                display_paging_comparison_table(out, comp_result);
                out << "\n";
            } catch (const std::exception& e) {
                out << "\nComparison failed with error: " << e.what() << "\n\n";
            }
            continue;
        }

        std::unique_ptr<PageReplacementAlgorithm> algorithm;
        std::string algo_name;
        switch (choice) {
            case PagingChoice::FIFO:
                algorithm = std::make_unique<FIFO>();
                algo_name = "FIFO";
                break;
            case PagingChoice::LRU:
                algorithm = std::make_unique<LRU>();
                algo_name = "LRU";
                break;
            case PagingChoice::Optimal:
                algorithm = std::make_unique<Optimal>();
                algo_name = "Optimal";
                break;
            case PagingChoice::CompareAll:
            case PagingChoice::ReturnToMainMenu:
                return true;
        }

        try {
            PageReplacementResult result = algorithm->simulate(ref_string, frame_count);
            out << "\n[" << algo_name << " Page Replacement Simulation]\n";
            out << "Simulation completed successfully with " << result.total_references
                << " reference(s) across " << frame_count << " frame(s).\n";
            display_paging_simulation_results(out, result, frame_count);
            out << "\n";
        } catch (const std::exception& e) {
            out << "\nSimulation failed with error: " << e.what() << "\n\n";
        }
    }
}

void print_memory_menu(std::ostream& out) {
    out << "\n========================================\n"
        << "           Memory Allocation            \n"
        << "========================================\n"
        << "1. First Fit\n"
        << "2. Best Fit\n"
        << "3. Worst Fit\n"
        << "4. Compare all three strategies\n"
        << "5. Return to main menu\n"
        << "========================================\n";
}

std::optional<MemoryChoice> read_memory_choice(std::istream& in, std::ostream& out) {
    int choice_val = 0;
    while (true) {
        if (!read_int(in, out, "Enter your choice (1-5): ", choice_val)) {
            return std::nullopt;
        }
        if (choice_val < 1 || choice_val > 5) {
            out << "Error: Choice must be between 1 and 5.\n";
            continue;
        }
        return static_cast<MemoryChoice>(choice_val);
    }
}

static bool read_operation_type(std::istream& in, std::ostream& out, MemoryOperationType& op_type) {
    std::string line;
    while (true) {
        out << "  Operation type (1: Allocate, 2: Deallocate): ";
        if (!std::getline(in, line)) {
            return false;
        }
        const auto start = line.find_first_not_of(" \t\r\n");
        if (start == std::string::npos) {
            out << "Error: Input cannot be empty. Please enter 1 for Allocate or 2 for Deallocate.\n";
            continue;
        }
        const auto end = line.find_last_not_of(" \t\r\n");
        const std::string trimmed = line.substr(start, end - start + 1);

        if (trimmed == "1" || trimmed == "a" || trimmed == "A" || trimmed == "allocate" || trimmed == "Allocate") {
            op_type = MemoryOperationType::Allocate;
            return true;
        }
        if (trimmed == "2" || trimmed == "d" || trimmed == "D" || trimmed == "deallocate" || trimmed == "Deallocate") {
            op_type = MemoryOperationType::Deallocate;
            return true;
        }
        out << "Error: Invalid operation type. Please enter 1 for Allocate or 2 for Deallocate.\n";
    }
}

static bool read_optional_pid(std::istream& in, std::ostream& out, const std::string& prompt, std::optional<int>& pid_out) {
    std::string line;
    while (true) {
        out << prompt;
        if (!std::getline(in, line)) {
            return false;
        }
        const auto start = line.find_first_not_of(" \t\r\n");
        if (start == std::string::npos) {
            pid_out = std::nullopt;
            return true;
        }
        const auto end = line.find_last_not_of(" \t\r\n");
        const std::string trimmed = line.substr(start, end - start + 1);

        try {
            std::size_t pos = 0;
            long val = std::stol(trimmed, &pos);
            if (pos != trimmed.size()) {
                out << "Error: Trailing non-numeric characters detected. Please enter a valid integer.\n";
                continue;
            }
            if (val < std::numeric_limits<int>::min() || val > std::numeric_limits<int>::max()) {
                out << "Error: Number is out of integer range.\n";
                continue;
            }
            int int_val = static_cast<int>(val);
            if (int_val < 0) {
                pid_out = std::nullopt;
            } else {
                pid_out = int_val;
            }
            return true;
        } catch (const std::invalid_argument&) {
            out << "Error: Invalid numeric input. Please enter an integer.\n";
        } catch (const std::out_of_range&) {
            out << "Error: Number is out of integer range.\n";
        }
    }
}

static bool read_memory_operation(std::istream& in, std::ostream& out, int op_num, int total_ops, MemoryOperation& op) {
    out << "\n--- Operation " << op_num << " of " << total_ops << " ---\n";
    MemoryOperationType op_type = MemoryOperationType::Allocate;
    if (!read_operation_type(in, out, op_type)) {
        return false;
    }

    if (op_type == MemoryOperationType::Allocate) {
        int req_id = 0;
        if (!read_positive_int(in, out, "    Logical Request ID: ", req_id)) {
            return false;
        }
        int size_val = 0;
        if (!read_positive_int(in, out, "    Allocation size (bytes): ", size_val)) {
            return false;
        }
        std::optional<int> pid = std::nullopt;
        if (!read_optional_pid(in, out, "    Process ID (or -1 if none): ", pid)) {
            return false;
        }
        op = MemoryOperation::alloc(req_id, static_cast<std::size_t>(size_val), pid);
        return true;
    } else {
        int req_id = 0;
        if (!read_positive_int(in, out, "    Logical Request ID to deallocate: ", req_id)) {
            return false;
        }
        op = MemoryOperation::dealloc(req_id);
        return true;
    }
}

bool run_memory_cli(std::istream& in, std::ostream& out) {
    while (true) {
        print_memory_menu(out);

        auto choice_opt = read_memory_choice(in, out);
        if (!choice_opt.has_value()) {
            return false;
        }

        MemoryChoice choice = choice_opt.value();
        if (choice == MemoryChoice::ReturnToMainMenu) {
            return true;
        }

        int total_memory_val = 0;
        if (!read_positive_int(in, out, "Enter total memory size (bytes): ", total_memory_val)) {
            return false;
        }
        std::size_t total_memory = static_cast<std::size_t>(total_memory_val);

        int op_count = 0;
        if (!read_non_negative_int(in, out, "Enter number of operations: ", op_count)) {
            return false;
        }

        if (choice == MemoryChoice::CompareAll) {
            std::vector<MemoryOperation> workload;
            workload.reserve(static_cast<std::size_t>(op_count));

            for (int i = 1; i <= op_count; ++i) {
                MemoryOperation op;
                if (!read_memory_operation(in, out, i, op_count, op)) {
                    return false;
                }
                workload.push_back(op);
            }

            try {
                auto comp_result = MemoryComparator{}.compare(total_memory, workload);
                out << "\nComparison completed successfully across "
                    << comp_result.size() << " memory allocation strategies.\n";
                display_memory_comparison_table(out, comp_result);
                out << "\n";
            } catch (const std::exception& e) {
                out << "\nComparison failed with error: " << e.what() << "\n\n";
            }
            continue;
        }

        AllocationStrategy strategy = AllocationStrategy::FirstFit;
        switch (choice) {
            case MemoryChoice::FirstFit:
                strategy = AllocationStrategy::FirstFit;
                break;
            case MemoryChoice::BestFit:
                strategy = AllocationStrategy::BestFit;
                break;
            case MemoryChoice::WorstFit:
                strategy = AllocationStrategy::WorstFit;
                break;
            case MemoryChoice::CompareAll:
            case MemoryChoice::ReturnToMainMenu:
                return true;
        }

        std::string strategy_name = std::string(to_string(strategy));
        out << "\n[" << strategy_name << " Memory Allocation]\n";

        MemoryManager manager(total_memory, strategy);
        std::unordered_map<int, int> active_allocations;

        for (int i = 1; i <= op_count; ++i) {
            MemoryOperation op;
            if (!read_memory_operation(in, out, i, op_count, op)) {
                return false;
            }

            if (op.type == MemoryOperationType::Allocate) {
                if (active_allocations.find(op.request_id) != active_allocations.end()) {
                    out << "Allocation failed: Duplicate active logical request ID "
                        << op.request_id << ".\n";
                } else {
                    AllocationResult alloc_res =
                        manager.allocate(op.size, strategy, op.process_id);
                    if (alloc_res.success) {
                        active_allocations[op.request_id] = alloc_res.allocation_id.value();
                        out << "Allocation successful: Request ID " << op.request_id
                            << " allocated at address " << alloc_res.start_address
                            << " (" << alloc_res.size << " bytes, Internal ID: "
                            << alloc_res.allocation_id.value() << ").\n";
                    } else {
                        out << "Allocation failed for request ID " << op.request_id
                            << ": " << alloc_res.error_message << "\n";
                    }
                }
            } else {
                auto it = active_allocations.find(op.request_id);
                if (it == active_allocations.end()) {
                    out << "Deallocation failed: Request ID " << op.request_id
                        << " is not active.\n";
                } else {
                    int actual_id = it->second;
                    bool freed = manager.deallocate(actual_id);
                    if (freed) {
                        active_allocations.erase(it);
                        out << "Deallocation successful: Request ID " << op.request_id
                            << " (Internal ID: " << actual_id << ") freed.\n";
                    } else {
                        out << "Deallocation failed: Internal allocation ID "
                            << actual_id << " could not be freed.\n";
                    }
                }
            }
        }

        display_memory_blocks(out, manager.blocks());
        display_memory_metrics(out, manager.calculate_metrics());
        out << "\n";
    }
}

void print_experiments_menu(std::ostream& out) {
    out << "\n========================================\n"
        << "       Linux/POSIX Experiments          \n"
        << "========================================\n"
        << "1. Process Creation\n"
        << "2. Thread Creation\n"
        << "3. Thread Synchronization\n"
        << "4. Pipe-based IPC\n"
        << "5. Return to Main Menu\n"
        << "========================================\n";
}

std::optional<ExperimentChoice> read_experiment_choice(std::istream& in, std::ostream& out) {
    int choice_val = 0;
    while (true) {
        if (!read_int(in, out, "Enter your choice (1-5): ", choice_val)) {
            return std::nullopt;
        }
        if (choice_val < 1 || choice_val > 5) {
            out << "Error: Choice must be between 1 and 5.\n";
            continue;
        }
        return static_cast<ExperimentChoice>(choice_val);
    }
}

bool run_experiments_cli(
    std::istream& in,
    std::ostream& out,
    OutputFormat format,
    std::vector<reporting::JsonValue>* json_accumulator) {

    std::ostream& prompt_stream = (format == OutputFormat::Json) ? std::cerr : out;
    std::vector<reporting::JsonValue> local_accumulator;
    std::vector<reporting::JsonValue>& target_accumulator =
        json_accumulator ? *json_accumulator : local_accumulator;

    while (true) {
        print_experiments_menu(prompt_stream);

        auto choice_opt = read_experiment_choice(in, prompt_stream);
        if (!choice_opt.has_value()) {
            if (format == OutputFormat::Json && !json_accumulator) {
                out << reporting::JsonValue::array(std::move(target_accumulator)).serialize(true) << "\n";
            }
            return false;
        }

        ExperimentChoice choice = choice_opt.value();
        if (choice == ExperimentChoice::ReturnToMainMenu) {
            if (format == OutputFormat::Json && !json_accumulator) {
                out << reporting::JsonValue::array(std::move(target_accumulator)).serialize(true) << "\n";
            }
            return true;
        }

        switch (choice) {
            case ExperimentChoice::ProcessCreation: {
                auto result = experiments::run_process_experiment();
                if (format == OutputFormat::Json) {
                    target_accumulator.push_back(reporting::to_json(result));
                } else {
                    out << "\n[Linux/POSIX Process Creation Experiment]\n";
                    display_process_experiment_result(out, result, format);
                    out << "\n";
                }
                break;
            }
            case ExperimentChoice::ThreadCreation: {
                auto result = experiments::run_thread_experiment();
                if (format == OutputFormat::Json) {
                    target_accumulator.push_back(reporting::to_json(result));
                } else {
                    out << "\n[Linux/POSIX Thread Creation Experiment]\n";
                    display_thread_experiment_result(out, result, format);
                    out << "\n";
                }
                break;
            }
            case ExperimentChoice::ThreadSynchronization: {
                auto result = experiments::run_synchronization_experiment();
                if (format == OutputFormat::Json) {
                    target_accumulator.push_back(reporting::to_json(result));
                } else {
                    out << "\n[Linux/POSIX Thread Synchronization Experiment]\n";
                    display_synchronization_experiment_result(out, result, format);
                    out << "\n";
                }
                break;
            }
            case ExperimentChoice::PipeIpc: {
                auto result = experiments::run_pipe_ipc_experiment();
                if (format == OutputFormat::Json) {
                    target_accumulator.push_back(reporting::to_json(result));
                } else {
                    out << "\n[Linux/POSIX Pipe-based IPC Experiment]\n";
                    display_pipe_ipc_experiment_result(out, result, format);
                    out << "\n";
                }
                break;
            }
            case ExperimentChoice::ReturnToMainMenu:
                return true;
        }
    }
}

int run_cli(std::istream& in, std::ostream& out, OutputFormat format) {
    std::ostream& prompt_stream = (format == OutputFormat::Json) ? std::cerr : out;
    std::vector<reporting::JsonValue> json_results;

    auto finalize_json = [&]() {
        if (format == OutputFormat::Json) {
            out << reporting::JsonValue::array(std::move(json_results)).serialize(true) << "\n";
        }
    };

    while (true) {
        print_main_menu(prompt_stream);

        auto choice_opt = read_menu_choice(in, prompt_stream);
        if (!choice_opt.has_value()) {
            if (format == OutputFormat::HumanReadable) {
                out << "\nEnd of input reached. Exiting OScope.\n";
            } else {
                finalize_json();
            }
            return 0;
        }

        AlgorithmChoice choice = choice_opt.value();
        if (choice == AlgorithmChoice::Exit) {
            if (format == OutputFormat::HumanReadable) {
                out << "\nExiting OScope. Goodbye!\n";
            } else {
                finalize_json();
            }
            return 0;
        }

        if (choice == AlgorithmChoice::Paging) {
            if (!run_paging_cli(in, prompt_stream)) {
                if (format == OutputFormat::HumanReadable) {
                    out << "\nEnd of input reached. Exiting OScope.\n";
                } else {
                    finalize_json();
                }
                return 0;
            }
            continue;
        }

        if (choice == AlgorithmChoice::MemoryAllocation) {
            if (!run_memory_cli(in, prompt_stream)) {
                if (format == OutputFormat::HumanReadable) {
                    out << "\nEnd of input reached. Exiting OScope.\n";
                } else {
                    finalize_json();
                }
                return 0;
            }
            continue;
        }

        if (choice == AlgorithmChoice::LinuxExperiments) {
            if (!run_experiments_cli(in, out, format, &json_results)) {
                if (format == OutputFormat::HumanReadable) {
                    out << "\nEnd of input reached. Exiting OScope.\n";
                } else {
                    finalize_json();
                }
                return 0;
            }
            continue;
        }

        if (choice == AlgorithmChoice::Deadlock) {
            if (!run_deadlock_cli(in, out, format, &json_results)) {
                if (format == OutputFormat::HumanReadable) {
                    out << "\nEnd of input reached. Exiting OScope.\n";
                } else {
                    finalize_json();
                }
                return 0;
            }
            continue;
        }

        if (choice == AlgorithmChoice::DiskScheduling) {
            if (!run_disk_cli(in, out, format, &json_results)) {
                if (format == OutputFormat::HumanReadable) {
                    out << "\nEnd of input reached. Exiting OScope.\n";
                } else {
                    finalize_json();
                }
                return 0;
            }
            continue;
        }

        // Algorithm-specific configuration
        int rr_quantum = 0;
        if (choice == AlgorithmChoice::RoundRobin || choice == AlgorithmChoice::CompareAll) {
            out << "\n[Round Robin Configuration]\n";
            if (!read_positive_int(in, out, "Enter time quantum: ", rr_quantum)) {
                out << "\nEnd of input reached. Exiting OScope.\n";
                return 0;
            }
        }

        int mlfq_q0 = 0;
        int mlfq_q1 = 0;
        int mlfq_q2 = 0;
        if (choice == AlgorithmChoice::MLFQ || choice == AlgorithmChoice::CompareAll) {
            out << "\n[MLFQ Configuration]\n";
            if (!read_positive_int(in, out, "Enter time quantum for Queue 0 (Q0): ", mlfq_q0) ||
                !read_positive_int(in, out, "Enter time quantum for Queue 1 (Q1): ", mlfq_q1) ||
                !read_positive_int(in, out, "Enter time quantum for Queue 2 (Q2): ", mlfq_q2)) {
                out << "\nEnd of input reached. Exiting OScope.\n";
                return 0;
            }
        }

        // Process input
        auto processes_opt = read_processes(in, out, choice);
        if (!processes_opt.has_value()) {
            out << "\nEnd of input reached. Exiting OScope.\n";
            return 0;
        }

        const auto& processes = processes_opt.value();

        if (choice == AlgorithmChoice::CompareAll) {
            try {
                std::string rr_name = "Round Robin (q=" + std::to_string(rr_quantum) + ")";
                std::string mlfq_name = "MLFQ (q0=" + std::to_string(mlfq_q0) +
                                        ", q1=" + std::to_string(mlfq_q1) +
                                        ", q2=" + std::to_string(mlfq_q2) + ")";

                std::vector<std::pair<std::string, std::shared_ptr<SchedulingAlgorithm>>> algorithms = {
                    {"FCFS", std::make_shared<FCFS>()},
                    {"SJF", std::make_shared<SJF>()},
                    {"SRTF", std::make_shared<SRTF>()},
                    {"Priority", std::make_shared<Priority>()},
                    {rr_name, std::make_shared<RoundRobin>(rr_quantum)},
                    {mlfq_name, std::make_shared<MLFQ>(mlfq_q0, mlfq_q1, mlfq_q2)}
                };

                auto comparison_entries = SchedulingComparator::compare(processes, algorithms);
                out << "\nComparison completed successfully across "
                    << comparison_entries.size() << " algorithm(s).\n";
                display_comparison_table(out, comparison_entries);
                out << "\n";
            } catch (const std::exception& e) {
                out << "\nComparison failed with error: " << e.what() << "\n\n";
            }
            continue;
        }

        // Instantiate selected algorithm
        std::unique_ptr<SchedulingAlgorithm> algorithm;
        switch (choice) {
            case AlgorithmChoice::FCFS:
                algorithm = std::make_unique<FCFS>();
                break;
            case AlgorithmChoice::SJF:
                algorithm = std::make_unique<SJF>();
                break;
            case AlgorithmChoice::SRTF:
                algorithm = std::make_unique<SRTF>();
                break;
            case AlgorithmChoice::Priority:
                algorithm = std::make_unique<Priority>();
                break;
            case AlgorithmChoice::RoundRobin:
                algorithm = std::make_unique<RoundRobin>(rr_quantum);
                break;
            case AlgorithmChoice::MLFQ:
                algorithm = std::make_unique<MLFQ>(mlfq_q0, mlfq_q1, mlfq_q2);
                break;
            case AlgorithmChoice::CompareAll:
            case AlgorithmChoice::Paging:
            case AlgorithmChoice::Exit:
                return 0;
        }

        try {
            SchedulingSimulationResult result = algorithm->schedule(processes);
            out << "\nSimulation completed successfully.\n";
            out << "Scheduled " << result.process_results.size() << " process(es) across "
                << result.timeline.size() << " timeline execution segment(s).\n";
            display_simulation_results(out, processes, result);
            out << "\n";
        } catch (const std::exception& e) {
            out << "\nSimulation failed with error: " << e.what() << "\n\n";
        }
    }
}

void display_execution_timeline(std::ostream& out, const SchedulingSimulationResult& result) {
    out << "\n=== Execution Timeline ===\n";
    if (result.timeline.empty()) {
        out << "No execution segments recorded (timeline is empty).\n";
        return;
    }

    int first_start = result.timeline.front().start_time;
    int final_end = result.timeline.back().end_time;
    out << "Total Simulation Interval: [" << first_start << " -> " << final_end
        << "] (Duration: " << (final_end - first_start) << ")\n\n";

    out << "Gantt Chart:\n";
    for (std::size_t i = 0; i < result.timeline.size(); ++i) {
        const auto& seg = result.timeline[i];
        if (i > 0 && seg.start_time > result.timeline[i - 1].end_time) {
            out << "| [IDLE " << result.timeline[i - 1].end_time << "-" << seg.start_time << "] ";
        }
        out << "| [P" << seg.pid << " " << seg.start_time << "-" << seg.end_time << "] ";
    }
    out << "|\n\n";

    out << "Execution Segments:\n";
    for (std::size_t i = 0; i < result.timeline.size(); ++i) {
        const auto& seg = result.timeline[i];
        if (i > 0 && seg.start_time > result.timeline[i - 1].end_time) {
            out << "  [" << result.timeline[i - 1].end_time << " -> " << seg.start_time
                << "] IDLE (CPU Idle)\n";
        }
        out << "  [" << seg.start_time << " -> " << seg.end_time
            << "] Process PID " << seg.pid << "\n";
    }
}

void display_process_metrics_table(std::ostream& out, const std::vector<Process>& processes, const SchedulingSimulationResult& result) {
    out << "\n=== Process Metrics Table ===\n";
    if (result.process_results.empty()) {
        out << "No process metrics available (simulation result is empty).\n";
        return;
    }

    std::unordered_map<int, const Process*> process_map;
    for (const auto& proc : processes) {
        process_map[proc.pid] = &proc;
    }

    const auto orig_flags = out.flags();

    out << std::right
        << std::setw(6) << "PID"
        << std::setw(10) << "Arrival"
        << std::setw(10) << "Burst"
        << std::setw(13) << "Completion"
        << std::setw(13) << "Turnaround"
        << std::setw(11) << "Waiting"
        << std::setw(11) << "Response"
        << "\n";
    out << std::string(74, '-') << "\n";

    for (const auto& pr : result.process_results) {
        auto it = process_map.find(pr.pid);
        const bool found = (it != process_map.end());

        out << std::setw(6) << pr.pid;
        if (found) {
            out << std::setw(10) << it->second->arrival_time
                << std::setw(10) << it->second->burst_time;
        } else {
            out << std::setw(10) << "N/A"
                << std::setw(10) << "N/A";
        }
        out << std::setw(13) << pr.completion_time
            << std::setw(13) << pr.turnaround_time
            << std::setw(11) << pr.waiting_time
            << std::setw(11) << pr.response_time
            << "\n";
    }

    out.flags(orig_flags);
}

void display_average_metrics(std::ostream& out, const SchedulingSimulationResult& result) {
    out << "\n=== Average Metrics ===\n";
    if (result.process_results.empty()) {
        out << "No process metrics available to calculate averages (simulation result is empty).\n";
        return;
    }

    SchedulingMetrics metrics = calculate_metrics(result);

    const auto orig_flags = out.flags();
    const auto orig_prec = out.precision();

    out << std::fixed << std::setprecision(2);
    out << "Average Waiting Time:    " << metrics.average_waiting_time << "\n"
        << "Average Turnaround Time: " << metrics.average_turnaround_time << "\n"
        << "Average Response Time:   " << metrics.average_response_time << "\n";

    out.flags(orig_flags);
    out.precision(orig_prec);
}

void display_simulation_results(std::ostream& out, const std::vector<Process>& processes, const SchedulingSimulationResult& result) {
    display_execution_timeline(out, result);
    display_process_metrics_table(out, processes, result);
    display_average_metrics(out, result);
}

void display_comparison_table(std::ostream& out, const std::vector<SchedulingComparisonEntry>& entries) {
    out << "\n=== Scheduling Algorithm Comparison ===\n";
    if (entries.empty()) {
        out << "No comparison results available (empty comparison entries).\n";
        return;
    }

    bool all_empty = true;
    for (const auto& entry : entries) {
        if (!entry.simulation_result.process_results.empty()) {
            all_empty = false;
            break;
        }
    }
    if (all_empty) {
        out << "No process metrics available to calculate averages (simulation result is empty).\n";
        return;
    }

    const auto orig_flags = out.flags();
    const auto orig_prec = out.precision();

    out << std::left << std::setw(26) << "Algorithm"
        << std::right
        << std::setw(14) << "Avg Waiting"
        << std::setw(16) << "Avg Turnaround"
        << std::setw(14) << "Avg Response"
        << "\n";
    out << std::string(70, '-') << "\n";

    out << std::fixed << std::setprecision(2);
    for (const auto& entry : entries) {
        out << std::left << std::setw(26) << entry.algorithm_name
            << std::right
            << std::setw(14) << entry.average_waiting_time()
            << std::setw(16) << entry.average_turnaround_time()
            << std::setw(14) << entry.average_response_time()
            << "\n";
    }

    out.flags(orig_flags);
    out.precision(orig_prec);
}

void display_paging_steps(std::ostream& out, const PageReplacementResult& result, int frame_count) {
    (void)frame_count;
    out << "\n=== Page Replacement Step-by-Step Execution ===\n";
    if (result.steps.empty()) {
        out << "No page references recorded (reference string is empty).\n";
        return;
    }

    const auto orig_flags = out.flags();

    out << std::right
        << std::setw(6) << "Step"
        << std::setw(8) << "Page"
        << std::setw(10) << "Result"
        << std::setw(11) << "Evicted"
        << "  " << "Frames"
        << "\n";
    out << std::string(55, '-') << "\n";

    for (std::size_t i = 0; i < result.steps.size(); ++i) {
        const auto& step = result.steps[i];
        out << std::setw(6) << (i + 1)
            << std::setw(8) << step.page
            << std::setw(10) << (step.is_fault ? "Fault" : "Hit");
        if (step.evicted_page.has_value()) {
            out << std::setw(11) << *step.evicted_page;
        } else {
            out << std::setw(11) << "None";
        }
        out << "  [";
        for (std::size_t f = 0; f < step.frames.size(); ++f) {
            if (f > 0) out << ", ";
            if (step.frames[f] == -1) {
                out << "-1";
            } else {
                out << step.frames[f];
            }
        }
        out << "]\n";
    }

    out.flags(orig_flags);
}

void display_paging_metrics(std::ostream& out, const PageReplacementResult& result) {
    out << "\n=== Page Replacement Metrics ===\n";
    const auto orig_flags = out.flags();
    const auto orig_prec = out.precision();

    out << std::fixed << std::setprecision(2);
    out << "Total Page References: " << result.total_references << "\n"
        << "Page Faults:           " << result.page_faults << "\n"
        << "Page Hits:             " << result.page_hits << "\n"
        << "Page-Fault Rate:       " << (result.fault_rate * 100.0) << "% (" << result.fault_rate << ")\n"
        << "Page-Hit Rate:         " << (result.hit_rate * 100.0) << "% (" << result.hit_rate << ")\n";

    out.flags(orig_flags);
    out.precision(orig_prec);
}

void display_paging_simulation_results(std::ostream& out, const PageReplacementResult& result, int frame_count) {
    display_paging_steps(out, result, frame_count);
    display_paging_metrics(out, result);
}

void display_paging_comparison_table(std::ostream& out, const PageReplacementComparisonResult& result) {
    out << "\n=== Page Replacement Algorithm Comparison ===\n";
    if (result.empty()) {
        out << "No comparison results available (empty comparison entries).\n";
        return;
    }

    out << "Frame Count: " << result.frame_count
        << " | Total References: " << result.reference_string.size() << "\n\n";

    const auto orig_flags = out.flags();
    const auto orig_prec = out.precision();

    out << std::left << std::setw(14) << "Algorithm"
        << std::right
        << std::setw(14) << "References"
        << std::setw(10) << "Faults"
        << std::setw(8) << "Hits"
        << std::setw(15) << "Fault Rate"
        << std::setw(15) << "Hit Rate"
        << "\n";
    out << std::string(76, '-') << "\n";

    out << std::fixed << std::setprecision(2);
    for (const auto& entry : result.entries) {
        out << std::left << std::setw(14) << entry.algorithm_name
            << std::right
            << std::setw(14) << entry.total_references()
            << std::setw(10) << entry.page_faults()
            << std::setw(8) << entry.page_hits()
            << std::setw(14) << (entry.fault_rate() * 100.0) << "%"
            << std::setw(14) << (entry.hit_rate() * 100.0) << "%"
            << "\n";
    }

    out.flags(orig_flags);
    out.precision(orig_prec);
}

void display_memory_blocks(std::ostream& out, const std::vector<MemoryBlock>& blocks) {
    out << "\n=== Memory Block Layout ===\n";
    if (blocks.empty()) {
        out << "No memory blocks available.\n";
        return;
    }

    const auto orig_flags = out.flags();

    out << std::left << std::setw(8) << "Block"
        << std::setw(16) << "Start Address"
        << std::setw(12) << "Size (B)"
        << std::setw(12) << "Status"
        << std::setw(12) << "Alloc ID"
        << std::setw(10) << "PID"
        << "\n";
    out << std::string(70, '-') << "\n";

    for (std::size_t i = 0; i < blocks.size(); ++i) {
        const auto& block = blocks[i];
        out << std::left << std::setw(8) << (i + 1)
            << std::setw(16) << block.start_address
            << std::setw(12) << block.size
            << std::setw(12) << (block.is_allocated ? "Allocated" : "Free");

        if (block.allocation_id.has_value()) {
            out << std::setw(12) << block.allocation_id.value();
        } else {
            out << std::setw(12) << "-";
        }

        if (block.process_id.has_value()) {
            out << std::setw(10) << block.process_id.value();
        } else {
            out << std::setw(10) << "-";
        }

        out << "\n";
    }

    out.flags(orig_flags);
}

void display_memory_metrics(std::ostream& out, const MemoryMetrics& metrics) {
    out << "\n=== Memory Allocation Metrics ===\n";
    const auto orig_flags = out.flags();
    const auto orig_prec = out.precision();

    out << std::fixed << std::setprecision(2);
    out << "Total Memory:           " << metrics.total_memory << " bytes\n"
        << "Allocated Memory:       " << metrics.allocated_memory << " bytes\n"
        << "Free Memory:            " << metrics.free_memory << " bytes\n"
        << "Largest Free Block:     " << metrics.largest_free_block << " bytes\n"
        << "External Fragmentation: " << (metrics.external_fragmentation * 100.0) << "% ("
        << metrics.external_fragmentation << ")\n";

    out.flags(orig_flags);
    out.precision(orig_prec);
}

void display_memory_comparison_table(std::ostream& out, const MemoryComparisonResult& result) {
    out << "\n=== Memory Allocation Strategy Comparison ===\n";
    if (result.empty()) {
        out << "No comparison results available (empty comparison entries).\n";
        return;
    }

    out << "Total Memory: " << result.total_memory << " bytes"
        << " | Total Workload Operations: " << result.workload.size() << "\n\n";

    const auto orig_flags = out.flags();
    const auto orig_prec = out.precision();

    out << std::left << std::setw(12) << "Strategy"
        << std::right
        << std::setw(10) << "Attempts"
        << std::setw(10) << "Success"
        << std::setw(10) << "Failures"
        << std::setw(14) << "Success Rate"
        << std::setw(14) << "Allocated (B)"
        << std::setw(12) << "Free (B)"
        << std::setw(14) << "Largest Free"
        << std::setw(12) << "Ext Frag"
        << "\n";
    out << std::string(98, '-') << "\n";

    out << std::fixed << std::setprecision(2);
    for (const auto& entry : result.entries) {
        out << std::left << std::setw(12) << entry.strategy_name
            << std::right
            << std::setw(10) << entry.allocation_requests_attempted
            << std::setw(10) << entry.successful_allocations
            << std::setw(10) << entry.failed_allocations
            << std::setw(13) << (entry.allocation_success_rate * 100.0) << "%"
            << std::setw(14) << entry.final_allocated_memory()
            << std::setw(12) << entry.final_free_memory()
            << std::setw(14) << entry.final_largest_free_block()
            << std::setw(11) << (entry.final_external_fragmentation() * 100.0) << "%"
            << "\n";
    }

    out.flags(orig_flags);
    out.precision(orig_prec);
}

void display_process_experiment_result(
    std::ostream& out,
    const experiments::ProcessExperimentResult& result,
    OutputFormat format) {
    if (format == OutputFormat::Json) {
        out << reporting::serialize_result(result, true) << "\n";
        return;
    }

    out << "=== Process Creation Experiment Result ===\n";
    out << "Status:                 " << (result.is_success() ? "SUCCESS" : "FAILURE") << "\n";
    out << "Parent PID:             " << result.parent_pid << "\n";
    if (result.child_pid > 0) {
        out << "Child PID:              " << result.child_pid << "\n";
    } else {
        out << "Child PID:              N/A\n";
    }
    if (result.exited_normally) {
        out << "Child Termination:      Normal exit (code " << result.exit_code << ")\n";
    } else if (result.termination_signal >= 0) {
        out << "Child Termination:      Killed by signal " << result.termination_signal << "\n";
    } else {
        out << "Child Termination:      Not available / failed to reap\n";
    }
    out << "Details:                " << result.message << "\n";
}

void display_thread_experiment_result(
    std::ostream& out,
    const experiments::ThreadExperimentResult& result,
    OutputFormat format) {
    if (format == OutputFormat::Json) {
        out << reporting::serialize_result(result, true) << "\n";
        return;
    }

    out << "=== Thread Creation Experiment Result ===\n";
    out << "Status:                 " << (result.success ? "SUCCESS" : "FAILURE") << "\n";
    out << "Requested Threads:      " << result.requested_threads << "\n";
    out << "Started Threads:        " << result.started_threads << "\n";
    out << "Completed Threads:      " << result.completed_threads << "\n";
    out << "Worker Outputs:         [";
    for (std::size_t i = 0; i < result.worker_results.size(); ++i) {
        if (i > 0) out << ", ";
        out << "Thread " << (i + 1) << " => " << result.worker_results[i];
    }
    out << "]\n";
    if (!result.error_message.empty()) {
        out << "Error:                  " << result.error_message << "\n";
    }
}

void display_synchronization_experiment_result(
    std::ostream& out,
    const experiments::SynchronizationExperimentResult& result,
    OutputFormat format) {
    if (format == OutputFormat::Json) {
        out << reporting::serialize_result(result, true) << "\n";
        return;
    }

    out << "=== Thread Synchronization Experiment Result ===\n";
    out << "Status:                 " << (result.success ? "SUCCESS" : "FAILURE") << "\n";
    out << "Concurrent Threads:     " << result.num_threads << "\n";
    out << "Iterations Per Thread:  " << result.iterations_per_thread << "\n";
    out << "Completed Threads:      " << result.threads_completed << "\n";
    out << "Expected Counter:       " << result.expected_counter << "\n";
    out << "Actual Counter:         " << result.actual_counter << "\n";
    if (result.success) {
        out << "Synchronization Check:  PASSED (Counter exact match, no data race detected)\n";
    } else {
        out << "Synchronization Check:  FAILED (" << result.error_message << ")\n";
    }
}

void display_pipe_ipc_experiment_result(
    std::ostream& out,
    const experiments::PipeIpcExperimentResult& result,
    OutputFormat format) {
    if (format == OutputFormat::Json) {
        out << reporting::serialize_result(result, true) << "\n";
        return;
    }

    out << "=== Pipe-based IPC Experiment Result ===\n";
    out << "Status:                 " << (result.is_success() ? "SUCCESS" : "FAILURE") << "\n";
    out << "Direction:              Child -> Parent (POSIX pipe)\n";
    out << "Parent PID:             " << result.parent_pid << "\n";
    if (result.child_pid > 0) {
        out << "Child PID:              " << result.child_pid << "\n";
    } else {
        out << "Child PID:              N/A\n";
    }
    if (result.child_exited_normally) {
        out << "Child Exit Code:        " << result.child_exit_code << "\n";
    } else if (result.child_termination_signal >= 0) {
        out << "Child Termination:      Signal " << result.child_termination_signal << "\n";
    }
    out << "Sent Message:           \"" << result.sent_message << "\"\n";
    out << "Received Message:       \"" << result.received_message << "\"\n";
    if (!result.error_message.empty()) {
        out << "Error:                  " << result.error_message << "\n";
    }
}

// ============================================================================
// Deadlock Management CLI Implementation
// ============================================================================

void print_deadlock_menu(std::ostream& out) {
    out << "\n========================================\n"
        << "          Deadlock Management           \n"
        << "========================================\n"
        << "1. Banker's Safety Algorithm\n"
        << "2. Simulate Resource Request\n"
        << "3. Deadlock Detection\n"
        << "4. Return to Main Menu\n"
        << "========================================\n";
}

std::optional<DeadlockChoice> read_deadlock_choice(std::istream& in, std::ostream& out) {
    int choice_val = 0;
    while (true) {
        if (!read_int(in, out, "Enter your choice (1-4): ", choice_val)) {
            return std::nullopt;
        }
        if (choice_val < 1 || choice_val > 4) {
            out << "Error: Choice must be between 1 and 4.\n";
            continue;
        }
        return static_cast<DeadlockChoice>(choice_val);
    }
}

namespace {

bool read_resource_vector(std::istream& in, std::ostream& out, const std::string& label, int m, std::vector<int>& vec) {
    vec.assign(m, 0);
    out << label << " (" << m << " space-separated integers): ";
    std::string line;
    while (std::getline(in, line)) {
        if (line.empty() || line.find_first_not_of(" \t\r\n") == std::string::npos) {
            continue;
        }
        std::istringstream iss(line);
        bool ok = true;
        for (int j = 0; j < m; ++j) {
            int val;
            if (!(iss >> val) || val < 0) {
                ok = false;
                break;
            }
            vec[j] = val;
        }
        if (!ok) {
            out << "Error: Enter exactly " << m << " non-negative integers: ";
            continue;
        }
        return true;
    }
    return false;
}

bool read_resource_matrix(std::istream& in, std::ostream& out, const std::string& matrix_name, int n, int m, std::vector<std::vector<int>>& mat) {
    mat.assign(n, std::vector<int>(m, 0));
    out << "Enter " << matrix_name << " matrix (" << n << " rows of " << m << " integers):\n";
    for (int i = 0; i < n; ++i) {
        std::ostringstream prompt;
        prompt << "  P" << i;
        if (!read_resource_vector(in, out, prompt.str(), m, mat[i])) {
            return false;
        }
    }
    return true;
}

std::optional<deadlock::DeadlockState> read_deadlock_state(std::istream& in, std::ostream& out) {
    deadlock::DeadlockState state;
    if (!read_positive_int(in, out, "Enter number of processes: ", state.num_processes)) {
        return std::nullopt;
    }
    if (!read_positive_int(in, out, "Enter number of resource types: ", state.num_resources)) {
        return std::nullopt;
    }
    if (!read_resource_vector(in, out, "Enter Available resources", state.num_resources, state.available)) {
        return std::nullopt;
    }
    if (!read_resource_matrix(in, out, "Allocation", state.num_processes, state.num_resources, state.allocation)) {
        return std::nullopt;
    }
    while (true) {
        if (!read_resource_matrix(in, out, "Max claim", state.num_processes, state.num_resources, state.max)) {
            return std::nullopt;
        }
        std::string err;
        state.compute_need();
        if (!state.validate(&err)) {
            out << "Validation error: " << err << "\nPlease re-enter the Max matrix.\n";
            continue;
        }
        break;
    }
    return state;
}

} // namespace

void display_safety_result(std::ostream& out, const deadlock::SafetyResult& result, const deadlock::DeadlockState& state) {
    out << "\n=== Banker's Safety Analysis ===\n";
    out << "System State:           " << (result.is_safe ? "SAFE" : "UNSAFE") << "\n";
    out << "Analysis:               " << result.message << "\n";
    if (result.is_safe) {
        out << "Safe Execution Sequence:";
        for (size_t i = 0; i < result.safe_sequence.size(); ++i) {
            out << " P" << result.safe_sequence[i];
            if (i + 1 < result.safe_sequence.size()) out << " ->";
        }
        out << "\n";
    } else {
        out << "Blocked Processes:     ";
        for (size_t i = 0; i < result.blocked_processes.size(); ++i) {
            if (i > 0) out << ", ";
            out << "P" << result.blocked_processes[i];
        }
        out << "\n";
        out << "Note: An unsafe state means the system cannot guarantee that all processes can finish\n"
            << "under maximum claims; it does not necessarily mean a deadlock exists at this instant.\n";
    }

    // Tabular display of state
    out << "\nResource Matrices Summary:\n";
    out << std::left << std::setw(8) << "Process"
        << std::setw(16) << "Allocation"
        << std::setw(16) << "Max Claim"
        << std::setw(16) << "Need\n";
    out << "--------------------------------------------------------\n";
    for (int i = 0; i < state.num_processes; ++i) {
        std::ostringstream alloc_ss, max_ss, need_ss;
        for (int j = 0; j < state.num_resources; ++j) {
            alloc_ss << state.allocation[i][j] << " ";
            max_ss << state.max[i][j] << " ";
            int need_val = (i < static_cast<int>(state.need.size()) && j < static_cast<int>(state.need[i].size()))
                               ? state.need[i][j]
                               : (state.max[i][j] - state.allocation[i][j]);
            need_ss << need_val << " ";
        }
        out << "P" << std::left << std::setw(7) << i
            << std::setw(16) << alloc_ss.str()
            << std::setw(16) << max_ss.str()
            << std::setw(16) << need_ss.str() << "\n";
    }
    out << "\nAvailable Resources:    ";
    for (int j = 0; j < state.num_resources; ++j) {
        out << state.available[j] << " ";
    }
    out << "\n";
}

void display_resource_request_result(std::ostream& out, const deadlock::ResourceRequestResult& result) {
    out << "\n=== Resource Request Simulation ===\n";
    out << "Requesting Process:     P" << result.process_id << "\n";
    out << "Requested Resources:    [";
    for (size_t i = 0; i < result.request.size(); ++i) {
        if (i > 0) out << ", ";
        out << result.request[i];
    }
    out << "]\n";
    out << "Allocation Decision:    " << (result.granted ? "GRANTED" : "DENIED") << "\n";
    out << "Reason:                 " << result.message << "\n";
    if (result.granted) {
        out << "Resulting Safe Sequence:";
        for (size_t i = 0; i < result.safe_sequence.size(); ++i) {
            out << " P" << result.safe_sequence[i];
            if (i + 1 < result.safe_sequence.size()) out << " ->";
        }
        out << "\n";
    } else {
        out << "Original system state has been preserved uncorrupted.\n";
    }
}

void display_deadlock_detection_result(std::ostream& out, const deadlock::DetectionResult& result) {
    out << "\n=== Deadlock Detection Analysis ===\n";
    out << "Detection Result:       " << (result.is_deadlocked ? "DEADLOCK DETECTED" : "NO DEADLOCK") << "\n";
    out << "Diagnostic Message:     " << result.message << "\n";
    if (result.is_deadlocked) {
        out << "Deadlocked Processes:   ";
        for (size_t i = 0; i < result.deadlocked_processes.size(); ++i) {
            if (i > 0) out << ", ";
            out << "P" << result.deadlocked_processes[i];
        }
        out << "\n";
    } else {
        out << "Execution Status:       All active processes can acquire pending resources and finish.\n";
    }
}

bool run_deadlock_cli(
    std::istream& in,
    std::ostream& out,
    OutputFormat format,
    std::vector<reporting::JsonValue>* json_accumulator) {

    std::ostream& prompt_stream = (format == OutputFormat::Json) ? std::cerr : out;
    std::vector<reporting::JsonValue> local_accumulator;
    std::vector<reporting::JsonValue>& target_accumulator =
        json_accumulator ? *json_accumulator : local_accumulator;

    while (true) {
        print_deadlock_menu(prompt_stream);
        auto choice_opt = read_deadlock_choice(in, prompt_stream);
        if (!choice_opt.has_value()) {
            if (format == OutputFormat::Json && !json_accumulator) {
                out << reporting::JsonValue::array(std::move(target_accumulator)).serialize(true) << "\n";
            }
            return false;
        }

        DeadlockChoice choice = choice_opt.value();
        if (choice == DeadlockChoice::ReturnToMainMenu) {
            if (format == OutputFormat::Json && !json_accumulator) {
                out << reporting::JsonValue::array(std::move(target_accumulator)).serialize(true) << "\n";
            }
            return true;
        }

        switch (choice) {
            case DeadlockChoice::SafetyAnalysis: {
                auto state_opt = read_deadlock_state(in, prompt_stream);
                if (!state_opt.has_value()) {
                    return false;
                }
                auto res = deadlock::check_safety(state_opt.value());
                if (format == OutputFormat::Json) {
                    target_accumulator.push_back(reporting::to_json(res, state_opt.value()));
                } else {
                    display_safety_result(out, res, state_opt.value());
                }
                break;
            }
            case DeadlockChoice::ResourceRequest: {
                auto state_opt = read_deadlock_state(in, prompt_stream);
                if (!state_opt.has_value()) {
                    return false;
                }
                int proc_id = 0;
                while (true) {
                    if (!read_int(in, prompt_stream, "Enter requesting process ID (e.g. 0): ", proc_id)) {
                        return false;
                    }
                    if (proc_id < 0 || proc_id >= state_opt.value().num_processes) {
                        prompt_stream << "Error: Process ID must be between 0 and "
                                      << (state_opt.value().num_processes - 1) << ".\n";
                        continue;
                    }
                    break;
                }
                std::vector<int> req;
                if (!read_resource_vector(in, prompt_stream, "Enter requested resources", state_opt.value().num_resources, req)) {
                    return false;
                }
                auto res = deadlock::request_resources(state_opt.value(), proc_id, req);
                if (format == OutputFormat::Json) {
                    target_accumulator.push_back(reporting::to_json(res));
                } else {
                    display_resource_request_result(out, res);
                }
                break;
            }
            case DeadlockChoice::DeadlockDetection: {
                int num_p = 0;
                int num_r = 0;
                if (!read_positive_int(in, prompt_stream, "Enter number of processes: ", num_p) ||
                    !read_positive_int(in, prompt_stream, "Enter number of resource types: ", num_r)) {
                    return false;
                }
                std::vector<int> avail;
                if (!read_resource_vector(in, prompt_stream, "Enter Available resources", num_r, avail)) {
                    return false;
                }
                std::vector<std::vector<int>> alloc, req_mat;
                if (!read_resource_matrix(in, prompt_stream, "Allocation", num_p, num_r, alloc) ||
                    !read_resource_matrix(in, prompt_stream, "Request", num_p, num_r, req_mat)) {
                    return false;
                }
                auto res = deadlock::detect_deadlock(num_p, num_r, avail, alloc, req_mat);
                if (format == OutputFormat::Json) {
                    target_accumulator.push_back(reporting::to_json(res));
                } else {
                    display_deadlock_detection_result(out, res);
                }
                break;
            }
            case DeadlockChoice::ReturnToMainMenu:
                return true;
        }
    }
}

// ============================================================================
// Disk Scheduling CLI Implementation
// ============================================================================

void print_disk_menu(std::ostream& out) {
    out << "\n========================================\n"
        << "            Disk Scheduling             \n"
        << "========================================\n"
        << "1. First-Come, First-Served (FCFS)\n"
        << "2. Shortest Seek Time First (SSTF)\n"
        << "3. SCAN (Elevator)\n"
        << "4. Circular SCAN (C-SCAN)\n"
        << "5. LOOK\n"
        << "6. Circular LOOK (C-LOOK)\n"
        << "7. Compare all disk algorithms\n"
        << "8. Return to Main Menu\n"
        << "========================================\n";
}

std::optional<DiskChoice> read_disk_choice(std::istream& in, std::ostream& out) {
    int choice_val = 0;
    while (true) {
        if (!read_int(in, out, "Enter your choice (1-8): ", choice_val)) {
            return std::nullopt;
        }
        if (choice_val < 1 || choice_val > 8) {
            out << "Error: Choice must be between 1 and 8.\n";
            continue;
        }
        return static_cast<DiskChoice>(choice_val);
    }
}

namespace {

std::optional<disk::DiskConfig> read_disk_config(std::istream& in, std::ostream& out, bool needs_direction) {
    disk::DiskConfig config;
    if (!read_non_negative_int(in, out, "Enter minimum cylinder (default 0): ", config.min_cylinder)) {
        return std::nullopt;
    }
    while (true) {
        if (!read_positive_int(in, out, "Enter maximum cylinder (default 199): ", config.max_cylinder)) {
            return std::nullopt;
        }
        if (config.max_cylinder <= config.min_cylinder) {
            out << "Error: Maximum cylinder must be greater than minimum cylinder (" << config.min_cylinder << ").\n";
            continue;
        }
        break;
    }
    while (true) {
        if (!read_non_negative_int(in, out, "Enter initial head position: ", config.initial_head)) {
            return std::nullopt;
        }
        if (config.initial_head < config.min_cylinder || config.initial_head > config.max_cylinder) {
            out << "Error: Head position must be in range [" << config.min_cylinder << ", " << config.max_cylinder << "].\n";
            continue;
        }
        break;
    }
    if (needs_direction) {
        while (true) {
            int dir_val = 1;
            if (!read_int(in, out, "Enter initial direction (1 for Increasing/Up, 2 for Decreasing/Down): ", dir_val)) {
                return std::nullopt;
            }
            if (dir_val == 1) {
                config.direction = disk::Direction::Increasing;
                break;
            } else if (dir_val == 2) {
                config.direction = disk::Direction::Decreasing;
                break;
            }
            out << "Error: Direction must be 1 (Increasing) or 2 (Decreasing).\n";
        }
    }
    return config;
}

std::optional<std::vector<int>> read_disk_requests(std::istream& in, std::ostream& out, const disk::DiskConfig& config) {
    out << "Enter sequence of cylinder requests (e.g. 98 183 37 122 14 124 65 67): ";
    std::string line;
    while (std::getline(in, line)) {
        if (line.empty() || line.find_first_not_of(" \t\r\n") == std::string::npos) {
            return std::vector<int>();
        }
        std::istringstream iss(line);
        std::vector<int> reqs;
        int val;
        bool ok = true;
        while (iss >> val) {
            if (val < config.min_cylinder || val > config.max_cylinder) {
                out << "Error: Cylinder " << val << " is out of range ["
                    << config.min_cylinder << ", " << config.max_cylinder << "]. Re-enter line: ";
                ok = false;
                break;
            }
            reqs.push_back(val);
        }
        if (!ok) continue;
        return reqs;
    }
    return std::nullopt;
}

} // namespace

void display_disk_result(std::ostream& out, const disk::DiskSchedulingResult& result) {
    out << "\n=== Disk Scheduling Result: " << result.algorithm_name << " ===\n";
    out << "Serviced Requests:      [";
    for (size_t i = 0; i < result.serviced_requests.size(); ++i) {
        if (i > 0) out << ", ";
        out << result.serviced_requests[i];
    }
    out << "]\n";
    out << "Head Movement Path:     ";
    for (size_t i = 0; i < result.head_path.size(); ++i) {
        if (i > 0) out << " -> ";
        out << result.head_path[i];
    }
    out << "\n";
    out << "Total Head Movement:    " << result.total_head_movement << " cylinders\n";
    if (result.wraparound_movement > 0) {
        out << "  (Includes circular wraparound traversal: " << result.wraparound_movement << " cylinders)\n";
    }
    out << std::fixed << std::setprecision(2);
    out << "Average Head Movement:  " << result.average_head_movement << " cylinders/request\n";
    out << "Initial Head Position:  " << result.initial_head_position << "\n";
    out << "Final Head Position:    " << result.final_head_position << "\n";
    out << std::defaultfloat;
}

void display_disk_comparison_table(std::ostream& out, const disk::DiskComparisonResult& result) {
    out << "\n========================================================================================\n"
        << "                            Disk Scheduling Comparison                                  \n"
        << "========================================================================================\n";
    out << std::left << std::setw(32) << "Algorithm"
        << std::right << std::setw(22) << "Total Movement (cyl)"
        << std::right << std::setw(20) << "Avg Movement/Req"
        << std::right << std::setw(14) << "Final Head\n";
    out << "----------------------------------------------------------------------------------------\n";
    for (const auto& item : result.results) {
        out << std::left << std::setw(32) << item.algorithm_name
            << std::right << std::setw(22) << item.total_head_movement
            << std::right << std::fixed << std::setprecision(2) << std::setw(20) << item.average_head_movement
            << std::right << std::setw(14) << item.final_head_position << "\n";
    }
    out << "========================================================================================\n"
        << "Note: C-SCAN and C-LOOK include wraparound circular return seek distance in total movement.\n"
        << std::defaultfloat;
}

bool run_disk_cli(
    std::istream& in,
    std::ostream& out,
    OutputFormat format,
    std::vector<reporting::JsonValue>* json_accumulator) {

    std::ostream& prompt_stream = (format == OutputFormat::Json) ? std::cerr : out;
    std::vector<reporting::JsonValue> local_accumulator;
    std::vector<reporting::JsonValue>& target_accumulator =
        json_accumulator ? *json_accumulator : local_accumulator;

    while (true) {
        print_disk_menu(prompt_stream);
        auto choice_opt = read_disk_choice(in, prompt_stream);
        if (!choice_opt.has_value()) {
            if (format == OutputFormat::Json && !json_accumulator) {
                out << reporting::JsonValue::array(std::move(target_accumulator)).serialize(true) << "\n";
            }
            return false;
        }

        DiskChoice choice = choice_opt.value();
        if (choice == DiskChoice::ReturnToMainMenu) {
            if (format == OutputFormat::Json && !json_accumulator) {
                out << reporting::JsonValue::array(std::move(target_accumulator)).serialize(true) << "\n";
            }
            return true;
        }

        bool needs_dir = (choice != DiskChoice::FCFS && choice != DiskChoice::SSTF);
        auto config_opt = read_disk_config(in, prompt_stream, needs_dir);
        if (!config_opt.has_value()) {
            return false;
        }
        auto reqs_opt = read_disk_requests(in, prompt_stream, config_opt.value());
        if (!reqs_opt.has_value()) {
            return false;
        }

        if (choice == DiskChoice::CompareAll) {
            auto comp_result = disk::compare_all_disk(reqs_opt.value(), config_opt.value());
            if (format == OutputFormat::Json) {
                target_accumulator.push_back(reporting::to_json(comp_result));
            } else {
                display_disk_comparison_table(out, comp_result);
            }
        } else {
            disk::DiskAlgorithm algo;
            switch (choice) {
                case DiskChoice::FCFS: algo = disk::DiskAlgorithm::FCFS; break;
                case DiskChoice::SSTF: algo = disk::DiskAlgorithm::SSTF; break;
                case DiskChoice::SCAN: algo = disk::DiskAlgorithm::SCAN; break;
                case DiskChoice::CSCAN: algo = disk::DiskAlgorithm::CSCAN; break;
                case DiskChoice::LOOK: algo = disk::DiskAlgorithm::LOOK; break;
                case DiskChoice::CLOOK: algo = disk::DiskAlgorithm::CLOOK; break;
                default: algo = disk::DiskAlgorithm::FCFS; break;
            }
            auto res = disk::schedule_disk(algo, reqs_opt.value(), config_opt.value());
            if (format == OutputFormat::Json) {
                target_accumulator.push_back(reporting::to_json(res));
            } else {
                display_disk_result(out, res);
            }
        }
    }
}

} // namespace oscope
