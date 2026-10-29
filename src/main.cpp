#include <iostream>
#include <string_view>

#include "oscope/cli.hpp"

int main(int argc, char* argv[]) {
    oscope::OutputFormat format = oscope::OutputFormat::HumanReadable;

    std::string_view demo_mode;

    for (int i = 1; i < argc; ++i) {
        std::string_view arg(argv[i]);
        if (arg == "--json" || arg == "-j") {
            format = oscope::OutputFormat::Json;
        } else if (arg == "--format=json") {
            format = oscope::OutputFormat::Json;
        } else if (arg == "--format" && i + 1 < argc) {
            std::string_view val(argv[++i]);
            if (val == "json") {
                format = oscope::OutputFormat::Json;
            }
        } else if (arg.rfind("--demo-", 0) == 0 || arg == "--demo" || arg == "--fs-ops" || arg == "--paging-ops" || arg == "--process-ops") {
            demo_mode = arg;
        } else if (arg == "--help" || arg == "-h") {
            std::cout << "OScope - Interactive Operating Systems Learning & Experimentation Platform\n\n"
                      << "Usage:\n"
                      << "  oscope [options]\n\n"
                      << "Options:\n"
                      << "  -j, --json              Output experiment results in structured JSON format\n"
                      << "  --format <format>       Specify experiment output format: human (default) or json\n"
                      << "  --demo-all              Execute comprehensive demonstrations for all modules\n"
                      << "  --demo-paging           Demonstrate address translation, demand paging, and thrashing\n"
                      << "  --paging-ops            Execute virtual memory and address translation operations from stdin\n"
                      << "  --demo-process          Demonstrate process lifecycle state machine transitions\n"
                      << "  --process-ops           Execute process lifecycle operations from stdin\n"
                      << "  --demo-sync             Demonstrate thread synchronization (Peterson's, POSIX semaphores, producer-consumer)\n"
                      << "  --demo-coffman          Demonstrate Coffman conditions and deadlock prevention\n"
                      << "  --demo-monitor          Observe real Linux host CPU, memory, and process state\n"
                      << "  --demo-fs               Demonstrate educational filesystem allocation and bitmap\n"
                      << "  --demo-fs-frag          Demonstrate external fragmentation under contiguous allocation\n"
                      << "  --demo-fs-full          Demonstrate disk capacity limits and out-of-space recovery\n"
                      << "  --fs-ops                Execute simulated filesystem operations from stdin\n"
                      << "  --demo-ipc              Demonstrate POSIX FIFO, shared memory, and message queue IPC\n"
                      << "  --demo-lifecycle        Demonstrate process exec, zombie reaping, and orphan adoption\n"
                      << "  --demo-disk             Demonstrate disk scheduling algorithms (FCFS, SSTF, SCAN, etc.)\n"
                      << "  -h, --help              Display this help message and exit\n";
            return 0;
        }
    }

    if (!demo_mode.empty()) {
        if (demo_mode == "--demo-all" || demo_mode == "--demo") {
            oscope::run_all_demos(std::cout, format);
        } else if (demo_mode == "--demo-paging") {
            oscope::run_demo_address_translation(std::cout, format);
        } else if (demo_mode == "--paging-ops") {
            oscope::run_paging_operations(std::cin, std::cout, format);
        } else if (demo_mode == "--demo-process") {
            oscope::run_demo_process_state_machine(std::cout, format);
        } else if (demo_mode == "--process-ops") {
            oscope::run_process_operations(std::cin, std::cout, format);
        } else if (demo_mode == "--demo-sync") {
            oscope::run_demo_sync(std::cout, format);
        } else if (demo_mode == "--demo-coffman") {
            oscope::run_demo_coffman_conditions(std::cout, format);
        } else if (demo_mode == "--demo-monitor") {
            oscope::run_demo_host_monitoring(std::cout, format);
        } else if (demo_mode == "--demo-fs") {
            oscope::run_demo_filesystem(std::cout, format);
        } else if (demo_mode == "--demo-fs-frag") {
            oscope::run_demo_filesystem_fragmentation(std::cout, format);
        } else if (demo_mode == "--demo-fs-full") {
            oscope::run_demo_filesystem_capacity(std::cout, format);
        } else if (demo_mode == "--fs-ops") {
            oscope::run_filesystem_operations(std::cin, std::cout, format);
        } else if (demo_mode == "--demo-ipc") {
            oscope::run_demo_ipc_extensions(std::cout, format);
        } else if (demo_mode == "--demo-lifecycle") {
            oscope::run_demo_process_lifecycle(std::cout, format);
        } else if (demo_mode == "--demo-disk") {
            oscope::run_demo_disk(std::cout, format);
        }
        return 0;
    }

    return oscope::run_cli(std::cin, std::cout, format);
}
