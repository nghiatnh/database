cmake_minimum_required(VERSION 3.10)
project(CppDatabase)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${CMAKE_SOURCE_DIR}/bin)

# Include directories
include_directories(cpp/include/)

# Automatically get all source files
file(GLOB SOURCES cpp/src/*.cpp)

# Add executable
add_executable(cpp_database ${SOURCES})

# Compiler options
target_compile_options(cpp_database PRIVATE -O3 -Wall -Wextra -Wpedantic)

# Testing
enable_testing()
add_subdirectory(external/googletest)
add_subdirectory(tests)
