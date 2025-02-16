import tkinter as tk

class Slider(tk.Canvas):
    def __init__(self, parent, label: str, min_val: float, max_val: float, default_val: float, command=None, resolution=1):
        super().__init__(parent, height=40, bg="#2A2B35", highlightthickness=0)

        self.label = label
        self.min_val = min_val
        self.max_val = max_val
        self.command = command
        self.resolution = resolution

        self.width = 260
        self.slider_width = int(self.width * 0.95)
        self.text_width = int(self.width * 0.05) 
        self.slider_height = 8
        self.dot_radius = 8

        self.current_value = default_val

        # Create a frame to hold all elements
        self.container = tk.Frame(parent, bg="#2A2B35")
        self.container.pack(pady=2, padx=5, fill=tk.X)

        # Create slider row (slider + value)
        self.slider_row = tk.Frame(self.container, bg="#2A2B35")
        self.slider_row.pack(fill=tk.X)

        # Create slider canvas
        super().__init__(self.slider_row, height=40, width=self.slider_width, bg="#2A2B35", highlightthickness=0)
        self.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Create value label (to the right of slider)
        self.value_label = tk.Label(self.slider_row, text=str(round(default_val, 1)), bg="#2A2B35", fg="white", width=4)
        self.value_label.pack(side=tk.RIGHT, padx=(5, 0), pady=(5.5, 0))

        # Create slider components
        self.track = self.create_rectangle(10, 20, self.slider_width - 10, 20 + self.slider_height, fill="#D3D3D3", outline="")
        self.progress = self.create_rectangle(10, 20, 10, 20 + self.slider_height, fill="#006CE8", outline="")
        self.knob = self.create_oval(10, 16, 10 + self.dot_radius * 2, 16 + self.dot_radius * 2, fill="#0059BF", outline="black")

        # Create label directly above the slider (aligned to the left)
        self.label_text = self.create_text(10, 8, text=label, fill="white", font=("Arial", 10), anchor="w")

        # Bind events for interaction
        self.bind("<B1-Motion>", self.move_knob)
        self.bind("<Button-1>", self.move_knob)

        self.update_slider_position()

    def move_knob(self, event):
        """ Move the slider knob based on mouse position """
        x = max(10, min(event.x, self.slider_width - 10))

        # Convert x position to value
        percentage = (x - 10) / (self.slider_width - 20)
        new_value = self.min_val + percentage * (self.max_val - self.min_val)
        new_value = round(new_value / self.resolution) * self.resolution

        # Update the slider only if value changes
        if new_value != self.current_value:
            self.current_value = new_value
            self.update_slider_position()

            # Update value display
            self.value_label.config(text=str(round(new_value, 1)))

            if self.command:
                self.command(new_value)

    def update_slider_position(self):
        """ Update visual representation of the slider """
        percentage = (self.current_value - self.min_val) / (self.max_val - self.min_val)
        knob_x = int(10 + percentage * (self.slider_width - 20))

        # Update progress bar
        self.coords(self.progress, 10, 20, knob_x, 20 + self.slider_height)

        # Update knob position
        self.coords(self.knob, knob_x - self.dot_radius, 16, knob_x + self.dot_radius, 16 + self.dot_radius * 2)

    def get_value(self):
        """ Return the current value of the slider """
        return self.current_value

    def set_value(self, value):
        """ Set the slider value programmatically """
        self.current_value = max(self.min_val, min(value, self.max_val))
        self.update_slider_position()
        self.value_label.config(text=str(self.current_value))  # Update the displayed value
