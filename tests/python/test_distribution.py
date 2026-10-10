import sys
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


from sikpro.data import Dataset
from sikpro.engine import AnalysisEngine


class TestDistribution(unittest.TestCase):

    def test_distribution(self):

        dataset = Dataset(
            name="Test",
            rows=7,
            columns=1,
        )

        dataset.data = [
            [10],
            [20],
            [20],
            [30],
            [30],
            [30],
            [40],
        ]

        result = AnalysisEngine().run(
            dataset,
            "Descriptive",
            "Distribution",
        )

        self.assertEqual(
            result["count"],
            7
        )

        self.assertEqual(
            result["minimum"],
            10.0
        )

        self.assertEqual(
            result["maximum"],
            40.0
        )

        self.assertEqual(
            sum(
                item["frequency"]
                for item in result["bins"]
            ),
            7
        )

    def test_blank_and_invalid_cells_are_ignored(self):

        dataset = Dataset(
            name="Test",
            rows=6,
            columns=1,
        )

        dataset.data = [
            [""],
            [10],
            ["abc"],
            [10],
            [20],
            [None],
        ]

        result = AnalysisEngine().run(
            dataset,
            "Descriptive",
            "Distribution",
        )

        self.assertEqual(
            result["count"],
            3
        )

        self.assertEqual(
            result["minimum"],
            10.0
        )

        self.assertEqual(
            result["maximum"],
            20.0
        )


if __name__ == "__main__":
    unittest.main()