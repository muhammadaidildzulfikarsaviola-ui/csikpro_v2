import customtkinter as ctk
from tkinter import messagebox

from sikpro.ui.popups.base_popup import BaseAnalysisPopup


class AnalysisSettingsPopup(BaseAnalysisPopup):
    """Reusable multi-column and row-range selector for non-descriptive tools."""

    def __init__(self, parent, dataset, category, method, on_run):
        self.dataset = dataset
        self.category = category
        self.method = method
        self.on_run = on_run
        self.column_vars = []
        self.row_mode = None
        self.problem_entry = None
        super().__init__(
            parent,
            f"{category} / {method}",
            width=560,
            height=650,
        )

    def _build(self):
        self.build_header(
            self.method,
            f"{self.category}  ·  Select source columns and observation range",
        )
        self._build_selection()
        self.build_buttons(self._run)

    def _build_selection(self):
        frame = ctk.CTkFrame(self.dialog, fg_color="#F7F8FA", corner_radius=10)
        frame.pack(fill="both", expand=True, padx=20, pady=4)

        ctk.CTkLabel(
            frame, text="COLUMNS", text_color="#737B86",
            font=("Segoe UI", 10, "bold"),
        ).pack(anchor="w", padx=14, pady=(12, 5))

        actions = ctk.CTkFrame(frame, fg_color="transparent")
        actions.pack(fill="x", padx=12, pady=(0, 4))
        ctk.CTkButton(
            actions, text="Select all", width=82, height=25,
            command=self._select_all,
        ).pack(side="left", padx=(0, 6))
        ctk.CTkButton(
            actions, text="Clear", width=64, height=25,
            fg_color="#E5E7EB", text_color="#20242A",
            hover_color="#D1D5DB", command=self._clear_all,
        ).pack(side="left")

        columns_frame = ctk.CTkScrollableFrame(
            frame, fg_color="#FFFFFF", corner_radius=8, height=155,
        )
        columns_frame.pack(fill="x", padx=12, pady=(0, 10))

        headers = getattr(self.dataset, "headers", [])
        count = getattr(self.dataset, "columns", 0)
        for index in range(count):
            header = headers[index] if index < len(headers) else f"C{index + 1}"
            label = f"C{index + 1}" if header == f"C{index + 1}" else f"C{index + 1}  {header}"
            var = ctk.BooleanVar(value=index == 0)
            self.column_vars.append(var)
            ctk.CTkCheckBox(
                columns_frame, text=label, variable=var,
            ).grid(row=index // 3, column=index % 3, sticky="w", padx=8, pady=4)

        ctk.CTkLabel(
            frame, text="OBSERVATION ROWS", text_color="#737B86",
            font=("Segoe UI", 10, "bold"),
        ).pack(anchor="w", padx=14, pady=(2, 4))

        self.row_mode = ctk.StringVar(value="all")
        row_modes = ctk.CTkFrame(frame, fg_color="transparent")
        row_modes.pack(fill="x", padx=12)
        ctk.CTkRadioButton(
            row_modes, text="All rows", variable=self.row_mode,
            value="all", command=self._toggle_range,
        ).pack(side="left", padx=(0, 18))
        ctk.CTkRadioButton(
            row_modes, text="Selected range", variable=self.row_mode,
            value="range", command=self._toggle_range,
        ).pack(side="left")

        range_frame = ctk.CTkFrame(frame, fg_color="transparent")
        range_frame.pack(fill="x", padx=12, pady=(6, 8))
        ctk.CTkLabel(range_frame, text="From").pack(side="left")
        self.start_entry = ctk.CTkEntry(range_frame, width=70, height=28)
        self.start_entry.insert(0, "1")
        self.start_entry.pack(side="left", padx=(6, 14))
        ctk.CTkLabel(range_frame, text="To").pack(side="left")
        self.end_entry = ctk.CTkEntry(range_frame, width=70, height=28)
        self.end_entry.insert(0, str(getattr(self.dataset, "rows", 1)))
        self.end_entry.pack(side="left", padx=6)
        self._toggle_range()

        self.option_vars = {}
        if self.category == "Control Chart" and self.method in ("p", "np"):
            self._add_option(frame, "sample_size", "Sample size per subgroup", "100")
        elif self.category == "Control Chart" and self.method == "u":
            self._add_option(frame, "unit_size", "Units inspected per sample", "1")

        if self.category == "Quality Tools" and self.method == "Fishbone":
            problem_line = ctk.CTkFrame(frame, fg_color="transparent")
            problem_line.pack(fill="x", padx=12, pady=(4, 8))
            ctk.CTkLabel(problem_line, text="Effect / problem", width=120, anchor="w").pack(side="left")
            self.problem_entry = ctk.CTkEntry(problem_line, width=300)
            self.problem_entry.insert(0, "Effect / problem")
            self.problem_entry.pack(side="left", fill="x", expand=True)

        help_text = self._help_text()
        ctk.CTkLabel(
            frame, text=help_text, text_color="#737B86",
            font=("Segoe UI", 9), justify="left", wraplength=490,
        ).pack(anchor="w", padx=14, pady=(0, 12))

    def _add_option(self, parent, key, label, default):
        line = ctk.CTkFrame(parent, fg_color="transparent")
        line.pack(fill="x", padx=12, pady=4)
        ctk.CTkLabel(line, text=label, width=190, anchor="w").pack(side="left")
        entry = ctk.CTkEntry(line, width=90, height=28)
        entry.insert(0, default)
        entry.pack(side="left")
        self.option_vars[key] = entry

    def _help_text(self):
        if self.category == "Control Chart":
            if self.method in ("I-MR", "MR", "p", "np", "c", "u"):
                return "Select one column for this chart. X-bar R and X-bar S use one measurement column per subgroup."
            return "Select 2 to 10 measurement columns. Each row is treated as one subgroup."
        if self.method == "Scatter Plot":
            return "Select at least two columns. The first selected column is X and the second is Y."
        if self.method == "Defect Concentration":
            return "Select two columns: location X and location Y. Repeated coordinate pairs indicate concentration."
        if self.method == "Fishbone":
            return "Optional source format: first selected column contains a 6M branch; second contains a cause."
        return "The source dataset is not modified. Analysis runs on a temporary subset."

    def _toggle_range(self):
        state = "normal" if self.row_mode.get() == "range" else "disabled"
        self.start_entry.configure(state=state)
        self.end_entry.configure(state=state)

    def _select_all(self):
        for var in self.column_vars:
            var.set(True)

    def _clear_all(self):
        for var in self.column_vars:
            var.set(False)

    def _run(self):
        columns = [index for index, var in enumerate(self.column_vars) if var.get()]
        if not columns:
            messagebox.showwarning(self.method, "Select at least one column.", parent=self.dialog)
            return
        if self.category == "Control Chart":
            if self.method in ("I-MR", "MR", "p", "np", "c", "u") and len(columns) != 1:
                messagebox.showwarning(self.method, "This chart requires exactly one selected column.", parent=self.dialog)
                return
            if self.method in ("X-bar R", "X-bar S") and not 2 <= len(columns) <= 10:
                messagebox.showwarning(self.method, "Select between 2 and 10 measurement columns.", parent=self.dialog)
                return
        if self.category == "Relationship" and len(columns) < 2:
            messagebox.showwarning(self.method, "Select at least two columns.", parent=self.dialog)
            return
        if self.category == "Quality Tools" and self.method == "Defect Concentration" and len(columns) < 2:
            messagebox.showwarning(self.method, "Select location X and location Y columns.", parent=self.dialog)
            return
        if self.category == "Quality Tools" and self.method == "Fishbone" and len(columns) < 2:
            messagebox.showwarning(self.method, "Select at least two columns for category and cause.", parent=self.dialog)
            return

        start_row, end_row = 1, getattr(self.dataset, "rows", 1)
        if self.row_mode.get() == "range":
            try:
                start_row = int(self.start_entry.get())
                end_row = int(self.end_entry.get())
            except ValueError:
                messagebox.showwarning(self.method, "Rows must be valid integers.", parent=self.dialog)
                return
            if start_row < 1 or end_row > self.dataset.rows or start_row > end_row:
                messagebox.showwarning(
                    self.method,
                    f"Select a valid row range between 1 and {self.dataset.rows}.",
                    parent=self.dialog,
                )
                return

        options = {}
        for key, entry in self.option_vars.items():
            try:
                value = float(entry.get().strip())
                if value <= 0:
                    raise ValueError
                if key == "sample_size" and not value.is_integer():
                    raise ValueError
                options[key] = int(value) if value.is_integer() else value
            except ValueError:
                messagebox.showwarning(self.method, f"{key.replace('_', ' ').title()} must be a number greater than zero.", parent=self.dialog)
                return

        if self.problem_entry is not None:
            options["problem"] = self.problem_entry.get().strip() or "Effect / problem"

        settings = {
            "columns": columns,
            "row_mode": self.row_mode.get(),
            "start_row": start_row,
            "end_row": end_row,
            "options": options,
        }
        success = self.on_run(settings)
        if success is not False:
            self.close()
