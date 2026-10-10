import math
import sys
import unittest
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from sikpro.data import Dataset
from sikpro.engine import AnalysisEngine


def make_dataset(rows):
    columns = max((len(row) for row in rows), default=1)
    dataset = Dataset(name="Edge case test", rows=len(rows), columns=columns)
    dataset.data = [list(row) for row in rows]
    return dataset


class TestAnalysisEdgeCases(unittest.TestCase):
    def setUp(self):
        self.engine = AnalysisEngine()

    def test_multicolumn_descriptive_results_are_independent(self):
        dataset = make_dataset([[1, 100], [2, 200], [3, 300]])
        result = self.engine.run(dataset, "Descriptive", "Summary Statistics")
        self.assertEqual(len(result["by_column"]), 2)
        self.assertEqual(result["by_column"][0]["result"]["mean"], 2.0)
        self.assertEqual(result["by_column"][1]["result"]["mean"], 200.0)
        self.assertEqual(result["count"], 6)

    def test_nonfinite_values_are_ignored_by_descriptive_and_frequency(self):
        dataset = make_dataset([[1], [float("inf")], [float("-inf")], [float("nan")], [3]])
        summary = self.engine.run(dataset, "Descriptive", "Summary Statistics")
        frequency = self.engine.run(dataset, "Descriptive", "Frequency")
        self.assertEqual(summary["count"], 2)
        self.assertEqual(summary["mean"], 2.0)
        self.assertEqual(frequency["count"], 2)
        self.assertEqual(sum(row["frequency"] for row in frequency["rows"]), 2)

    def test_all_invalid_numeric_data_returns_clear_error(self):
        dataset = make_dataset([[""], ["bad"], [None], [float("inf")]])
        with self.assertRaisesRegex(ValueError, "No numeric data"):
            self.engine.run(dataset, "Descriptive", "Summary Statistics")

    def test_parametric_distribution_fits_produce_parameters(self):
        dataset = make_dataset([[1], [2], [3], [4], [5]])
        for distribution in ("Normal", "Uniform", "Exponential", "Lognormal"):
            with self.subTest(distribution=distribution):
                result = self.engine.run(
                    dataset, "Descriptive", "Distribution",
                    {"distribution_type": distribution},
                )
                self.assertEqual(result["distribution_type"], distribution)
                self.assertTrue(result["fit_parameters"])
                self.assertEqual(len(result["expected_counts"]), len(result["bins"]))

    def test_distribution_rejects_values_outside_support(self):
        with self.assertRaisesRegex(ValueError, "non-negative"):
            self.engine.run(
                make_dataset([[-1], [2], [3]]), "Descriptive", "Distribution",
                {"distribution_type": "Exponential"},
            )
        with self.assertRaisesRegex(ValueError, "strictly positive"):
            self.engine.run(
                make_dataset([[0], [2], [3]]), "Descriptive", "Distribution",
                {"distribution_type": "Lognormal"},
            )

    def test_unknown_analysis_method_is_explicit(self):
        with self.assertRaisesRegex(NotImplementedError, "not implemented"):
            self.engine.run(make_dataset([[1]]), "Descriptive", "Unknown")


if __name__ == "__main__":
    unittest.main()
