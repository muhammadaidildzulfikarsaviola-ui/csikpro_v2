from copy import deepcopy
from datetime import datetime


class AnalysisHistory:
    """In-memory analysis history with project-file serialization."""

    LIMIT = 100

    def __init__(self, entries=None):
        self.entries = []
        if entries:
            for entry in entries:
                self._append_loaded(entry)

    def add(
        self,
        *,
        analysis,
        method,
        dataset_name,
        dataset_index,
        columns,
        row_mode,
        start_row,
        end_row,
        options=None,
        result=None,
        timestamp=None,
    ):
        entry = {
            "analysis": str(analysis),
            "method": str(method),
            "dataset_name": str(dataset_name),
            "dataset_index": dataset_index,
            "columns": [int(value) for value in columns],
            "row_mode": str(row_mode),
            "start_row": int(start_row),
            "end_row": int(end_row),
            "options": deepcopy(options or {}),
            "result": deepcopy(result),
            "timestamp": (
                timestamp
                or datetime.now().astimezone().isoformat(
                    timespec="seconds"
                )
            ),
        }

        self.entries.insert(0, entry)
        del self.entries[self.LIMIT:]
        return deepcopy(entry)

    def get(self, index):
        return deepcopy(self.entries[index])

    def clear(self):
        self.entries.clear()

    def to_list(self):
        return deepcopy(self.entries)

    @classmethod
    def from_list(cls, entries):
        history = cls()
        if not isinstance(entries, list):
            return history

        for entry in entries:
            history._append_loaded(entry)

        return history

    def _append_loaded(self, entry):
        if not isinstance(entry, dict):
            return

        try:
            normalized = {
                "analysis": str(entry.get("analysis", "")),
                "method": str(entry.get("method", "")),
                "dataset_name": str(
                    entry.get("dataset_name", "")
                ),
                "dataset_index": entry.get(
                    "dataset_index",
                    0
                ),
                "columns": [
                    int(value)
                    for value in entry.get("columns", [])
                ],
                "row_mode": str(
                    entry.get("row_mode", "all")
                ),
                "start_row": int(
                    entry.get("start_row", 1)
                ),
                "end_row": int(
                    entry.get("end_row", 1)
                ),
                "options": deepcopy(
                    entry.get("options", {})
                ),
                "result": deepcopy(
                    entry.get("result")
                ),
                "timestamp": str(
                    entry.get("timestamp", "")
                ),
            }
        except (TypeError, ValueError):
            return

        if not normalized["analysis"] or not normalized["method"]:
            return

        self.entries.append(normalized)
        del self.entries[self.LIMIT:]
