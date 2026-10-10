import customtkinter as ctk

from sikpro.ui.popups.base_popup import (
    BaseAnalysisPopup
)
from tkinter import messagebox

class DistributionPopup(
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

        self.distribution_type = (
            ctk.StringVar(
                value="Auto Detect"
            )
        )

        super().__init__(
            parent,
            "Descriptive / Distribution",
            width=520,
            height=560
        )

    # ======================================================
    # BUILD
    # ======================================================

    def _build(self):

        self.build_header(
            "Distribution"
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

        # ==================================================
        # SECTION TITLE
        # ==================================================

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
            height=125
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

        # Selalu buka dari C1
        try:
            column_frame._parent_canvas.yview_moveto(
                0.0
            )
        except Exception:
            pass

        # ==================================================
        # DISTRIBUTION TYPE
        # ==================================================

        ctk.CTkLabel(
            frame,
            text="Distribution Type",
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

        ctk.CTkComboBox(
            frame,
            variable=self.distribution_type,
            values=[
                "Auto Detect",
                "Histogram",
                "Normal",
                "Uniform",
                "Exponential",
                "Lognormal",
            ],
            width=275
        ).pack(
            anchor="w",
            padx=14,
            pady=(0, 10)
        )

        # ==================================================
        # BOTTOM CONTROL BAR
        # ==================================================

        bottom_frame = ctk.CTkFrame(
            frame,
            fg_color="transparent"
        )

        bottom_frame.pack(
            fill="x",
            padx=14,
            pady=(0, 14)
        )

        # ==================================================
        # ROWS
        # ==================================================

        rows_frame = ctk.CTkFrame(
            bottom_frame,
            fg_color="transparent"
        )

        rows_frame.pack(
            side="left"
        )

        ctk.CTkLabel(
            rows_frame,
            text="Rows",
            font=(
                "Segoe UI",
                12,
                "bold"
            )
        ).pack(
            side="left",
            padx=(0, 10)
        )

        ctk.CTkRadioButton(
            rows_frame,
            text="All",
            variable=self.row_mode,
            value="all"
        ).pack(
            side="left",
            padx=(0, 8)
        )

        ctk.CTkRadioButton(
            rows_frame,
            text="Selected",
            variable=self.row_mode,
            value="range"
        ).pack(
            side="left"
        )

        # ==================================================
        # ACTION BUTTONS
        # ==================================================

        action_frame = ctk.CTkFrame(
            bottom_frame,
            fg_color="transparent"
        )

        action_frame.pack(
            side="right"
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
            side="left",
            padx=(0, 6)
        )

        ctk.CTkButton(
            action_frame,
            text="Run",
            width=75,
            height=30,
            command=self._run
        ).pack(
            side="left"
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
                "Distribution",
                "Please select at least one column.",
                parent=self.dialog
            )

            return

        settings = {
            "columns": selected_columns,
            "row_mode": self.row_mode.get(),
            "distribution_type": (
                self.distribution_type.get()
            )
        }

        success = self.on_run(
            settings
        )

        if success is not False:
            self.close()