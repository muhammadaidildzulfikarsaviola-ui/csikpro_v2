#pragma once

#include <pybind11/embed.h>
#include <string>

class PythonBridge {
public:
    PythonBridge();
    std::string analyze(const std::string& datasetJson,
                        const std::string& category,
                        const std::string& method,
                        const std::string& optionsJson = "{}");

private:
    // Declared before engine_: Python objects must be released before the
    // interpreter is shut down (members are destroyed in reverse order).
    pybind11::scoped_interpreter interpreter_;
    pybind11::object engine_;
};
