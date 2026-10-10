import tkinter as tk


class SplashScreen:
    def __init__(self, on_complete):
        self.on_complete = on_complete

        self.root = tk.Tk()
        self.root.title("SIKPRO V2")
        self.root.geometry("500x300")
        self.root.resizable(False, False)

        self._center_window()

        self.title_label = tk.Label(
            self.root,
            text="SIKPRO V2",
            font=("Segoe UI", 26, "bold"),
        )
        self.title_label.pack(pady=(75, 8))

        self.status_label = tk.Label(
            self.root,
            text="Initializing...",
            font=("Segoe UI", 10),
        )
        self.status_label.pack()

        self.progress = tk.Canvas(
            self.root,
            width=300,
            height=8,
            highlightthickness=0,
        )
        self.progress.pack(pady=22)

        self.progress.create_rectangle(
            0,
            0,
            300,
            8,
            outline="",
        )

        self.progress.create_rectangle(
            0,
            0,
            0,
            8,
            outline="",
            tags="bar",
        )

        self.progress_value = 0

        self._animate()

    def _center_window(self):
        self.root.update_idletasks()

        width = 500
        height = 300

        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        x = (screen_width - width) // 2
        y = (screen_height - height) // 2

        self.root.geometry(
            f"{width}x{height}+{x}+{y}"
        )

    def _animate(self):
        if self.progress_value <= 300:
            self.progress.coords(
                "bar",
                0,
                0,
                self.progress_value,
                8,
            )

            self.progress_value += 4

            self.root.after(
                15,
                self._animate,
            )

            return

        self.status_label.config(
            text="Starting SIKPRO V2..."
        )

        self.root.after(
            400,
            self._finish,
        )

    def _finish(self):
        self.root.destroy()
        self.on_complete()

    def run(self):
        self.root.mainloop()