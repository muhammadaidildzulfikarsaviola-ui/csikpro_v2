import customtkinter as ctk


class ResultPanel:

    def __init__(
        self,
        main_window,
        parent
    ):

        self.main_window = main_window
        self.parent = parent

        self.frame = None
        self.header = None
        self.result_tabs = None
        self.result_chart_frame = None
        self.result_stats_frame = None
        self.result_rules_frame = None
        self.result_history_frame = None

        self.maximized = False

        self.build()

    # ==========================================================
    # BUILD
    # ==========================================================

    def build(self):

        mw = self.main_window

        self.frame = ctk.CTkFrame(
            self.parent,
            fg_color=mw.SURFACE,
            corner_radius=mw._ui(14),
            border_width=1,
            border_color=mw.BORDER
        )

        self.frame.grid(
            row=0,
            column=2,
            sticky="nsew",
            padx=(
                mw._ui(8),
                0
            )
        )

        self.frame.grid_rowconfigure(
            1,
            weight=1
        )

        self.frame.grid_columnconfigure(
            0,
            weight=1
        )

        self._build_header()

        if mw.result_open:
            self._build_tabs()

    # ==========================================================
    # HEADER
    # ==========================================================

    def _build_header(self):

        mw = self.main_window

        header_frame = ctk.CTkFrame(
            self.frame,
            fg_color="transparent"
        )

        header_frame.grid(
            row=0,
            column=0,
            sticky="ew",
            padx=mw._ui(10),
            pady=(
                mw._ui(8),
                2
            )
        )

        header_frame.grid_columnconfigure(
            0,
            weight=1
        )

        self.header = ctk.CTkButton(
            header_frame,
            text=(
                "RESULT"
                if mw.result_open
                else "RESULT"
            ),
            height=mw._ui(32),
            corner_radius=mw._ui(8),
            fg_color="transparent",
            hover_color=mw.SURFACE_ALT,
            text_color=mw.TEXT,
            anchor="w",
            font=mw._font(
                11,
                True
            ),
            command=mw._toggle_result
        )

        self.header.grid(
            row=0,
            column=0,
            sticky="ew"
        )

        self.maximize_button = ctk.CTkButton(
            header_frame,
            text="[ ]",
            width=mw._ui(42),
            height=mw._ui(32),
            corner_radius=mw._ui(8),
            fg_color="transparent",
            hover_color=mw.SURFACE_ALT,
            text_color=mw.TEXT,
            command=self.toggle_maximize
        )

        self.maximize_button.grid(
            row=0,
            column=1,
            padx=(4, 0)
        )

        self.minimize_button = ctk.CTkButton(
            header_frame,
            text="[-]",
            width=mw._ui(42),
            height=mw._ui(32),
            corner_radius=mw._ui(8),
            fg_color="transparent",
            hover_color=mw.SURFACE_ALT,
            text_color=mw.TEXT,
            command=self.toggle_minimize
        )

        self.minimize_button.grid(
            row=0,
            column=2,
            padx=(4, 0)
        )

    # ==========================================================
    # TABS
    # ==========================================================

    def _build_tabs(self):

        if self.result_tabs is not None:
            return

        mw = self.main_window

        tabs = ctk.CTkTabview(
            self.frame,
            corner_radius=mw._ui(10),
            fg_color=mw.SURFACE_ALT
        )

        self.result_tabs = tabs

        tabs.grid(
            row=1,
            column=0,
            sticky="nsew",
            padx=mw._ui(12),
            pady=(
                0,
                mw._ui(14)
            )
        )

        chart = tabs.add(
            "Chart"
        )

        self.result_chart_frame = chart

        stats_tab = tabs.add(
            "Stats"
        )

        stats = ctk.CTkScrollableFrame(
            stats_tab,
            fg_color="transparent",
            scrollbar_button_color="#B8BEC6",
            scrollbar_button_hover_color="#9FA6AF"
        )

        stats.pack(
            fill="both",
            expand=True
        )

        self.result_stats_frame = stats

        rules = tabs.add(
            "Rules"
        )

        self.result_rules_frame = rules

        history_tab = tabs.add("History")
        history = ctk.CTkScrollableFrame(
            history_tab,
            fg_color="transparent",
            scrollbar_button_color="#B8BEC6",
            scrollbar_button_hover_color="#9FA6AF",
        )
        history.pack(fill="both", expand=True, padx=mw._ui(4), pady=mw._ui(4))
        self.result_history_frame = history

        history_actions = ctk.CTkFrame(
            history_tab,
            fg_color="transparent",
        )
        history_actions.pack(fill="x", padx=mw._ui(8), pady=(0, mw._ui(8)))
        ctk.CTkButton(
            history_actions,
            text="Clear History",
            height=mw._ui(28),
            fg_color="transparent",
            border_width=1,
            border_color=mw.BORDER,
            text_color=mw.TEXT,
            hover_color=mw.SURFACE_ALT,
            command=mw._clear_analysis_history,
        ).pack(side="right")

        self._empty_result(
            chart,
            "Chart",
            "Analysis chart will appear here."
        )

        self._empty_result(
            stats,
            "Statistics",
            "Statistical results will appear here."
        )

        self._empty_result(
            rules,
            "Nelson Rules",
            "Rule detection results will appear here."
        )

        if mw.last_analysis_result is not None:
            mw._render_last_analysis()

        self.refresh_history()

    def refresh_history(self):
        frame = self.result_history_frame
        if frame is None or not frame.winfo_exists():
            return

        for widget in frame.winfo_children():
            widget.destroy()

        entries = self.main_window.analysis_history.to_list()
        if not entries:
            ctk.CTkLabel(
                frame,
                text="No analysis history yet.",
                text_color=self.main_window.MUTED,
                font=self.main_window._font(10),
            ).pack(pady=self.main_window._ui(24))
            return

        mw = self.main_window
        for index, entry in enumerate(entries):
            columns = entry.get("columns", [])
            column_label = ", ".join(f"C{value + 1}" for value in columns) or "No column info"
            row_mode = entry.get("row_mode", "all")
            if row_mode == "range":
                rows_label = f"Rows {entry.get('start_row', 1)}-{entry.get('end_row', 1)}"
            else:
                rows_label = "All rows"

            timestamp = entry.get("timestamp", "")
            if "T" in timestamp:
                timestamp = timestamp.replace("T", " ")[:19]

            button = ctk.CTkButton(
                frame,
                text=(
                    f"{entry.get('analysis', 'Analysis')} / {entry.get('method', '')}\n"
                    f"{entry.get('dataset_name', 'Dataset')}\n"
                    f"{column_label} · {rows_label}\n"
                    f"{timestamp}"
                ),
                anchor="w",
                height=mw._ui(78),
                corner_radius=mw._ui(8),
                fg_color=mw.SURFACE,
                hover_color=mw.ACCENT_SOFT,
                border_width=1,
                border_color=mw.BORDER,
                text_color=mw.TEXT,
                font=mw._font(9),
                command=lambda selected=index: mw._open_history_entry(selected),
            )
            button.pack(fill="x", padx=mw._ui(5), pady=mw._ui(4))

    # ==========================================================
    # VISIBILITY
    # ==========================================================

    def toggle_visibility(self):

        mw = self.main_window

        if mw.result_open:

            if self.result_tabs is None:
                self._build_tabs()

            self.result_tabs.grid()

        else:

            if self.result_tabs is not None:
                self.result_tabs.grid_remove()

    # ==========================================================
    # MAXIMIZE
    # ==========================================================

    def toggle_maximize(self):

        if self.maximized:

            self.restore()

        else:

            self.maximized = True

            self.main_window._set_result_maximized(
                True
            )

            self.maximize_button.configure(
                text="[R]"
            )

    # ==========================================================
    # MINIMIZE
    # ==========================================================

    def toggle_minimize(self):

        if self.maximized:

            self.restore()

        else:

            self.main_window._toggle_result()

    # ==========================================================
    # RESTORE
    # ==========================================================

    def restore(self):

        self.maximized = False

        self.main_window._set_result_maximized(
            False
        )

        self.maximize_button.configure(
            text="[ ]"
        )

    # ==========================================================
    # EMPTY RESULT
    # ==========================================================

    def _empty_result(
        self,
        parent,
        title,
        description
    ):

        mw = self.main_window

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
            text_color=mw.TEXT,
            font=mw._font(
                16,
                True
            )
        ).pack(
            pady=(
                mw._ui(60),
                5
            )
        )

        ctk.CTkLabel(
            frame,
            text=description,
            text_color=mw.MUTED,
            font=mw._font(10)
        ).pack()
