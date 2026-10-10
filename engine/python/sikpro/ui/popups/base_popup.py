import customtkinter as ctk


class BaseAnalysisPopup:

    def __init__(
        self,
        parent,
        title,
        width=520,
        height=560
    ):

        self.parent = parent

        self.dialog = ctk.CTkToplevel(
            parent
        )

        self.dialog.title(
            title
        )

        self.dialog.geometry(
            f"{width}x{height}"
        )

        self.dialog.resizable(
            False,
            False
        )

        self.dialog.transient(
            parent
        )

        self.dialog.grab_set()

        self._build()

    # ======================================================
    # BUILD
    # ======================================================

    def _build(self):

        raise NotImplementedError

    # ======================================================
    # HEADER
    # ======================================================

    def build_header(
        self,
        title,
        subtitle="Analysis Settings"
    ):

        ctk.CTkLabel(
            self.dialog,
            text=title,
            font=(
                "Segoe UI",
                18,
                "bold"
            )
        ).pack(
            anchor="w",
            padx=24,
            pady=(18, 2)
        )

        ctk.CTkLabel(
            self.dialog,
            text=subtitle,
            text_color="#737B86",
            font=(
                "Segoe UI",
                10
            )
        ).pack(
            anchor="w",
            padx=24,
            pady=(0, 10)
        )

    # ======================================================
    # BUTTONS
    # ======================================================

    def build_buttons(
        self,
        on_run
    ):

        button_frame = ctk.CTkFrame(
            self.dialog,
            fg_color="transparent"
        )

        button_frame.pack(
            side="bottom",
            fill="x",
            padx=20,
            pady=14
        )

        ctk.CTkButton(
            button_frame,
            text="Cancel",
            width=90,
            fg_color="#F7F8FA",
            text_color="#20242A",
            hover_color="#E1E5EA",
            command=self.close
        ).pack(
            side="right",
            padx=(8, 0)
        )

        ctk.CTkButton(
            button_frame,
            text="Run",
            width=90,
            command=on_run
        ).pack(
            side="right"
        )

    # ======================================================
    # CLOSE
    # ======================================================

    def close(self):

        try:
            self.dialog.grab_release()
        except Exception:
            pass

        self.dialog.destroy()