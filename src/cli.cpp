#include "oscope/cli.hpp"

#include <iostream>
#include <limits>
#include <memory>
#include <string>
#include <unordered_set>
#include <vector>

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
        if (choice == AlgorithmChoice::Priority) {
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
        << "  CPU Scheduling Simulation Platform    \n"
        << "========================================\n"
        << "1. Run FCFS\n"
        << "2. Run SJF\n"
        << "3. Run SRTF\n"
        << "4. Run non-preemptive Priority\n"
        << "5. Run Round Robin\n"
        << "6. Run MLFQ\n"
        << "7. Exit\n"
        << "========================================\n";
}

std::optional<AlgorithmChoice> read_menu_choice(std::istream& in, std::ostream& out) {
    int choice_val = 0;
    while (true) {
        if (!read_int(in, out, "Enter your choice (1-7): ", choice_val)) {
            return std::nullopt;
        }
        if (choice_val < 1 || choice_val > 7) {
            out << "Error: Choice must be between 1 and 7.\n";
            continue;
        }
        return static_cast<AlgorithmChoice>(choice_val);
    }
}

int run_cli(std::istream& in, std::ostream& out) {
    while (true) {
        print_main_menu(out);

        auto choice_opt = read_menu_choice(in, out);
        if (!choice_opt.has_value()) {
            out << "\nEnd of input reached. Exiting OScope.\n";
            return 0;
        }

        AlgorithmChoice choice = choice_opt.value();
        if (choice == AlgorithmChoice::Exit) {
            out << "\nExiting OScope. Goodbye!\n";
            return 0;
        }

        // Algorithm-specific configuration
        int rr_quantum = 0;
        if (choice == AlgorithmChoice::RoundRobin) {
            out << "\n[Round Robin Configuration]\n";
            if (!read_positive_int(in, out, "Enter time quantum: ", rr_quantum)) {
                out << "\nEnd of input reached. Exiting OScope.\n";
                return 0;
            }
        }

        int mlfq_q0 = 0;
        int mlfq_q1 = 0;
        int mlfq_q2 = 0;
        if (choice == AlgorithmChoice::MLFQ) {
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
            case AlgorithmChoice::Exit:
                return 0;
        }

        try {
            SchedulingSimulationResult result = algorithm->schedule(processes);
            out << "\nSimulation completed successfully.\n";
            out << "Scheduled " << result.process_results.size() << " process(es) across "
                << result.timeline.size() << " timeline execution segment(s).\n\n";
        } catch (const std::exception& e) {
            out << "\nSimulation failed with error: " << e.what() << "\n\n";
        }
    }
}

} // namespace oscope
