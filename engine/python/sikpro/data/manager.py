from .dataset import Dataset


class DatasetManager:

    def __init__(self):

        self.datasets = []

        self.active_index = None

        self.create_dataset(
            "Dataset 1"
        )

    # ==========================================================
    # ACTIVE DATASET
    # ==========================================================

    @property
    def active_dataset(self):

        if self.active_index is None:
            return None

        if not self.datasets:
            return None

        return self.datasets[
            self.active_index
        ]

    # ==========================================================
    # CREATE
    # ==========================================================

    def create_dataset(
        self,
        name=None,
    ):

        if name is None:

            name = self._generate_name()

        dataset = Dataset(
            name=name
        )

        self.datasets.append(
            dataset
        )

        self.active_index = (
            len(self.datasets) - 1
        )

        return dataset

    # ==========================================================
    # DELETE
    # ==========================================================

    def delete_dataset(
        self,
        index=None,
    ):

        if index is None:
            index = self.active_index

        if index is None:
            return False

        if not (
            0 <= index <
            len(self.datasets)
        ):
            return False

        if len(self.datasets) <= 1:

            raise ValueError(
                "At least one dataset "
                "must exist."
            )

        del self.datasets[index]

        if self.active_index >= len(
            self.datasets
        ):

            self.active_index = (
                len(self.datasets) - 1
            )

        elif index < self.active_index:

            self.active_index -= 1

        return True

    # ==========================================================
    # RENAME
    # ==========================================================

    def rename_dataset(
        self,
        index,
        name,
    ):

        if not (
            0 <= index <
            len(self.datasets)
        ):
            raise IndexError(
                "Dataset index out of range."
            )

        name = str(name).strip()

        if not name:
            raise ValueError(
                "Dataset name cannot be empty."
            )

        self.datasets[
            index
        ].name = name

    # ==========================================================
    # DUPLICATE
    # ==========================================================

    def duplicate_dataset(
        self,
        index=None,
        new_name=None,
    ):

        if index is None:
            index = self.active_index

        if index is None:
            return None

        if not (
            0 <= index <
            len(self.datasets)
        ):
            raise IndexError(
                "Dataset index out of range."
            )

        source = self.datasets[
            index
        ]

        if new_name is None:

            new_name = (
                f"{source.name} Copy"
            )

        duplicate = source.duplicate(
            new_name
        )

        self.datasets.append(
            duplicate
        )

        self.active_index = (
            len(self.datasets) - 1
        )

        return duplicate

    # ==========================================================
    # SELECT
    # ==========================================================

    def set_active(
        self,
        index,
    ):

        if not (
            0 <= index <
            len(self.datasets)
        ):
            raise IndexError(
                "Dataset index out of range."
            )

        self.active_index = index

        return self.active_dataset

    # ==========================================================
    # GET
    # ==========================================================

    def get_dataset(
        self,
        index,
    ):

        if not (
            0 <= index <
            len(self.datasets)
        ):
            raise IndexError(
                "Dataset index out of range."
            )

        return self.datasets[
            index
        ]

    # ==========================================================
    # COUNT
    # ==========================================================

    @property
    def count(self):

        return len(
            self.datasets
        )

    # ==========================================================
    # NAMES
    # ==========================================================

    @property
    def names(self):

        return [
            dataset.name
            for dataset in self.datasets
        ]

    # ==========================================================
    # GENERATE NAME
    # ==========================================================

    def _generate_name(self):

        number = 1

        existing = set(
            self.names
        )

        while (
            f"Dataset {number}"
            in existing
        ):

            number += 1

        return (
            f"Dataset {number}"
        )

    # ==========================================================
    # EXPORT STATE
    # ==========================================================

    def to_dict(self):

        return {
            "active_index": self.active_index,
            "datasets": [
                dataset.to_dict()
                for dataset in self.datasets
            ],
        }

    # ==========================================================
    # DEBUG
    # ==========================================================

    def __repr__(self):

        return (
            f"DatasetManager("
            f"count={self.count}, "
            f"active={self.active_dataset}"
            f")"
        )