# pylint: disable=line-too-long, unused-argument, missing-module-docstring, missing-class-docstring, missing-function-docstring, disallowed-name
import tkinter as tk


class ProgressBar:
    def __init__(self, master, height=20, bg_color="#161719", fg_color="#2D8BFF", border_color=None):
        self.height = height
        self.fg_color = fg_color
        self.bg_color = bg_color
        border = border_color or bg_color

        self.canvas = tk.Canvas(master, height=height, bg=bg_color, highlightthickness=0)
        self.canvas.pack(fill=tk.X, expand=True, padx=15)
        self.bg_rect = self.canvas.create_rectangle(0, 0, 0, height, outline=border, fill=bg_color, width=1)
        self.progress_rect = self.canvas.create_rectangle(0, 0, 0, height, outline="", fill=fg_color)

        master.bind("<Configure>", lambda e: self._resize())
        self._resize()

    def _resize(self):
        w = self.canvas.winfo_width()
        self.canvas.coords(self.bg_rect, 0, 0, w, self.height)
        self.set_progress(0)

    def set_progress(self, progress):
        w = self.canvas.winfo_width()
        self.canvas.coords(self.progress_rect, 0, 0, w * progress, self.height)
        self.canvas.update_idletasks()
