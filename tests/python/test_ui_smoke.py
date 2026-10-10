import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


@unittest.skipUnless(sys.platform == "win32", "Tk GUI smoke test runs on Windows only")
class TestWindowsUiSmoke(unittest.TestCase):
    def test_all_analysis_renderers_and_history_cleanup(self):
        from sikpro.data import Dataset
        from sikpro.ui.main_window import MainWindow

        app = None
        try:
            app = MainWindow()
            numeric_rows = [
                [10.01, 10.03, 10.00],
                [9.98, 10.01, 9.99],
                [10.02, 10.04, 10.01],
                [9.99, 10.00, 9.98],
                [10.00, 10.02, 10.00],
                [10.03, 10.05, 10.02],
            ]
            count_rows = [[5], [7], [4], [6], [5], [8]]
            category_rows = [
                ["Scratch", "Front", "Left"],
                ["Scratch", "Front", "Right"],
                ["Dent", "Side", "Left"],
                ["Scratch", "Front", "Left"],
                ["Crack", "Back", "Center"],
            ]
            fishbone_rows = [
                ["Man", "Operator needs training"],
                ["Machine", "Blade is worn"],
                ["Mother Nature", "Humidity is high"],
            ]

            def make_dataset(name, headers, rows, options=None, distribution_type=None):
                dataset = Dataset(name=name, rows=len(rows), columns=len(headers))
                dataset.headers = list(headers)
                dataset.data = [list(row) for row in rows]
                dataset.metadata.update({
                    "analysis_columns": list(range(len(headers))),
                    "analysis_row_mode": "all",
                    "analysis_start_row": 1,
                    "analysis_end_row": len(rows),
                    "analysis_source_dataset": name,
                    "analysis_source_index": 0,
                    "analysis_options": dict(options or {}),
                })
                if distribution_type:
                    dataset.metadata["distribution_type"] = distribution_type
                return dataset

            scenarios = [
                ("Control Chart", "I-MR", make_dataset("I-MR", ["A"], [[r[0]] for r in numeric_rows])),
                ("Control Chart", "MR", make_dataset("MR", ["A"], [[r[0]] for r in numeric_rows])),
                ("Control Chart", "X-bar R", make_dataset("X-bar R", ["A", "B", "C"], numeric_rows)),
                ("Control Chart", "X-bar S", make_dataset("X-bar S", ["A", "B", "C"], numeric_rows)),
                ("Control Chart", "p", make_dataset("p", ["Cacat"], count_rows, {"sample_size": 100})),
                ("Control Chart", "np", make_dataset("np", ["Cacat"], count_rows, {"sample_size": 100})),
                ("Control Chart", "c", make_dataset("c", ["Cacat"], count_rows)),
                ("Control Chart", "u", make_dataset("u", ["Cacat"], count_rows, {"unit_size": 10})),
                ("Descriptive", "Summary Statistics", make_dataset("Summary", ["A", "B"], [r[:2] for r in numeric_rows])),
                ("Descriptive", "Frequency", make_dataset("Frequency", ["A"], [[r[0]] for r in numeric_rows])),
                ("Descriptive", "Distribution", make_dataset("Distribution", ["A"], [[r[0]] for r in numeric_rows], distribution_type="Normal")),
                ("Quality Tools", "Histogram", make_dataset("Histogram", ["A"], [[r[0]] for r in numeric_rows])),
                ("Quality Tools", "Pareto Chart", make_dataset("Pareto", ["Jenis", "X", "Y"], category_rows)),
                ("Quality Tools", "Check Sheet", make_dataset("Check Sheet", ["Jenis", "X", "Y"], category_rows)),
                ("Quality Tools", "Fishbone", make_dataset("Fishbone", ["Kategori6M", "Penyebab"], fishbone_rows, {"problem": "High defect rate"})),
                ("Quality Tools", "Defect Concentration", make_dataset("Concentration", ["X", "Y"], [r[1:] for r in category_rows])),
                ("Relationship", "Scatter Plot", make_dataset("Scatter", ["A", "B"], [r[:2] for r in numeric_rows])),
            ]

            with patch("tkinter.messagebox.showerror") as showerror:
                for category, method, dataset in scenarios:
                    with self.subTest(category=category, method=method):
                        app.selected_analysis = category
                        app.selected_method = method
                        success = app._run_analysis(dataset)
                        self.assertTrue(success, f"{category}/{method} failed")
                        self.assertTrue(app.analysis_history.entries)
                        app.root.update_idletasks()
                showerror.assert_not_called()

            self.assertGreaterEqual(len(app.analysis_history.entries), len(scenarios))
        finally:
            if app is not None:
                app.root.destroy()


if __name__ == "__main__":
    unittest.main()
