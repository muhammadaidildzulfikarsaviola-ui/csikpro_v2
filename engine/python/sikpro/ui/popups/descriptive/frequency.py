import customtkinter as ctk
from tkinter import messagebox

from sikpro.ui.popups.base_popup import (
    BaseAnalysisPopup
)


class FrequencyPopup(
    BaseAnalysisPopup
):

    def __init__(
        self,
        parent,
        dataset,
        on_run
    ):

        self.dataset = dataset
        self.on_run = on_run

        self.column_vars = []

        self.row_mode = ctk.StringVar(
            value="all"
        )

        super().__init__(
            parent,
            "Descriptive / Frequency",
            width=520,
            height=550
        )

    # ======================================================
    # BUILD
    # ======================================================

    def _build(self):

        self.build_header(
            "Frequency"
        )

        self._build_data_selection()

    # ======================================================
    # DATA SELECTION
    # ======================================================

    def _build_data_selection(self):

        frame = ctk.CTkFrame(
            self.dialog,
            fg_color="#F7F8FA",
            corner_radius=10
        )

        frame.pack(
            fill="x",
            padx=20,
            pady=4
        )

        ctk.CTkLabel(
            frame,
            text="DATA SELECTION",
            text_color="#737B86",
            font=(
                "Segoe UI",
                10,
                "bold"
            )
        ).pack(
            anchor="w",
            padx=14,
            pady=(12, 6)
        )

        # ==================================================
        # COLUMNS
        # ==================================================

        ctk.CTkLabel(
            frame,
            text="Columns",
            font=(
                "Segoe UI",
                12,
                "bold"
            )
        ).pack(
            anchor="w",
            padx=14
        )

        column_frame = ctk.CTkScrollableFrame(
            frame,
            fg_color="#FFFFFF",
            corner_radius=8,
            height=100
        )

        column_frame.pack(
            fill="x",
            padx=14,
            pady=(4, 10)
        )

        headers = getattr(
            self.dataset,
            "headers",
            []
        )

        column_count = getattr(
            self.dataset,
            "columns",
            0
        )

        for index in range(
            column_count
        ):

            name = (
                headers[index]
                if index < len(headers)
                else f"C{index + 1}"
            )

            display_name = (
                f"C{index + 1}"
                if name == f"C{index + 1}"
                else f"C{index + 1}   {name}"
            )

            var = ctk.BooleanVar(
                value=(index == 0)
            )

            self.column_vars.append(
                var
            )

            ctk.CTkCheckBox(
                column_frame,
                text=display_name,
                variable=var,
                width=130
            ).grid(
                row=index // 3,
                column=index % 3,
                sticky="w",
                padx=8,
                pady=4
            )

        try:
            column_frame._parent_canvas.yview_moveto(
                0.0
            )
        except Exception:
            pass

        # ==================================================
        # ROWS
        # ==================================================

        ctk.CTkLabel(
            frame,
            text="Rows",
            font=(
                "Segoe UI",
                12,
                "bold"
            )
        ).pack(
            anchor="w",
            padx=14,
            pady=(2, 3)
        )

        self.row_mode = ctk.StringVar(
            value="all"
        )

        row_mode_frame = ctk.CTkFrame(
            frame,
            fg_color="transparent"
        )

        row_mode_frame.pack(
            fill="x",
            padx=14
        )

        ctk.CTkRadioButton(
            row_mode_frame,
            text="All",
            variable=self.row_mode,
            value="all",
            command=self._toggle_row_range
        ).pack(
            side="left",
            padx=(0, 18)
        )

        ctk.CTkRadioButton(
            row_mode_frame,
            text="Selected",
            variable=self.row_mode,
            value="range",
            command=self._toggle_row_range
        ).pack(
            side="left"
        )

        # ==================================================
        # RANGE
        # ==================================================

        self.range_frame = ctk.CTkFrame(
            frame,
            fg_color="transparent"
        )

        self.range_frame.pack(
            fill="x",
            padx=14,
            pady=(7, 8)
        )

        ctk.CTkLabel(
            self.range_frame,
            text="From"
        ).pack(
            side="left"
        )

        self.start_entry = ctk.CTkEntry(
            self.range_frame,
            width=65,
            height=28
        )

        self.start_entry.pack(
            side="left",
            padx=(6, 16)
        )

        self.start_entry.insert(
            0,
            "1"
        )

        ctk.CTkLabel(
            self.range_frame,
            text="To"
        ).pack(
            side="left"
        )

        self.end_entry = ctk.CTkEntry(
            self.range_frame,
            width=65,
            height=28
        )

        self.end_entry.pack(
            side="left",
            padx=6
        )

        self.end_entry.insert(
            0,
            str(
                getattr(
                    self.dataset,
                    "rows",
                    200
                )
            )
        )

        self._toggle_row_range()

        # ==================================================
        # BUTTONS
        # ==================================================

        action_frame = ctk.CTkFrame(
            frame,
            fg_color="transparent"
        )

        action_frame.pack(
            fill="x",
            padx=14,
            pady=(2, 14)
        )

        ctk.CTkButton(
            action_frame,
            text="Cancel",
            width=75,
            height=30,
            fg_color="#E5E7EB",
            text_color="#20242A",
            hover_color="#D1D5DB",
            command=self.close
        ).pack(
            side="right",
            padx=(0, 6)
        )

        ctk.CTkButton(
            action_frame,
            text="Run",
            width=75,
            height=30,
            command=self._run
        ).pack(
            side="right"
        )

    # ======================================================
    # ROW RANGE
    # ======================================================

    def _toggle_row_range(self):

        selected = (
            self.row_mode.get()
            == "range"
        )

        state = (
            "normal"
            if selected
            else "disabled"
        )

        self.start_entry.configure(
            state=state
        )

        self.end_entry.configure(
            state=state
        )

    # ======================================================
    # RUN
    # ======================================================

    def _run(self):

        selected_columns = [
            index
            for index, var in enumerate(
                self.column_vars
            )
            if var.get()
        ]

        if not selected_columns:

            messagebox.showwarning(
                "Frequency",
                "Please select at least one column.",
                parent=self.dialog
            )

            return

        start_row = 1
        end_row = getattr(
            self.dataset,
            "rows",
            200
        )

        if self.row_mode.get() == "range":

            try:

                start_row = int(
                    self.start_entry.get()
                )

                end_row = int(
                    self.end_entry.get()
                )

            except ValueError:

                messagebox.showwarning(
                    "Frequency",
                    "Rows must contain valid numbers.",
                    parent=self.dialog
                )

                return

            if start_row < 1:

                messagebox.showwarning(
                    "Frequency",
                    "Starting row must be at least 1.",
                    parent=self.dialog
                )

                return

            if end_row > self.dataset.rows:

                messagebox.showwarning(
                    "Frequency",
                    (
                        f"Ending row cannot exceed "
                        f"{self.dataset.rows}."
                    ),
                    parent=self.dialog
                )

                return

            if start_row > end_row:

                messagebox.showwarning(
                    "Frequency",
                    "Starting row cannot exceed ending row.",
                    parent=self.dialog
                )

                return

        settings = {
            "columns": selected_columns,
            "row_mode": self.row_mode.get(),
            "start_row": start_row,
            "end_row": end_row
        }

        success = self.on_run(
            settings
        )

        if success is not False:
            self.close()