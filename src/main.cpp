#include <iostream>
#include <string_view>

#include "oscope/cli.hpp"

int main(int argc, char* argv[]) {
    oscope::OutputFormat format = oscope::OutputFormat::HumanReadable;

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
        } else if (arg == "--help" || arg == "-h") {
            std::cout << "OScope - Interactive Operating Systems Learning & Experimentation Platform\n\n"
                      << "Usage:\n"
                      << "  oscope [options]\n\n"
                      << "Options:\n"
                      << "  -j, --json          Output experiment results in structured JSON format\n"
                      << "  --format <format>   Specify experiment output format: human (default) or json\n"
                      << "  -h, --help          Display this help message and exit\n";
            return 0;
        }
    }

    return oscope::run_cli(std::cin, std::cout, format);
}
