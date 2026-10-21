#include "PythonBridge.h"

#include <cmath>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

namespace py = pybind11;

namespace {

std::vector<double> parseNumericInput(const std::string& input)
{
    std::vector<double> values;
    std::istringstream stream(input);
    std::string line;
    std::size_t lineNumber = 0;

    while (std::getline(stream, line)) {
        ++lineNumber;

        // Accept Windows-style line endings and ignore empty rows.
        if (!line.empty() && line.back() == '\\r')
            line.pop_back();

        if (line.find_first_not_of(" \\t") == std::string::npos)
            continue;

        std::size_t consumed = 0;
        double value = 0.0;
        try {
            value = std::stod(line, &consumed);
        } catch (const std::exception&) {
            throw std::invalid_argument(
                "Row " + std::to_string(lineNumber) +
                " is not a valid number: " + line
            );
        }

        if (line.find_first_not_of(" \\t", consumed) != std::string::npos) {
            throw std::invalid_argument(
                "Unexpected text after the number on row " +
                std::to_string(lineNumber) + "."
            );
        }

        if (!std::isfinite(value)) {
            throw std::invalid_argument(
                "Row " + std::to_string(lineNumber) +
                " must be a finite number."
            );
        }

        values.push_back(value);
    }

    if (values.empty())
        throw std::invalid_argument("Enter at least one numeric value.");

    return values;
}

} // namespace

PythonBridge::PythonBridge()
    : interpreter_(), engine_(py::none())
{
    py::module_::import("sys").attr("path").attr("insert")(
        0, SIKPRO_ENGINE_DIR
    );

    engine_ = py::module_::import("sikpro.engine")
                  .attr("AnalysisEngine")();
}

std::string PythonBridge::runSummaryStatistics(const std::string& input)
{
    try {
        const auto values = parseNumericInput(input);
        py::object dataset = py::module_::import("sikpro.data")
            .attr("Dataset")("Qt Dataset", static_cast<int>(values.size()), 1);

        py::list rows;
        for (const double value : values)
            rows.append(py::make_tuple(value));

        dataset.attr("data") = rows;
        dataset.attr("rows") = static_cast<int>(values.size());
        dataset.attr("columns") = 1;
        dataset.attr("headers") = py::make_tuple("C1");

        py::object result = engine_.attr("run")(
            dataset, "Descriptive", "Summary Statistics"
        );

        return py::str(py::module_::import("pprint")
            .attr("pformat")(result)).cast<std::string>();
    } catch (const py::error_already_set& e) {
        throw std::runtime_error(e.what());
    }
}
