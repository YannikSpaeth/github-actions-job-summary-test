cmake_minimum_required(VERSION 3.16)
project(demo_app LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# --- Utils library (shared between app and tests) ---
add_library(utils_lib STATIC src/utils.cpp)
target_include_directories(utils_lib PUBLIC include)

# --- Main executable ---
add_executable(demo_app src/main.cpp)
target_link_libraries(demo_app PRIVATE utils_lib)

# --- Google Test via FetchContent ---
include(FetchContent)
FetchContent_Declare(
  googletest
  GIT_REPOSITORY https://github.com/google/googletest.git
  GIT_TAG        v1.14.0
)
set(gtest_force_shared_crt ON CACHE BOOL "" FORCE)
FetchContent_MakeAvailable(googletest)

# --- Tests ---
enable_testing()

add_executable(demo_tests tests/test_utils.cpp)
target_link_libraries(demo_tests PRIVATE GTest::gtest_main utils_lib)

include(GoogleTest)
gtest_discover_tests(demo_tests)
