# pylint: disable=line-too-long, unused-argument, missing-module-docstring, missing-class-docstring, missing-function-docstring
import tkinter as tk


class Slider(tk.Canvas):
    def __init__(self, parent, label, min_val, max_val, default_val, command=None, resolution=1):
        self.label = label
        self.min_val = min_val
        self.max_val = max_val
        self.command = command
        self.resolution = resolution
        self.current_value = default_val
        self.value_entry = None

        slider_width = 260
        self.slider_width = int(slider_width * 0.95)
        self.slider_height = 8
        self.dot_radius = 8

        self.container = tk.Frame(parent, bg="#161719")
        self.container.pack(pady=2, padx=5, fill=tk.X)

        self.slider_row = tk.Frame(self.container, bg="#161719")
        self.slider_row.pack(fill=tk.X)

        super().__init__(self.slider_row, height=40, width=self.slider_width, bg="#161719", highlightthickness=0)
        self.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.value_label = tk.Label(self.slider_row, text=str(round(default_val, 1)), bg="#161719", fg="white", width=4)
        self.value_label.pack(side=tk.RIGHT, padx=(5, 0), pady=(5.5, 0))
        self.value_label.bind("<Button-1>", self.enable_text_input)

        self.track = self.create_rectangle(10, 20, self.slider_width - 10, 20 + self.slider_height, fill="#2A2C33", outline="")
        self.progress = self.create_rectangle(10, 20, 10, 20 + self.slider_height, fill="#2D8BFF", outline="")
        self.knob = self.create_oval(10, 16, 10 + self.dot_radius * 2, 16 + self.dot_radius * 2, fill="#2D8BFF", outline="#0E0F10")
        self.label_text = self.create_text(10, 8, text=label, fill="white", font=("Arial", 10), anchor="w")

        self.bind("<B1-Motion>", self.move_knob)
        self.bind("<Button-1>", self.move_knob)
        self.update_slider_position()

    def move_knob(self, event):
        x = max(10, min(event.x, self.slider_width - 10))
        pct = (x - 10) / (self.slider_width - 20)
        new_val = round((self.min_val + pct * (self.max_val - self.min_val)) / self.resolution) * self.resolution
        if new_val != self.current_value:
            self.current_value = new_val
            self.update_slider_position()
            if self.command:
                self.command(new_val)

    def update_slider_position(self):
        pct = (self.current_value - self.min_val) / (self.max_val - self.min_val)
        kx = int(10 + pct * (self.slider_width - 20))
        self.coords(self.progress, 10, 20, kx, 20 + self.slider_height)
        self.coords(self.knob, kx - self.dot_radius, 16, kx + self.dot_radius, 16 + self.dot_radius * 2)
        self.value_label.config(text=str(round(self.current_value, 1)))

    def get_value(self):
        return self.current_value

    def set_value(self, value):
        self.current_value = max(self.min_val, min(value, self.max_val))
        self.update_slider_position()

    def enable_text_input(self, event):
        self.value_entry = tk.Entry(self.slider_row, width=4, bg="#161719", fg="white", insertbackground="white")
        self.value_entry.insert(0, str(self.current_value))
        self.value_entry.pack(side=tk.RIGHT, padx=(5, 0), pady=(5.5, 0))
        self.value_label.pack_forget()
        self.value_entry.bind("<Return>", self.process_text_input)
        self.value_entry.bind("<FocusOut>", self.process_text_input)
        self.value_entry.focus()

    def process_text_input(self, event):
        try:
            value = round(float(self.value_entry.get()) / self.resolution) * self.resolution
            if self.min_val <= value <= self.max_val:
                self.set_value(value)
                if self.command:
                    self.command(value)
        except ValueError:
            pass
        self.value_entry.destroy()
        self.value_label.pack(side=tk.RIGHT, padx=(5, 0), pady=(5.5, 0))
