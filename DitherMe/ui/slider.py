""" Slider UI element """
# pylint: disable=line-too-long, unused-argument

import tkinter as tk

class Slider(tk.Canvas):
    """ Slider class """

    def __init__(self, parent, label: str, min_val: float, max_val: float, default_val: float, command=None, resolution=1):
        super().__init__(parent, height=40, bg="#161719", highlightthickness=0)

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
        self.value_entry = None

        self.current_value = default_val

        # Create a frame to hold all elements
        self.container = tk.Frame(parent, bg="#161719")
        self.container.pack(pady=2, padx=5, fill=tk.X)

        # Create slider row (slider + value)
        self.slider_row = tk.Frame(self.container, bg="#161719")
        self.slider_row.pack(fill=tk.X)

        # Create slider canvas
        super().__init__(self.slider_row, height=40, width=self.slider_width, bg="#161719", highlightthickness=0)
        self.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Create value label (to the right of slider)
        self.value_label = tk.Label(self.slider_row, text=str(round(default_val, 1)), bg="#161719", fg="white", width=4)
        self.value_label.pack(side=tk.RIGHT, padx=(5, 0), pady=(5.5, 0))

        # Bind event to allow user input
        self.value_label.bind("<Button-1>", self.enable_text_input)

        # Create slider components
        self.track = self.create_rectangle(
            10, 20, self.slider_width - 10, 20 + self.slider_height,
            fill="#2A2C33", outline=""
        )
        self.progress = self.create_rectangle(
            10, 20, 10, 20 + self.slider_height,
            fill="#2D8BFF", outline=""
        )
        self.knob = self.create_oval(
            10, 16, 10 + self.dot_radius * 2, 16 + self.dot_radius * 2,
            fill="#2D8BFF", outline="#0E0F10"
        )

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

        # Update the displayed value
        self.value_label.config(text=str(round(self.current_value, 1)))


    def get_value(self):
        """ Return the current value of the slider """

        return self.current_value


    def set_value(self, value):
        """ Set the slider value programmatically """

        self.current_value = max(self.min_val, min(value, self.max_val))
        self.update_slider_position()
        self.value_label.config(text=str(round(self.current_value, 1)))  # Update the displayed value


    def enable_text_input(self, event):
        """ Replace the label with an entry field for manual input """

        self.value_entry = tk.Entry(self.slider_row, width=4, bg="#161719", fg="white", insertbackground="white")
        self.value_entry.insert(0, str(self.current_value))
        self.value_entry.pack(side=tk.RIGHT, padx=(5, 0), pady=(5.5, 0))

        # Remove label
        self.value_label.pack_forget()

        # Bind events for finishing input
        self.value_entry.bind("<Return>", self.process_text_input)
        self.value_entry.bind("<FocusOut>", self.process_text_input)

        # Set focus
        self.value_entry.focus()


    def process_text_input(self, event):
        """ Validate and apply user input """

        try:
            value = float(self.value_entry.get())
            value = round(value / self.resolution) * self.resolution
            if self.min_val <= value <= self.max_val:
                self.set_value(value)  # Update slider value
                if self.command:
                    self.command(value)  # Ensure the command function is called
        except ValueError:
            pass  # Ignore invalid input

        # Remove entry field and restore label
        self.value_entry.destroy()
        self.value_label.pack(side=tk.RIGHT, padx=(5, 0), pady=(5.5, 0))
