from collections import Counter
from math import isfinite


class FrequencyAnalyzer:
    """Calculate frequency distribution from numeric dataset values."""

    def analyze(self, data):
        values = self._extract_numeric_values(data)

        if not values:
            raise ValueError("No numeric data available for analysis.")

        counts = Counter(values)
        total = len(values)

        rows = []
        cumulative = 0

        for value in sorted(counts):
            frequency = counts[value]
            cumulative += frequency

            rows.append({
                "value": value,
                "frequency": frequency,
                "percent": (frequency / total) * 100,
                "cumulative": cumulative,
            })

        return {
            "count": total,
            "rows": rows,
        }

    def _extract_numeric_values(self, data):
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