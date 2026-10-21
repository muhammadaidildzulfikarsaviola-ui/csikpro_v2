#include "MainWindow.h"
#include "bridge/PythonBridge.h"

#include <QAbstractItemView>
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

    auto* inputTitle = new QLabel("DATA INPUT");
    inputTitle->setStyleSheet("font-weight: 700; font-size: 15px;");
    left->addWidget(inputTitle);

    table_->setHorizontalHeaderLabels({"C1"});
    table_->horizontalHeader()->setSectionResizeMode(QHeaderView::Stretch);
    table_->verticalHeader()->setSectionResizeMode(QHeaderView::ResizeToContents);
    table_->setAlternatingRowColors(true);
    table_->setSelectionBehavior(QAbstractItemView::SelectItems);
    table_->setSelectionMode(QAbstractItemView::ExtendedSelection);
    table_->setEditTriggers(QAbstractItemView::DoubleClicked |
                            QAbstractItemView::EditKeyPressed |
                            QAbstractItemView::AnyKeyPressed);
    table_->setToolTip("Enter one numeric observation per row.");
    left->addWidget(table_);

    auto* run = new QPushButton("Run Summary Statistics");
    run->setMinimumHeight(36);
    left->addWidget(run);

    auto* outputTitle = new QLabel("ANALYSIS OUTPUT");
    outputTitle->setStyleSheet("font-weight: 700; font-size: 15px;");
    right->addWidget(outputTitle);

    output_->setReadOnly(true);
    output_->setPlaceholderText(
        "Analysis results will appear here after you enter numeric data."
    );
    right->addWidget(output_);

    layout->addLayout(left, 3);
    layout->addLayout(right, 2);
    setCentralWidget(central);

    connect(run, &QPushButton::clicked, this, &MainWindow::runAnalysis);
}

void MainWindow::runAnalysis()
{
    QStringList values;
    for (int row = 0; row < table_->rowCount(); ++row) {
        auto* item = table_->item(row, 0);
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
