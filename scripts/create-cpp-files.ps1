$ErrorActionPreference = "Stop"
$root = "D:\Code\Sikpro-v2-with-c"

$files = @{
    "CMakeLists.txt" = @"
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

file(TO_CMAKE_PATH "${'$'}{CMAKE_SOURCE_DIR}/engine/python" SIKPRO_ENGINE_DIR)
target_compile_definitions(Sikpro PRIVATE
    SIKPRO_ENGINE_DIR="${'$'}{SIKPRO_ENGINE_DIR}"
)
"@

    "app\cpp\main.cpp" = @"
#include <QApplication>
#include <QMessageBox>
#include "bridge/PythonBridge.h"
#include "ui/MainWindow.h"

int main(int argc, char *argv[])
{
    QApplication app(argc, argv);
    QApplication::setApplicationName("SIKPRO");

    try {
        PythonBridge bridge;
        MainWindow window(bridge);
        window.show();
        return app.exec();
    } catch (const std::exception& e) {
        QMessageBox::critical(nullptr, "SIKPRO startup error",
                              QString::fromUtf8(e.what()));
        return 1;
    }
}
"@

    "app\cpp\bridge\PythonBridge.h" = @"
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
"@

    "app\cpp\bridge\PythonBridge.cpp" = @"
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
"@

    "app\cpp\ui\MainWindow.h" = @"
#pragma once
#include <QMainWindow>

class QTableWidget;
class QPlainTextEdit;
class PythonBridge;

class MainWindow : public QMainWindow {
    Q_OBJECT
public:
    explicit MainWindow(PythonBridge& bridge, QWidget* parent = nullptr);

private slots:
    void runAnalysis();

private:
    PythonBridge& bridge_;
    QTableWidget* table_;
    QPlainTextEdit* output_;
};
"@

    "app\cpp\ui\MainWindow.cpp" = @"
#include "MainWindow.h"
#include "bridge/PythonBridge.h"

#include <QHeaderView>
#include <QHBoxLayout>
#include <QLabel>
#include <QMessageBox>
#include <QPlainTextEdit>
#include <QPushButton>
#include <QTableWidget>
#include <QVBoxLayout>
#include <QWidget>

MainWindow::MainWindow(PythonBridge& bridge, QWidget* parent)
    : QMainWindow(parent), bridge_(bridge),
      table_(new QTableWidget(20, 1, this)),
      output_(new QPlainTextEdit(this))
{
    setWindowTitle("SIKPRO | Statistical Process Control");
    resize(1100, 720);

    auto* central = new QWidget(this);
    auto* layout = new QHBoxLayout(central);
    auto* left = new QVBoxLayout();
    auto* right = new QVBoxLayout();

    left->addWidget(new QLabel("DATA INPUT"));
    table_->setHorizontalHeaderLabels({"C1"});
    table_->horizontalHeader()->setSectionResizeMode(QHeaderView::Stretch);
    table_->setAlternatingRowColors(true);
    left->addWidget(table_);

    auto* run = new QPushButton("Run Summary Statistics");
    left->addWidget(run);

    right->addWidget(new QLabel("ANALYSIS OUTPUT"));
    output_->setReadOnly(true);
    right->addWidget(output_);

    layout->addLayout(left, 3);
    layout->addLayout(right, 2);
    setCentralWidget(central);

    connect(run, &QPushButton::clicked, this, &MainWindow::runAnalysis);
}

void MainWindow::runAnalysis()
{
    QStringList values;
    for (int r = 0; r < table_->rowCount(); ++r) {
        auto* item = table_->item(r, 0);
        if (item && !item->text().trimmed().isEmpty())
            values << item->text().trimmed();
    }

    try {
        output_->setPlainText(QString::fromStdString(
            bridge_.runSummaryStatistics(values.join('\n').toStdString())
        ));
    } catch (const std::exception& e) {
        QMessageBox::warning(this, "Analysis failed",
                             QString::fromUtf8(e.what()));
    }
}
"@
}

foreach ($relative in $files.Keys) {
    $path = Join-Path $root $relative
    New-Item -ItemType Directory -Path (Split-Path -Parent $path) -Force |
        Out-Null
    Set-Content -Path $path -Value $files[$relative] -Encoding utf8
}

Write-Host "C++ foundation files created."
