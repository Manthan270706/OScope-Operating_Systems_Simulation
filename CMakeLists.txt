cmake_minimum_required(VERSION 3.20)

project(OScope
    VERSION 0.1.0
    DESCRIPTION "Interactive Operating Systems learning and experimentation platform"
    LANGUAGES CXX
)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

add_library(oscope_core
    src/scheduling/fcfs.cpp
    src/scheduling/sjf.cpp
    src/scheduling/srtf.cpp
    src/scheduling/priority.cpp
    src/scheduling/round_robin.cpp
    src/scheduling/mlfq.cpp
    src/scheduling_metrics.cpp
    src/scheduling_comparison.cpp
    src/paging/fifo.cpp
    src/paging/lru.cpp
    src/paging/optimal.cpp
    src/paging/page_replacement_comparison.cpp
    src/cli.cpp
)

target_include_directories(oscope_core
    PUBLIC
    ${PROJECT_SOURCE_DIR}/include
)

add_executable(oscope
    src/main.cpp
)

target_link_libraries(oscope
    PRIVATE
    oscope_core
)

target_include_directories(oscope
    PRIVATE
        ${PROJECT_SOURCE_DIR}/include
)

if(CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang")
    target_compile_options(oscope PRIVATE
        -Wall
        -Wextra
        -Wpedantic
    )
endif()

include(CTest)
enable_testing()

include(FetchContent)

FetchContent_Declare(
    googletest
    URL https://github.com/google/googletest/archive/refs/tags/v1.17.0.zip
    DOWNLOAD_EXTRACT_TIMESTAMP TRUE
)

FetchContent_MakeAvailable(googletest)

add_executable(oscope_tests
    tests/process_test.cpp
    tests/sjf_test.cpp
    tests/srtf_test.cpp
    tests/priority_test.cpp
    tests/round_robin_test.cpp
    tests/mlfq_test.cpp
    tests/scheduling_comparison_test.cpp
    tests/cli_test.cpp
    tests/paging_fifo_test.cpp
    tests/paging_lru_test.cpp
    tests/paging_optimal_test.cpp
    tests/paging_comparison_test.cpp
    tests/paging_cli_test.cpp
)

target_link_libraries(oscope_tests
    PRIVATE
    oscope_core
    GTest::gtest_main
)

target_include_directories(oscope_tests
    PRIVATE
    ${PROJECT_SOURCE_DIR}/include
)

include(GoogleTest)
gtest_discover_tests(oscope_tests)
