cmake_minimum_required(VERSION 3.10)
project(UAVProbabilityField)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Find threading library
find_package(Threads REQUIRED)

# Source files
set(SOURCES
    src/main.cpp
    src/CSVLoader.cpp
    src/FieldGenerator.cpp
)

# Header files
set(HEADERS
    include/Config.h
    include/CSVLoader.h
    include/DroneDatabase.h
    include/FastMath.h
    include/FieldGenerator.h
    include/States.h
    include/Threats.h
)

# Create executable
add_executable(uav_pipeline ${SOURCES} ${HEADERS})

# Link threading library
target_link_libraries(uav_pipeline PRIVATE Threads::Threads)

# Include directories
target_include_directories(uav_pipeline PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/include)

# Enable all warnings
if(MSVC)
    target_compile_options(uav_pipeline PRIVATE /W4 /std:c++17)
else()
    target_compile_options(uav_pipeline PRIVATE -Wall -Wextra -Wpedantic -std=c++17)
endif()
