#pragma once
#include <pybind11/embed.h>
#include <string>

class PythonBridge {
public:
    PythonBridge();
    std::string runSummaryStatistics(const std::string& input);

private:
    pybind11::scoped_interpreter interpreter_;
    pybind11::object engine_;
};
