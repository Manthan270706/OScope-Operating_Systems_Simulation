cmake_minimum_required(VERSION 3.20)

project(OScope
    VERSION 0.1.0
    DESCRIPTION "Interactive Operating Systems learning and experimentation platform"
    LANGUAGES CXX
)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

add_executable(oscope
    src/main.cpp
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

add_subdirectory(/usr/src/googletest ${CMAKE_BINARY_DIR}/googletest)

add_executable(oscope_tests
    tests/smoke_test.cpp
)

target_link_libraries(oscope_tests
    PRIVATE
        GTest::gtest_main
)

include(GoogleTest)
gtest_discover_tests(oscope_tests)
