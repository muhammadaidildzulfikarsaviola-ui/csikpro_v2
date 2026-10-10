import sys
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


from sikpro.data import Dataset
from sikpro.engine import AnalysisEngine


class TestFrequency(unittest.TestCase):
    def test_frequency_distribution(self):

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
            "Frequency",
        )

        self.assertEqual(
            result["count"],
            7
        )

        rows = result["rows"]

        self.assertEqual(
            len(rows),
            4
        )

        self.assertEqual(
            rows[0]["value"],
            10.0
        )

        self.assertEqual(
            rows[0]["frequency"],
            1
        )

        self.assertAlmostEqual(
            rows[0]["percent"],
            14.285714285714286
        )

        self.assertEqual(
            rows[0]["cumulative"],
            1
        )

        self.assertEqual(
            rows[1]["value"],
            20.0
        )

        self.assertEqual(
            rows[1]["frequency"],
            2
        )

        self.assertAlmostEqual(
            rows[1]["percent"],
            28.57142857142857
        )

        self.assertEqual(
            rows[1]["cumulative"],
            3
        )

        self.assertEqual(
            rows[2]["value"],
            30.0
        )

        self.assertEqual(
            rows[2]["frequency"],
            3
        )

        self.assertAlmostEqual(
            rows[2]["percent"],
            42.857142857142854
        )

        self.assertEqual(
            rows[2]["cumulative"],
            6
        )

        self.assertEqual(
            rows[3]["value"],
            40.0
        )

        self.assertEqual(
            rows[3]["frequency"],
            1
        )

        self.assertAlmostEqual(
            rows[3]["percent"],
            14.285714285714285
        )

        self.assertEqual(
            rows[3]["cumulative"],
            7
        )
if __name__ == "__main__":
    unittest.main()