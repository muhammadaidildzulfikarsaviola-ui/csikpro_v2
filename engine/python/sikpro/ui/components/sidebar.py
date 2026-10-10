import customtkinter as ctk


class Sidebar:

    def __init__(
        self,
        main_window,
        parent,
        width
    ):

        self.main_window = main_window

        self.frame = ctk.CTkFrame(
            parent,
            width=width,
            fg_color=main_window.SURFACE,
            corner_radius=main_window._ui(14),
            border_width=1,
            border_color=main_window.BORDER
        )

        self.frame.grid(
            row=0,
            column=0,
            sticky="nsw",
            padx=(
                0,
                main_window._ui(8)
            )
        )

        self.frame.grid_propagate(
            False
        )

        self.frame.pack_propagate(
            False
        )

        self.frame.grid_columnconfigure(
            0,
            weight=1,
            minsize=0
        )

        self.frame.grid_rowconfigure(
            3,
            weight=1
        )

    def refresh_dataset(self):

        if not self.frame.winfo_exists():
            return

        for widget in (
            self.frame.winfo_children()
        ):

            try:
                row = int(
                    widget.grid_info().get(
                        "row",
                        -1
                    )
                )
            except (
                TypeError,
                ValueError
            ):
                row = -1

            if row in (0, 1):
                widget.destroy()
