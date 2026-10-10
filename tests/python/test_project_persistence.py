import json
import sys
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from sikpro.data import DatasetManager
from sikpro.data.dataset import Dataset
from sikpro.logic.history import AnalysisHistory
from sikpro.ui.main_window import MainWindow


class FakeRoot:
    def __init__(self):
        self.last_title = ""

    def title(self, value):
        self.last_title = value


def make_window():
    window = MainWindow.__new__(MainWindow)
    window.root = FakeRoot()
    window.dataset_manager = DatasetManager()
    first = Dataset(name="Raw Data", rows=2, columns=2)
    first.headers = ["Batch", "Length"]
    first.data = [[1, 10.5], [2, 10.7]]
    first.metadata["source"] = "test source"
    second = Dataset(name="Analysis Data", rows=3, columns=1)
    second.headers = ["Defects"]
    second.data = [[2], [0], [3]]
    window.dataset_manager.datasets = [first, second]
    window.dataset_manager.active_index = 1

    window._sync_sheet_to_dataset = lambda: None
    window._update_window_title = lambda: None
    window.project_path = None
    window.project_name = "Untitled"
    window.project_dirty = True
    window.selected_analysis = "Control Chart"
    window.selected_method = "p"
    window.dataset_open = True
    window.result_open = False
    window.analysis_history = AnalysisHistory()
    window.analysis_history.add(
        analysis="Control Chart",
        method="p",
        dataset_name="Analysis Data",
        dataset_index=1,
        columns=[0],
        row_mode="range",
        start_row=1,
        end_row=3,
        options={"sample_size": 20},
        result={
            "chart_type": "p",
            "status": "IN CONTROL",
            "series": [{"values": [0.1, 0.0, 0.15], "center": 0.1,
                        "ucl": 0.3, "lcl": 0.0}],
        },
        timestamp="2026-10-10T00:00:00+07:00",
    )
    window.last_analysis_result = {
        "chart_type": "p",
        "status": "IN CONTROL",
        "series": [{"values": [0.1, 0.0, 0.15], "center": 0.1,
                    "ucl": 0.3, "lcl": 0.0}],
    }
    window.last_analysis_method = "p"
    window.last_analysis_analysis = "Control Chart"
    return window


class TestProjectPersistence(unittest.TestCase):
    def test_save_and_restore_preserves_project_state(self):
        source = make_window()

        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "round_trip.spc"
            source._save_to_path(str(path))

            self.assertTrue(path.exists())
            self.assertFalse(source.project_dirty)
            self.assertEqual(source.project_name, "round_trip")

            with path.open("r", encoding="utf-8") as project_file:
                saved_state = json.load(project_file)

            restored = MainWindow.__new__(MainWindow)
            restored.root = FakeRoot()
            restored._update_window_title = lambda: None
            restored._restore_project_state(saved_state)

        self.assertEqual(restored.dataset_manager.count, 2)
        self.assertEqual(restored.dataset_manager.active_index, 1)
        self.assertEqual(restored.dataset_manager.active_dataset.name, "Analysis Data")
        self.assertEqual(restored.dataset_manager.active_dataset.data, [[2], [0], [3]])
        self.assertEqual(restored.dataset_manager.active_dataset.headers, ["Defects"])
        self.assertEqual(restored.dataset_manager.datasets[0].metadata["source"], "test source")
        self.assertEqual(restored.selected_analysis, "Control Chart")
        self.assertEqual(restored.selected_method, "p")
        self.assertTrue(restored.dataset_open)
        self.assertFalse(restored.result_open)
        self.assertEqual(restored.last_analysis_method, "p")
        self.assertEqual(restored.last_analysis_analysis, "Control Chart")
        self.assertEqual(restored.last_analysis_result["status"], "IN CONTROL")
        self.assertEqual(len(restored.analysis_history.entries), 1)
        self.assertEqual(restored.analysis_history.entries[0]["options"], {"sample_size": 20})
        self.assertEqual(restored.analysis_history.entries[0]["result"]["chart_type"], "p")

    def test_open_project_does_not_overwrite_loaded_data_with_old_sheet(self):
        source = make_window()

        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "saved_project.spc"
            source._save_to_path(str(path))

            target = make_window()
            target.project_dirty = False
            target.root.winfo_children = lambda: []
            target._build_interface = lambda: None
            target._update_window_title = lambda: None

            def overwrite_with_stale_sheet():
                target.dataset_manager.active_dataset.data = [["STALE SHEET"]]

            target._sync_sheet_to_dataset = overwrite_with_stale_sheet

            with patch(
                "sikpro.ui.main_window.filedialog.askopenfilename",
                return_value=str(path),
            ), patch("sikpro.ui.main_window.messagebox.showerror") as showerror:
                target._open_project()

            self.assertEqual(
                target.dataset_manager.active_dataset.data,
                [[2], [0], [3]],
            )
            showerror.assert_not_called()

    def test_restore_rejects_project_without_datasets(self):
        restored = MainWindow.__new__(MainWindow)

        with self.assertRaisesRegex(ValueError, "does not contain any dataset"):
            restored._restore_project_state({
                "format": MainWindow.PROJECT_FILETYPE,
                "datasets": [],
            })


if __name__ == "__main__":
    unittest.main()
