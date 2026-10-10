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
    dataset = Dataset(name="Quality tools test", rows=len(rows), columns=columns)
    dataset.data = [list(row) for row in rows]
    return dataset


class TestQualityTools(unittest.TestCase):
    def setUp(self):
        self.engine = AnalysisEngine()

    def test_pareto_frequency_order_and_cumulative_percent(self):
        dataset = make_dataset([
            ["Scratch"], ["Scratch"], ["Dent"], ["Other"], [""]
        ])
        result = self.engine.run(dataset, "Quality Tools", "Pareto Chart")
        column = result["by_column"][0]
        self.assertEqual(column["total"], 4)
        self.assertEqual(column["items"][0]["category"], "Scratch")
        self.assertEqual(column["items"][0]["count"], 2)
        self.assertAlmostEqual(column["items"][-1]["cumulative_percent"], 100.0)

    def test_check_sheet_counts_nonempty_categories(self):
        dataset = make_dataset([["A"], ["B"], ["A"], [""], [None]])
        result = self.engine.run(dataset, "Quality Tools", "Check Sheet")
        items = {item["category"]: item["count"] for item in result["by_column"][0]["items"]}
        self.assertEqual(items, {"A": 2, "B": 1})
        self.assertEqual(result["by_column"][0]["total"], 3)

    def test_fishbone_supports_mother_nature_alias(self):
        dataset = make_dataset([
            ["Mother Nature", "Humidity is high"],
            ["Machine", "Blade is worn"],
        ])
        result = self.engine.run(
            dataset, "Quality Tools", "Fishbone",
            {"problem": "High defect rate"},
        )
        self.assertEqual(result["problem"], "High defect rate")
        branches = {branch["category"]: branch["causes"] for branch in result["branches"]}
        self.assertIn("Humidity is high", branches["Environment"])
        self.assertIn("Blade is worn", branches["Machine"])
        self.assertNotIn("Mother Nature: Humidity is high", branches["Method"])

    def test_defect_concentration_counts_location_pairs(self):
        dataset = make_dataset([
            ["Front", "Left"], ["Front", "Left"],
            ["Front", "Right"], ["Back", "Left"],
        ])
        result = self.engine.run(dataset, "Quality Tools", "Defect Concentration")
        counts = {(point["x"], point["y"]): point["count"] for point in result["points"]}
        self.assertEqual(counts[("Front", "Left")], 2)
        self.assertEqual(result["total"], 4)

    def test_scatter_plot_reports_perfect_positive_correlation(self):
        dataset = make_dataset([[1, 2], [2, 4], [3, 6], [4, 8]])
        result = self.engine.run(dataset, "Relationship", "Scatter Plot")
        self.assertEqual(result["count"], 4)
        self.assertAlmostEqual(result["correlation"], 1.0)

    def test_scatter_plot_rejects_insufficient_columns(self):
        dataset = make_dataset([[1], [2]])
        with self.assertRaisesRegex(ValueError, "at least two selected columns"):
            self.engine.run(dataset, "Relationship", "Scatter Plot")


if __name__ == "__main__":
    unittest.main()
