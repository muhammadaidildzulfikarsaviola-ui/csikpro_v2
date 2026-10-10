#include "PythonBridge.h"
#include <stdexcept>

namespace py = pybind11;

PythonBridge::PythonBridge()
    : interpreter_(), engine_(py::none())
{
    py::module_::import("sys").attr("path").attr("insert")(
        0, SIKPRO_ENGINE_DIR
    );

    engine_ = py::module_::import("sikpro.engine")
                  .attr("AnalysisEngine")();
}

std::string PythonBridge::runSummaryStatistics(
    const std::string& input)
{
    try {
        py::object dataset = py::module_::import("sikpro.data")
            .attr("Dataset")("Qt Dataset", 1, 1);

        py::list rows;
        std::string line;
        std::string current;

        for (char ch : input) {
            if (ch == '\n' || ch == '\r') {
                if (!current.empty()) {
                    rows.append(py::make_tuple(current));
                    current.clear();
                }
            } else {
                current += ch;
            }
        }

        if (!current.empty())
            rows.append(py::make_tuple(current));

        dataset.attr("data") = rows;
        dataset.attr("rows") = py::len(rows);
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
