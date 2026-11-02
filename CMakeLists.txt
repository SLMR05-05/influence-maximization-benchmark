cmake_minimum_required(VERSION 3.18)
project(IM_Metaheuristic_Research VERSION 0.1.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# Optimization flags
if(MSVC)
    add_compile_options(/O2 /W4 /permissive-)
else()
    add_compile_options(-O3 -march=native -Wall -Wextra -Wpedantic)
endif()

# Find OpenMP for parallel Monte Carlo simulations
find_package(OpenMP)
if(OpenMP_CXX_FOUND)
    message(STATUS "OpenMP found! Enabling multi-threaded simulations.")
endif()

# Core C++ library
add_library(im_core_lib STATIC
    cpp_core/src/graph.cpp
    cpp_core/src/diffusion.cpp
    cpp_core/src/monte_carlo.cpp
    cpp_core/src/evaluator.cpp
)

target_include_directories(im_core_lib PUBLIC
    cpp_core/include
)

if(OpenMP_CXX_FOUND)
    target_link_libraries(im_core_lib PUBLIC OpenMP::OpenMP_CXX)
endif()

# Find pybind11 for Python bindings
find_package(pybind11 CONFIG QUIET)
if(NOT pybind11_FOUND)
    # Fallback to python module pybind11 if installed via pip
    execute_process(
        COMMAND python3 -m pybind11 --cmakedir
        OUTPUT_VARIABLE PYBIND11_CMAKE_DIR
        OUTPUT_STRIP_TRAILING_WHITESPACE
        ERROR_QUIET
    )
    if(PYBIND11_CMAKE_DIR)
        list(APPEND CMAKE_PREFIX_PATH "${PYBIND11_CMAKE_DIR}")
        find_package(pybind11 CONFIG REQUIRED)
    endif()
endif()

if(pybind11_FOUND)
    message(STATUS "pybind11 found! Building Python extension module '_im_core'.")
    pybind11_add_module(_im_core
        cpp_core/bindings/bindings.cpp
    )
    target_link_libraries(_im_core PRIVATE im_core_lib)
    
    # Place the compiled extension directly into src/im_research
    set_target_properties(_im_core PROPERTIES
        LIBRARY_OUTPUT_DIRECTORY "${CMAKE_CURRENT_SOURCE_DIR}/src/im_research"
        RUNTIME_OUTPUT_DIRECTORY "${CMAKE_CURRENT_SOURCE_DIR}/src/im_research"
    )
endif()

