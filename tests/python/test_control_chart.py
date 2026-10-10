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
    dataset = Dataset(name="Control chart test", rows=len(rows), columns=columns)
    dataset.data = [list(row) for row in rows]
    return dataset


class TestControlCharts(unittest.TestCase):
    def setUp(self):
        self.engine = AnalysisEngine()

    def test_imr_and_mr(self):
        dataset = make_dataset([[10], [11], [9], [12], [10], [11]])
        imr = self.engine.run(dataset, "Control Chart", "I-MR")
        mr = self.engine.run(dataset, "Control Chart", "MR")
        self.assertEqual(imr["chart_type"], "I-MR")
        self.assertEqual(len(imr["series"]), 2)
        self.assertEqual(len(imr["rules"]), 8)
        self.assertEqual(mr["chart_type"], "MR")
        self.assertEqual(len(mr["series"][0]["values"]), 5)
        self.assertEqual(mr["rules"], [])
        self.assertEqual(mr["series"][0]["lcl"], 0.0)

    def test_xbar_r_and_xbar_s(self):
        dataset = make_dataset([
            [10.0, 10.1, 9.9],
            [10.2, 10.1, 10.0],
            [9.8, 10.0, 10.1],
            [10.1, 10.2, 10.0],
        ])
        for method in ("X-bar R", "X-bar S"):
            with self.subTest(method=method):
                result = self.engine.run(dataset, "Control Chart", method)
                self.assertEqual(result["chart_type"], method)
                self.assertEqual(len(result["series"]), 2)
                self.assertEqual(len(result["series"][0]["values"]), 4)
                for series in result["series"]:
                    self.assertLessEqual(series["lcl"], series["center"])
                    self.assertGreaterEqual(series["ucl"], series["center"])

    def test_attribute_charts_and_fixed_sample_size(self):
        dataset = make_dataset([[5], [7], [4], [6]])
        p = self.engine.run(dataset, "Control Chart", "p", {"sample_size": 100})
        np_chart = self.engine.run(dataset, "Control Chart", "np", {"sample_size": 100})
        c_chart = self.engine.run(dataset, "Control Chart", "c")
        u_chart = self.engine.run(dataset, "Control Chart", "u", {"unit_size": 10})

        self.assertAlmostEqual(p["series"][0]["center"], 0.055)
        self.assertAlmostEqual(np_chart["series"][0]["center"], 5.5)
        self.assertAlmostEqual(c_chart["series"][0]["center"], 5.5)
        self.assertAlmostEqual(u_chart["series"][0]["center"], 0.55)
        for result in (p, np_chart, c_chart, u_chart):
            self.assertEqual(result["rules"], [])

    def test_invalid_chart_inputs_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "sample size"):
            self.engine.run(make_dataset([[101], [2]]), "Control Chart", "p", {"sample_size": 100})
        with self.assertRaisesRegex(ValueError, "whole-number"):
            self.engine.run(make_dataset([[1.5], [2]]), "Control Chart", "c")
        with self.assertRaisesRegex(ValueError, "negative"):
            self.engine.run(make_dataset([[-1], [2]]), "Control Chart", "u")
        with self.assertRaisesRegex(ValueError, "at least 2"):
            self.engine.run(make_dataset([[1]]), "Control Chart", "I-MR")

    def test_subgroup_chart_requires_two_to_ten_columns(self):
        with self.assertRaisesRegex(ValueError, "2 to 10"):
            self.engine.run(make_dataset([[1], [2]]), "Control Chart", "X-bar R")


if __name__ == "__main__":
    unittest.main()
