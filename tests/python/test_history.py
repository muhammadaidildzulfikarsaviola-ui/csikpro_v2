import sys
import unittest
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from sikpro.logic.history import AnalysisHistory


class TestAnalysisHistory(unittest.TestCase):
    def test_add_and_get_use_independent_copies(self):
        history = AnalysisHistory()
        source_result = {"mean": 5.0, "values": [1, 2, 3]}
        history.add(
            analysis="Descriptive",
            method="Summary Statistics",
            dataset_name="Test",
            dataset_index=0,
            columns=[0],
            row_mode="all",
            start_row=1,
            end_row=3,
            result=source_result,
        )
        source_result["values"].append(4)
        loaded = history.get(0)
        self.assertEqual(loaded["result"]["values"], [1, 2, 3])
        loaded["result"]["values"].append(9)
        self.assertEqual(history.get(0)["result"]["values"], [1, 2, 3])

    def test_history_is_limited_to_most_recent_100_entries(self):
        history = AnalysisHistory()
        for index in range(105):
            history.add(
                analysis="Descriptive",
                method="Frequency",
                dataset_name=f"Dataset {index}",
                dataset_index=0,
                columns=[0],
                row_mode="all",
                start_row=1,
                end_row=1,
                result={"index": index},
            )
        self.assertEqual(len(history.entries), 100)
        self.assertEqual(history.get(0)["result"]["index"], 104)
        self.assertEqual(history.get(99)["result"]["index"], 5)

    def test_loading_ignores_malformed_entries(self):
        history = AnalysisHistory.from_list([
            {"analysis": "Descriptive", "method": "Frequency", "columns": ["0"]},
            {"analysis": "", "method": "Frequency"},
            "not a history object",
            {"analysis": "Descriptive", "method": "Summary Statistics", "columns": ["bad"]},
        ])
        self.assertEqual(len(history.entries), 1)
        self.assertEqual(history.entries[0]["columns"], [0])


if __name__ == "__main__":
    unittest.main()
