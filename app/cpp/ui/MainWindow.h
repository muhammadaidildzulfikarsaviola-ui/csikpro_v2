#pragma once

#include <QMainWindow>
#include <QJsonObject>
#include <QString>

class QComboBox;
class QCloseEvent;
class QPlainTextEdit;
class QTabWidget;
class QTableWidget;
class PythonBridge;

class MainWindow : public QMainWindow {
    Q_OBJECT
public:
    explicit MainWindow(PythonBridge& bridge, QWidget* parent = nullptr);

protected:
    void closeEvent(QCloseEvent* event) override;

private Q_SLOTS:
    void runAnalysis();
    void importCsv();
    void exportCsv();
    void openProject();
    void saveProject();
    void newDataset();
    void addDataset();
    void deleteDataset();
    void switchDataset(int index);
    void clearDataset();

private:
    void addRow();
    void addColumn();
    void removeRow();
    void removeColumn();
    void updateMethodList();
    void refreshDatasetList();
    void loadActiveDataset(int index);
    void storeActiveDataset();
    void displayResult(const QString& json);
    void markProjectDirty();
    bool confirmDiscardChanges();
    QString datasetJson() const;
    QString projectJson() const;
    void loadProject(const QString& path);
    void setStatus(const QString& message);

    PythonBridge& bridge_;
    QTableWidget* table_;
    QPlainTextEdit* output_;
    QTableWidget* resultTable_;
    QComboBox* category_;
    QComboBox* method_;
    QComboBox* datasetSelector_;
    QPlainTextEdit* rawOutput_;
    QTabWidget* resultTabs_;
    QString datasetName_;
    QString projectPath_;
    QJsonObject savedProjectState_;
    QJsonObject datasetMetadata_;
    bool loadingDataset_ = false;
    bool projectDirty_ = false;
    bool analysisSelectionChanged_ = false;
};
