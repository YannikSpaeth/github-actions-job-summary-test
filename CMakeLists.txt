cmake_minimum_required(VERSION 3.16)
project(demo_app LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

add_executable(demo_app
    src/main.cpp
    src/utils.cpp
)

target_include_directories(demo_app PRIVATE include)
