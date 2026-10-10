from collections import Counter
from math import isfinite

from sikpro.logic.distribution import DistributionAnalyzer


class QualityToolsAnalyzer:
    """Data-driven implementations of common quality tools."""

    FISHBONE_CATEGORIES = (
        "Man", "Machine", "Method", "Material", "Measurement", "Environment"
    )

    def analyze(self, dataset, method, options=None):
        method = str(method).strip()
        options = options or {}
        rows = getattr(dataset, "data", dataset)
        columns = getattr(dataset, "columns", None)
        if columns is None:
            columns = max((len(row) for row in rows if isinstance(row, (list, tuple))), default=1)

        if method == "Histogram":
            return self._histogram(dataset)
        if method == "Pareto Chart":
            return self._pareto(rows, columns)
        if method == "Check Sheet":
            return self._check_sheet(rows, columns)
        if method == "Fishbone":
            return self._fishbone(rows, columns, options)
        if method == "Defect Concentration":
            return self._defect_concentration(rows, columns)
        raise NotImplementedError(f"Quality tool not supported: {method}")

    @staticmethod
    def _cell(row, index):
        cells = row if isinstance(row, (list, tuple)) else [row]
        if index >= len(cells):
            return None
        value = cells[index]
        if value is None:
            return None
        value = str(value).strip()
        return value or None

    @staticmethod
    def _histogram(dataset):
        analyzer = DistributionAnalyzer()
        rows = dataset.data
        headers = getattr(dataset, "headers", [])
        results = []
        for index in range(getattr(dataset, "columns", 1)):
            single = [[row[index] if index < len(row) else ""] for row in rows]
            result = analyzer.analyze(single, "Histogram")
            name = headers[index] if index < len(headers) else f"C{index + 1}"
            results.append({"column_index": index, "column_name": f"C{index + 1}  {name}", "result": result})
        if len(results) == 1:
            return results[0]["result"]
        return {"tool": "Histogram", "by_column": results}

    def _pareto(self, rows, columns):
        if columns < 1:
            raise ValueError("Pareto Chart requires at least one selected column.")
        by_column = []
        for index in range(columns):
            values = [self._cell(row, index) for row in rows]
            counts = Counter(value for value in values if value is not None)
            if not counts:
                continue
            ordered = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
            total = sum(counts.values())
            cumulative = 0
            items = []
            for category, count in ordered:
                cumulative += count
                items.append({
                    "category": category,
                    "count": count,
                    "percent": count / total * 100,
                    "cumulative_percent": cumulative / total * 100,
                })
            by_column.append({"column_index": index, "column_name": f"C{index + 1}", "items": items, "total": total})
        if not by_column:
            raise ValueError("No non-empty categories found for Pareto Chart.")
        return {"tool": "Pareto Chart", "by_column": by_column}

    def _check_sheet(self, rows, columns):
        by_column = []
        for index in range(columns):
            counts = Counter(
                value for value in (self._cell(row, index) for row in rows)
                if value is not None
            )
            if counts:
                by_column.append({
                    "column_index": index,
                    "column_name": f"C{index + 1}",
                    "items": [
                        {"category": category, "count": count}
                        for category, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))
                    ],
                    "total": sum(counts.values()),
                })
        if not by_column:
            raise ValueError("No non-empty data found for Check Sheet.")
        return {"tool": "Check Sheet", "by_column": by_column}

    def _fishbone(self, rows, columns, options=None):
        branches = {name: [] for name in self.FISHBONE_CATEGORIES}
        if columns >= 2:
            for row in rows:
                category = self._cell(row, 0)
                cause = self._cell(row, 1)
                if not category or not cause:
                    continue
                normalized = category.strip().lower()
                aliases = {
                    "mother nature": "Environment",
                    "environmental": "Environment",
                }
                matched = aliases.get(normalized) or next(
                    (name for name in branches if name.lower() == normalized),
                    None,
                )
                if matched:
                    branches[matched].append(cause)
                else:
                    branches["Method"].append(f"{category}: {cause}")
        return {
            "tool": "Fishbone",
            "problem": (options or {}).get("problem", "Effect / problem"),
            "branches": [
                {"category": category, "causes": causes}
                for category, causes in branches.items()
            ],
            "instructions": "Optional input format: first selected column = 6M category; second selected column = cause.",
        }

    def _defect_concentration(self, rows, columns):
        if columns < 2:
            raise ValueError("Defect Concentration requires two columns: location X and location Y.")
        counts = Counter()
        for row in rows:
            x = self._cell(row, 0)
            y = self._cell(row, 1)
            if x is not None and y is not None:
                counts[(x, y)] += 1
        if not counts:
            raise ValueError("No coordinate/location pairs found for Defect Concentration.")
        return {
            "tool": "Defect Concentration",
            "x_label": "Location X (C1)",
            "y_label": "Location Y (C2)",
            "points": [
                {"x": x, "y": y, "count": count}
                for (x, y), count in sorted(counts.items())
            ],
            "total": sum(counts.values()),
        }


class ScatterPlotAnalyzer:
    """Build scatter-plot points from the first two selected numeric columns."""

    @staticmethod
    def _number(value):
        if value is None or isinstance(value, bool):
            return None
        try:
            number = float(str(value).strip().replace(",", ""))
        except (TypeError, ValueError):
            return None
        return number if isfinite(number) else None

    def analyze(self, dataset):
        if getattr(dataset, "columns", 0) < 2:
            raise ValueError("Scatter Plot requires at least two selected columns.")
        points = []
        for row_index, row in enumerate(dataset.data):
            if len(row) < 2:
                continue
            x, y = self._number(row[0]), self._number(row[1])
            if x is not None and y is not None:
                points.append({"x": x, "y": y, "row": row_index + 1})
        if len(points) < 2:
            raise ValueError("Scatter Plot requires at least two rows with numeric X and Y values.")

        xs = [point["x"] for point in points]
        ys = [point["y"] for point in points]
        x_mean = sum(xs) / len(xs)
        y_mean = sum(ys) / len(ys)
        denominator = sum((x - x_mean) ** 2 for x in xs) * sum((y - y_mean) ** 2 for y in ys)
        correlation = None
        if denominator > 0:
            correlation = sum((x - x_mean) * (y - y_mean) for x, y in zip(xs, ys)) / denominator ** 0.5
        headers = getattr(dataset, "headers", [])
        return {
            "tool": "Scatter Plot",
            "x_label": headers[0] if headers else "C1",
            "y_label": headers[1] if len(headers) > 1 else "C2",
            "points": points,
            "count": len(points),
            "correlation": correlation,
        }
