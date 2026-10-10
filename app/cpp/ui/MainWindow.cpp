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
