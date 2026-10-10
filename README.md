# SIKPRO C++ / Python

Production migration of SIKPRO desktop UI to C++ and Qt 6 while retaining the existing Python analysis engine.

## Architecture

- **Desktop UI:** C++17 and Qt 6 Widgets
- **Python integration:** pybind11 embedding
- **Analysis engine:** Python package migrated from the established SIKPRO V2 codebase
- **Build system:** CMake
- **Tests:** C++ tests and existing Python regression tests

## Requirements

- Windows 10/11 x64
- Visual Studio 2022 Build Tools (MSVC C++ workload)
- CMake 3.25+
- Qt 6.x MSVC x64 installation
- CPython 3.11 x64 with development headers and libraries
- pybind11 available to CMake

## Build

Configure CMake with explicit Qt and Python paths for your installed environment. See `docs/BUILD_WINDOWS.md`.

## Migration policy

The legacy repository remains the source of truth for calculation behavior until each Python engine test passes against the migrated package. Existing .spc project compatibility must be preserved. Do not remove the old implementation until regression tests and end-to-end workflows pass.

## Current status

The production foundation is being established. The existing Python analysis modules and their tests are being ported in place; no calculation behavior should be reimplemented in C++ without a separate technical justification.
