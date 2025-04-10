# Test executable
file(GLOB SOURCES src/*.cpp)
add_executable(unit_test ${SOURCES})
target_include_directories(unit_test PRIVATE ${CMAKE_SOURCE_DIR}/cpp/include)

# Link Google Test
target_link_libraries(unit_test
    gtest
    gtest_main
)

# Auto-discover tests
include(GoogleTest)
gtest_discover_tests(unit_test)