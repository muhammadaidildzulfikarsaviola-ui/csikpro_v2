# SIKPRO

SIKPRO is migrating from a Python desktop interface to a native C++17 / Qt 6 Widgets application. Statistical calculations remain in the Python engine so the existing calculation conventions and regression tests remain the reference.

## Architecture

- `app/cpp/main.cpp` starts Qt and owns the embedded Python bridge for the application's lifetime.
- `app/cpp/ui/MainWindow.*` provides the worksheet, analysis navigation, file actions, and results panel.
- `app/cpp/bridge/PythonBridge.*` converts the current worksheet to the existing `Dataset` API and dispatches through `AnalysisEngine`.
- `engine/python/sikpro/data/` contains the Python dataset model and manager.
- `engine/python/sikpro/engine/` dispatches analyses in `engine/python/sikpro/logic/`.
- `engine/python/sikpro/ui/` is the retained Python desktop implementation and documents existing workflows.
- `tests/python/` contains regression tests for descriptive, frequency, distribution, control-chart, quality-tool, and persistence behavior.

## Current Qt functionality

The Qt worksheet supports editable headers, multiple columns and rows, spreadsheet copy/paste, row/column addition and deletion, clearing, CSV import/export, dataset add/switch/delete, and `.spc` open/save. Analysis settings allow method-appropriate column and row-range selection. Analysis navigation dispatches Summary Statistics, Frequency, Distribution, I-MR, MR, X-bar R, X-bar S, p, np, c, u, Histogram, Pareto Chart, Check Sheet, Fishbone, Defect Concentration, and Scatter Plot through the Python engine. Results have a readable text view and a table view; raw engine JSON remains available in a separate detail tab. Sample size, unit size, distribution family, and fishbone problem are configurable only for methods that consume them.

Control-chart calculations, center lines, limits, status, and Nelson rule findings are produced by the existing Python implementation. X-bar R/S treat each selected row as a subgroup; I-MR/MR and attribute charts use the single selected column; Scatter Plot and the two-coordinate quality tool use the first two selected columns. The analysis dialog passes selected source-column indexes and the requested row interval using the metadata convention already consumed by `AnalysisEngine`.

The numeric analysis flow reports blank, nonnumeric, or incomplete subgroup values that the existing engine will skip. It does not change the Python engine's established parsing or calculation behavior.

The `.spc` file remains UTF-8 JSON with `format: "SPC Dataset"`, version 1, datasets, active index, metadata, selected analysis, history, and last-result fields. The Qt UI follows the legacy restore defaults of 200 rows and columns when those fields are omitted, accepts Python-style decimal integer strings for dimensions and active index, and rejects malformed or out-of-range active indexes and unsupported saved analysis selections. It preserves unknown top-level and active-dataset keys, inactive datasets, and original JSON types for untouched cells. A JSON null displays as a blank cell and remains null until that cell is edited or cleared; edited, pasted, and CSV-imported cell contents are saved as strings, including numeric-looking text. New analysis history entries use the legacy field names and are limited to 100 entries. Qt currently rejects any individual dataset larger than one million cells as a UI safety limit; the legacy Python loader has no corresponding limit. This is a source-level schema match; no real historical `.spc` sample has been round-tripped through the Qt application. CSV import treats the first row as headers.

## Requirements

- Windows 10/11 x64
- Visual Studio 2022 Build Tools with the MSVC C++ workload
- CMake 3.25 or newer
- Qt 6.12 or newer, built for the same MSVC architecture
- CPython 3.11 x64 with development headers and import library
- pybind11 CMake package compatible with that Python installation

The current numerical engine uses Python standard-library modules only. The retained Python desktop UI additionally imports CustomTkinter, tksheet, and Matplotlib. Install those only when running that legacy interface. Python regression tests use the standard library's `unittest` runner.

## Configure and build on Windows

See [docs/BUILD_WINDOWS.md](docs/BUILD_WINDOWS.md) for environment setup and commands to run locally. Python, pybind11, and Qt must use matching x64 architecture and compatible MSVC builds. The application embeds CPython in-process, so the target machine also needs the matching Python 3.11 runtime and engine files at the configured relative source layout unless the deployment packaging is extended.

## Known migration gaps

- Runtime/build integration has not yet been verified on Windows.
- Results are presented as readable text and a generic scalar-field table. Dedicated control-chart, histogram, Pareto, and scatter visualizations and analysis-specific interpretations remain unimplemented. The current CMake target only links Qt Widgets; plotting has not been added.
- Analysis currently runs synchronously on the UI thread, so larger datasets can temporarily block window interaction.
- Dataset switching/add/delete and analysis column/range selection are available, but dataset rename/duplicate and analysis history browsing are not yet exposed in Qt.
- CSV export writes every worksheet row, including blank trailing rows.
- Existing Python project persistence is implemented through the legacy UI layer. Qt compatibility is based on source inspection and still needs review against representative historical `.spc` samples.

No calculations have been reimplemented in C++; engine behavior remains authoritative.
