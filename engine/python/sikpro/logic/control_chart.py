from math import isfinite, sqrt
from statistics import mean


class ControlChartAnalyzer:
    """Statistical control-chart calculations for variable and attribute data."""

    RULE_NAMES = {
        1: "One point beyond 3 sigma",
        2: "Nine consecutive points on one side",
        3: "Six consecutive points increasing or decreasing",
        4: "Fourteen points alternating up and down",
        5: "Two of three points beyond 2 sigma on one side",
        6: "Four of five points beyond 1 sigma on one side",
        7: "Fifteen consecutive points within 1 sigma",
        8: "Eight consecutive points beyond 1 sigma on both sides",
    }

    XR = {
        2: (1.880, 0.000, 3.267, 1.128),
        3: (1.023, 0.000, 2.574, 1.693),
        4: (0.729, 0.000, 2.282, 2.059),
        5: (0.577, 0.000, 2.114, 2.326),
        6: (0.483, 0.000, 2.004, 2.534),
        7: (0.419, 0.076, 1.924, 2.704),
        8: (0.373, 0.136, 1.864, 2.847),
        9: (0.337, 0.184, 1.816, 2.970),
        10: (0.308, 0.223, 1.777, 3.078),
    }
    XS = {
        2: (2.659, 0.000, 3.267),
        3: (1.954, 0.000, 2.568),
        4: (1.628, 0.000, 2.266),
        5: (1.427, 0.000, 2.089),
        6: (1.287, 0.030, 1.970),
        7: (1.182, 0.118, 1.882),
        8: (1.099, 0.185, 1.815),
        9: (1.032, 0.239, 1.761),
        10: (0.975, 0.284, 1.716),
    }

    def analyze(self, dataset, chart_type="I-MR", options=None):
        chart_type = str(chart_type).strip()
        options = options or {}
        columns = getattr(dataset, "columns", 1)
        if chart_type in ("I-MR", "MR", "p", "np", "c", "u") and columns != 1:
            raise ValueError(f"{chart_type} Chart requires exactly one selected column.")
        if chart_type == "I-MR":
            return self._imr(dataset)
        if chart_type == "MR":
            return self._mr(dataset)
        if chart_type in ("X-bar R", "X-bar S"):
            return self._subgroup_chart(dataset, chart_type)
        if chart_type in ("p", "np", "c", "u"):
            return self._attribute_chart(dataset, chart_type, options)
        raise NotImplementedError(f"Control chart not supported: {chart_type}")

    @staticmethod
    def _number(value):
        if value is None or isinstance(value, bool):
            return None
        text = str(value).strip()
        if not text:
            return None
        try:
            number = float(text.replace(",", ""))
        except (TypeError, ValueError):
            return None
        return number if isfinite(number) else None

    @classmethod
    def _columns(cls, dataset):
        rows = dataset.data if hasattr(dataset, "data") else dataset
        columns = getattr(dataset, "columns", None)
        if columns is None:
            columns = max((len(row) for row in rows if isinstance(row, (list, tuple))), default=1)
        return rows, columns

    @classmethod
    def _values(cls, dataset, column=0):
        rows, _ = cls._columns(dataset)
        values = []
        for row in rows:
            cells = row if isinstance(row, (list, tuple)) else [row]
            value = cls._number(cells[column] if column < len(cells) else None)
            if value is not None:
                values.append(value)
        return values

    @classmethod
    def _imr(cls, dataset):
        values = cls._values(dataset, 0)
        if len(values) < 2:
            raise ValueError("I-MR Chart requires at least 2 numeric observations.")
        center = mean(values)
        moving_ranges = [abs(values[i] - values[i - 1]) for i in range(1, len(values))]
        mr_center = mean(moving_ranges)
        series = [
            {"title": "Individuals (I)", "values": values, "center": center,
             "ucl": center + 2.66 * mr_center, "lcl": center - 2.66 * mr_center},
            {"title": "Moving Range (MR)", "values": moving_ranges, "center": mr_center,
             "ucl": 3.267 * mr_center, "lcl": 0.0},
        ]
        return cls._result("I-MR", series, values, mr_center / 1.128)

    @classmethod
    def _mr(cls, dataset):
        values = cls._values(dataset, 0)
        if len(values) < 2:
            raise ValueError("MR Chart requires at least 2 numeric observations.")
        moving_ranges = [
            abs(values[index] - values[index - 1])
            for index in range(1, len(values))
        ]
        center = mean(moving_ranges)
        series = [{
            "title": "Moving Range (MR)",
            "values": moving_ranges,
            "center": center,
            "ucl": 3.267 * center,
            "lcl": 0.0,
        }]
        result = cls._result("MR", series, moving_ranges, None)
        result["rules"] = []
        return result

    @classmethod
    def _subgroup_chart(cls, dataset, chart_type):
        rows, columns = cls._columns(dataset)
        if columns < 2 or columns > 10:
            raise ValueError(f"{chart_type} requires 2 to 10 measurement columns per subgroup.")
        subgroups = []
        for row in rows:
            cells = row if isinstance(row, (list, tuple)) else [row]
            group = [cls._number(cells[i] if i < len(cells) else None) for i in range(columns)]
            if all(value is not None for value in group):
                subgroups.append(group)
        if len(subgroups) < 2:
            raise ValueError(f"{chart_type} requires at least two complete subgroups.")
        means = [mean(group) for group in subgroups]
        ranges = [max(group) - min(group) for group in subgroups]
        grand_mean = mean(means)
        rbar = mean(ranges)
        n = columns

        if chart_type == "X-bar R":
            a2, d3, d4, _ = cls.XR[n]
            series = [
                {"title": "X-bar", "values": means, "center": grand_mean,
                 "ucl": grand_mean + a2 * rbar, "lcl": grand_mean - a2 * rbar},
                {"title": "Range (R)", "values": ranges, "center": rbar,
                 "ucl": d4 * rbar, "lcl": d3 * rbar},
            ]
        else:
            a3, b3, b4 = cls.XS[n]
            s_values = []
            for group in subgroups:
                variance = sum((value - mean(group)) ** 2 for value in group) / (n - 1)
                s_values.append(sqrt(variance))
            sbar = mean(s_values)
            series = [
                {"title": "X-bar", "values": means, "center": grand_mean,
                 "ucl": grand_mean + a3 * sbar, "lcl": grand_mean - a3 * sbar},
                {"title": "Standard Deviation (S)", "values": s_values, "center": sbar,
                 "ucl": b4 * sbar, "lcl": b3 * sbar},
            ]
        sigma = (series[0]["ucl"] - series[0]["center"]) / 3
        return cls._result(chart_type, series, means, sigma)

    @classmethod
    def _attribute_chart(cls, dataset, chart_type, options):
        values = cls._values(dataset, 0)
        if not values:
            raise ValueError(f"{chart_type} Chart requires numeric count data.")
        if any(value < 0 for value in values):
            raise ValueError("Attribute chart counts cannot be negative.")
        if chart_type in ("p", "np", "c", "u") and any(value != int(value) for value in values):
            raise ValueError(f"{chart_type} Chart requires whole-number count data.")

        if chart_type in ("p", "np"):
            sample_size_value = cls._number(options.get("sample_size", 100))
            if (
                sample_size_value is None
                or sample_size_value < 1
                or not sample_size_value.is_integer()
            ):
                raise ValueError("Sample size must be a positive integer.")
            sample_size = int(sample_size_value)
            if any(value > sample_size for value in values):
                raise ValueError("Defective count cannot exceed the sample size.")
            pbar = sum(values) / (len(values) * sample_size)
            sigma = sqrt(pbar * (1 - pbar) / sample_size) if 0 <= pbar <= 1 else 0
            if chart_type == "p":
                points = [value / sample_size for value in values]
                center = pbar
                ucl, lcl = min(1.0, pbar + 3 * sigma), max(0.0, pbar - 3 * sigma)
            else:
                points = values
                center = sample_size * pbar
                spread = sample_size * sigma
                ucl, lcl = min(float(sample_size), center + 3 * spread), max(0.0, center - 3 * spread)
        elif chart_type == "c":
            points = values
            center = mean(values)
            spread = sqrt(center)
            ucl, lcl = center + 3 * spread, max(0.0, center - 3 * spread)
        else:
            unit_size = cls._number(options.get("unit_size", 1))
            if unit_size is None or unit_size <= 0:
                raise ValueError("Unit size must be a finite number greater than zero.")
            points = [value / unit_size for value in values]
            center = mean(points)
            spread = sqrt(center / unit_size)
            ucl, lcl = center + 3 * spread, max(0.0, center - 3 * spread)

        series = [{"title": f"{chart_type} Chart", "values": points,
                   "center": center, "ucl": ucl, "lcl": lcl}]
        sigma = (ucl - center) / 3 if ucl > center else 0
        return cls._result(chart_type, series, points, sigma, apply_rules=False)

    @classmethod
    def _result(cls, chart_type, series, primary_values, sigma, apply_rules=True):
        for item in series:
            item["out_of_control_points"] = [
                index + 1 for index, value in enumerate(item["values"])
                if value > item["ucl"] or value < item["lcl"]
            ]
        rules = cls._nelson_rules(primary_values, series[0]["center"], sigma) if apply_rules else []
        outside = sorted({
            point for item in series for point in item["out_of_control_points"]
        })
        rule_points = {point for rule in rules for point in rule["points"]}
        flagged = sorted(set(outside) | rule_points)
        return {
            "chart_type": chart_type,
            "count": len(primary_values),
            "series": series,
            "values": primary_values,
            "rules": rules,
            "out_of_control_points": flagged,
            "status": "OUT OF CONTROL" if flagged else "IN CONTROL",
        }

    @classmethod
    def _nelson_rules(cls, values, center, sigma):
        hits = {rule: set() for rule in range(1, 9)}
        if not values or sigma is None or sigma <= 0:
            return [
                {"rule": number, "name": cls.RULE_NAMES[number],
                 "violated": False, "points": []}
                for number in range(1, 9)
            ]
        z = [(value - center) / sigma for value in values]
        for i, value in enumerate(z):
            if abs(value) > 3:
                hits[1].add(i + 1)
        for start in range(len(z) - 8):
            window = z[start:start + 9]
            if all(v > 0 for v in window) or all(v < 0 for v in window):
                hits[2].update(range(start + 1, start + 10))
        for start in range(len(z) - 5):
            window = z[start:start + 6]
            if all(window[i] < window[i + 1] for i in range(5)) or all(
                window[i] > window[i + 1] for i in range(5)
            ):
                hits[3].update(range(start + 1, start + 7))
        for start in range(len(z) - 13):
            diffs = [z[start + i + 1] - z[start + i] for i in range(13)]
            if (all(diffs[i] > 0 for i in range(0, 13, 2)) and all(diffs[i] < 0 for i in range(1, 13, 2))) or (
                all(diffs[i] < 0 for i in range(0, 13, 2)) and all(diffs[i] > 0 for i in range(1, 13, 2))
            ):
                hits[4].update(range(start + 1, start + 15))
        for start in range(len(z) - 2):
            window = z[start:start + 3]
            positive = [i for i, v in enumerate(window) if v > 2]
            negative = [i for i, v in enumerate(window) if v < -2]
            if len(positive) >= 2:
                hits[5].update(start + i + 1 for i in positive)
            if len(negative) >= 2:
                hits[5].update(start + i + 1 for i in negative)
        for start in range(len(z) - 4):
            window = z[start:start + 5]
            positive = [i for i, v in enumerate(window) if v > 1]
            negative = [i for i, v in enumerate(window) if v < -1]
            if len(positive) >= 4:
                hits[6].update(start + i + 1 for i in positive)
            if len(negative) >= 4:
                hits[6].update(start + i + 1 for i in negative)
        for start in range(len(z) - 14):
            if all(-1 < v < 1 for v in z[start:start + 15]):
                hits[7].update(range(start + 1, start + 16))
        for start in range(len(z) - 7):
            window = z[start:start + 8]
            if all(abs(v) > 1 for v in window) and any(v > 1 for v in window) and any(v < -1 for v in window):
                hits[8].update(range(start + 1, start + 9))
        return [
            {"rule": number, "name": cls.RULE_NAMES[number],
             "violated": bool(hits[number]), "points": sorted(hits[number])}
            for number in range(1, 9)
        ]


class IMRChartAnalyzer:
    """Backward-compatible wrapper for the original I-MR engine API."""

    def analyze(self, dataset):
        return ControlChartAnalyzer().analyze(dataset, "I-MR")
