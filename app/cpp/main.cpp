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
