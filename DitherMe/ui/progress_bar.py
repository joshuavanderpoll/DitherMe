""" Progress bar UI element """
# pylint: disable=line-too-long, unused-argument

import tkinter as tk

class ProgressBar:
    """ Progress bar class """

    def __init__(self, master, height=20, bg_color='#161719', fg_color='#2D8BFF', border_color=None):
        self.master = master
        self.height = height
        self.fg_color = fg_color
        self.bg_color = bg_color
        self.border_color = border_color if border_color else bg_color

        self.canvas = tk.Canvas(master, height=height, bg=self.bg_color, highlightthickness=0)
        self.canvas.pack(fill=tk.X, expand=True, padx=15)

        self.bg_rect = self.canvas.create_rectangle(0, 0, 0, height, outline=self.border_color, fill=self.bg_color, width=1)
        self.progress_bar = self.canvas.create_rectangle(0, 0, 0, height, outline="", fill=self.fg_color)

        master.bind("<Configure>", self.on_resize)
        self.update_bar_width()


    def on_resize(self, event):
        """ Update progress bar width when parent resizes """

        self.update_bar_width()


    def update_bar_width(self):
        """ Update progress bar width """

        width = self.canvas.winfo_width()
        self.canvas.coords(self.bg_rect, 0, 0, width, self.height)
        self.set_progress(0)

    def set_progress(self, progress):
        """ Set progress bar width """

        width = self.canvas.winfo_width()
        self.canvas.coords(self.progress_bar, 0, 0, width * progress, self.height)
        self.canvas.update_idletasks()
