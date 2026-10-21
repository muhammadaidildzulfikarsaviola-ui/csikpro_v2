#include "MainWindow.h"
#include "bridge/PythonBridge.h"

#include <QAbstractItemView>
#include <QApplication>
#include <QByteArray>
#include <QComboBox>
#include <QClipboard>
#include <QFile>
#include <QFileDevice>
#include <QFileDialog>
#include <QFileInfo>
#include <QHeaderView>
#include <QHBoxLayout>
#include <QJsonArray>
#include <QJsonDocument>
#include <QJsonObject>
#include <QLabel>
#include <QInputDialog>
#include <QDialog>
#include <QDialogButtonBox>
#include <QDateTime>
#include <functional>
#include <QFormLayout>
#include <QCheckBox>
#include <QCloseEvent>
#include <QDoubleSpinBox>
#include <QListWidget>
#include <QSpinBox>
#include <QKeyEvent>
#include <QKeySequence>
#include <QLineEdit>
#include <QMenuBar>
#include <QMessageBox>
#include <QPlainTextEdit>
#include <QPushButton>
#include <QStatusBar>
#include <QSignalBlocker>
#include <QStringList>
#include <QTableWidget>
#include <QTextStream>
#include <QTabWidget>
#include <QToolBar>
#include <QVariant>
#include <QVBoxLayout>
#include <QWidget>
#include <QRegularExpression>
#include <QList>
#include <cmath>
#include <limits>
#include <stdexcept>

namespace {
class SpreadsheetTable final : public QTableWidget {
public:
    using QTableWidget::QTableWidget;
protected:
    void keyPressEvent(QKeyEvent* event) override
    {
        if (event->matches(QKeySequence::Copy)) {
            const auto ranges = selectedRanges();
            if (!ranges.isEmpty()) {
                const auto range = ranges.first();
                QStringList lines;
                for (int row = range.topRow(); row <= range.bottomRow(); ++row) {
                    QStringList cells;
                    for (int column = range.leftColumn(); column <= range.rightColumn(); ++column) {
                        auto* cell = item(row, column);
                        cells << (cell ? cell->text() : QString());
                    }
                    lines << cells.join('\t');
                }
                QApplication::clipboard()->setText(lines.join('\n'));
            }
            return;
        }
        if (event->matches(QKeySequence::Paste)) {
            const QStringList lines = QApplication::clipboard()->text().split(QRegularExpression("\\r?\\n"), Qt::SkipEmptyParts);
            const int startRow = currentRow() < 0 ? 0 : currentRow();
            const int startColumn = currentColumn() < 0 ? 0 : currentColumn();
            int neededColumns = columnCount();
            QList<QStringList> rows;
            for (const QString& line : lines) {
                rows << line.split(QRegularExpression("\\t"));
                neededColumns = qMax(neededColumns, startColumn + static_cast<int>(rows.last().size()));
            }
            if (!rows.isEmpty()) {
                setRowCount(qMax(rowCount(), startRow + static_cast<int>(rows.size())));
                setColumnCount(neededColumns);
                for (int column = 0; column < columnCount(); ++column)
                    if (!horizontalHeaderItem(column)) setHorizontalHeaderItem(column, new QTableWidgetItem(QString("C%1").arg(column + 1)));
                for (int r = 0; r < rows.size(); ++r)
                    for (int c = 0; c < rows[r].size(); ++c)
                        setItem(startRow + r, startColumn + c, new QTableWidgetItem(rows[r][c]));
            }
            return;
        }
        QTableWidget::keyPressEvent(event);
    }
};

QStringList splitCsv(const QString& line)
{
    QStringList fields;
    QString field;
    bool quoted = false;
    for (qsizetype i = 0; i < line.size(); ++i) {
        const QChar ch = line.at(i);
        if (ch == QLatin1Char('"')) {
            if (quoted && i + 1 < line.size() && line.at(i + 1) == QLatin1Char('"')) {
                field += ch;
                ++i;
            } else {
                quoted = !quoted;
            }
        } else if (ch == QLatin1Char(',') && !quoted) {
            fields << field;
            field.clear();
        } else {
            field += ch;
        }
    }
    fields << field;
    return fields;
}

QString csvField(QString value)
{
    if (value.contains(QLatin1Char(',')) || value.contains(QLatin1Char('"')) ||
        value.contains(QLatin1Char('\n')) || value.contains(QLatin1Char('\r')))
        value = QLatin1Char('"') + QString(value).replace("\"", "\"\"") + QLatin1Char('"');
    return value;
}

QString jsonCellText(const QJsonValue& value)
{
    if (value.isString()) return value.toString();
    if (value.isDouble()) return QString::number(value.toDouble(), 'g', 17);
    if (value.isBool()) return value.toBool() ? "true" : "false";
    if (value.isArray()) return QString::fromUtf8(QJsonDocument(value.toArray()).toJson(QJsonDocument::Compact));
    if (value.isObject()) return QString::fromUtf8(QJsonDocument(value.toObject()).toJson(QJsonDocument::Compact));
    return {};
}

constexpr int OriginalCellValueRole = Qt::UserRole;
constexpr int HasOriginalCellValueRole = Qt::UserRole + 1;

bool legacyInteger(const QJsonValue& value, int& result)
{
    if (value.isBool()) {
        result = value.toBool() ? 1 : 0;
        return true;
    }
    if (value.isString()) {
        QString text = value.toString().trimmed();
        if (text.isEmpty()) return false;
        int digitStart = (text.startsWith(QLatin1Char('+')) || text.startsWith(QLatin1Char('-'))) ? 1 : 0;
        if (digitStart == text.size()) return false;
        QString digits;
        digits.reserve(text.size());
        for (qsizetype i = 0; i < text.size(); ++i) {
            const QChar character = text.at(i);
            if (character == QLatin1Char('_')) {
                if (i <= digitStart || i + 1 >= text.size() || !text.at(i - 1).isDigit() || !text.at(i + 1).isDigit())
                    return false;
                continue;
            }
            if (i >= digitStart && !character.isDigit()) return false;
            digits.append(character);
        }
        bool ok = false;
        const qlonglong parsed = digits.toLongLong(&ok, 10);
        if (!ok || parsed < std::numeric_limits<int>::min() || parsed > std::numeric_limits<int>::max())
            return false;
        result = static_cast<int>(parsed);
        return true;
    }
    if (!value.isDouble()) return false;
    const double number = value.toDouble();
    if (!std::isfinite(number))
        return false;
    const double truncated = std::trunc(number);
    if (truncated < std::numeric_limits<int>::min() || truncated > std::numeric_limits<int>::max())
        return false;
    result = static_cast<int>(truncated);
    return true;
}

QStringList methodsForCategory(const QString& category)
{
    if (category == "Descriptive") return {"Summary Statistics", "Frequency", "Distribution"};
    if (category == "Control Chart") return {"I-MR", "MR", "X-bar R", "X-bar S", "p", "np", "c", "u"};
    if (category == "Quality Tools") return {"Histogram", "Pareto Chart", "Check Sheet", "Fishbone", "Defect Concentration"};
    if (category == "Relationship") return {"Scatter Plot"};
    return {};
}

bool isEngineNumeric(QString value)
{
    value = value.trimmed();
    if (value.isEmpty()) return false;
    value.remove(',');
    bool ok = false;
    const double number = value.toDouble(&ok);
    return ok && std::isfinite(number);
}

QString displayLabel(QString key)
{
    key.replace('_', ' ');
    if (!key.isEmpty()) key[0] = key[0].toUpper();
    return key;
}

QString resultText(const QJsonValue& value, const QString& label = {}, int depth = 0)
{
    const QString indent(depth * 2, QLatin1Char(' '));
    if (value.isObject()) {
        QString out;
        const QJsonObject object = value.toObject();
        const QString title = object.value("title").toString(object.value("column_name").toString(object.value("category").toString()));
        if (!title.isEmpty()) out += indent + title + "\n";
        for (auto it = object.begin(); it != object.end(); ++it) {
            if (it.key() == "title" || it.key() == "column_name" || it.key() == "category") continue;
            const QJsonValue child = it.value();
            if (child.isObject() || child.isArray())
                out += resultText(child, displayLabel(it.key()), depth + (title.isEmpty() ? 0 : 1));
            else
                out += QString(indent.size() + (title.isEmpty() ? 0 : 2), QLatin1Char(' ')) + displayLabel(it.key()) + ": " + jsonCellText(child) + "\n";
        }
        return out;
    }
    if (value.isArray()) {
        QString out;
        const QJsonArray array = value.toArray();
        if (!array.isEmpty() && array.first().isObject()) {
            const int shown = qMin(100, static_cast<int>(array.size()));
            for (int i = 0; i < shown; ++i)
                out += resultText(array[i], {}, depth);
            if (array.size() > shown)
                out += indent + QString("… %1 more records are available in Engine details (JSON).\n").arg(array.size() - shown);
        } else {
            QStringList values;
            const int shown = qMin(50, static_cast<int>(array.size()));
            for (int i = 0; i < shown; ++i) values << jsonCellText(array[i]);
            out += indent + (label.isEmpty() ? QString() : displayLabel(label) + ": ") + values.join(", ") + "\n";
            if (array.size() > shown)
                out += indent + QString("… %1 more values are available in Engine details (JSON).\n").arg(array.size() - shown);
        }
        return out;
    }
    return indent + (label.isEmpty() ? QString() : displayLabel(label) + ": ") + jsonCellText(value) + "\n";
}

const QStringList categories = {"Descriptive", "Control Chart", "Quality Tools", "Relationship"};
}

MainWindow::MainWindow(PythonBridge& bridge, QWidget* parent)
    : QMainWindow(parent), bridge_(bridge), table_(new SpreadsheetTable(30, 4, this)),
      output_(new QPlainTextEdit(this)), resultTable_(new QTableWidget(this)),
      category_(new QComboBox(this)),
      method_(new QComboBox(this)), datasetSelector_(new QComboBox(this)),
      rawOutput_(new QPlainTextEdit(this)),
      resultTabs_(new QTabWidget(this)),
      datasetName_("Dataset 1")
{
    setWindowTitle("SIKPRO | Statistical Process Control");
    resize(1280, 800);
    setMinimumSize(960, 620);

    auto* fileMenu = menuBar()->addMenu("&File");
    fileMenu->addAction("New dataset", this, &MainWindow::newDataset, QKeySequence::New);
    fileMenu->addAction("Open SPC project…", this, &MainWindow::openProject, QKeySequence::Open);
    fileMenu->addAction("Save SPC project…", this, &MainWindow::saveProject, QKeySequence::Save);
    fileMenu->addSeparator();
    fileMenu->addAction("Import CSV…", this, &MainWindow::importCsv);
    fileMenu->addAction("Export CSV…", this, &MainWindow::exportCsv);

    auto* toolbar = addToolBar("Dataset");
    toolbar->setMovable(false);
    toolbar->addAction("New", this, &MainWindow::newDataset);
    toolbar->addAction("Open", this, &MainWindow::openProject);
    toolbar->addAction("Save", this, &MainWindow::saveProject);
    toolbar->addSeparator();
    toolbar->addAction("Import CSV", this, &MainWindow::importCsv);
    toolbar->addAction("Export CSV", this, &MainWindow::exportCsv);

    auto* central = new QWidget(this);
    auto* root = new QHBoxLayout(central);
    root->setContentsMargins(12, 12, 12, 12);
    root->setSpacing(12);

    auto* sidebar = new QVBoxLayout();
    sidebar->addWidget(new QLabel("ANALYSIS", this));
    category_->addItems(categories);
    sidebar->addWidget(category_);
    sidebar->addWidget(method_);
    auto* run = new QPushButton("Run analysis", this);
    run->setDefault(true);
    sidebar->addWidget(run);
    sidebar->addSpacing(12);
    sidebar->addWidget(new QLabel("DATASET", this));
    sidebar->addWidget(datasetSelector_);
    auto* addDatasetButton = new QPushButton("Add dataset", this);
    auto* deleteDatasetButton = new QPushButton("Delete dataset", this);
    sidebar->addWidget(addDatasetButton);
    sidebar->addWidget(deleteDatasetButton);
    auto* addRowButton = new QPushButton("Add row", this);
    auto* addColumnButton = new QPushButton("Add column", this);
    auto* removeRowButton = new QPushButton("Remove selected row", this);
    auto* removeColumnButton = new QPushButton("Remove selected column", this);
    auto* clearButton = new QPushButton("Clear data", this);
    sidebar->addWidget(addRowButton);
    sidebar->addWidget(addColumnButton);
    sidebar->addWidget(removeRowButton);
    sidebar->addWidget(removeColumnButton);
    sidebar->addWidget(clearButton);
    sidebar->addStretch();
    auto* help = new QLabel("Edit headers by double-clicking them. Paste tabular data from a spreadsheet. Blank cells are ignored by numeric analyses.", this);
    help->setWordWrap(true);
    help->setStyleSheet("color: #667085;");
    sidebar->addWidget(help);
    sidebar->setSpacing(8);

    auto* workspace = new QVBoxLayout();
    auto* heading = new QLabel("Data worksheet", this);
    heading->setStyleSheet("font-size: 18px; font-weight: 600;");
    workspace->addWidget(heading);
    table_->setHorizontalHeaderLabels({"C1", "C2", "C3", "C4"});
    table_->horizontalHeader()->setSectionResizeMode(QHeaderView::Stretch);
    table_->verticalHeader()->setDefaultSectionSize(27);
    table_->setAlternatingRowColors(true);
    table_->setSelectionBehavior(QAbstractItemView::SelectItems);
    table_->setSelectionMode(QAbstractItemView::ExtendedSelection);
    table_->setEditTriggers(QAbstractItemView::DoubleClicked | QAbstractItemView::EditKeyPressed | QAbstractItemView::AnyKeyPressed);
    table_->setToolTip("Paste tab-separated data copied from Excel or another spreadsheet.");
    workspace->addWidget(table_, 1);

    auto* results = new QVBoxLayout();
    results->addWidget(new QLabel("RESULTS", this));
    output_->setReadOnly(true);
    output_->setPlaceholderText("Choose an analysis and run it to see a readable result summary.");
    rawOutput_->setReadOnly(true);
    rawOutput_->setPlaceholderText("The engine response is available as JSON for diagnostics.");
    resultTabs_->addTab(output_, "Summary");
    resultTable_->setColumnCount(3);
    resultTable_->setHorizontalHeaderLabels({"Section", "Field", "Value"});
    resultTable_->horizontalHeader()->setSectionResizeMode(QHeaderView::Stretch);
    resultTable_->setEditTriggers(QAbstractItemView::NoEditTriggers);
    resultTable_->setAlternatingRowColors(true);
    resultTabs_->addTab(resultTable_, "Result table");
    resultTabs_->addTab(rawOutput_, "Engine details (JSON)");
    results->addWidget(resultTabs_, 1);

    root->addLayout(sidebar, 1);
    root->addLayout(workspace, 4);
    root->addLayout(results, 2);
    setCentralWidget(central);
    statusBar()->showMessage("Ready");

    connect(category_, &QComboBox::currentTextChanged, this, [this] { updateMethodList(); analysisSelectionChanged_ = true; markProjectDirty(); });
    connect(method_, &QComboBox::currentTextChanged, this, [this] { analysisSelectionChanged_ = true; markProjectDirty(); });
    connect(run, &QPushButton::clicked, this, &MainWindow::runAnalysis);
    connect(addRowButton, &QPushButton::clicked, this, &MainWindow::addRow);
    connect(addColumnButton, &QPushButton::clicked, this, &MainWindow::addColumn);
    connect(removeRowButton, &QPushButton::clicked, this, &MainWindow::removeRow);
    connect(removeColumnButton, &QPushButton::clicked, this, &MainWindow::removeColumn);
    connect(clearButton, &QPushButton::clicked, this, &MainWindow::clearDataset);
    connect(table_, &QTableWidget::itemChanged, this, [this](QTableWidgetItem* item) {
        if (loadingDataset_) return;
        if (item->data(HasOriginalCellValueRole).toBool())
            item->setData(HasOriginalCellValueRole, false);
        markProjectDirty();
    });
    connect(addDatasetButton, &QPushButton::clicked, this, &MainWindow::addDataset);
    connect(deleteDatasetButton, &QPushButton::clicked, this, &MainWindow::deleteDataset);
    connect(datasetSelector_, qOverload<int>(&QComboBox::currentIndexChanged), this, &MainWindow::switchDataset);
    connect(table_->horizontalHeader(), &QHeaderView::sectionDoubleClicked, this, [this](int column) {
        bool accepted = false;
        const QString oldName = table_->horizontalHeaderItem(column)->text();
        const QString name = QInputDialog::getText(this, "Rename column", "Column name:", QLineEdit::Normal, oldName, &accepted).trimmed();
        if (accepted && !name.isEmpty()) { table_->horizontalHeaderItem(column)->setText(name); markProjectDirty(); }
    });
    updateMethodList();
    refreshDatasetList();
    projectDirty_ = false;
    analysisSelectionChanged_ = false;
    setWindowTitle("SIKPRO | Statistical Process Control");
}

void MainWindow::closeEvent(QCloseEvent* event)
{
    if (confirmDiscardChanges()) event->accept();
    else event->ignore();
}

void MainWindow::updateMethodList()
{
    method_->clear();
    method_->addItems(methodsForCategory(category_->currentText()));
}

void MainWindow::refreshDatasetList()
{
    const QSignalBlocker blocker(datasetSelector_);
    datasetSelector_->clear();
    const QJsonArray datasets = savedProjectState_.value("datasets").toArray();
    if (datasets.isEmpty()) {
        datasetSelector_->addItem(datasetName_);
        datasetSelector_->setCurrentIndex(0);
        return;
    }
    for (int i = 0; i < datasets.size(); ++i) {
        const QString name = datasets[i].toObject().value("name").toString("Dataset");
        datasetSelector_->addItem(name);
    }
    datasetSelector_->setCurrentIndex(qBound(0, savedProjectState_.value("active_index").toInt(0), static_cast<int>(datasets.size()) - 1));
}

void MainWindow::storeActiveDataset()
{
    const QJsonObject current = QJsonDocument::fromJson(datasetJson().toUtf8()).object();
    if (savedProjectState_.isEmpty()) {
        savedProjectState_ = {{"format", "SPC Dataset"}, {"version", 1}, {"project_name", datasetName_},
            {"active_index", 0}, {"datasets", QJsonArray{current}}, {"dataset_open", true},
            {"result_open", true}, {"analysis_history", QJsonArray{}},
            {"last_analysis_result", QJsonValue::Null}, {"last_analysis_method", QJsonValue::Null},
            {"last_analysis_analysis", QJsonValue::Null}};
        datasetSelector_->setCurrentIndex(0);
        return;
    }
    QJsonArray datasets = savedProjectState_.value("datasets").toArray();
    int index = savedProjectState_.value("active_index").toInt(0);
    if (datasets.isEmpty()) { datasets.append(current); index = 0; }
    else {
        index = qBound(0, index, static_cast<int>(datasets.size()) - 1);
        QJsonObject merged = datasets[index].toObject();
        for (const QString& key : {QStringLiteral("name"), QStringLiteral("rows"), QStringLiteral("columns"), QStringLiteral("headers"), QStringLiteral("data"), QStringLiteral("metadata")})
            if (current.contains(key)) merged.insert(key, current.value(key));
        datasets[index] = merged;
    }
    savedProjectState_.insert("datasets", datasets);
    savedProjectState_.insert("active_index", index);
    if (analysisSelectionChanged_ || !savedProjectState_.contains("selected_analysis"))
        savedProjectState_.insert("selected_analysis", category_->currentText());
    if (analysisSelectionChanged_ || !savedProjectState_.contains("selected_method"))
        savedProjectState_.insert("selected_method", method_->currentText());
    datasetName_ = current.value("name").toString(datasetName_);
    if (datasetSelector_->currentIndex() == index) datasetSelector_->setItemText(index, datasetName_);
}

void MainWindow::loadActiveDataset(int index)
{
    const QJsonArray datasets = savedProjectState_.value("datasets").toArray();
    if (index < 0 || index >= datasets.size()) return;
    const QJsonObject dataset = datasets[index].toObject();
    int rowCount = 200;
    int columnCount = 200;
    legacyInteger(dataset.value("rows"), rowCount);
    legacyInteger(dataset.value("columns"), columnCount);
    const QJsonArray headers = dataset.value("headers").toArray();
    const QJsonArray rows = dataset.value("data").toArray();
    loadingDataset_ = true;
    table_->clearContents();
    table_->setRowCount(rowCount);
    table_->setColumnCount(columnCount);
    for (int column = 0; column < columnCount; ++column) {
        const QString header = column < headers.size() ? jsonCellText(headers[column]) : QString();
        table_->setHorizontalHeaderItem(column, new QTableWidgetItem(header.isEmpty() ? QString("C%1").arg(column + 1) : header));
    }
    for (int row = 0; row < qMin(rowCount, static_cast<int>(rows.size())); ++row) {
        const QJsonArray values = rows[row].toArray();
        for (int column = 0; column < qMin(columnCount, static_cast<int>(values.size())); ++column) {
            auto* item = new QTableWidgetItem(jsonCellText(values[column]));
            item->setData(OriginalCellValueRole, values[column].toVariant());
            item->setData(HasOriginalCellValueRole, true);
            table_->setItem(row, column, item);
        }
    }
    datasetName_ = dataset.value("name").toString("Dataset");
    datasetMetadata_ = dataset.value("metadata").toObject();
    loadingDataset_ = false;
    datasetSelector_->setCurrentIndex(index);
    setWindowTitle(datasetName_ + (projectDirty_ ? " * | SIKPRO" : " | SIKPRO"));
    output_->clear();
    rawOutput_->clear();
    resultTable_->setRowCount(0);
}

void MainWindow::switchDataset(int index)
{
    if (index < 0) return;
    const int current = savedProjectState_.value("active_index").toInt(0);
    if (!savedProjectState_.isEmpty() && index == current) return;
    storeActiveDataset();
    savedProjectState_.insert("active_index", index);
    loadActiveDataset(index);
    markProjectDirty();
    setStatus("Active dataset changed.");
}

void MainWindow::addDataset()
{
    storeActiveDataset();
    QJsonObject dataset{{"name", QString("Dataset %1").arg(savedProjectState_.value("datasets").toArray().size() + 1)},
        {"rows", 30}, {"columns", 4}, {"headers", QJsonArray{"C1", "C2", "C3", "C4"}},
        {"data", QJsonArray{}}, {"metadata", QJsonObject{{"description", ""}, {"source", ""}, {"created_by", "SIKPRO V2"}}}};
    QJsonArray rows;
    for (int row = 0; row < 30; ++row) rows.append(QJsonArray{"", "", "", ""});
    dataset.insert("data", rows);
    QJsonArray datasets = savedProjectState_.value("datasets").toArray();
    datasets.append(dataset);
    const int index = datasets.size() - 1;
    savedProjectState_.insert("datasets", datasets);
    savedProjectState_.insert("active_index", index);
    refreshDatasetList();
    loadActiveDataset(index);
    markProjectDirty();
    setStatus("Dataset added.");
}

void MainWindow::deleteDataset()
{
    storeActiveDataset();
    QJsonArray datasets = savedProjectState_.value("datasets").toArray();
    if (datasets.size() <= 1) {
        QMessageBox::information(this, "Delete dataset", "A project must keep at least one dataset.");
        return;
    }
    const int removed = savedProjectState_.value("active_index").toInt(0);
    datasets.removeAt(removed);
    const int active = qMin(removed, static_cast<int>(datasets.size()) - 1);
    savedProjectState_.insert("datasets", datasets);
    savedProjectState_.insert("active_index", active);
    refreshDatasetList();
    loadActiveDataset(active);
    markProjectDirty();
    setStatus("Dataset deleted.");
}

QString MainWindow::datasetJson() const
{
    QJsonArray headers, rows;
    for (int column = 0; column < table_->columnCount(); ++column)
        headers.append(table_->horizontalHeaderItem(column) ? table_->horizontalHeaderItem(column)->text() : QString("C%1").arg(column + 1));
    for (int row = 0; row < table_->rowCount(); ++row) {
        QJsonArray values;
        for (int column = 0; column < table_->columnCount(); ++column) {
            auto* item = table_->item(row, column);
            if (item && item->data(HasOriginalCellValueRole).toBool()) {
                const QVariant original = item->data(OriginalCellValueRole);
                values.append(original.isValid() ? QJsonValue::fromVariant(original) : QJsonValue(QJsonValue::Null));
            } else {
                values.append(item ? QJsonValue(item->text()) : QJsonValue(QString()));
            }
        }
        rows.append(values);
    }
    QJsonObject metadata = datasetMetadata_;
    if (metadata.isEmpty()) metadata = {{"description", ""}, {"source", ""}, {"created_by", "SIKPRO V2"}};
    QJsonObject state{{"name", datasetName_}, {"rows", table_->rowCount()}, {"columns", table_->columnCount()},
                      {"headers", headers}, {"data", rows}, {"metadata", metadata}};
    return QString::fromUtf8(QJsonDocument(state).toJson(QJsonDocument::Compact));
}

void MainWindow::runAnalysis()
{
    const QString category = category_->currentText();
    const QString method = method_->currentText();
    QDialog dialog(this);
    dialog.setWindowTitle(category + " / " + method + " settings");
    auto* form = new QFormLayout(&dialog);
    auto* columns = new QListWidget(&dialog);
    columns->setSelectionMode(QAbstractItemView::NoSelection);
    columns->setMaximumHeight(220);
    const bool singleColumn = category == "Control Chart" &&
        (method == "I-MR" || method == "MR" || method == "p" || method == "np" || method == "c" || method == "u");
    const bool pairColumns = method == "Scatter Plot" || method == "Fishbone" || method == "Defect Concentration";
    for (int column = 0; column < table_->columnCount(); ++column) {
        const QString header = table_->horizontalHeaderItem(column)->text();
        auto* item = new QListWidgetItem(QString("C%1  %2").arg(column + 1).arg(header), columns);
        item->setFlags(item->flags() | Qt::ItemIsUserCheckable);
        const bool initiallyChecked = singleColumn ? column == 0 :
            pairColumns ? column < 2 :
            (category == "Control Chart" && (method == "X-bar R" || method == "X-bar S") ? column < qMin(4, table_->columnCount()) : true);
        item->setCheckState(initiallyChecked ? Qt::Checked : Qt::Unchecked);
    }
    form->addRow("Source columns", columns);

    auto* useRange = new QCheckBox("Limit observations to a row range", &dialog);
    auto* startRow = new QSpinBox(&dialog);
    auto* endRow = new QSpinBox(&dialog);
    startRow->setRange(1, table_->rowCount());
    endRow->setRange(1, table_->rowCount());
    startRow->setValue(1);
    endRow->setValue(table_->rowCount());
    startRow->setEnabled(false);
    endRow->setEnabled(false);
    QObject::connect(useRange, &QCheckBox::toggled, startRow, &QSpinBox::setEnabled);
    QObject::connect(useRange, &QCheckBox::toggled, endRow, &QSpinBox::setEnabled);
    auto* rangeFields = new QWidget(&dialog);
    auto* rangeLayout = new QHBoxLayout(rangeFields);
    rangeLayout->setContentsMargins(0, 0, 0, 0);
    rangeLayout->addWidget(useRange);
    rangeLayout->addWidget(new QLabel("From", rangeFields));
    rangeLayout->addWidget(startRow);
    rangeLayout->addWidget(new QLabel("To", rangeFields));
    rangeLayout->addWidget(endRow);
    form->addRow("Observation rows", rangeFields);

    QJsonObject options;
    if (category == "Control Chart" && (method == "p" || method == "np")) {
        auto* size = new QSpinBox(&dialog);
        size->setRange(1, 1000000000);
        size->setValue(100);
        form->addRow("Sample size per subgroup", size);
        QObject::connect(&dialog, &QDialog::accepted, &dialog, [&, size] { options.insert("sample_size", size->value()); });
    } else if (category == "Control Chart" && method == "u") {
        auto* size = new QDoubleSpinBox(&dialog);
        size->setRange(0.000001, 1.0e12);
        size->setDecimals(6);
        size->setValue(1.0);
        form->addRow("Units inspected per sample", size);
        QObject::connect(&dialog, &QDialog::accepted, &dialog, [&, size] { options.insert("unit_size", size->value()); });
    } else if (category == "Descriptive" && method == "Distribution") {
        auto* type = new QComboBox(&dialog);
        type->addItems({"Auto Detect", "Histogram", "Normal", "Uniform", "Exponential", "Lognormal"});
        form->addRow("Distribution model", type);
        QObject::connect(&dialog, &QDialog::accepted, &dialog, [&, type] { options.insert("distribution_type", type->currentText()); });
    } else if (category == "Quality Tools" && method == "Fishbone") {
        auto* problem = new QLineEdit("Effect / problem", &dialog);
        form->addRow("Effect / problem", problem);
        QObject::connect(&dialog, &QDialog::accepted, &dialog, [&, problem] { options.insert("problem", problem->text().trimmed().isEmpty() ? "Effect / problem" : problem->text().trimmed()); });
    }
    auto* buttons = new QDialogButtonBox(QDialogButtonBox::Ok | QDialogButtonBox::Cancel, &dialog);
    QObject::connect(buttons, &QDialogButtonBox::accepted, &dialog, &QDialog::accept);
    QObject::connect(buttons, &QDialogButtonBox::rejected, &dialog, &QDialog::reject);
    form->addRow(buttons);
    if (dialog.exec() != QDialog::Accepted) return;

    QList<int> selectedColumns;
    for (int column = 0; column < columns->count(); ++column)
        if (columns->item(column)->checkState() == Qt::Checked) selectedColumns << column;
    if (selectedColumns.isEmpty()) {
        QMessageBox::warning(this, "Select columns", "Choose at least one source column.");
        return;
    }
    if (singleColumn && selectedColumns.size() != 1) {
        QMessageBox::warning(this, method, "This chart requires exactly one source column.");
        return;
    }
    if (category == "Control Chart" && (method == "X-bar R" || method == "X-bar S") &&
        (selectedColumns.size() < 2 || selectedColumns.size() > 10)) {
        QMessageBox::warning(this, method, "Select between 2 and 10 measurement columns; each row is one subgroup.");
        return;
    }
    if (pairColumns && selectedColumns.size() < 2) {
        QMessageBox::warning(this, method, "Choose at least two columns. The first two selected columns are used.");
        return;
    }
    if (useRange->isChecked() && startRow->value() > endRow->value()) {
        QMessageBox::warning(this, "Invalid row range", "The first row must be less than or equal to the last row.");
        return;
    }

    output_->clear();
    rawOutput_->clear();
    resultTable_->setRowCount(0);
    storeActiveDataset();
    savedProjectState_.insert("last_analysis_result", QJsonValue::Null);
    savedProjectState_.insert("last_analysis_method", QJsonValue::Null);
    savedProjectState_.insert("last_analysis_analysis", QJsonValue::Null);
    markProjectDirty();
    QJsonArray headers, rows, originalColumns;
    const int firstRow = useRange->isChecked() ? startRow->value() - 1 : 0;
    const int lastRow = useRange->isChecked() ? endRow->value() : table_->rowCount();
    for (int column : selectedColumns) {
        headers.append(table_->horizontalHeaderItem(column)->text());
        originalColumns.append(column);
    }
    for (int row = firstRow; row < lastRow; ++row) {
        QJsonArray values;
        for (int column : selectedColumns) {
            auto* cell = table_->item(row, column);
            values.append(cell ? cell->text() : QString());
        }
        rows.append(values);
    }
    QJsonObject source = {{"name", datasetName_}, {"rows", static_cast<int>(rows.size())}, {"columns", static_cast<int>(headers.size())},
        {"headers", headers}, {"data", rows}, {"metadata", QJsonObject{{"analysis_columns", originalColumns}}}};
    const QString optionsJson = QString::fromUtf8(QJsonDocument(options).toJson(QJsonDocument::Compact));
    QString inputNote;
    const bool numericAnalysis = category == "Descriptive" || category == "Control Chart" ||
        (category == "Quality Tools" && method == "Histogram") ||
        (category == "Relationship" && method == "Scatter Plot");
    if (numericAnalysis) {
        if (category == "Control Chart" && (method == "X-bar R" || method == "X-bar S")) {
            int omittedSubgroups = 0;
            for (const QJsonValue& rowValue : rows) {
                bool complete = true;
                for (const QJsonValue& cell : rowValue.toArray())
                    if (!isEngineNumeric(cell.toString())) { complete = false; break; }
                if (!complete) ++omittedSubgroups;
            }
            if (omittedSubgroups > 0)
                inputNote = QString("%1 incomplete or nonnumeric subgroup rows will be omitted by the Python engine.").arg(omittedSubgroups);
        } else if (category == "Relationship" && method == "Scatter Plot") {
            int omittedPairs = 0;
            for (const QJsonValue& rowValue : rows) {
                const QJsonArray values = rowValue.toArray();
                if (values.size() < 2 || !isEngineNumeric(values[0].toString()) || !isEngineNumeric(values[1].toString()))
                    ++omittedPairs;
            }
            if (omittedPairs > 0)
                inputNote = QString("%1 rows have a missing or nonnumeric X/Y value and will be omitted by the Python engine.").arg(omittedPairs);
        } else {
            int blankCells = 0;
            int invalidCells = 0;
            for (const QJsonValue& rowValue : rows) {
                for (const QJsonValue& cell : rowValue.toArray()) {
                    const QString value = cell.toString().trimmed();
                    if (value.isEmpty()) ++blankCells;
                    else if (!isEngineNumeric(value)) ++invalidCells;
                }
            }
            if (blankCells > 0 || invalidCells > 0) {
                inputNote = QString("The Python engine will ignore %1 blank cell(s) and %2 nonnumeric or non-finite cell(s).")
                    .arg(blankCells).arg(invalidCells);
            }
        }
    }
    try {
        const std::string result = bridge_.analyze(QJsonDocument(source).toJson(QJsonDocument::Compact).toStdString(),
            category.toStdString(), method.toStdString(), optionsJson.toStdString());
        const QByteArray resultBytes = QByteArray::fromStdString(result);
        QJsonParseError resultError;
        const QJsonDocument resultDocument = QJsonDocument::fromJson(resultBytes, &resultError);
        if (resultError.error != QJsonParseError::NoError ||
            (!resultDocument.isObject() && !resultDocument.isArray())) {
            throw std::runtime_error("Analysis engine returned invalid structured JSON.");
        }
        displayResult(QString::fromUtf8(resultBytes));
        const QJsonObject resultObject = resultDocument.object();
        if (!inputNote.isEmpty()) {
            output_->appendPlainText("\nInput handling\n" + inputNote);
            const int row = resultTable_->rowCount();
            resultTable_->insertRow(row);
            resultTable_->setItem(row, 0, new QTableWidgetItem("Input handling"));
            resultTable_->setItem(row, 1, new QTableWidgetItem("Omitted values"));
            resultTable_->setItem(row, 2, new QTableWidgetItem(inputNote));
        }
        QJsonObject state = savedProjectState_;
        state.insert("last_analysis_result", resultObject);
        state.insert("last_analysis_method", method);
        state.insert("last_analysis_analysis", category);
        QJsonArray history = state.value("analysis_history").toArray();
        QJsonObject entry{{"analysis", category}, {"method", method}, {"dataset_name", datasetName_},
            {"dataset_index", state.value("active_index").toInt(0)}, {"columns", originalColumns},
            {"row_mode", useRange->isChecked() ? "range" : "all"},
            {"start_row", useRange->isChecked() ? startRow->value() : 1},
            {"end_row", useRange->isChecked() ? endRow->value() : table_->rowCount()},
            {"options", options}, {"result", resultObject},
            {"timestamp", QDateTime::currentDateTime().toString(Qt::ISODate)}};
        history.insert(0, entry);
        while (history.size() > 100) history.removeAt(static_cast<int>(history.size()) - 1);
        state.insert("analysis_history", history);
        savedProjectState_ = state;
        markProjectDirty();
        setStatus(category + " / " + method + " completed.");
    } catch (const std::exception& error) {
        output_->setPlainText(QString("%1 / %2 failed.\n\n%3")
            .arg(category, method, QString::fromUtf8(error.what()) +
                 (inputNote.isEmpty() ? QString() : "\n\n" + inputNote)));
        QMessageBox::warning(this, "Analysis could not run", QString::fromUtf8(error.what()));
        setStatus("Analysis failed. Review the input and chart requirements.");
    }
}

void MainWindow::addRow() { table_->insertRow(table_->rowCount()); markProjectDirty(); }
void MainWindow::addColumn()
{
    const int column = table_->columnCount();
    table_->insertColumn(column);
    table_->setHorizontalHeaderItem(column, new QTableWidgetItem(QString("C%1").arg(column + 1)));
    markProjectDirty();
}
void MainWindow::removeRow()
{
    const int row = table_->currentRow();
    if (row < 0) setStatus("Select a row to remove.");
    else if (table_->rowCount() <= 1) setStatus("At least one row must remain.");
    else { table_->removeRow(row); markProjectDirty(); }
}
void MainWindow::removeColumn()
{
    const int column = table_->currentColumn();
    if (column >= 0 && table_->columnCount() > 1) { table_->removeColumn(column); markProjectDirty(); }
    else setStatus("Select a column to remove. At least one column must remain.");
}

void MainWindow::clearDataset()
{
    if (QMessageBox::question(this, "Clear dataset", "Remove all cell values from this dataset?") != QMessageBox::Yes) return;
    table_->clearContents();
    markProjectDirty();
    setStatus("Dataset values cleared.");
}

void MainWindow::newDataset()
{
    if (!confirmDiscardChanges()) return;
    loadingDataset_ = true;
    datasetName_ = "Dataset 1";
    projectPath_.clear();
    savedProjectState_ = {};
    datasetMetadata_ = {};
    table_->clearContents();
    table_->setRowCount(30);
    table_->setColumnCount(4);
    for (int column = 0; column < 4; ++column)
        table_->setHorizontalHeaderItem(column, new QTableWidgetItem(QString("C%1").arg(column + 1)));
    loadingDataset_ = false;
    output_->clear();
    rawOutput_->clear();
    resultTable_->setRowCount(0);
    storeActiveDataset();
    refreshDatasetList();
    projectDirty_ = false;
    analysisSelectionChanged_ = false;
    setWindowTitle("SIKPRO | Statistical Process Control");
    setStatus("New dataset created.");
}

void MainWindow::importCsv()
{
    const QString path = QFileDialog::getOpenFileName(this, "Import data", {}, "CSV files (*.csv);;Text files (*.txt);;All files (*.*)");
    if (path.isEmpty()) return;
    QFile file(path);
    if (!file.open(QIODevice::ReadOnly | QIODevice::Text)) { QMessageBox::warning(this, "Import failed", file.errorString()); return; }
    QTextStream in(&file);
    QStringList lines;
    while (!in.atEnd()) lines << in.readLine();
    if (lines.isEmpty()) { QMessageBox::warning(this, "Import failed", "The selected file is empty."); return; }
    const QStringList headers = splitCsv(lines.takeFirst());
    int columns = headers.size();
    for (const QString& line : lines) columns = qMax(columns, static_cast<int>(splitCsv(line).size()));
    loadingDataset_ = true;
    table_->clearContents();
    table_->setRowCount(qMax(1, static_cast<int>(lines.size())));
    table_->setColumnCount(qMax(1, columns));
    for (int column = 0; column < table_->columnCount(); ++column)
        table_->setHorizontalHeaderItem(column, new QTableWidgetItem(column < headers.size() && !headers[column].isEmpty() ? headers[column] : QString("C%1").arg(column + 1)));
    for (int row = 0; row < lines.size(); ++row) {
        const QStringList fields = splitCsv(lines[row]);
        for (int column = 0; column < fields.size(); ++column) table_->setItem(row, column, new QTableWidgetItem(fields[column]));
    }
    loadingDataset_ = false;
    datasetName_ = QFileInfo(path).completeBaseName();
    storeActiveDataset();
    refreshDatasetList();
    markProjectDirty();
    setStatus(QString("Imported %1 data rows from %2.").arg(lines.size()).arg(QFileInfo(path).fileName()));
}

void MainWindow::exportCsv()
{
    const QString path = QFileDialog::getSaveFileName(this, "Export data", datasetName_ + ".csv", "CSV files (*.csv)");
    if (path.isEmpty()) return;
    QFile file(path);
    if (!file.open(QIODevice::WriteOnly | QIODevice::Text)) { QMessageBox::warning(this, "Export failed", file.errorString()); return; }
    QTextStream out(&file);
    for (int column = 0; column < table_->columnCount(); ++column) { if (column) out << ','; out << csvField(table_->horizontalHeaderItem(column) ? table_->horizontalHeaderItem(column)->text() : QString("C%1").arg(column + 1)); }
    out << "\r\n";
    for (int row = 0; row < table_->rowCount(); ++row) {
        for (int column = 0; column < table_->columnCount(); ++column) {
            if (column) out << ',';
            auto* item = table_->item(row, column);
            out << csvField(item ? item->text() : QString());
        }
        out << "\r\n";
    }
    out.flush();
    if (out.status() != QTextStream::Ok || file.error() != QFileDevice::NoError) {
        QMessageBox::warning(this, "Export failed", file.errorString().isEmpty() ? "The CSV data could not be written completely." : file.errorString());
        return;
    }
    setStatus("Dataset exported as CSV.");
}

QString MainWindow::projectJson() const
{
    const QJsonDocument dataset = QJsonDocument::fromJson(datasetJson().toUtf8());
    QJsonObject state = savedProjectState_;
    if (state.isEmpty()) {
        state = {{"format", "SPC Dataset"}, {"version", 1}, {"project_name", datasetName_},
            {"active_index", 0}, {"datasets", QJsonArray{dataset.object()}},
            {"dataset_open", true}, {"result_open", true}, {"analysis_history", QJsonArray{}},
            {"last_analysis_result", QJsonValue::Null}, {"last_analysis_method", QJsonValue::Null},
            {"last_analysis_analysis", QJsonValue::Null}};
    }
    QJsonArray datasets = state.value("datasets").toArray();
    int activeIndex = state.value("active_index").toInt(0);
    if (datasets.isEmpty()) { datasets.append(dataset.object()); activeIndex = 0; }
    else {
        if (activeIndex < 0 || activeIndex >= datasets.size()) activeIndex = 0;
        QJsonObject merged = datasets[activeIndex].toObject();
        for (const QString& key : {QStringLiteral("name"), QStringLiteral("rows"), QStringLiteral("columns"), QStringLiteral("headers"), QStringLiteral("data"), QStringLiteral("metadata")})
            if (dataset.object().contains(key)) merged.insert(key, dataset.object().value(key));
        datasets[activeIndex] = merged;
    }
    state.insert("datasets", datasets);
    state.insert("active_index", activeIndex);
    if (analysisSelectionChanged_ || !state.contains("selected_analysis"))
        state.insert("selected_analysis", category_->currentText());
    if (analysisSelectionChanged_ || !state.contains("selected_method"))
        state.insert("selected_method", method_->currentText());
    state.insert("project_name", datasetName_);
    return QString::fromUtf8(QJsonDocument(state).toJson(QJsonDocument::Indented));
}

void MainWindow::saveProject()
{
    storeActiveDataset();
    QString path = projectPath_;
    if (path.isEmpty()) path = QFileDialog::getSaveFileName(this, "Save SPC project", datasetName_ + ".spc", "SPC Dataset (*.spc)");
    if (path.isEmpty()) return;
    if (QFileInfo(path).suffix().isEmpty()) path += ".spc";
    QFile file(path);
    if (!file.open(QIODevice::WriteOnly | QIODevice::Text)) { QMessageBox::warning(this, "Save failed", file.errorString()); return; }
    QJsonObject state = QJsonDocument::fromJson(projectJson().toUtf8()).object();
    state.insert("project_name", QFileInfo(path).completeBaseName());
    const QByteArray contents = QJsonDocument(state).toJson(QJsonDocument::Indented);
    if (file.write(contents) != contents.size() || !file.flush() || file.error() != QFileDevice::NoError) {
        QMessageBox::warning(this, "Save failed", file.errorString().isEmpty() ? "The project file could not be written completely." : file.errorString());
        return;
    }
    projectPath_ = path;
    savedProjectState_ = state;
    projectDirty_ = false;
    analysisSelectionChanged_ = false;
    setWindowTitle(datasetName_ + " | SIKPRO");
    setStatus("SPC project saved.");
}

void MainWindow::openProject()
{
    const QString path = QFileDialog::getOpenFileName(this, "Open SPC project", {}, "SPC Dataset (*.spc);;All files (*.*)");
    if (!path.isEmpty() && confirmDiscardChanges()) loadProject(path);
}

void MainWindow::loadProject(const QString& path)
{
    QFile file(path);
    if (!file.open(QIODevice::ReadOnly | QIODevice::Text)) { QMessageBox::warning(this, "Open failed", file.errorString()); return; }
    QJsonParseError error;
    const QJsonDocument doc = QJsonDocument::fromJson(file.readAll(), &error);
    if (error.error != QJsonParseError::NoError || !doc.isObject()) { QMessageBox::warning(this, "Open failed", "The project file is not valid JSON."); return; }
    const QJsonObject state = doc.object();
    const QJsonArray datasets = state.value("datasets").toArray();
    if (state.value("format").toString() != "SPC Dataset" || datasets.isEmpty()) {
        QMessageBox::warning(this, "Open failed", "This is not a valid SPC Dataset project or it contains no datasets."); return;
    }
    int activeIndex = 0;
    if (state.contains("active_index") && !legacyInteger(state.value("active_index"), activeIndex)) {
        QMessageBox::warning(this, "Open failed", "The project active_index must be an integer or numeric integer string.");
        return;
    }
    if (activeIndex < 0 || activeIndex >= datasets.size()) {
        QMessageBox::warning(this, "Open failed", "The project active_index is outside the available dataset range.");
        return;
    }
    for (const QJsonValue& value : datasets) {
        if (!value.isObject()) { QMessageBox::warning(this, "Open failed", "Every project dataset must be an object."); return; }
        const QJsonObject dataset = value.toObject();
        int rows = 200;
        int columns = 200;
        if ((dataset.contains("rows") && !legacyInteger(dataset.value("rows"), rows)) ||
            (dataset.contains("columns") && !legacyInteger(dataset.value("columns"), columns))) {
            QMessageBox::warning(this, "Open failed", "Dataset row and column counts must be integers or numeric integer strings.");
            return;
        }
        if (rows < 1 || columns < 1 || rows > 1000000 || columns > 10000 ||
            static_cast<qint64>(rows) * columns > 1000000) {
            QMessageBox::warning(this, "Open failed", "A project dataset has invalid or excessively large dimensions.");
            return;
        }
    }
    const QString category = state.contains("selected_analysis")
        ? state.value("selected_analysis").toString() : QString("Control Chart");
    const QString method = state.contains("selected_method")
        ? state.value("selected_method").toString() : QString("I-MR");
    if (!methodsForCategory(category).contains(method)) {
        QMessageBox::warning(this, "Open failed", "The saved analysis category or method is unsupported.");
        return;
    }
    savedProjectState_ = state;
    savedProjectState_.insert("active_index", activeIndex);
    projectPath_ = path;
    category_->setCurrentText(category);
    updateMethodList();
    method_->setCurrentText(method);
    refreshDatasetList();
    loadActiveDataset(activeIndex);
    setWindowTitle(QFileInfo(path).completeBaseName() + " | SIKPRO");
    projectDirty_ = false;
    analysisSelectionChanged_ = false;
    setStatus("SPC project opened.");
}

void MainWindow::setStatus(const QString& message) { statusBar()->showMessage(message, 5000); }

void MainWindow::markProjectDirty()
{
    projectDirty_ = true;
    setWindowTitle(datasetName_ + " * | SIKPRO");
}

bool MainWindow::confirmDiscardChanges()
{
    if (!projectDirty_) return true;
    const QMessageBox::StandardButton choice = QMessageBox::warning(this, "Unsaved project changes",
        "The current project has unsaved changes.",
        QMessageBox::Save | QMessageBox::Discard | QMessageBox::Cancel,
        QMessageBox::Save);
    if (choice == QMessageBox::Discard) return true;
    if (choice == QMessageBox::Save) {
        saveProject();
        return !projectDirty_;
    }
    return false;
}

void MainWindow::displayResult(const QString& json)
{
    resultTable_->setRowCount(0);
    QJsonParseError error;
    const QJsonDocument document = QJsonDocument::fromJson(json.toUtf8(), &error);
    if (error.error != QJsonParseError::NoError) {
        output_->setPlainText("The analysis completed, but its result could not be displayed as JSON.");
        rawOutput_->setPlainText(json);
        resultTabs_->setCurrentWidget(output_);
        return;
    }
    const QJsonValue root = document.isObject() ? QJsonValue(document.object()) : QJsonValue(document.array());
    output_->setPlainText(resultText(root).trimmed());
    rawOutput_->setPlainText(QString::fromUtf8(document.toJson(QJsonDocument::Indented)));
    auto appendRow = [this](const QString& section, const QString& field, const QString& value) {
        const int row = resultTable_->rowCount();
        resultTable_->insertRow(row);
        resultTable_->setItem(row, 0, new QTableWidgetItem(section));
        resultTable_->setItem(row, 1, new QTableWidgetItem(field));
        resultTable_->setItem(row, 2, new QTableWidgetItem(value));
    };
    std::function<void(const QJsonValue&, const QString&)> collect;
    collect = [&](const QJsonValue& value, const QString& section) {
        if (value.isObject()) {
            const QJsonObject object = value.toObject();
            const QString title = object.value("title").toString(object.value("column_name").toString(object.value("category").toString()));
            const QString currentSection = title.isEmpty() ? section : (section.isEmpty() ? title : section + " / " + title);
            for (auto it = object.begin(); it != object.end(); ++it) {
                if (it.key() == "title" || it.key() == "column_name" || it.key() == "category") continue;
                if (it.value().isObject() || it.value().isArray()) collect(it.value(), currentSection + " / " + displayLabel(it.key()));
                else appendRow(currentSection, displayLabel(it.key()), jsonCellText(it.value()));
            }
        } else if (value.isArray()) {
            const QJsonArray array = value.toArray();
            if (!array.isEmpty() && (array.first().isObject() || array.first().isArray())) {
                const int shown = qMin(100, static_cast<int>(array.size()));
                for (int i = 0; i < shown; ++i) {
                    const QJsonValue child = array[i];
                    QString itemName = child.toObject().value("title").toString(child.toObject().value("column_name").toString(child.toObject().value("category").toString()));
                    if (itemName.isEmpty()) itemName = QString("Item %1").arg(i + 1);
                    collect(child, section + " / " + itemName);
                }
                if (array.size() > shown)
                    appendRow(section, "Additional records", QString("%1 more; see Engine details (JSON)").arg(array.size() - shown));
            } else {
                QStringList values;
                const int shown = qMin(50, static_cast<int>(array.size()));
                for (int i = 0; i < shown; ++i) values << jsonCellText(array[i]);
                appendRow(section, "Values", values.join(", "));
                if (array.size() > shown)
                    appendRow(section, "Additional values", QString("%1 more; see Engine details (JSON)").arg(array.size() - shown));
            }
        } else {
            appendRow(section.isEmpty() ? "Result" : section, "Value", jsonCellText(value));
        }
    };
    collect(root, "");
    if (output_->toPlainText().trimmed().isEmpty())
        output_->setPlainText("The analysis returned no result fields. See Engine details (JSON) for the raw response.");
    if (resultTable_->rowCount() == 0)
        appendRow("Result", "Summary", "No result fields were returned.");
    resultTabs_->setCurrentWidget(output_);
}
