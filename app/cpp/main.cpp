#include <QApplication>
#include <QMessageBox>
#include <exception>
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
        int exitCode = 0;
        {
            // Keep Qt responsive to non-Python work and allow bridge calls to
            // acquire the interpreter GIL when the UI dispatches an analysis.
            pybind11::gil_scoped_release release;
            exitCode = app.exec();
        }
        return exitCode;
    } catch (const std::exception& e) {
        QMessageBox::critical(nullptr, "SIKPRO startup error",
                              QString::fromUtf8(e.what()));
        return 1;
    }
}
