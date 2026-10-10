from math import ceil, sqrt, isfinite, exp, log, pi


class DistributionAnalyzer:
    """Build histogram data and overlay selected theoretical distributions."""

    SUPPORTED_DISTRIBUTIONS = ("Histogram", "Normal", "Uniform", "Exponential", "Lognormal")

    def analyze(self, data, distribution_type="Auto Detect"):
        requested_type = str(distribution_type or "Auto Detect").strip() or "Auto Detect"
        if requested_type == "Auto Detect":
            actual_type = "Histogram"
        elif requested_type in self.SUPPORTED_DISTRIBUTIONS:
            actual_type = requested_type
        else:
            raise NotImplementedError(
                f"Distribution type not implemented: {requested_type}. "
                f"Available: {', '.join(self.SUPPORTED_DISTRIBUTIONS)}."
            )

        values = self._extract_numeric_values(data)
        if not values:
            raise ValueError("No numeric data available for analysis.")

        minimum, maximum, count = min(values), max(values), len(values)
        if minimum == maximum:
            if actual_type != "Histogram":
                raise ValueError(
                    f"{actual_type} fit needs at least two distinct numeric values."
                )
            return {
                "count": count,
                "minimum": minimum,
                "maximum": maximum,
                "distribution_type": actual_type,
                "requested_distribution_type": requested_type,
                "bins": [{"lower": minimum, "upper": maximum, "frequency": count}],
                "fit_parameters": {},
                "expected_counts": [],
            }

        bin_count = max(1, ceil(sqrt(count)))
        width = (maximum - minimum) / bin_count
        bins = []
        for index in range(bin_count):
            lower = minimum + index * width
            upper = maximum if index == bin_count - 1 else minimum + (index + 1) * width
            bins.append({"lower": lower, "upper": upper, "frequency": 0})

        for value in values:
            index = min(int((value - minimum) / width), bin_count - 1)
            bins[index]["frequency"] += 1

        fit_parameters = {}
        expected_counts = []
        if actual_type != "Histogram":
            fit_parameters, expected_counts = self._fit_distribution(
                values, bins, actual_type
            )

        return {
            "count": count,
            "minimum": minimum,
            "maximum": maximum,
            "distribution_type": actual_type,
            "requested_distribution_type": requested_type,
            "bins": bins,
            "fit_parameters": fit_parameters,
            "expected_counts": expected_counts,
        }

    @staticmethod
    def _fit_distribution(values, bins, distribution_type):
        count = len(values)
        centers = [(item["lower"] + item["upper"]) / 2 for item in bins]
        width = bins[0]["upper"] - bins[0]["lower"]
        parameters = {}

        if distribution_type == "Normal":
            mu = sum(values) / count
            sigma = sqrt(sum((value - mu) ** 2 for value in values) / count)
            if sigma <= 0:
                raise ValueError("Normal fit requires non-zero variation.")
            parameters = {"mean": mu, "standard_deviation": sigma}
            pdf = lambda x: exp(-0.5 * ((x - mu) / sigma) ** 2) / (sigma * sqrt(2 * pi))

        elif distribution_type == "Uniform":
            lower, upper = min(values), max(values)
            if upper <= lower:
                raise ValueError("Uniform fit requires at least two distinct values.")
            parameters = {"minimum": lower, "maximum": upper}
            pdf = lambda x: 1 / (upper - lower) if lower <= x <= upper else 0.0

        elif distribution_type == "Exponential":
            if any(value < 0 for value in values):
                raise ValueError("Exponential fit requires non-negative data.")
            mu = sum(values) / count
            if mu <= 0:
                raise ValueError("Exponential fit requires a positive mean.")
            rate = 1 / mu
            parameters = {"rate": rate, "mean": mu}
            pdf = lambda x: rate * exp(-rate * x) if x >= 0 else 0.0

        elif distribution_type == "Lognormal":
            if any(value <= 0 for value in values):
                raise ValueError("Lognormal fit requires strictly positive data.")
            logged = [log(value) for value in values]
            mu = sum(logged) / count
            sigma = sqrt(sum((value - mu) ** 2 for value in logged) / count)
            if sigma <= 0:
                raise ValueError("Lognormal fit requires non-zero variation.")
            parameters = {"mu_log": mu, "sigma_log": sigma}
            def pdf(x):
                if x <= 0:
                    return 0.0
                return exp(-0.5 * ((log(x) - mu) / sigma) ** 2) / (x * sigma * sqrt(2 * pi))
        else:
            return {}, []

        expected = [max(0.0, pdf(center) * width * count) for center in centers]
        return parameters, expected

    def _extract_numeric_values(self, data):
        if hasattr(data, "data"):
            data = data.data
        values = []
        for item in data:
            cells = item if isinstance(item, (list, tuple)) else [item]
            for value in cells:
                number = self._to_number(value)
                if number is not None:
                    values.append(number)
        return values

    @staticmethod
    def _to_number(value):
        if value is None or isinstance(value, bool):
            return None
        try:
            number = float(str(value).strip().replace(",", ""))
        except (TypeError, ValueError):
            return None
        return number if isfinite(number) else None
