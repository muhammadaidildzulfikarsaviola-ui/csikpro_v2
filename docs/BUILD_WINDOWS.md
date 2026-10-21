# Windows setup and build

These commands are instructions for the developer to run in a Visual Studio 2022 x64 developer environment. They are documented here and have not been run as part of this source-only migration work.

## Prerequisites

Install Visual Studio 2022 Build Tools with the Desktop development with C++ workload, CMake 3.25+, Qt 6.12+ for MSVC x64 with the Widgets component, CPython 3.11 x64 including headers and its import library, and pybind11. Use one consistent x64 toolchain. Ensure CMake can find Qt through `CMAKE_PREFIX_PATH`, pybind11 through `CMAKE_PREFIX_PATH` or `pybind11_DIR`, and the intended Python through `Python3_ROOT_DIR`.

The numerical engine currently imports only Python standard-library modules. The old Python UI requires `customtkinter`, `tksheet`, and `matplotlib`, but those packages are not needed by the C++ bridge's `sikpro.engine` import path.

## Configure and build

From the repository root in a configured x64 developer shell, adjust the installation paths and run:

```powershell
cmake -S . -B build `
  -DCMAKE_PREFIX_PATH="C:/Qt/6.12.0/msvc2022_64" `
  -DPython3_ROOT_DIR="C:/Python311" `
  -Dpybind11_DIR="C:/Python311/Lib/site-packages/pybind11/share/cmake/pybind11"
cmake --build build --config Release
```

If pybind11 is provided by a different package manager, point `pybind11_DIR` at that package's CMake config directory instead. Do not mix x86 and x64 libraries or Python/Qt builds from incompatible toolchains.

The bridge adds `engine/python` to the embedded interpreter's module path using the source tree path configured by CMake. The current executable is therefore a development layout, not a self-contained installer. A distributable package still needs a deployment plan for the Python runtime, engine package, and any required runtime DLLs.

## Source-only status

The migration handover explicitly defers configure, build, compilation, and runtime verification. The commands above are for later developer verification; this repository change does not claim a successful build or launch.
