#include <iostream>

#include "oscope/cli.hpp"

int main() {
    return oscope::run_cli(std::cin, std::cout);
}
