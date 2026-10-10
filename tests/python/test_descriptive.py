import sys
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


from sikpro.data import Dataset
from sikpro.engine import AnalysisEngine


class TestSummaryStatistics(unittest.TestCase):

    def test_summary_statistics(self):
        dataset = Dataset(
            name="Test",
            rows=5,
            columns=1,
        )

        dataset.data = [
            [10],
            [20],
            [20],
            [30],
            [40],
        ]

        result = AnalysisEngine().run(
            dataset,
            "Descriptive",
            "Summary Statistics",
        )

        self.assertEqual(result["count"], 5)
        self.assertEqual(result["mean"], 24.0)
        self.assertEqual(result["median"], 20.0)
        self.assertEqual(result["mode"], 20.0)
        self.assertEqual(result["minimum"], 10.0)
        self.assertEqual(result["maximum"], 40.0)
        self.assertEqual(result["range"], 30.0)
        self.assertEqual(result["q1"], 15.0)
        self.assertEqual(result["q3"], 35.0)
        self.assertEqual(result["iqr"], 20.0)

    def test_blank_and_invalid_cells_are_ignored(self):
        dataset = Dataset(
            name="Test",
            rows=5,
            columns=1,
        )

        dataset.data = [
            [""],
            ["10"],
            ["abc"],
            [20],
            [None],
        ]

        result = AnalysisEngine().run(
            dataset,
            "Descriptive",
            "Summary Statistics",
        )

        self.assertEqual(result["count"], 2)
        self.assertEqual(result["mean"], 15.0)
        self.assertEqual(result["median"], 15.0)


if __name__ == "__main__":
    unittest.main()
