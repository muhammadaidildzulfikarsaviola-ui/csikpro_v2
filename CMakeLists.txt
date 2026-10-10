cmake_minimum_required(VERSION 3.25)
project(Sikpro LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_AUTOMOC ON)

find_package(Qt6 6.12 REQUIRED COMPONENTS Widgets)
find_package(Python3 3.11 EXACT REQUIRED COMPONENTS Interpreter Development)
find_package(pybind11 CONFIG REQUIRED)

qt_add_executable(Sikpro
    app/cpp/main.cpp
    app/cpp/bridge/PythonBridge.cpp
    app/cpp/bridge/PythonBridge.h
    app/cpp/ui/MainWindow.cpp
    app/cpp/ui/MainWindow.h
)

target_include_directories(Sikpro PRIVATE app/cpp)
target_link_libraries(Sikpro PRIVATE Qt6::Widgets pybind11::embed)

file(TO_CMAKE_PATH "{CMAKE_SOURCE_DIR}/engine/python" SIKPRO_ENGINE_DIR)
target_compile_definitions(Sikpro PRIVATE
    SIKPRO_ENGINE_DIR="{SIKPRO_ENGINE_DIR}"
)

target_compile_definitions(Sikpro PRIVATE QT_NO_KEYWORDS)

