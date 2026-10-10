from sikpro.logic import (
    SummaryStatisticsAnalyzer,
    FrequencyAnalyzer,
    DistributionAnalyzer,
    ControlChartAnalyzer,
    QualityToolsAnalyzer,
    ScatterPlotAnalyzer,
)


class AnalysisEngine:
    """Dispatch analysis methods to the corresponding calculation engines."""

    def __init__(self):
        self._analyzers = {
            ("Descriptive", "Summary Statistics"): SummaryStatisticsAnalyzer(),
            ("Descriptive", "Frequency"): FrequencyAnalyzer(),
            ("Descriptive", "Distribution"): DistributionAnalyzer(),
            ("Control Chart", "I-MR"): ControlChartAnalyzer(),
            ("Control Chart", "MR"): ControlChartAnalyzer(),
            ("Control Chart", "X-bar R"): ControlChartAnalyzer(),
            ("Control Chart", "X-bar S"): ControlChartAnalyzer(),
            ("Control Chart", "p"): ControlChartAnalyzer(),
            ("Control Chart", "np"): ControlChartAnalyzer(),
            ("Control Chart", "c"): ControlChartAnalyzer(),
            ("Control Chart", "u"): ControlChartAnalyzer(),
            ("Quality Tools", "Histogram"): QualityToolsAnalyzer(),
            ("Quality Tools", "Pareto Chart"): QualityToolsAnalyzer(),
            ("Quality Tools", "Check Sheet"): QualityToolsAnalyzer(),
            ("Quality Tools", "Fishbone"): QualityToolsAnalyzer(),
            ("Quality Tools", "Defect Concentration"): QualityToolsAnalyzer(),
            ("Relationship", "Scatter Plot"): ScatterPlotAnalyzer(),
        }

    def run(self, dataset, logic, method, options=None):
        key = (str(logic).strip(), str(method).strip())
        options = options or {}
        analyzer = self._analyzers.get(key)
        if analyzer is None:
            raise NotImplementedError(
                f"Analysis not implemented: {logic} / {method}"
            )

        if key[0] == "Control Chart":
            return analyzer.analyze(dataset, key[1], options)

        if key[0] == "Quality Tools":
            return analyzer.analyze(dataset, key[1], options)

        if key == ("Relationship", "Scatter Plot"):
            return analyzer.analyze(dataset)

        if key == ("Descriptive", "Distribution"):
            distribution_type = options.get("distribution_type", "Auto Detect")
            if getattr(dataset, "columns", 1) <= 1:
                return analyzer.analyze(dataset, distribution_type)
            return self._analyze_columns(
                dataset,
                lambda values: analyzer.analyze(values, distribution_type),
            )

        if getattr(dataset, "columns", 1) <= 1:
            return analyzer.analyze(dataset)

        return self._analyze_columns(dataset, analyzer.analyze)

    @staticmethod
    def _analyze_columns(dataset, analyze):
        """Analyze selected columns independently rather than pooling values."""
        source_columns = (
            getattr(dataset, "metadata", {}).get("analysis_columns", [])
        )
        results = []
        for index in range(dataset.columns):
            values = [
                [row[index] if index < len(row) else ""]
                for row in dataset.data
            ]
            column_result = analyze(values)
            original_index = (
                source_columns[index]
                if index < len(source_columns)
                else index
            )
            header = (
                dataset.headers[index]
                if index < len(getattr(dataset, "headers", []))
                else f"C{original_index + 1}"
            )
            label = f"C{original_index + 1}"
            if header and header != label:
                label = f"{label}  {header}"
            results.append({
                "column_index": original_index,
                "column_name": label,
                "result": column_result,
            })
        return {
            "by_column": results,
            "count": sum(
                item["result"].get("count", 0)
                for item in results
            ),
        }
