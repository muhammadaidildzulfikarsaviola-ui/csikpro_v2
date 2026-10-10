import json
import os
from copy import deepcopy
import tkinter as tk
from tkinter import filedialog, messagebox

import customtkinter as ctk
import tksheet

from sikpro.data import DatasetManager
from sikpro.data.dataset import Dataset
from sikpro.ui.components.sidebar import Sidebar
from sikpro.ui.components.panels.result_panel import ResultPanel

from sikpro.engine import AnalysisEngine
from sikpro.logic.history import AnalysisHistory
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure



class MainWindow:

    # ==========================================================
    # COLORS
    # ==========================================================

    BG = "#F3F5F7"
    SURFACE = "#FFFFFF"
    SURFACE_ALT = "#F7F8FA"
    BORDER = "#E1E5EA"

    TEXT = "#20242A"
    MUTED = "#737B86"

    ACCENT = "#3B82F6"
    ACCENT_HOVER = "#2563EB"
    ACCENT_SOFT = "#EAF2FF"

    # ==========================================================
    # DATASET / PROJECT
    # ==========================================================

    DEFAULT_ROWS = 200
    DEFAULT_COLUMNS = 200
    PROJECT_EXTENSION = ".spc"
    PROJECT_FILETYPE = "SPC Dataset"

    # ==========================================================
    # SIDEBAR
    # ==========================================================

    SIDEBAR_WIDTH = 180
    RESULT_WIDTH = 360

    # ==========================================================
    # SCALE
    # ==========================================================

    SCALE_LEVELS = [
        0.85,
        0.95,
        1.00,
        1.10,
        1.20,
        1.30,
        1.40,
        1.50,
        1.60,
        1.75,
        2.00,
    ]

    # ==========================================================
    # INIT
    # ==========================================================

    def __init__(self):

        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")

        self.root = ctk.CTk()

        self.root.title("SIKPRO V2")

        self.root.geometry(
            f"{self.root.winfo_screenwidth()}x"
            f"{self.root.winfo_screenheight()}+0+0"
        )

        self.root.after(
            100,
            lambda: self.root.state("zoomed")
        )

        self.root.minsize(
            1180,
            700
        )

        # ======================================================
        # SCALE
        # ======================================================

        self.scale_index = 8

        self.ui_scale = (
            self.SCALE_LEVELS[
                self.scale_index
            ]
        )

        # ======================================================
        # DATASET ENGINE
        # ======================================================

        self.dataset_manager = DatasetManager()
        self.analysis_engine = AnalysisEngine()
        self.analysis_sections = {}

        self.result_stats_frame = None
        self.result_tabs = None
        self.last_analysis_result = None
        self.last_analysis_method = None
        self.last_analysis_analysis = None
        self.analysis_history = AnalysisHistory()
        self.result_chart_frame = None
        self.analysis_dialog = None

        self.sheet = None

        # ======================================================
        # UI STATE
        # ======================================================

        self.dataset_open = True
        self.result_open = True

        self.selected_analysis = "Control Chart"
        self.selected_method = "I-MR"

        self.analysis_sections = {}

        self.sheet = None

        # ======================================================
        # PROJECT STATE
        # ======================================================

        self.project_path = None
        self.project_dirty = False
        self.project_name = "Untitled"

        # ======================================================
        # BUILD
        # ======================================================

        self._build_interface()

        self._bind_global_shortcuts()

        self.root.protocol(
            "WM_DELETE_WINDOW",
            self._on_close
        )

        self._update_window_title()

    # ==========================================================
    # FONT
    # ==========================================================

    def _font(
        self,
        size,
        bold=False
    ):

        return (
            "Segoe UI",
            max(
                8,
                int(
                    size * self.ui_scale
                )
            ),
            "bold"
            if bold
            else "normal",
        )

    # ==========================================================
    # UI SIZE
    # ==========================================================

    def _ui(
        self,
        value
    ):

        return max(
            1,
            int(
                value *
                min(
                    self.ui_scale,
                    1.20
                )
            )
        )

    # ==========================================================
    # PROJECT STATE
    # ==========================================================

    def _mark_dirty(
        self,
        dirty=True
    ):

        self.project_dirty = dirty

        self._update_window_title()

    def _update_window_title(self):

        name = (
            self.project_name
            or "Untitled"
        )

        marker = (
            " *"
            if self.project_dirty
            else ""
        )

        self.root.title(
            f"{name}{marker} - SIKPRO V2"
        )

    def _project_state(self):

        self._sync_sheet_to_dataset()

        return {
            "format": self.PROJECT_FILETYPE,
            "version": 1,
            "project_name": self.project_name,
            "active_index": (
                self.dataset_manager.active_index
            ),
            "datasets": (
                self.dataset_manager.to_dict()[
                    "datasets"
                ]
            ),
            "selected_analysis": (
                self.selected_analysis
            ),
            "selected_method": (
                self.selected_method
            ),
            "dataset_open": (
                self.dataset_open
            ),
            "result_open": (
                self.result_open
            ),
            "analysis_history": (
                self.analysis_history.to_list()
            ),
            "last_analysis_result": deepcopy(self.last_analysis_result),
            "last_analysis_method": self.last_analysis_method,
            "last_analysis_analysis": self.last_analysis_analysis,
        }

    def _restore_project_state(
        self,
        state
    ):

        datasets = state.get(
            "datasets",
            []
        )

        if (
            not isinstance(
                datasets,
                list
            )
            or not datasets
        ):

            raise ValueError(
                "Project does not contain "
                "any dataset."
            )

        manager = DatasetManager()

        manager.datasets = []

        for raw in datasets:

            rows = int(
                raw.get(
                    "rows",
                    self.DEFAULT_ROWS
                )
            )

            columns = int(
                raw.get(
                    "columns",
                    self.DEFAULT_COLUMNS
                )
            )

            dataset = Dataset(
                name=str(
                    raw.get(
                        "name",
                        "Dataset"
                    )
                ),
                rows=rows,
                columns=columns,
            )

            headers = raw.get(
                "headers",
                []
            )

            data = raw.get(
                "data",
                []
            )

            if isinstance(
                headers,
                list
            ):

                for i in range(
                    min(
                        columns,
                        len(headers)
                    )
                ):

                    dataset.headers[i] = str(
                        headers[i]
                    )

            if isinstance(
                data,
                list
            ):

                for r in range(
                    min(
                        rows,
                        len(data)
                    )
                ):

                    row = data[r]

                    if not isinstance(
                        row,
                        list
                    ):
                        continue

                    for c in range(
                        min(
                            columns,
                            len(row)
                        )
                    ):

                        dataset.data[r][c] = (
                            row[c]
                        )

            metadata = raw.get(
                "metadata",
                {}
            )

            if isinstance(
                metadata,
                dict
            ):

                dataset.metadata.update(
                    metadata
                )

            manager.datasets.append(
                dataset
            )

        active_index = state.get(
            "active_index",
            0
        )

        try:

            active_index = int(
                active_index
            )

        except (
            TypeError,
            ValueError
        ):

            active_index = 0

        manager.active_index = max(
            0,
            min(
                active_index,
                len(
                    manager.datasets
                ) - 1
            )
        )

        self.dataset_manager = manager

        self.selected_analysis = (
            state.get(
                "selected_analysis",
                "Control Chart"
            )
        )

        self.selected_method = (
            state.get(
                "selected_method",
                "I-MR"
            )
        )

        self.dataset_open = bool(
            state.get(
                "dataset_open",
                True
            )
        )

        self.result_open = bool(
            state.get(
                "result_open",
                True
            )
        )

        self.analysis_history = AnalysisHistory.from_list(
            state.get(
                "analysis_history",
                []
            )
        )

        self.last_analysis_result = deepcopy(state.get("last_analysis_result"))
        self.last_analysis_method = state.get("last_analysis_method")
        self.last_analysis_analysis = state.get("last_analysis_analysis")

    # ==========================================================
    # SAVE
    # ==========================================================

    def _save_to_path(
        self,
        path
    ):

        state = self._project_state()

        with open(
            path,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                state,
                file,
                ensure_ascii=False,
                indent=2
            )

        self.project_path = path

        self.project_name = os.path.splitext(
            os.path.basename(path)
        )[0]

        self._mark_dirty(False)

    def _save_project(self):

        if self.project_path:

            try:

                self._save_to_path(
                    self.project_path
                )

                return True

            except Exception as error:

                messagebox.showerror(
                    "Save Project",
                    (
                        "Unable to save project."
                        f"\n\n{error}"
                    ),
                    parent=self.root
                )

                return False

        return self._save_project_as()

    def _save_project_as(self):

        path = filedialog.asksaveasfilename(
            parent=self.root,
            title="Save SPC Dataset",
            defaultextension=(
                self.PROJECT_EXTENSION
            ),
            filetypes=[
                (
                    self.PROJECT_FILETYPE,
                    f"*{self.PROJECT_EXTENSION}"
                ),
                (
                    "All Files",
                    "*.*"
                ),
            ],
            initialfile=(
                self.project_name
                if self.project_name != "Untitled"
                else "SPC Dataset"
            ),
        )

        if not path:
            return False

        try:

            self._save_to_path(
                path
            )

            return True

        except Exception as error:

            messagebox.showerror(
                "Save Project",
                (
                    "Unable to save project."
                    f"\n\n{error}"
                ),
                parent=self.root
            )

            return False

    # ==========================================================
    # OPEN
    # ==========================================================

    def _open_project(self):

        if not self._confirm_unsaved_changes():
            return

        path = filedialog.askopenfilename(
            parent=self.root,
            title="Open SPC Dataset",
            filetypes=[
                (
                    self.PROJECT_FILETYPE,
                    f"*{self.PROJECT_EXTENSION}"
                ),
                (
                    "All Files",
                    "*.*"
                ),
            ],
        )

        if not path:
            return

        try:

            with open(
                path,
                "r",
                encoding="utf-8"
            ) as file:

                state = json.load(
                    file
                )

            if state.get(
                "format"
            ) != self.PROJECT_FILETYPE:

                raise ValueError(
                    "This file is not a valid "
                    "SPC Dataset project."
                )

            self._restore_project_state(
                state
            )

            self.project_path = path

            self.project_name = (
                os.path.splitext(
                    os.path.basename(path)
                )[0]
            )

            self._mark_dirty(False)

            # The dataset manager has already been replaced by the loaded
            # project. Do not sync the old sheet into the newly loaded data.
            self._rebuild_interface(sync_current=False)

        except Exception as error:

            messagebox.showerror(
                "Open Project",
                (
                    "Unable to open project."
                    f"\n\n{error}"
                ),
                parent=self.root
            )

    # ==========================================================
    # NEW / CLOSE PROJECT
    # ==========================================================

    def _new_project(self):

        if not self._confirm_unsaved_changes():
            return

        self.dataset_manager = (
            DatasetManager()
        )

        self.selected_analysis = (
            "Control Chart"
        )

        self.selected_method = (
            "I-MR"
        )

        self.dataset_open = True
        self.result_open = True

        self.project_path = None
        self.project_name = "Untitled"

        self.last_analysis_result = None
        self.last_analysis_method = None
        self.last_analysis_analysis = None
        self.analysis_history = AnalysisHistory()

        self._mark_dirty(False)

        self._rebuild_interface()

    def _close_project(self):

        if not self._confirm_unsaved_changes():
            return

        self.dataset_manager = (
            DatasetManager()
        )

        self.selected_analysis = (
            "Control Chart"
        )

        self.selected_method = (
            "I-MR"
        )

        self.dataset_open = True
        self.result_open = True

        self.project_path = None
        self.project_name = "Untitled"

        self.last_analysis_result = None
        self.last_analysis_method = None
        self.last_analysis_analysis = None
        self.analysis_history = AnalysisHistory()

        self._mark_dirty(False)

        self._rebuild_interface()

    def _confirm_unsaved_changes(self):

        if not self.project_dirty:
            return True

        answer = messagebox.askyesnocancel(
            "Unsaved Changes",
            (
                "This project has unsaved changes."
                "\n\n"
                "Do you want to save them "
                "before continuing?"
            ),
            parent=self.root
        )

        if answer is None:
            return False

        if answer:

            return self._save_project()

        return True

    # ==========================================================
    # GLOBAL SHORTCUTS
    # ==========================================================

    def _bind_global_shortcuts(self):

        self.root.bind_all(
            "<Control-n>",
            lambda event:
            self._new_project()
        )

        self.root.bind_all(
            "<Control-N>",
            lambda event:
            self._new_project()
        )

        self.root.bind_all(
            "<Control-o>",
            lambda event:
            self._open_project()
        )

        self.root.bind_all(
            "<Control-O>",
            lambda event:
            self._open_project()
        )

        self.root.bind_all(
            "<Control-s>",
            lambda event:
            self._save_project()
        )

        self.root.bind_all(
            "<Control-S>",
            lambda event:
            self._save_project()
        )

        self.root.bind_all(
            "<Control-Shift-s>",
            lambda event:
            self._save_project_as()
        )

        self.root.bind_all(
            "<Control-Shift-S>",
            lambda event:
            self._save_project_as()
        )

    # ==========================================================
    # HEADER - RIBBON
    # ==========================================================

    def _build_header(self):

        # ======================================================
        # COMPACT OFFICE STYLE RIBBON HEADER
        # ======================================================

        header = ctk.CTkFrame(
            self.root,
            fg_color=self.SURFACE,
            corner_radius=0,
            height=self._ui(132),
        )

        header.pack(
            side="top",
            fill="x"
        )

        header.pack_propagate(False)

        # ======================================================
        # TOP ROW
        # ======================================================

        top = ctk.CTkFrame(
            header,
            fg_color=self.SURFACE,
            corner_radius=0,
            height=self._ui(56),
        )

        top.pack(
            side="top",
            fill="x"
        )

        top.pack_propagate(False)

        # ======================================================
        # BRAND
        # ======================================================

        brand = ctk.CTkFrame(
            top,
            fg_color="transparent"
        )

        brand.pack(
            side="left",
            padx=self._ui(12)
        )

        ctk.CTkLabel(
            brand,
            text="S",
            width=self._ui(38),
            height=self._ui(38),
            corner_radius=self._ui(10),
            fg_color=self.ACCENT,
            text_color="#FFFFFF",
            font=self._font(
                16,
                True
            ),
        ).pack(
            side="left",
            padx=(
                0,
                self._ui(8)
            )
        )

        brand_text = ctk.CTkFrame(
            brand,
            fg_color="transparent"
        )

        brand_text.pack(
            side="left"
        )

        ctk.CTkLabel(
            brand_text,
            text="SIKPRO V2",
            text_color=self.TEXT,
            font=self._font(
                15,
                True
            ),
        ).pack(
            anchor="w"
        )

        ctk.CTkLabel(
            brand_text,
            text="Statistical Process Control",
            text_color=self.MUTED,
            font=self._font(7),
        ).pack(
            anchor="w"
        )

        # ======================================================
        # RIBBON TABS
        # ======================================================

        tab_bar = ctk.CTkFrame(
            top,
            fg_color="transparent"
        )

        tab_bar.pack(
            side="left",
            fill="y",
            padx=self._ui(8)
        )

        self.ribbon_tabs = {}

        tabs = [
            ("home", "Home"),
            ("file", "File"),
            ("edit", "Edit"),
            ("view", "View"),
            ("project", "Project"),
            ("help", "Help"),
        ]

        for key, label in tabs:

            button = ctk.CTkButton(
                tab_bar,
                text=label,
                width=self._ui(68),
                height=self._ui(34),
                corner_radius=self._ui(5),
                fg_color="transparent",
                hover_color=self.SURFACE_ALT,
                text_color=self.TEXT,
                font=self._font(
                    8
                ),
                border_width=0,
                command=lambda k=key:
                self._set_ribbon_tab(k),
            )

            button.pack(
                side="left",
                padx=1,
                pady=self._ui(10)
            )

            self.ribbon_tabs[key] = button

        # ======================================================
        # RIGHT SIDE
        # ======================================================

        project_name = (
            self.project_name
            if self.project_name != "Untitled"
            else "Untitled"
        )

        ctk.CTkLabel(
            top,
            text=(
                f"📄  {project_name}"
                + (
                    "  •  Unsaved"
                    if self.project_dirty
                    else ""
                )
            ),
            text_color=(
                self.ACCENT
                if self.project_dirty
                else self.MUTED
            ),
            font=self._font(
                8,
                self.project_dirty
            ),
        ).pack(
            side="right",
            padx=self._ui(8)
        )

        ctk.CTkButton(
            top,
            text="⚙",
            width=self._ui(38),
            height=self._ui(36),
            corner_radius=self._ui(8),
            fg_color="transparent",
            hover_color=self.SURFACE_ALT,
            text_color=self.MUTED,
            font=self._font(
                16
            ),
            command=self._open_settings,
        ).pack(
            side="right",
            padx=self._ui(8)
        )

        # ======================================================
        # RIBBON COMMAND AREA
        # ======================================================

        self.ribbon_area = ctk.CTkFrame(
            header,
            fg_color="#F8F9FB",
            corner_radius=0,
            height=self._ui(76),
            border_width=1,
            border_color=self.BORDER,
        )

        self.ribbon_area.pack(
            side="top",
            fill="both",
            expand=True
        )

        self.ribbon_area.pack_propagate(False)

        self._set_ribbon_tab(
            "home"
        )

    def _set_ribbon_tab(
        self,
        tab
    ):

        if not hasattr(
            self,
            "ribbon_tabs"
        ):
            return

        for key, button in self.ribbon_tabs.items():

            selected = key == tab

            button.configure(
                fg_color=(
                    self.ACCENT_SOFT
                    if selected
                    else "transparent"
                ),
                text_color=(
                    self.ACCENT
                    if selected
                    else self.TEXT
                ),
                font=self._font(
                    8,
                    selected
                )
            )

        for widget in self.ribbon_area.winfo_children():
            widget.destroy()

        if tab == "home":

            self._build_ribbon_group(
                "PROJECT",
                [
                    ("📄", "New", self._new_project),
                    ("📂", "Open", self._open_project),
                    ("💾", "Save", self._save_project),
                ]
            )

            self._build_ribbon_group(
                "EDIT",
                [
                    ("↶", "Undo", self._undo),
                    ("↷", "Redo", self._redo),
                ]
            )

            self._build_ribbon_group(
                "CLIPBOARD",
                [
                    ("✂️", "Cut", self._cut),
                    ("📋", "Copy", self._copy),
                    ("📌", "Paste", self._paste),
                ]
            )

            self._build_ribbon_group(
                "SELECTION",
                [
                    (
                        "☑️",
                        "Select All",
                        self._select_all_cells
                    ),
                    (
                        "🗑️",
                        "Delete",
                        self._delete_selection
                    ),
                ]
            )

            self._build_ribbon_group(
                "ANALYSIS",
                [
                    (
                        "▶️",
                        "Run Analysis",
                        self._run_analysis
                    ),
                ]
            )

        elif tab == "file":

            self._build_ribbon_group(
                "PROJECT",
                [
                    ("📄", "New", self._new_project),
                    ("📂", "Open", self._open_project),
                    ("💾", "Save", self._save_project),
                    (
                        "💾",
                        "Save As",
                        self._save_project_as
                    ),
                ]
            )

            self._build_ribbon_group(
                "PROJECT CONTROL",
                [
                    (
                        "📁",
                        "Close",
                        self._close_project
                    ),
                    (
                        "🚪",
                        "Exit",
                        self._on_close
                    ),
                ]
            )

        elif tab == "edit":

            self._build_ribbon_group(
                "HISTORY",
                [
                    ("↶", "Undo", self._undo),
                    ("↷", "Redo", self._redo),
                ]
            )

            self._build_ribbon_group(
                "CLIPBOARD",
                [
                    ("✂️", "Cut", self._cut),
                    ("📋", "Copy", self._copy),
                    ("📌", "Paste", self._paste),
                ]
            )

            self._build_ribbon_group(
                "SELECTION",
                [
                    (
                        "☑️",
                        "Select All",
                        self._select_all_cells
                    ),
                    (
                        "🗑️",
                        "Delete",
                        self._delete_selection
                    ),
                ]
            )

        elif tab == "view":

            self._build_ribbon_group(
                "PANELS",
                [
                    (
                        "📊",
                        "Dataset",
                        self._toggle_dataset
                    ),
                    (
                        "📈",
                        "Result",
                        self._toggle_result
                    ),
                ]
            )

            self._build_ribbon_group(
                "DISPLAY",
                [
                    (
                        "⚙",
                        "Settings",
                        self._open_settings
                    ),
                ]
            )

        elif tab == "project":

            self._build_ribbon_group(
                "PROJECT",
                [
                    (
                        "💾",
                        "Save",
                        self._save_project
                    ),
                    (
                        "💾",
                        "Save As",
                        self._save_project_as
                    ),
                    (
                        "ℹ️",
                        "Information",
                        self._project_information
                    ),
                ]
            )

            self._build_ribbon_group(
                "DATASET",
                [
                    (
                        "➕",
                        "New Dataset",
                        self._new_dataset
                    ),
                    (
                        "📑",
                        "Duplicate",
                        self._duplicate_dataset
                    ),
                    (
                        "🗑️",
                        "Delete",
                        self._delete_dataset
                    ),
                ]
            )

        elif tab == "help":

            self._build_ribbon_group(
                "HELP",
                [
                    (
                        "❓",
                        "About",
                        self._about
                    ),
                ]
            )

    # ==========================================================
    # RIBBON GROUP
    # ==========================================================

    def _build_ribbon_group(
        self,
        title,
        buttons
    ):

        # Vertical separator between ribbon groups.
        if self.ribbon_area.winfo_children():

            ctk.CTkFrame(
                self.ribbon_area,
                width=1,
                fg_color=self.BORDER,
            ).pack(
                side="left",
                fill="y",
                pady=self._ui(8),
                padx=self._ui(3),
            )

        group = ctk.CTkFrame(
            self.ribbon_area,
            fg_color="transparent"
        )

        group.pack(
            side="left",
            fill="y",
            padx=self._ui(5),
        )

        command_area = ctk.CTkFrame(
            group,
            fg_color="transparent"
        )

        command_area.pack(
            side="top",
            fill="both",
            expand=True
        )

        for emoji, label, command in buttons:

            button = ctk.CTkButton(
                command_area,
                text=f"{emoji}\n{label}",
                width=self._ui(58),
                height=self._ui(52),
                corner_radius=self._ui(6),
                fg_color="transparent",
                hover_color="#E9EDF2",
                text_color=self.TEXT,
                font=self._font(7),
                command=command,
            )

            button.pack(
                side="left",
                padx=1,
                pady=self._ui(3),
            )

        ctk.CTkLabel(
            group,
            text=title,
            text_color=self.MUTED,
            font=self._font(
                6,
                True
            ),
        ).pack(
            side="bottom",
            pady=(
                0,
                self._ui(2)
            )
        )

    # ==========================================================
    # SETTINGS
    # ==========================================================

    def _open_settings(self):

        window = ctk.CTkToplevel(
            self.root
        )

        window.title(
            "Settings"
        )

        window.geometry(
            "340x230"
        )

        window.resizable(
            False,
            False
        )

        window.configure(
            fg_color=self.SURFACE
        )

        window.transient(
            self.root
        )

        window.grab_set()

        ctk.CTkLabel(
            window,
            text="Appearance",
            text_color=self.TEXT,
            font=self._font(
                16,
                True
            ),
        ).pack(
            anchor="w",
            padx=24,
            pady=(
                22,
                2
            ),
        )

        ctk.CTkLabel(
            window,
            text="Interface scale",
            text_color=self.MUTED,
            font=self._font(10),
        ).pack(
            anchor="w",
            padx=24,
        )

        scale_frame = ctk.CTkFrame(
            window,
            fg_color=self.SURFACE_ALT,
            corner_radius=10,
        )

        scale_frame.pack(
            fill="x",
            padx=24,
            pady=16,
        )

        scale_frame.grid_columnconfigure(
            0,
            weight=1
        )

        scale_frame.grid_columnconfigure(
            1,
            weight=2
        )

        scale_frame.grid_columnconfigure(
            2,
            weight=1
        )

        ctk.CTkButton(
            scale_frame,
            text="−",
            width=42,
            height=38,
            corner_radius=8,
            fg_color=self.SURFACE,
            hover_color="#ECEFF3",
            text_color=self.TEXT,
            font=self._font(
                16,
                True
            ),
            command=lambda:
            self._change_scale(-1),
        ).grid(
            row=0,
            column=0,
            padx=(
                8,
                4
            ),
            pady=8,
        )

        ctk.CTkLabel(
            scale_frame,
            text=self._scale_text(),
            text_color=self.ACCENT,
            font=self._font(
                13,
                True
            ),
        ).grid(
            row=0,
            column=1
        )

        ctk.CTkButton(
            scale_frame,
            text="+",
            width=42,
            height=38,
            corner_radius=8,
            fg_color=self.SURFACE,
            hover_color="#ECEFF3",
            text_color=self.TEXT,
            font=self._font(
                16,
                True
            ),
            command=lambda:
            self._change_scale(1),
        ).grid(
            row=0,
            column=2,
            padx=(
                4,
                8
            ),
            pady=8,
        )

        ctk.CTkLabel(
            window,
            text="Changes apply immediately.",
            text_color=self.MUTED,
            font=self._font(9),
        ).pack(
            anchor="w",
            padx=24,
        )

    def _scale_text(self):

        return (
            f"{int(self.ui_scale * 100)}%"
        )

    def _change_scale(
        self,
        direction
    ):

        self._sync_sheet_to_dataset()

        new_index = (
            self.scale_index +
            direction
        )

        if not (
            0 <= new_index <
            len(self.SCALE_LEVELS)
        ):

            return

        self.scale_index = new_index

        self.ui_scale = (
            self.SCALE_LEVELS[
                self.scale_index
            ]
        )

        self._rebuild_interface()

    # ==========================================================
    # REBUILD
    # ==========================================================

    def _rebuild_interface(self, *, sync_current=True):

        if sync_current:
            self._sync_sheet_to_dataset()

        for widget in (
            self.root.winfo_children()
        ):

            widget.destroy()

        self.analysis_sections = {}

        self.sheet = None

        self._build_interface()

        self._update_window_title()

    # ==========================================================
    # INTERFACE
    # ==========================================================

    def _build_interface(self):

        self._build_header()

        self._build_content()

    # ==========================================================
    # CONTENT
    # ==========================================================

    def _build_content(self):

        self.content_frame = ctk.CTkFrame(
            self.root,
            fg_color=self.BG,
            corner_radius=0
        )

        self.content_frame.pack(
            fill="both",
            expand=True,
            padx=self._ui(16),
            pady=(
                self._ui(14),
                self._ui(16)
            )
        )

        outer = self.content_frame

        sidebar_width = self._ui(
            self.SIDEBAR_WIDTH
        )

        outer.grid_columnconfigure(
            0,
            weight=0,
            minsize=sidebar_width
        )

        outer.grid_columnconfigure(
            1,
            weight=3,
            minsize=self._ui(500)
        )

        outer.grid_columnconfigure(
            2,
            weight=2,
            minsize=self._ui(300)
        )

        outer.grid_rowconfigure(
            0,
            weight=1
        )

        self._build_sidebar(
            outer,
            sidebar_width
        )

        self._build_workspace(
            outer
        )

        self._build_result(
            outer
        )

    # ==========================================================
    # SIDEBAR
    # ==========================================================

    def _build_sidebar(
        self,
        parent,
        width
    ):

        self.sidebar = Sidebar(
            self,
            parent,
            width
        )

        self.sidebar_frame = (
            self.sidebar.frame
        )

        self._build_dataset(
            self.sidebar_frame
        )

        self._build_analysis(
            self.sidebar_frame
        )

        self._build_selected_analysis(
            self.sidebar_frame
        )

    def _refresh_dataset_sidebar(self):

        if not hasattr(
            self,
            "sidebar"
        ):
            return

        self.sidebar.refresh_dataset()

        self._build_dataset(
            self.sidebar_frame
        )
    # ==========================================================
    # DATASET
    # ==========================================================

    def _build_dataset(
        self,
        parent
    ):

        header = ctk.CTkButton(
            parent,
            text=(
                "⌃  DATASET"
                if self.dataset_open
                else "⌄  DATASET"
            ),
            height=self._ui(34),
            corner_radius=self._ui(7),
            fg_color="transparent",
            hover_color=self.SURFACE_ALT,
            text_color=self.TEXT,
            anchor="w",
            font=self._font(
                10,
                True
            ),
            command=self._toggle_dataset,
        )

        header.grid(
            row=0,
            column=0,
            sticky="ew",
            padx=self._ui(7),
            pady=(
                self._ui(6),
                0
            )
        )

        if not self.dataset_open:
            return

        frame = ctk.CTkFrame(
            parent,
            fg_color="transparent"
        )

        frame.grid(
            row=1,
            column=0,
            sticky="ew",
            padx=self._ui(8),
            pady=(
                0,
                self._ui(5)
            )
        )

        dataset_list = ctk.CTkScrollableFrame(
            frame,
            height=self._ui(55),
            fg_color=self.SURFACE_ALT,
            corner_radius=self._ui(8),
        )

        dataset_list.pack(
            fill="x"
        )

        for index, dataset in enumerate(
            self.dataset_manager.datasets
        ):

            self._create_dataset_item(
                dataset_list,
                index,
                dataset.name
            )

        buttons = ctk.CTkFrame(
            frame,
            fg_color="transparent"
        )

        buttons.pack(
            fill="x",
            pady=(
                self._ui(4),
                0
            )
        )

        for index in range(3):

            buttons.grid_columnconfigure(
                index,
                weight=1
            )

        ctk.CTkButton(
            buttons,
            text="+",
            height=self._ui(28),
            corner_radius=self._ui(7),
            fg_color=self.SURFACE_ALT,
            hover_color="#ECEFF3",
            text_color=self.TEXT,
            font=self._font(
                10,
                True
            ),
            command=self._new_dataset,
        ).grid(
            row=0,
            column=0,
            sticky="ew",
            padx=(0, 2)
        )

        ctk.CTkButton(
            buttons,
            text="Duplicate",
            height=self._ui(28),
            corner_radius=self._ui(7),
            fg_color=self.SURFACE_ALT,
            hover_color="#ECEFF3",
            text_color=self.TEXT,
            font=self._font(7),
            command=self._duplicate_dataset,
        ).grid(
            row=0,
            column=1,
            sticky="ew",
            padx=2
        )

        ctk.CTkButton(
            buttons,
            text="Import",
            height=self._ui(28),
            corner_radius=self._ui(7),
            fg_color=self.SURFACE_ALT,
            hover_color="#ECEFF3",
            text_color=self.TEXT,
            font=self._font(7),
            command=self._import_dataset,
        ).grid(
            row=0,
            column=2,
            sticky="ew",
            padx=(
                2,
                0
            )
        )

    # ==========================================================
    # DATASET ITEM
    # ==========================================================

    def _create_dataset_item(
        self,
        parent,
        index,
        name
    ):

        selected = (
            index ==
            self.dataset_manager.active_index
        )

        item = ctk.CTkFrame(
            parent,
            fg_color=(
                self.ACCENT_SOFT
                if selected
                else self.SURFACE
            ),
            corner_radius=self._ui(7),
            height=self._ui(30)
        )

        item.pack(
            fill="x",
            padx=3,
            pady=1
        )

        item.pack_propagate(
            False
        )

        item.grid_columnconfigure(
            0,
            weight=1
        )

        ctk.CTkButton(
            item,
            text=(
                f"●  {name}"
                if selected
                else f"○  {name}"
            ),
            height=self._ui(24),
            fg_color="transparent",
            hover_color=(
                "#DDEAFF"
                if selected
                else "#F0F2F5"
            ),
            text_color=(
                self.ACCENT
                if selected
                else self.TEXT
            ),
            anchor="w",
            font=self._font(
                8,
                True
            ),
            command=lambda i=index:
            self._select_dataset(i)
        ).grid(
            row=0,
            column=0,
            sticky="ew",
            padx=2
        )

        ctk.CTkButton(
            item,
            text="✎",
            width=self._ui(24),
            height=self._ui(24),
            corner_radius=self._ui(5),
            fg_color="transparent",
            hover_color="#E8ECF1",
            text_color=self.MUTED,
            font=self._font(9),
            command=lambda i=index:
            self._rename_dataset(i)
        ).grid(
            row=0,
            column=1,
            padx=2
        )

    def _delete_dataset(self):

        if len(self.dataset_manager.datasets) <= 1:
            messagebox.showwarning(
                "Delete Dataset",
                "At least one dataset must remain.",
                parent=self.root
            )
            return

        dataset = self.dataset_manager.active_dataset

        answer = messagebox.askyesno(
            "Delete Dataset",
            f'Delete "{dataset.name}"?',
            parent=self.root
        )

        if not answer:
            return

        self._sync_sheet_to_dataset()

        index = self.dataset_manager.active_index

        del self.dataset_manager.datasets[index]

        if index >= len(self.dataset_manager.datasets):
            index = len(self.dataset_manager.datasets) - 1

        self.dataset_manager.active_index = index

        self._mark_dirty(True)

        self._refresh_dataset_sidebar()
        self._load_active_dataset_into_sheet()

    # ==========================================================
    # DATASET ACTIONS
    # ==========================================================

    def _select_dataset(
        self,
        index
    ):

        if index == self.dataset_manager.active_index:
            return

        self._sync_sheet_to_dataset()

        self.dataset_manager.set_active(
            index
        )

        self._mark_dirty(True)

        self._refresh_dataset_sidebar()

        self._load_active_dataset_into_sheet()

    def _refresh_workspace(self):

        if not hasattr(
            self,
            "workspace_frame"
        ):
            return

        if not self.workspace_frame.winfo_exists():
            return

        for widget in (
            self.workspace_frame.winfo_children()
        ):
            widget.destroy()

        self.sheet = None

        self._build_workspace_contents(
            self.workspace_frame
        )

    def _rename_dataset(
        self,
        index
    ):

        dialog = ctk.CTkInputDialog(
            text="Enter dataset name:",
            title="Rename Dataset"
        )

        name = dialog.get_input()

        if name is None:
            return

        name = name.strip()

        if not name:
            return

        self._sync_sheet_to_dataset()

        self.dataset_manager.rename_dataset(
            index,
            name
        )

        self._mark_dirty(True)

        self._refresh_dataset_sidebar()

        self._update_workspace_header()

    def _new_dataset(self):

        self._sync_sheet_to_dataset()

        self.dataset_manager.create_dataset()

        self._mark_dirty(True)

        self._refresh_dataset_sidebar()

        self._load_active_dataset_into_sheet()

    def _duplicate_dataset(self):

        self._sync_sheet_to_dataset()

        self.dataset_manager.duplicate_dataset()

        self._mark_dirty(True)

        self._refresh_dataset_sidebar()

        self._load_active_dataset_into_sheet()


    def _delete_dataset(self):

        if len(self.dataset_manager.datasets) <= 1:
            messagebox.showwarning(
                "Delete Dataset",
                "At least one dataset must remain.",
                parent=self.root
            )
            return

        dataset = self.dataset_manager.active_dataset

        answer = messagebox.askyesno(
            "Delete Dataset",
            f'Delete "{dataset.name}"?',
            parent=self.root
        )

        if not answer:
            return

        self._sync_sheet_to_dataset()

        index = self.dataset_manager.active_index

        del self.dataset_manager.datasets[index]

        if index >= len(
            self.dataset_manager.datasets
        ):
            index = len(
                self.dataset_manager.datasets
            ) - 1

        self.dataset_manager.active_index = index

        self._mark_dirty(True)

        self._refresh_dataset_sidebar()
        self._load_active_dataset_into_sheet()

    def _load_active_dataset_into_sheet(self):

        if self.sheet is None:
            return

        dataset = (
            self.dataset_manager.active_dataset
        )

        if dataset is None:
            return

        try:

            self.sheet.set_sheet_data(
                dataset.data,
                redraw=False
            )

            self.sheet.headers(
                dataset.headers,
                redraw=False
            )

            self.sheet.redraw()

            self._update_workspace_header()

        except Exception as error:

            print(
                "Dataset sheet load error:",
                error
            )

    def _import_dataset(self):

        messagebox.showinfo(
            "Import Dataset",
            "Dataset import will be connected here.",
            parent=self.root
        )

    def _toggle_dataset(self):

        self.dataset_open = (
            not self.dataset_open
        )

        self._mark_dirty(True)

        self._rebuild_interface()

    # ==========================================================
    # ANALYSIS
    # ==========================================================

    def _build_analysis(
        self,
        parent
    ):

        title = ctk.CTkLabel(
            parent,
            text="ANALYSIS",
            text_color=self.TEXT,
            font=self._font(
                10,
                True
            ),
            anchor="w"
        )

        title.grid(
            row=2,
            column=0,
            sticky="ew",
            padx=self._ui(12),
            pady=(
                self._ui(7),
                self._ui(3)
            )
        )

        frame = ctk.CTkScrollableFrame(
            parent,
            fg_color="transparent",
            scrollbar_button_color="#B8BEC6",
            scrollbar_button_hover_color="#9FA6AF"
        )

        frame.grid(
            row=3,
            column=0,
            sticky="nsew",
            padx=self._ui(6),
            pady=(
                0,
                self._ui(4)
            )
        )

        self._create_analysis_dropdown(
            frame,
            "Descriptive",
            [
                "Summary Statistics",
                "Frequency",
                "Distribution"
            ]
        )

        self._create_analysis_dropdown(
            frame,
            "Control Chart",
            [
                "I-MR",
                "MR",
                "X-bar R",
                "X-bar S",
                "p",
                "np",
                "c",
                "u"
            ]
        )

        self._create_analysis_dropdown(
            frame,
            "Quality Tools",
            [
                "Histogram",
                "Pareto Chart",
                "Check Sheet",
                "Fishbone",
                "Defect Concentration"
            ]
        )

        self._create_analysis_dropdown(
            frame,
            "Relationship",
            [
                "Scatter Plot"
            ]
        )

    # ==========================================================
    # ANALYSIS DROPDOWN
    # ==========================================================

    def _create_analysis_dropdown(
        self,
        parent,
        category,
        options
    ):

        container = ctk.CTkFrame(
            parent,
            fg_color="transparent"
        )

        container.pack(
            fill="x",
            pady=1
        )

        header = ctk.CTkButton(
            container,
            text=f"›  {category}",
            height=self._ui(32),
            corner_radius=self._ui(7),
            fg_color="transparent",
            hover_color=self.SURFACE_ALT,
            text_color=self.TEXT,
            anchor="w",
            font=self._font(
                9,
                True
            ),
            command=lambda:
            self._toggle_analysis(
                category
            )
        )

        header.pack(
            fill="x"
        )

        options_frame = ctk.CTkFrame(
            container,
            fg_color=self.SURFACE_ALT,
            corner_radius=self._ui(7)
        )

        self.analysis_sections[
            category
        ] = {
            "header": header,
            "options": options_frame,
            "open": False
        }

        for option in options:

            button = ctk.CTkButton(
                options_frame,
                text=f"○  {option}",
                height=self._ui(27),
                corner_radius=self._ui(5),
                fg_color="transparent",
                hover_color="#ECEFF3",
                text_color=self.MUTED,
                anchor="w",
                font=self._font(8),
                command=lambda
                c=category,
                o=option:
                self._select_analysis(
                    c,
                    o
                )
            )

            button.pack(
                fill="x",
                padx=3,
                pady=1
            )

    def _toggle_analysis(
        self,
        category
    ):

        section = (
            self.analysis_sections[
                category
            ]
        )

        if section["open"]:

            section[
                "options"
            ].pack_forget()

            section[
                "header"
            ].configure(
                text=f"›  {category}"
            )

            section[
                "open"
            ] = False

        else:

            section[
                "options"
            ].pack(
                fill="x",
                pady=1
            )

            section[
                "header"
            ].configure(
                text=f"⌄  {category}"
            )

            section[
                "open"
            ] = True

    def _select_analysis(
        self,
        category,
        option
    ):

        self.selected_analysis = (
            category
        )

        self.selected_method = (
            option
        )

        self._mark_dirty(True)

        self._update_selected_analysis()
        self._select_result_tab()

        for (
            name,
            section
        ) in self.analysis_sections.items():

            for widget in (
                section[
                    "options"
                ].winfo_children()
            ):

                text = widget.cget(
                    "text"
                )

                current = (
                    text.replace(
                        "○  ",
                        ""
                    ).replace(
                        "●  ",
                        ""
                    )
                )

                if (
                    name == category
                    and current == option
                ):

                    widget.configure(
                        text=f"●  {option}",
                        text_color=self.ACCENT
                    )

                else:

                    widget.configure(
                        text=f"○  {current}",
                        text_color=self.MUTED
                    )

    # ==========================================================
    # SELECTED ANALYSIS
    # ==========================================================

    def _build_selected_analysis(
        self,
        parent
    ):

        container = ctk.CTkFrame(
            parent,
            fg_color=self.SURFACE,
            corner_radius=0
        )

        container.grid(
            row=4,
            column=0,
            sticky="ew",
            padx=self._ui(9),
            pady=(
                self._ui(3),
                self._ui(4)
            )
        )

        selected = ctk.CTkFrame(
            container,
            fg_color=self.SURFACE_ALT,
            corner_radius=self._ui(8)
        )

        selected.pack(
            fill="x"
        )

        ctk.CTkLabel(
            selected,
            text="SELECTED",
            text_color=self.MUTED,
            font=self._font(
                7,
                True
            ),
            anchor="w"
        ).pack(
            fill="x",
            padx=self._ui(9),
            pady=(
                self._ui(6),
                1
            )
        )

        self.selected_label = ctk.CTkLabel(
            selected,
            text=(
                f"●  "
                f"{self.selected_analysis}"
                f" / "
                f"{self.selected_method}"
            ),
            text_color=self.ACCENT,
            font=self._font(
                8,
                True
            ),
            anchor="w"
        )

        self.selected_label.pack(
            fill="x",
            padx=self._ui(9),
            pady=(
                0,
                self._ui(6)
            )
        )

        ctk.CTkButton(
            parent,
            text="Run Analysis",
            height=self._ui(35),
            corner_radius=self._ui(8),
            fg_color=self.ACCENT,
            hover_color=self.ACCENT_HOVER,
            text_color="#FFFFFF",
            font=self._font(
                9,
                True
            ),
            command=self._open_analysis_dialog
        ).grid(
            row=5,
            column=0,
            sticky="ew",
            padx=self._ui(9),
            pady=(
                0,
                self._ui(9)
            )
        )

    def _update_selected_analysis(
        self
    ):

        if not hasattr(
            self,
            "selected_label"
        ):
            return

        self.selected_label.configure(
            text=(
                f"●  "
                f"{self.selected_analysis}"
                f" / "
                f"{self.selected_method}"
            )
        )

    # ==========================================================
    # WORKSPACE
    # ==========================================================

    def _build_workspace(
        self,
        parent
    ):

        self.workspace_frame = ctk.CTkFrame(
            parent,
            fg_color=self.SURFACE,
            corner_radius=self._ui(14),
            border_width=1,
            border_color=self.BORDER
        )

        self.workspace_frame.grid(
            row=0,
            column=1,
            sticky="nsew"
        )

        self.workspace_frame.grid_rowconfigure(
            1,
            weight=1
        )

        self.workspace_frame.grid_columnconfigure(
            0,
            weight=1
        )

        self._build_workspace_contents(
            self.workspace_frame
        )

    def _update_workspace_header(self):

        if not hasattr(
            self,
            "workspace_dataset_label"
        ):
            return

        dataset = (
            self.dataset_manager.active_dataset
        )

        self.workspace_dataset_label.configure(
            text=(
                dataset.name
                if dataset
                else "No Dataset"
            )
        )

    def _build_workspace_contents(
        self,
        workspace
    ):

        header = ctk.CTkFrame(
            workspace,
            fg_color="transparent"
        )

        header.grid(
            row=0,
            column=0,
            sticky="ew",
            padx=self._ui(20),
            pady=self._ui(18)
        )

        ctk.CTkLabel(
            header,
            text="WORKSPACE",
            text_color=self.TEXT,
            font=self._font(
                11,
                True
            )
        ).pack(
            side="left"
        )

        dataset = (
            self.dataset_manager.active_dataset
        )

        active_name = (
            dataset.name
            if dataset
            else "No Dataset"
        )

        self.workspace_dataset_label = (
            ctk.CTkLabel(
                header,
                text=active_name,
                text_color=self.MUTED,
                font=self._font(9)
            )
        )

        self.workspace_dataset_label.pack(
            side="right"
        )

        table_area = ctk.CTkFrame(
            workspace,
            fg_color=self.SURFACE_ALT,
            corner_radius=self._ui(10)
        )

        table_area.grid(
            row=1,
            column=0,
            sticky="nsew",
            padx=self._ui(16),
            pady=(
                0,
                self._ui(16)
            )
        )

        ctk.CTkLabel(
            table_area,
            text=(
                "Data table  •  "
                f"{dataset.rows if dataset else 0}"
                " × "
                f"{dataset.columns if dataset else 0}"
            ),
            text_color=self.MUTED,
            font=self._font(9)
        ).pack(
            anchor="w",
            padx=self._ui(14),
            pady=self._ui(12)
        )

        table_container = ctk.CTkFrame(
            table_area,
            fg_color="transparent"
        )

        table_container.pack(
            fill="both",
            expand=True,
            padx=8,
            pady=(
                0,
                8
            )
        )

        self._build_table(
            table_container
        )
    # ==========================================================
    # TABLE
    # ==========================================================

    def _build_table(
        self,
        parent
    ):

        dataset = (
            self.dataset_manager.active_dataset
        )

        if dataset is None:
            return

        self.sheet = tksheet.Sheet(
            parent,

            data=dataset.data,

            headers=dataset.headers,

            show_x_scrollbar=True,
            show_y_scrollbar=True,

            header_font=(
                "Segoe UI",
                10,
                "bold"
            ),

            table_font=(
                "Segoe UI",
                10,
                "normal"
            ),

            index_font=(
                "Segoe UI",
                10,
                "normal"
            ),

            header_bg=self.SURFACE,
            header_fg=self.MUTED,

            table_bg=self.SURFACE,
            table_fg=self.TEXT,

            index_bg=self.SURFACE,
            index_fg=self.MUTED,

            frame_bg=self.SURFACE_ALT,

            grid_color=self.BORDER,

            height=600,
            width=900,
        )

        self.sheet.enable_bindings(
            (
                "single_select",
                "drag_select",
                "row_select",
                "column_select",
                "arrowkeys",
                "edit_cell",
                "copy",
                "cut",
                "paste",
                "delete",
                "undo",
                "redo",
                "select_all",
                "edit_header",
            )
        )

        self.sheet.extra_bindings(
            [
                (
                    "<<SheetHeaderEditEnd>>",
                    self._header_renamed
                ),
                (
                    "<<SheetModified>>",
                    self._sheet_modified
                ),
            ]
        )

        self.sheet.bind(
            "<Control-a>",
            self._select_all_cells
        )

        self.sheet.bind(
            "<Control-A>",
            self._select_all_cells
        )

        self.sheet.bind(
            "<Control-z>",
            self._undo
        )

        self.sheet.bind(
            "<Control-Z>",
            self._undo
        )

        self.sheet.bind(
            "<Control-y>",
            self._redo
        )

        self.sheet.bind(
            "<Control-Y>",
            self._redo
        )

        self.sheet.bind(
            "<Control-c>",
            self._copy
        )

        self.sheet.bind(
            "<Control-C>",
            self._copy
        )

        self.sheet.bind(
            "<Control-x>",
            self._cut
        )

        self.sheet.bind(
            "<Control-X>",
            self._cut
        )

        self.sheet.bind(
            "<Control-v>",
            self._paste
        )

        self.sheet.bind(
            "<Control-V>",
            self._paste
        )

        self.sheet.bind(
            "<Delete>",
            self._delete_selection
        )

        self.sheet.pack(
            fill="both",
            expand=True
        )

    def _sheet_modified(
        self,
        event=None
    ):

        self._mark_dirty(True)

    # ==========================================================
    # TABLE SHORTCUTS
    # ==========================================================

    def _select_all_cells(
        self,
        event=None
    ):

        try:

            self.sheet.select_all()

        except Exception as error:

            print(
                "Select all error:",
                error
            )

        return "break"

    def _undo(
        self,
        event=None
    ):

        try:

            if self.sheet:

                self.sheet.undo()

                self._mark_dirty(True)

        except Exception as error:

            print(
                "Undo error:",
                error
            )

        return "break"

    def _redo(
        self,
        event=None
    ):

        try:

            if self.sheet:

                self.sheet.redo()

                self._mark_dirty(True)

        except Exception as error:

            print(
                "Redo error:",
                error
            )

        return "break"

    def _copy(
        self,
        event=None
    ):

        try:

            if self.sheet:

                self.sheet.copy()

        except Exception as error:

            print(
                "Copy error:",
                error
            )

        return "break"

    def _cut(
        self,
        event=None
    ):

        try:

            if self.sheet:

                self.sheet.cut()

                self._mark_dirty(True)

        except Exception as error:

            print(
                "Cut error:",
                error
            )

        return "break"

    def _paste(
        self,
        event=None
    ):

        try:

            if self.sheet:

                self.sheet.paste()

                self._mark_dirty(True)

        except Exception as error:

            print(
                "Paste error:",
                error
            )

        return "break"

    def _delete_selection(
        self,
        event=None
    ):

        try:

            if self.sheet:

                self.sheet.delete()

                self._mark_dirty(True)

        except Exception as error:

            print(
                "Delete error:",
                error
            )

        return "break"

    # ==========================================================
    # HEADER RENAME
    # ==========================================================

    def _header_renamed(
        self,
        event
    ):

        try:

            column_index = event[1]

            new_name = event[3]

            if new_name is None:
                return

            new_name = str(
                new_name
            ).strip()

            if not new_name:

                new_name = (
                    f"C{column_index + 1}"
                )

            dataset = (
                self.dataset_manager.active_dataset
            )

            dataset.rename_header(
                column_index,
                new_name
            )

            self._mark_dirty(True)

        except Exception as error:

            print(
                "Header rename error:",
                error
            )

    # ==========================================================
    # DATASET SYNC
    # ==========================================================

    def _sync_sheet_to_dataset(self):

        if self.sheet is None:
            return

        dataset = (
            self.dataset_manager.active_dataset
        )

        if dataset is None:
            return

        try:

            # Compatible with the installed tksheet version.
            current_data = (
                self.sheet.get_sheet_data()
            )

            for row_index in range(
                min(
                    dataset.rows,
                    len(current_data)
                )
            ):

                row = current_data[
                    row_index
                ]

                for column_index in range(
                    min(
                        dataset.columns,
                        len(row)
                    )
                ):

                    dataset.data[
                        row_index
                    ][
                        column_index
                    ] = row[
                        column_index
                    ]

            current_headers = (
                self.sheet.headers()
            )

            if current_headers:

                for index in range(
                    min(
                        dataset.columns,
                        len(current_headers)
                    )
                ):

                    dataset.headers[
                        index
                    ] = str(
                        current_headers[
                            index
                        ]
                    )

        except Exception as error:

            print(
                "Dataset sync error:",
                error
            )

    # ==========================================================
    # RESULT
    # ==========================================================

    def _build_result(
        self,
        parent
    ):

        self.result_panel = ResultPanel(
            self,
            parent
        )

        self.result_frame = (
            self.result_panel.frame
        )

        self.result_tabs = (
            self.result_panel.result_tabs
        )

        self.result_chart_frame = (
            self.result_panel.result_chart_frame
        )

        self.result_stats_frame = (
            self.result_panel.result_stats_frame
        )
        self.result_rules_frame = (
            self.result_panel.result_rules_frame
        )

    # ==========================================================
    # RESULT TOGGLE
    # ==========================================================

    def _show_stats_placeholder(
        self,
        parent
    ):

        for widget in parent.winfo_children():
            widget.destroy()

        ctk.CTkLabel(
            parent,
            text="Statistics",
            text_color=self.TEXT,
            font=self._font(
                16,
                True
            )
        ).pack(
            pady=(
                self._ui(60),
                5
            )
        )

        ctk.CTkLabel(
            parent,
            text="Run an analysis to see results.",
            text_color=self.MUTED,
            font=self._font(10)
        ).pack()

    def _toggle_result(self):

        self.result_open = (
            not self.result_open
        )

        self._mark_dirty(True)

        if hasattr(
            self,
            "result_panel"
        ):

            self.result_panel.toggle_visibility()

    def _set_result_maximized(
        self,
        maximized
    ):

        if not hasattr(
            self,
            "result_panel"
        ):
            return

        if maximized:

            # Hide sidebar
            if hasattr(
                self,
                "sidebar_frame"
            ):
                self.sidebar_frame.grid_remove()

            # Hide workspace
            if hasattr(
                self,
                "workspace_frame"
            ):
                self.workspace_frame.grid_remove()

            # Result takes the full content area
            self.result_panel.frame.grid_configure(
                row=0,
                column=0,
                columnspan=3,
                sticky="nsew",
                padx=0
            )

            self.content_frame.grid_columnconfigure(
                0,
                weight=1,
                minsize=0
            )

            self.content_frame.grid_columnconfigure(
                1,
                weight=0,
                minsize=0
            )

            self.content_frame.grid_columnconfigure(
                2,
                weight=0,
                minsize=0
            )

        else:

            # Restore sidebar
            if hasattr(
                self,
                "sidebar_frame"
            ):
                self.sidebar_frame.grid()

            # Restore workspace
            if hasattr(
                self,
                "workspace_frame"
            ):
                self.workspace_frame.grid()

            # Restore result position
            self.result_panel.frame.grid_configure(
                row=0,
                column=2,
                columnspan=1,
                sticky="nsew",
                padx=(
                    self._ui(8),
                    0
                )
            )

            self.content_frame.grid_columnconfigure(
                0,
                weight=0,
                minsize=self._ui(
                    self.SIDEBAR_WIDTH
                )
            )

            self.content_frame.grid_columnconfigure(
                1,
                weight=3,
                minsize=self._ui(500)
            )

            self.content_frame.grid_columnconfigure(
                2,
                weight=2,
                minsize=self._ui(300)
            )
#randomize tabs
    def _select_result_tab(self, analysis=None, method=None):
        if self.result_tabs is None:
            return
        analysis = analysis or self.selected_analysis
        method = method or self.selected_method
        if analysis == "Descriptive":
            self.result_tabs.set("Chart" if method == "Distribution" else "Stats")
        elif analysis == "Quality Tools" and method == "Check Sheet":
            self.result_tabs.set("Stats")
        else:
            self.result_tabs.set("Chart")

    def _empty_result(
        self,
        parent,
        title,
        description
    ):

        frame = ctk.CTkFrame(
            parent,
            fg_color="transparent"
        )

        frame.pack(
            expand=True
        )

        ctk.CTkLabel(
            frame,
            text=title,
            text_color=self.TEXT,
            font=self._font(
                16,
                True
            )
        ).pack(
            pady=(
                self._ui(60),
                5
            )
        )

        ctk.CTkLabel(
            frame,
            text=description,
            text_color=self.MUTED,
            font=self._font(10)
        ).pack()

    # ==========================================================
    # PROJECT / HELP
    # ==========================================================
    def _display_summary_statistics(self, result):
        if self.result_stats_frame is None:
            return

        frame = self.result_stats_frame
        for widget in frame.winfo_children():
            widget.destroy()

        ctk.CTkLabel(
            frame, text="Summary Statistics", text_color=self.TEXT,
            font=self._font(16, True),
        ).pack(anchor="w", padx=self._ui(16), pady=(self._ui(16), self._ui(10)))

        column_results = result.get("by_column") or [
            {"column_name": "", "result": result}
        ]
        statistics = [
            ("Count", "count"), ("Mean", "mean"), ("Median", "median"),
            ("Mode", "mode"), ("Minimum", "minimum"), ("Maximum", "maximum"),
            ("Range", "range"), ("Variance", "variance"),
            ("Std. Deviation", "std_dev"), ("Sample Variance", "sample_variance"),
            ("Sample Std. Deviation", "sample_std_dev"), ("Q1", "q1"),
            ("Q3", "q3"), ("IQR", "iqr"),
        ]

        for column_result in column_results:
            column_name = column_result.get("column_name", "")
            if column_name:
                ctk.CTkLabel(
                    frame, text=column_name, text_color=self.ACCENT,
                    font=self._font(11, True),
                ).pack(anchor="w", padx=self._ui(8), pady=(self._ui(12), self._ui(4)))

            values = column_result.get("result", {})
            for label, key in statistics:
                row = ctk.CTkFrame(frame, fg_color=self.SURFACE, corner_radius=self._ui(6))
                row.pack(fill="x", padx=self._ui(6), pady=self._ui(1))
                ctk.CTkLabel(
                    row, text=label, text_color=self.MUTED,
                    font=self._font(9), anchor="w",
                ).pack(side="left", padx=self._ui(8), pady=self._ui(5))
                ctk.CTkLabel(
                    row, text=str(values.get(key)), text_color=self.TEXT,
                    font=self._font(8, True), anchor="e",
                ).pack(side="right", padx=self._ui(8), pady=self._ui(5))

    def _display_frequency(self, result):
        if self.result_stats_frame is None:
            return

        frame = self.result_stats_frame
        for widget in frame.winfo_children():
            widget.destroy()

        ctk.CTkLabel(
            frame, text="Frequency Distribution", text_color=self.TEXT,
            font=self._font(16, True),
        ).pack(anchor="w", padx=self._ui(16), pady=(self._ui(16), self._ui(10)))

        column_results = result.get("by_column") or [
            {"column_name": "", "result": result}
        ]
        headers = ["Value", "Frequency", "Percent", "Cumulative"]

        for column_result in column_results:
            column_name = column_result.get("column_name", "")
            if column_name:
                ctk.CTkLabel(
                    frame, text=column_name, text_color=self.ACCENT,
                    font=self._font(11, True),
                ).pack(anchor="w", padx=self._ui(8), pady=(self._ui(12), self._ui(4)))

            table = ctk.CTkFrame(frame, fg_color=self.SURFACE, corner_radius=self._ui(8))
            table.pack(fill="x", padx=self._ui(8), pady=self._ui(4))
            for column, header in enumerate(headers):
                table.grid_columnconfigure(column, weight=1)
                ctk.CTkLabel(
                    table, text=header, text_color=self.MUTED,
                    font=self._font(8, True), anchor="center",
                ).grid(row=0, column=column, sticky="ew", padx=self._ui(4), pady=self._ui(7))

            rows = column_result.get("result", {}).get("rows", [])
            for row_index, row_data in enumerate(rows, start=1):
                values = [
                    f'{row_data["value"]:.2f}',
                    str(row_data["frequency"]),
                    f'{row_data["percent"]:.2f}%',
                    str(row_data["cumulative"]),
                ]
                for column, value in enumerate(values):
                    ctk.CTkLabel(
                        table, text=value, text_color=self.TEXT,
                        font=self._font(8), anchor="center",
                    ).grid(row=row_index, column=column, sticky="ew", padx=self._ui(4), pady=self._ui(6))

    def _display_distribution(self, result):
        if self.result_chart_frame is None:
            return

        frame = self.result_chart_frame
        for widget in frame.winfo_children():
            widget.destroy()

        ctk.CTkLabel(
            frame, text="Distribution", text_color=self.TEXT,
            font=self._font(16, True),
        ).pack(anchor="w", padx=self._ui(16), pady=(self._ui(16), self._ui(8)))

        column_results = result.get("by_column") or [
            {"column_name": "", "result": result}
        ]
        count = len(column_results)
        figure = Figure(figsize=(5, max(3, 2.7 * count)), dpi=100)
        axes = figure.subplots(count, 1, squeeze=False).flatten()

        for axis, column_result in zip(axes, column_results):
            values = column_result.get("result", {})
            bins = values.get("bins", [])
            labels = [
                f'{item["lower"]:.1f}–{item["upper"]:.1f}'
                for item in bins
            ]
            frequencies = [item["frequency"] for item in bins]
            axis.bar(labels, frequencies, label="Observed")
            expected = values.get("expected_counts", [])
            distribution_type = values.get("distribution_type", "Histogram")
            if expected and len(expected) == len(labels):
                axis.plot(labels, expected, marker="o", linewidth=1.5, label=f"{distribution_type} fit")
                axis.legend(loc="best", fontsize=7)
            axis.set_xlabel("Value Range")
            axis.set_ylabel("Frequency")
            title = column_result.get("column_name") or "Frequency Distribution"
            axis.set_title(f"{title} · {distribution_type}")
            axis.tick_params(axis="x", labelrotation=35)

        figure.tight_layout()
        canvas = FigureCanvasTkAgg(figure, master=frame)
        canvas.draw()
        canvas.get_tk_widget().pack(
            fill="both", expand=True, padx=self._ui(12), pady=self._ui(8)
        )

        stats_frame = self.result_stats_frame
        if stats_frame is not None:
            for widget in stats_frame.winfo_children():
                widget.destroy()
            has_parameters = False
            for column_result in column_results:
                values = column_result.get("result", {})
                parameters = values.get("fit_parameters", {})
                if not parameters:
                    continue
                has_parameters = True
                label = column_result.get("column_name") or values.get("distribution_type", "Distribution")
                ctk.CTkLabel(
                    stats_frame, text=label, text_color=self.ACCENT,
                    font=self._font(11, True),
                ).pack(anchor="w", padx=self._ui(8), pady=(self._ui(10), self._ui(4)))
                for key, value in parameters.items():
                    row = ctk.CTkFrame(stats_frame, fg_color=self.SURFACE, corner_radius=self._ui(6))
                    row.pack(fill="x", padx=self._ui(6), pady=self._ui(1))
                    ctk.CTkLabel(
                        row, text=key.replace("_", " ").title(),
                        text_color=self.MUTED, font=self._font(9), anchor="w",
                    ).pack(side="left", padx=self._ui(8), pady=self._ui(5))
                    ctk.CTkLabel(
                        row, text=f"{value:.5g}" if isinstance(value, (int, float)) else str(value),
                        text_color=self.TEXT, font=self._font(9, True), anchor="e",
                    ).pack(side="right", padx=self._ui(8), pady=self._ui(5))
            if not has_parameters:
                ctk.CTkLabel(
                    stats_frame, text="Histogram does not estimate a fitted distribution.",
                    text_color=self.MUTED, font=self._font(9),
                ).pack(anchor="w", padx=self._ui(10), pady=self._ui(10))

    def _project_information(
        self
    ):

        datasets = (
            self.dataset_manager.count
        )

        active = (
            self.dataset_manager.active_dataset
        )

        messagebox.showinfo(
            "Project Information",
            (
                f"Project: "
                f"{self.project_name}\n"
                f"File: "
                f"{self.project_path or 'Not saved'}\n"
                f"Datasets: "
                f"{datasets}\n"
                f"Active dataset: "
                f"{active.name if active else 'None'}"
            ),
            parent=self.root
        )

    def _about(
        self
    ):

        messagebox.showinfo(
            "About SIKPRO V2",
            (
                "SIKPRO V2\n"
                "Statistical Process Control\n\n"
                "SPC Dataset project format (.spc)"
            ),
            parent=self.root
        )

    # ==========================================================
    # ACTIONS
    # ==========================================================


    def _open_distribution_popup(
        self
    ):

        dataset = (
            self.dataset_manager.active_dataset
        )

        if dataset is None:
            return

        from sikpro.ui.popups.descriptive.distribution import (
            DistributionPopup
        )

        DistributionPopup(
            self.root,
            dataset,
            self._handle_distribution_popup
        )

    def _open_analysis_dialog(self):
        if self.selected_analysis == "Descriptive":
            if self.selected_method == "Distribution":
                self._open_distribution_popup()
                return
            if self.selected_method == "Summary Statistics":
                self._open_summary_statistics_popup()
                return
            if self.selected_method == "Frequency":
                self._open_frequency_popup()
                return

        dataset = self.dataset_manager.active_dataset
        if dataset is None:
            return

        from sikpro.ui.popups.analysis_settings import AnalysisSettingsPopup
        AnalysisSettingsPopup(
            self.root,
            dataset,
            self.selected_analysis,
            self.selected_method,
            self._handle_general_analysis_popup,
        )

    def _open_frequency_popup(
        self
    ):

        dataset = (
            self.dataset_manager.active_dataset
        )

        if dataset is None:
            return

        from sikpro.ui.popups.descriptive.frequency import (
            FrequencyPopup
        )

        FrequencyPopup(
            self.root,
            dataset,
            self._handle_frequency_popup
        )

    def _open_summary_statistics_popup(
        self
    ):

        dataset = (
            self.dataset_manager.active_dataset
        )

        if dataset is None:
            return

        from sikpro.ui.popups.descriptive.summary_statistics import (
            SummaryStatisticsPopup
        )

        SummaryStatisticsPopup(
            self.root,
            dataset,
            self._handle_summary_statistics_popup
        )
    def _build_analysis_dataset(self, settings, analysis_name):
        dataset = self.dataset_manager.active_dataset
        if dataset is None:
            return None

        selected_columns = sorted(set(settings.get("columns", [])))
        if not selected_columns:
            messagebox.showwarning(
                analysis_name,
                "Please select at least one column.",
                parent=self.root
            )
            return None

        if any(
            not isinstance(index, int) or not (0 <= index < dataset.columns)
            for index in selected_columns
        ):
            raise ValueError("Invalid column selection.")

        row_mode = settings.get("row_mode", "all")
        if row_mode == "range":
            try:
                start_row = int(settings.get("start_row", 1))
                end_row = int(settings.get("end_row", dataset.rows))
            except (TypeError, ValueError):
                raise ValueError("Rows must contain valid numbers.")
            if start_row < 1 or end_row > dataset.rows or start_row > end_row:
                raise ValueError(f"Invalid row range. Use 1-{dataset.rows}.")
            start, end = start_row - 1, end_row
        else:
            start_row, end_row, start, end = 1, dataset.rows, 0, dataset.rows

        selected_data = [
            [row[index] if index < len(row) else "" for index in selected_columns]
            for row in dataset.data[start:end]
        ]

        analysis_dataset = Dataset(
            name=f"{dataset.name} - {analysis_name}",
            rows=len(selected_data),
            columns=len(selected_columns)
        )
        analysis_dataset.headers = [
            dataset.headers[index] if index < len(dataset.headers) else f"C{index + 1}"
            for index in selected_columns
        ]
        analysis_dataset.data = [row.copy() for row in selected_data]
        analysis_dataset.metadata = dataset.metadata.copy()
        analysis_dataset.metadata.update({
            "analysis_columns": selected_columns,
            "analysis_row_mode": row_mode,
            "analysis_start_row": start_row,
            "analysis_end_row": end_row,
            "analysis_name": analysis_name,
            "analysis_source_dataset": dataset.name,
            "analysis_source_index": self.dataset_manager.active_index,
        })
        if "distribution_type" in settings:
            analysis_dataset.metadata["distribution_type"] = settings.get(
                "distribution_type", "Histogram"
            )
        analysis_dataset.metadata["analysis_options"] = dict(settings.get("options", {}))
        return analysis_dataset

    def _handle_summary_statistics_popup(self, settings):
        try:
            dataset = self._build_analysis_dataset(settings, "Summary Statistics")
            return False if dataset is None else self._run_analysis(dataset)
        except Exception as error:
            messagebox.showerror("Summary Statistics", str(error), parent=self.root)
            return False

    def _handle_frequency_popup(self, settings):
        try:
            dataset = self._build_analysis_dataset(settings, "Frequency")
            return False if dataset is None else self._run_analysis(dataset)
        except Exception as error:
            messagebox.showerror("Frequency", str(error), parent=self.root)
            return False

    def _handle_distribution_popup(self, settings):
        try:
            dataset = self._build_analysis_dataset(settings, "Distribution")
            return False if dataset is None else self._run_analysis(dataset)
        except Exception as error:
            messagebox.showerror("Distribution", str(error), parent=self.root)
            return False
    def _handle_general_analysis_popup(self, settings):
        try:
            dataset = self._build_analysis_dataset(
                settings,
                self.selected_method,
            )
            return False if dataset is None else self._run_analysis(dataset)
        except Exception as error:
            messagebox.showerror(
                self.selected_method,
                str(error),
                parent=self.root,
            )
            return False

    def _open_legacy_analysis_dialog(
        self
    ):

        if self.analysis_dialog is not None:

            try:
                if self.analysis_dialog.winfo_exists():
                    self.analysis_dialog.focus()
                    return

            except Exception:
                pass

        dataset = self.dataset_manager.active_dataset

        if dataset is None:
            return

        dialog = ctk.CTkToplevel(
            self.root
        )

        self.analysis_dialog = dialog

        dialog.title(
            f"{self.selected_analysis} / {self.selected_method}"
        )

        dialog.geometry(
            "460x520"
        )

        dialog.resizable(
            False,
            False
        )

        dialog.transient(
            self.root
        )

        dialog.grab_set()

        ctk.CTkLabel(
            dialog,
            text=self.selected_method,
            text_color=self.TEXT,
            font=self._font(
                18,
                True
            )
        ).pack(
            anchor="w",
            padx=24,
            pady=(24, 4)
        )

        ctk.CTkLabel(
            dialog,
            text="Analysis Settings",
            text_color=self.MUTED,
            font=self._font(10)
        ).pack(
            anchor="w",
            padx=24,
            pady=(0, 18)
        )

        data_frame = ctk.CTkFrame(
            dialog,
            fg_color=self.SURFACE_ALT,
            corner_radius=10
        )

        data_frame.pack(
            fill="x",
            padx=20,
            pady=5
        )

        ctk.CTkLabel(
            data_frame,
            text="DATA SELECTION",
            text_color=self.MUTED,
            font=self._font(
                10,
                True
            )
        ).pack(
            anchor="w",
            padx=14,
            pady=(14, 8)
        )

        ctk.CTkLabel(
            data_frame,
            text="Column",
            text_color=self.TEXT
        ).pack(
            anchor="w",
            padx=14
        )

        column_count = getattr(
            dataset,
            "columns",
            1
        )

        column_values = [
            f"C{i + 1}"
            for i in range(column_count)
        ]

        column_box = ctk.CTkComboBox(
            data_frame,
            values=column_values,
            width=180
        )

        column_box.pack(
            anchor="w",
            padx=14,
            pady=(4, 12)
        )

        column_box.set(
            column_values[0]
        )

        ctk.CTkLabel(
            data_frame,
            text="Rows",
            text_color=self.TEXT
        ).pack(
            anchor="w",
            padx=14
        )

        row_mode = ctk.StringVar(
            value="all"
        )

        ctk.CTkRadioButton(
            data_frame,
            text="All rows",
            variable=row_mode,
            value="all"
        ).pack(
            anchor="w",
            padx=14,
            pady=4
        )

        ctk.CTkRadioButton(
            data_frame,
            text="Selected range",
            variable=row_mode,
            value="range"
        ).pack(
            anchor="w",
            padx=14,
            pady=4
        )

        range_frame = ctk.CTkFrame(
            data_frame,
            fg_color="transparent"
        )

        range_frame.pack(
            fill="x",
            padx=14,
            pady=(2, 14)
        )

        ctk.CTkLabel(
            range_frame,
            text="From",
            text_color=self.TEXT
        ).pack(
            side="left"
        )

        start_entry = ctk.CTkEntry(
            range_frame,
            width=70
        )

        start_entry.pack(
            side="left",
            padx=(6, 12)
        )

        start_entry.insert(
            0,
            "1"
        )

        ctk.CTkLabel(
            range_frame,
            text="To",
            text_color=self.TEXT
        ).pack(
            side="left"
        )

        end_entry = ctk.CTkEntry(
            range_frame,
            width=70
        )

        end_entry.pack(
            side="left",
            padx=6
        )

        end_entry.insert(
            0,
            str(
                getattr(
                    dataset,
                    "rows",
                    200
                )
            )
        )

        button_frame = ctk.CTkFrame(
            dialog,
            fg_color="transparent"
        )

        button_frame.pack(
            fill="x",
            padx=20,
            pady=20
        )

        ctk.CTkButton(
            button_frame,
            text="Cancel",
            fg_color=self.SURFACE_ALT,
            text_color=self.TEXT,
            hover_color=self.BORDER,
            command=dialog.destroy
        ).pack(
            side="right",
            padx=(8, 0)
        )

        ctk.CTkButton(
            button_frame,
            text="Run",
            command=lambda: self._confirm_analysis_dialog(
                dialog,
                column_box.get(),
                row_mode.get(),
                start_entry.get(),
                end_entry.get()
            )
        ).pack(
            side="right"
        )

    def _confirm_analysis_dialog(
        self,
        dialog,
        column,
        row_mode,
        start_row,
        end_row
    ):

        dataset = self.dataset_manager.active_dataset

        if dataset is None:
            dialog.destroy()
            return

        try:

            column_index = (
                int(
                    column.replace(
                        "C",
                        ""
                    )
                ) - 1
            )

            data = dataset.data

            if row_mode == "all":

                selected_rows = data

            else:

                start = int(
                    start_row
                ) - 1

                end = int(
                    end_row
                )

                if start < 0:
                    start = 0

                if end > dataset.rows:
                    end = dataset.rows

                if start >= end:
                    raise ValueError(
                        "Invalid row range."
                    )

                selected_rows = data[
                    start:end
                ]

            selected_data = []

            for row in selected_rows:

                if (
                    column_index < 0
                    or column_index >= len(row)
                ):
                    continue

                value = row[
                    column_index
                ]

                selected_data.append([
                    value
                ])

            if not selected_data:
                raise ValueError(
                    "No data found in selected range."
                )

            analysis_dataset = (
                dataset.__class__(
                    name=dataset.name,
                    rows=len(selected_data),
                    columns=1
                )
            )

            analysis_dataset.headers[0] = (
                dataset.headers[column_index]
                if column_index < len(
                    dataset.headers
                )
                else column
            )

            analysis_dataset.data = (
                selected_data
            )

            dialog.destroy()

            self._run_analysis(
                analysis_dataset
            )

        except Exception as error:

            print(
                "Analysis settings error:",
                error
            )
    def _run_analysis(
        self,
        analysis_dataset=None
    ):
        if analysis_dataset is None:
            self._sync_sheet_to_dataset()
            dataset = self.dataset_manager.active_dataset
        else:
            dataset = analysis_dataset

        if dataset is None:
            return False

        self._clear_analysis_results()
        self.last_analysis_result = None
        self.last_analysis_method = None
        self.last_analysis_analysis = None

        try:
            options = dict(dataset.metadata.get("analysis_options", {}))
            if self.selected_method == "Distribution":
                options["distribution_type"] = dataset.metadata.get("distribution_type", "Auto Detect")

            result = self.analysis_engine.run(
                dataset,
                self.selected_analysis,
                self.selected_method,
                options=options
            )

            self.last_analysis_result = result
            self.last_analysis_method = self.selected_method
            self.last_analysis_analysis = self.selected_analysis

            metadata = getattr(dataset, "metadata", {}) or {}
            columns = metadata.get(
                "analysis_columns",
                list(range(getattr(dataset, "columns", 0)))
            )
            row_mode = metadata.get("analysis_row_mode", "all")
            start_row = metadata.get("analysis_start_row", 1)
            end_row = metadata.get("analysis_end_row", getattr(dataset, "rows", 1))
            dataset_index = metadata.get(
                "analysis_source_index",
                getattr(self.dataset_manager, "active_index", 0)
            )
            dataset_name = metadata.get(
                "analysis_source_dataset",
                getattr(dataset, "name", "Dataset")
            )
            self.analysis_history.add(
                analysis=self.selected_analysis,
                method=self.selected_method,
                dataset_name=dataset_name,
                dataset_index=dataset_index,
                columns=columns,
                row_mode=row_mode,
                start_row=start_row,
                end_row=end_row,
                options=options,
                result=result,
            )
            self._render_last_analysis()
            if hasattr(self, "result_panel"):
                self.result_panel.refresh_history()
            self._mark_dirty(True)
            return True

        except Exception as error:
            print("Analysis error:", error)
            messagebox.showerror("Analysis", str(error))

    def _render_last_analysis(self):
        if self.last_analysis_result is None:
            return

        method = self.last_analysis_method or self.selected_method
        analysis = self.last_analysis_analysis or self.selected_analysis
        result = self.last_analysis_result
        if analysis == "Control Chart":
            self._display_control_chart(result)
        elif analysis == "Quality Tools":
            self._display_quality_tool(result)
        elif analysis == "Relationship" and method == "Scatter Plot":
            self._display_scatter_plot(result)
        elif method == "Summary Statistics":
            self._display_summary_statistics(result)
        elif method == "Frequency":
            self._display_frequency(result)
        elif method == "Distribution":
            self._display_distribution(result)
        self._select_result_tab(analysis, method)

    def _display_control_chart(self, result):
        frame = self.result_chart_frame
        if frame is None:
            return
        for widget in frame.winfo_children():
            widget.destroy()

        status = result.get("status", "UNKNOWN")
        color = "#B91C1C" if status == "OUT OF CONTROL" else "#15803D"
        ctk.CTkLabel(
            frame,
            text=f'{result.get("chart_type", self.selected_method)}  |  {status}',
            text_color=color,
            font=self._font(13, True),
        ).pack(anchor="w", padx=self._ui(12), pady=(self._ui(10), self._ui(4)))

        series = result.get("series", [])
        if not series:
            ctk.CTkLabel(frame, text="No chart series available.", text_color=self.MUTED).pack(pady=20)
            return

        figure = Figure(figsize=(5, max(3.0, 2.7 * len(series))), dpi=100)
        axes = figure.subplots(len(series), 1, squeeze=False).flatten()
        for axis, item in zip(axes, series):
            values = item.get("values", [])
            x_values = list(range(1, len(values) + 1))
            axis.plot(x_values, values, marker="o", markersize=3, linewidth=1)
            axis.axhline(item.get("center", 0), linestyle="-", linewidth=1, label="CL")
            axis.axhline(item.get("ucl", 0), linestyle="--", linewidth=1, label="UCL")
            axis.axhline(item.get("lcl", 0), linestyle="--", linewidth=1, label="LCL")
            flagged = set(item.get("out_of_control_points", []))
            points = [index for index in x_values if index in flagged]
            if points:
                axis.scatter(points, [values[index - 1] for index in points], marker="o", s=32)
            axis.set_title(item.get("title", "Control Chart"))
            axis.set_ylabel("Value")
            axis.legend(loc="best", fontsize=7, ncol=3)
        axes[-1].set_xlabel("Subgroup / Observation")
        figure.tight_layout()
        canvas = FigureCanvasTkAgg(figure, master=frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=self._ui(10), pady=self._ui(8))

        rules_frame = self.result_rules_frame
        if rules_frame is not None:
            for widget in rules_frame.winfo_children():
                widget.destroy()
            ctk.CTkLabel(
                rules_frame, text="Nelson Rules 1-8", text_color=self.TEXT,
                font=self._font(13, True),
            ).pack(anchor="w", padx=self._ui(12), pady=(self._ui(12), self._ui(6)))
            if result.get("chart_type") == "MR":
                ctk.CTkLabel(
                    rules_frame,
                    text="Nelson Rules are not applied to the standalone MR chart.",
                    text_color=self.MUTED,
                    font=self._font(9),
                    wraplength=self._ui(310),
                    justify="left",
                ).pack(anchor="w", padx=self._ui(10), pady=self._ui(5))
            for rule in result.get("rules", []):
                violated = rule.get("violated", False)
                points = ", ".join(str(point) for point in rule.get("points", []))
                text = f'Rule {rule.get("rule")}: {rule.get("name")}\n'
                text += "VIOLATION" if violated else "No violation"
                if points:
                    text += f"  |  Points: {points}"
                ctk.CTkLabel(
                    rules_frame, text=text,
                    text_color="#B91C1C" if violated else self.MUTED,
                    font=self._font(9), anchor="w", justify="left",
                    wraplength=self._ui(310),
                ).pack(fill="x", anchor="w", padx=self._ui(10), pady=self._ui(5))

    def _display_quality_tool(self, result):
        frame = self.result_chart_frame
        if frame is None:
            return
        for widget in frame.winfo_children():
            widget.destroy()

        tool = result.get("tool", self.selected_method)
        ctk.CTkLabel(
            frame, text=tool, text_color=self.TEXT,
            font=self._font(14, True),
        ).pack(anchor="w", padx=self._ui(12), pady=(self._ui(10), self._ui(5)))

        if tool == "Histogram":
            self._display_distribution(result)
            return

        if tool in ("Pareto Chart", "Check Sheet"):
            by_column = result.get("by_column", [])
            if tool == "Check Sheet":
                self._display_check_sheet(result)
                return
            figure = Figure(figsize=(5, max(3.0, 2.8 * len(by_column))), dpi=100)
            axes = figure.subplots(max(1, len(by_column)), 1, squeeze=False).flatten()
            for axis, column in zip(axes, by_column):
                items = column.get("items", [])
                labels = [item["category"] for item in items]
                counts = [item["count"] for item in items]
                axis.bar(labels, counts)
                axis.set_title(column.get("column_name", "Pareto"))
                axis.set_ylabel("Count")
                axis.tick_params(axis="x", labelrotation=35)
                axis.set_ylim(bottom=0)
                if items:
                    cumulative_axis = axis.twinx()
                    cumulative_axis.plot(
                        labels,
                        [item["cumulative_percent"] for item in items],
                        marker="o",
                        linewidth=1,
                    )
                    cumulative_axis.set_ylim(0, 105)
                    cumulative_axis.set_ylabel("Cumulative %")
            figure.tight_layout()
            canvas = FigureCanvasTkAgg(figure, master=frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="both", expand=True, padx=self._ui(10), pady=self._ui(8))
            return

        if tool == "Fishbone":
            branches = result.get("branches", [])
            figure = Figure(figsize=(6, 4.3), dpi=100)
            axis = figure.add_subplot(111)
            axis.axis("off")
            axis.plot([0.05, 0.88], [0.5, 0.5], linewidth=2)
            axis.text(0.91, 0.5, result.get("problem", "Effect"), va="center", ha="left", wrap=True)
            for index, branch in enumerate(branches):
                upper = index % 2 == 0
                y = 0.5 + (0.28 if upper else -0.28)
                x = 0.15 + (index // 2) * 0.25
                axis.plot([x, x + 0.12], [y, 0.5], linewidth=1.5)
                axis.text(x, y + (0.02 if upper else -0.02), branch.get("category", ""),
                          fontsize=8, ha="center", va="bottom" if upper else "top")
                causes = branch.get("causes", [])
                label = "\n".join(f"• {cause}" for cause in causes[:5]) or "Add causes"
                axis.text(x - 0.01, y + (0.08 if upper else -0.08), label,
                          fontsize=7, ha="left", va="bottom" if upper else "top")
            figure.tight_layout()
            canvas = FigureCanvasTkAgg(figure, master=frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="both", expand=True, padx=self._ui(10), pady=self._ui(8))
            ctk.CTkLabel(
                frame, text=result.get("instructions", ""),
                text_color=self.MUTED, font=self._font(9),
            ).pack(anchor="w", padx=self._ui(12), pady=(0, self._ui(8)))
            return

        if tool == "Defect Concentration":
            points = result.get("points", [])
            labels_x = sorted({item["x"] for item in points})
            labels_y = sorted({item["y"] for item in points})
            x_lookup = {label: index for index, label in enumerate(labels_x)}
            y_lookup = {label: index for index, label in enumerate(labels_y)}
            figure = Figure(figsize=(5, 4), dpi=100)
            axis = figure.add_subplot(111)
            sizes = [35 + item["count"] * 22 for item in points]
            axis.scatter(
                [x_lookup[item["x"]] for item in points],
                [y_lookup[item["y"]] for item in points],
                s=sizes,
            )
            for item in points:
                axis.annotate(
                    str(item["count"]),
                    (x_lookup[item["x"]], y_lookup[item["y"]]),
                    xytext=(3, 3), textcoords="offset points", fontsize=7,
                )
            axis.set_xticks(list(x_lookup.values()), list(x_lookup.keys()))
            axis.set_yticks(list(y_lookup.values()), list(y_lookup.keys()))
            axis.set_xlabel(result.get("x_label", "X"))
            axis.set_ylabel(result.get("y_label", "Y"))
            axis.grid(True, linewidth=0.3)
            figure.tight_layout()
            canvas = FigureCanvasTkAgg(figure, master=frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="both", expand=True, padx=self._ui(10), pady=self._ui(8))
            return

    def _display_check_sheet(self, result):
        frame = self.result_stats_frame
        if frame is None:
            return
        for widget in frame.winfo_children():
            widget.destroy()
        ctk.CTkLabel(
            frame, text="Check Sheet", text_color=self.TEXT,
            font=self._font(14, True),
        ).pack(anchor="w", padx=self._ui(12), pady=(self._ui(12), self._ui(6)))
        for column in result.get("by_column", []):
            ctk.CTkLabel(
                frame, text=column.get("column_name", "Column"),
                text_color=self.ACCENT, font=self._font(11, True),
            ).pack(anchor="w", padx=self._ui(8), pady=(self._ui(10), self._ui(4)))
            for item in column.get("items", []):
                row = ctk.CTkFrame(frame, fg_color=self.SURFACE, corner_radius=self._ui(5))
                row.pack(fill="x", padx=self._ui(6), pady=self._ui(1))
                ctk.CTkLabel(
                    row, text=item["category"], text_color=self.TEXT,
                    font=self._font(9), anchor="w",
                ).pack(side="left", padx=self._ui(8), pady=self._ui(5))
                ctk.CTkLabel(
                    row, text=str(item["count"]), text_color=self.TEXT,
                    font=self._font(9, True), anchor="e",
                ).pack(side="right", padx=self._ui(8), pady=self._ui(5))

    def _display_scatter_plot(self, result):
        frame = self.result_chart_frame
        if frame is None:
            return
        for widget in frame.winfo_children():
            widget.destroy()
        ctk.CTkLabel(
            frame, text="Scatter Plot", text_color=self.TEXT,
            font=self._font(14, True),
        ).pack(anchor="w", padx=self._ui(12), pady=(self._ui(10), self._ui(5)))
        points = result.get("points", [])
        figure = Figure(figsize=(5, 3.8), dpi=100)
        axis = figure.add_subplot(111)
        axis.scatter([point["x"] for point in points], [point["y"] for point in points])
        axis.set_xlabel(result.get("x_label", "X"))
        axis.set_ylabel(result.get("y_label", "Y"))
        axis.grid(True, linewidth=0.3)
        figure.tight_layout()
        canvas = FigureCanvasTkAgg(figure, master=frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=self._ui(10), pady=self._ui(8))

        stats = self.result_stats_frame
        if stats is not None:
            for widget in stats.winfo_children():
                widget.destroy()
            correlation = result.get("correlation")
            text = "undefined" if correlation is None else f"{correlation:.4f}"
            ctk.CTkLabel(
                stats, text=f'Valid pairs: {result.get("count", len(points))}\nPearson correlation: {text}',
                text_color=self.TEXT, font=self._font(12, True),
                justify="left",
            ).pack(anchor="w", padx=self._ui(12), pady=self._ui(12))

    def _open_history_entry(self, index):
        try:
            entry = self.analysis_history.get(index)
        except (IndexError, TypeError):
            return False

        self.selected_analysis = entry["analysis"]
        self.selected_method = entry["method"]
        self.last_analysis_result = deepcopy(entry["result"])
        self.last_analysis_method = entry["method"]
        self.last_analysis_analysis = entry["analysis"]
        self._clear_analysis_results()
        self._render_last_analysis()
        return True

    def _clear_analysis_history(self):
        if not self.analysis_history.entries:
            return
        if not messagebox.askyesno(
            "Clear Analysis History",
            "Remove all saved analysis history from this project?",
            parent=self.root,
        ):
            return
        self.analysis_history.clear()
        if hasattr(self, "result_panel"):
            self.result_panel.refresh_history()
        self._mark_dirty(True)

    def _clear_analysis_results(self):

        for frame in (
            self.result_chart_frame,
            self.result_stats_frame,
            self.result_rules_frame,
        ):

            if frame is None:
                continue

            for widget in frame.winfo_children():
                widget.destroy()
    # ==========================================================
    # CLOSE
    # ==========================================================

    def _on_close(
        self
    ):

        if not self._confirm_unsaved_changes():
            return

        self._sync_sheet_to_dataset()

        self.root.destroy()

    # ==========================================================
    # RUN
    # ==========================================================

    def run(
        self
    ):

        self.root.mainloop()