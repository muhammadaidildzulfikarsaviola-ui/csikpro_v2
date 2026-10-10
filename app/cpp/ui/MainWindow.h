#pragma once
#include <QMainWindow>

class QTableWidget;
class QPlainTextEdit;
class PythonBridge;

class MainWindow : public QMainWindow {
    Q_OBJECT
public:
    explicit MainWindow(PythonBridge& bridge, QWidget* parent = nullptr);

private Q_SLOTS:
    void runAnalysis();

private:
    PythonBridge& bridge_;
    QTableWidget* table_;
    QPlainTextEdit* output_;
};

