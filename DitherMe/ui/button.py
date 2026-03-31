# pylint: disable=line-too-long, unused-argument, missing-module-docstring, missing-class-docstring, missing-function-docstring
import tkinter as tk


class Button(tk.Canvas):
    def __init__(self, parent, text, command=None, height=36, width=None, font=("Arial", 10), color_preview=False):
        super().__init__(
            parent, height=height, bg="#161719",
            highlightthickness=2, highlightbackground="#0E0F10", highlightcolor="#2D8BFF",
            bd=0, relief=tk.FLAT, cursor="hand2", takefocus=1,
        )
        self.command = command
        self.default_bg = "#22242A"
        self.hover_bg = "#2C2E35"
        self.click_bg = "#1A1C21"
        self.color_preview = color_preview

        self.pack(fill=tk.X, padx=8, pady=2)
        self.update_idletasks()
        self.width = self.winfo_width() if width is None else width

        self.button_rect = self.create_rectangle(0, 0, self.width, height, fill=self.default_bg, outline="")
        text_x = self.width * 0.45 if color_preview else self.width // 2
        self.button_text = self.create_text(text_x, height // 2, text=text, fill="#FFFFFF", font=font)

        if color_preview:
            r = height // 3
            px = self.width - r - 10
            py = height // 2
            self.color_circle = self.create_oval(px - r, py - r, px + r, py + r, fill="#FFFFFF", outline="white")

        self.bind("<Enter>",          lambda e: self.itemconfig(self.button_rect, fill=self.hover_bg))
        self.bind("<Leave>",          lambda e: self.itemconfig(self.button_rect, fill=self.default_bg))
        self.bind("<ButtonPress-1>",  lambda e: self.itemconfig(self.button_rect, fill=self.click_bg))
        self.bind("<ButtonRelease-1>",lambda e: self.itemconfig(self.button_rect, fill=self.hover_bg))
        self.bind("<Button-1>",       self._on_press)
        self.bind("<Return>",         self._on_key_activate)
        self.bind("<space>",          self._on_key_activate)
        self.bind("<FocusIn>",        lambda e: self.configure(highlightbackground="#2D8BFF"))
        self.bind("<FocusOut>",       lambda e: self.configure(highlightbackground="#0E0F10"))
        self.bind("<Configure>",      self._on_resize)

    def _on_press(self, event):
        if self.command:
            self.command()

    def _on_key_activate(self, event):
        self.itemconfig(self.button_rect, fill=self.click_bg)
        self.after(80, lambda: self.itemconfig(self.button_rect, fill=self.hover_bg))
        if self.command:
            self.command()

    def _on_resize(self, event):
        self.width = event.width
        h = self.winfo_height()
        self.coords(self.button_rect, 0, 0, self.width, h)
        text_x = self.width * 0.45 if self.color_preview else self.width // 2
        self.coords(self.button_text, text_x, h // 2)
        if self.color_preview:
            r = h // 3
            px = self.width - r - 10
            self.coords(self.color_circle, px - r, h // 2 - r, px + r, h // 2 + r)

    def update_preview_color(self, color):
        if self.color_preview:
            self.itemconfig(self.color_circle, fill=color)
