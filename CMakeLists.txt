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
