from copy import deepcopy


class Dataset:

    DEFAULT_ROWS = 200
    DEFAULT_COLUMNS = 200

    def __init__(
        self,
        name="Dataset 1",
        rows=None,
        columns=None,
    ):
        self.name = name

        self.rows = (
            rows
            if rows is not None
            else self.DEFAULT_ROWS
        )

        self.columns = (
            columns
            if columns is not None
            else self.DEFAULT_COLUMNS
        )

        self.headers = [
            f"C{i + 1}"
            for i in range(self.columns)
        ]

        self.data = [
            [
                ""
                for _ in range(self.columns)
            ]
            for _ in range(self.rows)
        ]

        self.metadata = {
            "description": "",
            "source": "",
            "created_by": "SIKPRO V2",
        }

    # ==========================================================
    # HEADER
    # ==========================================================

    def rename_header(
        self,
        index,
        name,
    ):

        if not (
            0 <= index < len(self.headers)
        ):
            raise IndexError(
                "Header index out of range."
            )

        name = str(name).strip()

        if not name:
            raise ValueError(
                "Header name cannot be empty."
            )

        self.headers[index] = name

    # ==========================================================
    # CELL
    # ==========================================================

    def set_cell(
        self,
        row,
        column,
        value,
    ):

        self._validate_position(
            row,
            column
        )

        self.data[row][column] = value

    def get_cell(
        self,
        row,
        column,
    ):

        self._validate_position(
            row,
            column
        )

        return self.data[row][column]

    # ==========================================================
    # ROW
    # ==========================================================

    def get_row(
        self,
        row,
    ):

        if not (
            0 <= row < self.rows
        ):
            raise IndexError(
                "Row index out of range."
            )

        return self.data[row].copy()

    # ==========================================================
    # COLUMN
    # ==========================================================

    def get_column(
        self,
        column,
    ):

        if not (
            0 <= column < self.columns
        ):
            raise IndexError(
                "Column index out of range."
            )

        return [
            row[column]
            for row in self.data
        ]

    # ==========================================================
    # CLEAR
    # ==========================================================

    def clear(self):

        self.data = [
            [
                ""
                for _ in range(
                    self.columns
                )
            ]
            for _ in range(
                self.rows
            )
        ]

    def clear_cell(
        self,
        row,
        column,
    ):

        self.set_cell(
            row,
            column,
            ""
        )

    # ==========================================================
    # COPY
    # ==========================================================

    def duplicate(
        self,
        new_name=None,
    ):

        cloned = deepcopy(
            self
        )

        if new_name:
            cloned.name = new_name

        return cloned

    # ==========================================================
    # VALIDATION
    # ==========================================================

    def _validate_position(
        self,
        row,
        column,
    ):

        if not (
            0 <= row < self.rows
        ):
            raise IndexError(
                "Row index out of range."
            )

        if not (
            0 <= column < self.columns
        ):
            raise IndexError(
                "Column index out of range."
            )

    # ==========================================================
    # INFO
    # ==========================================================

    def to_dict(self):

        return {
            "name": self.name,
            "rows": self.rows,
            "columns": self.columns,
            "headers": self.headers.copy(),
            "data": deepcopy(
                self.data
            ),
            "metadata": deepcopy(
                self.metadata
            ),
        }

    def __repr__(self):

        return (
            f"Dataset("
            f"name='{self.name}', "
            f"rows={self.rows}, "
            f"columns={self.columns}"
            f")"
        )