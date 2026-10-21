#include "PythonBridge.h"

#include <pybind11/stl.h>
#include <cstddef>
#include <filesystem>
#include <stdexcept>

namespace {
void validateDataset(const pybind11::dict& state)
{
    if (!state.contains("rows") || !state.contains("columns") ||
        !state.contains("headers") || !state.contains("data"))
        throw std::invalid_argument("Dataset must include rows, columns, headers, and data.");
    const int rows = state["rows"].cast<int>();
    const int columns = state["columns"].cast<int>();
    if (rows < 1 || columns < 1)
        throw std::invalid_argument("Dataset must contain at least one row and one column.");
    const pybind11::list headers = state["headers"].cast<pybind11::list>();
    const pybind11::list data = state["data"].cast<pybind11::list>();
    if (headers.size() != static_cast<std::size_t>(columns) ||
        data.size() != static_cast<std::size_t>(rows))
        throw std::invalid_argument("Dataset dimensions do not match the header or data arrays.");
    for (const pybind11::handle row : data) {
        if (!pybind11::isinstance<pybind11::list>(row) &&
            !pybind11::isinstance<pybind11::tuple>(row))
            throw std::invalid_argument("Every dataset row must be an array of cell values.");
        const pybind11::sequence cells = pybind11::reinterpret_borrow<pybind11::sequence>(row);
        if (cells.size() != static_cast<pybind11::ssize_t>(columns))
            throw std::invalid_argument("Every dataset row must have the same number of columns.");
    }
    if (state.contains("metadata") && !pybind11::isinstance<pybind11::dict>(state["metadata"]))
        throw std::invalid_argument("Dataset metadata must be a JSON object.");
}
}

namespace py = pybind11;

PythonBridge::PythonBridge() : interpreter_(), engine_(py::none())
{
    const std::string enginePath = std::filesystem::u8path(SIKPRO_ENGINE_DIR).u8string();
    py::module_::import("sys").attr("path").attr("insert")(0, py::str(enginePath.c_str()));
    engine_ = py::module_::import("sikpro.engine").attr("AnalysisEngine")();
}

std::string PythonBridge::analyze(const std::string& datasetJson,
                                  const std::string& category,
                                  const std::string& method,
                                  const std::string& optionsJson)
{
    py::gil_scoped_acquire gil;
    try {
        py::object json = py::module_::import("json");
        py::dict state = json.attr("loads")(datasetJson).cast<py::dict>();
        validateDataset(state);
        py::object datasetType = py::module_::import("sikpro.data").attr("Dataset");
        const std::string name = state.contains("name")
            ? py::str(state["name"]).cast<std::string>() : "Dataset";
        const int rows = state["rows"].cast<int>();
        const int columns = state["columns"].cast<int>();
        py::object dataset = datasetType(name, rows, columns);
        dataset.attr("headers") = state["headers"];
        dataset.attr("data") = state["data"];
        if (state.contains("metadata"))
            dataset.attr("metadata") = state["metadata"];
        py::object optionsValue = json.attr("loads")(optionsJson);
        if (!py::isinstance<py::dict>(optionsValue))
            throw std::invalid_argument("Analysis options must be a JSON object.");
        py::dict options = optionsValue.cast<py::dict>();
        py::object result = engine_.attr("run")(dataset, category, method, options);
        return py::str(json.attr("dumps")(result, py::arg("ensure_ascii") = false,
                                           py::arg("indent") = 2,
                                           py::arg("allow_nan") = false)).cast<std::string>();
    } catch (const std::invalid_argument&) {
        throw;
    } catch (const py::cast_error& error) {
        throw std::invalid_argument(std::string("Dataset or options JSON has invalid field types: ") + error.what());
    } catch (const py::error_already_set& error) {
        throw std::runtime_error(error.what());
    }
}
