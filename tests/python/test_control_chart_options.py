import sys
import unittest
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from sikpro.data import Dataset
from sikpro.engine import AnalysisEngine


class TestControlChartOptionValidation(unittest.TestCase):
    def setUp(self):
        self.dataset = Dataset(name="Options", rows=3, columns=1)
        self.dataset.data = [[2], [3], [4]]
        self.engine = AnalysisEngine()

    def test_sample_size_must_be_a_positive_integer(self):
        for invalid in (0, -1, 2.5, float("nan"), float("inf"), "not a number"):
            with self.subTest(value=invalid):
                with self.assertRaisesRegex(ValueError, "positive integer"):
                    self.engine.run(
                        self.dataset, "Control Chart", "p",
                        {"sample_size": invalid},
                    )

    def test_unit_size_must_be_finite_and_positive(self):
        for invalid in (0, -1, float("nan"), float("inf"), float("-inf"), "bad"):
            with self.subTest(value=invalid):
                with self.assertRaisesRegex(ValueError, "finite number greater than zero"):
                    self.engine.run(
                        self.dataset, "Control Chart", "u",
                        {"unit_size": invalid},
                    )


if __name__ == "__main__":
    unittest.main()
