from math import isfinite
from statistics import mean, median, multimode, pstdev, pvariance, stdev, variance


class SummaryStatisticsAnalyzer:
    """Calculate descriptive summary statistics from dataset values."""

    def analyze(self, data):
        values = self._extract_numeric_values(data)

        if not values:
            raise ValueError("No numeric data available for analysis.")

        count = len(values)
        minimum = min(values)
        maximum = max(values)

        result = {
            "count": count,
            "mean": mean(values),
            "median": median(values),
            "mode": self._mode(values),
            "minimum": minimum,
            "maximum": maximum,
            "range": maximum - minimum,
            "variance": pvariance(values),
            "std_dev": pstdev(values),
        }

        if count >= 2:
            result["sample_variance"] = variance(values)
            result["sample_std_dev"] = stdev(values)
        else:
            result["sample_variance"] = None
            result["sample_std_dev"] = None

        if count >= 2:
            sorted_values = sorted(values)
            midpoint = count // 2

            if count % 2 == 0:
                lower = sorted_values[:midpoint]
                upper = sorted_values[midpoint:]
            else:
                lower = sorted_values[:midpoint]
                upper = sorted_values[midpoint + 1:]

            q1 = median(lower) if lower else sorted_values[0]
            q3 = median(upper) if upper else sorted_values[-1]
        else:
            q1 = values[0]
            q3 = values[0]

        result["q1"] = q1
        result["q3"] = q3
        result["iqr"] = q3 - q1

        return result

    def _extract_numeric_values(self, data):
        """Extract valid numeric values from a Dataset or nested iterable."""
        if hasattr(data, "data"):
            data = data.data

        values = []

        for item in data:
            if isinstance(item, (list, tuple)):
                for value in item:
                    number = self._to_number(value)
                    if number is not None:
                        values.append(number)
            else:
                number = self._to_number(item)
                if number is not None:
                    values.append(number)

        return values

    @staticmethod
    def _to_number(value):
        if value is None:
            return None

        if isinstance(value, bool):
            return None

        if isinstance(value, (int, float)):
            number = float(value)
            return None if not isfinite(number) else number

        text = str(value).strip()

        if not text:
            return None

        try:
            number = float(text.replace(",", ""))
        except (TypeError, ValueError):
            return None

        return None if not isfinite(number) else number

    @staticmethod
    def _mode(values):
        modes = multimode(values)

        if not modes:
            return None

        if len(modes) == 1:
            return modes[0]

        return modes
