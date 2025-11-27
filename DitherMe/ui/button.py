""" Button UI element """
# pylint: disable=line-too-long, unused-argument

import tkinter as tk

class Button(tk.Canvas):
    """ Button class """

    def __init__(self, parent, text, command=None, height=36, width=None, font=("Arial", 10), color_preview=False):
        super().__init__(
            parent,
            height=height,
            bg="#161719",
            highlightthickness=2,
            highlightbackground="#0E0F10",
            highlightcolor="#2D8BFF",
            bd=0,
            relief=tk.FLAT,
            cursor="hand2",
            takefocus=1,
        )

        self.command = command
        self.default_bg = "#22242A"
        self.hover_bg = "#2C2E35"
        self.click_bg = "#1A1C21"
        self.text_color = "#FFFFFF"
        self.color_preview = color_preview
        self.preview_color = "#FFFFFF"

        # Expand button width to match parent width
        self.pack(fill=tk.X, padx=8, pady=2)

        # Get dynamic width after packing
        self.update_idletasks()
        self.width = self.winfo_width() if width is None else width

        # Draw button rectangle (full width)
        self.button_rect = self.create_rectangle(0, 0, self.width, height, fill=self.default_bg, outline="")

        # Draw centered text
        text_x_position = self.width * 0.45 if self.color_preview else self.width // 2
        self.button_text = self.create_text(text_x_position, height // 2, text=text, fill=self.text_color, font=font)

        # Draw color preview circle (if enabled)
        if self.color_preview:
            preview_radius = height // 3
            preview_x = self.width - preview_radius - 10
            preview_y = height // 2

            self.color_circle = self.create_oval(
                preview_x - preview_radius, preview_y - preview_radius,
                preview_x + preview_radius, preview_y + preview_radius,
                fill=self.preview_color, outline="white"
            )

        # Bind mouse events
        self.bind("<Enter>", self.on_hover)
        self.bind("<Leave>", self.on_leave)
        self.bind("<ButtonPress-1>", self.on_click)
        self.bind("<ButtonRelease-1>", self.on_release)
        self.bind("<Button-1>", self.on_button_press)
        self.bind("<Return>", self.on_key_activate)
        self.bind("<space>", self.on_key_activate)
        self.bind("<FocusIn>", self.on_focus_in)
        self.bind("<FocusOut>", self.on_focus_out)

        # Update width dynamically
        self.bind("<Configure>", self.resize_button)

    def resize_button(self, event):
        """ Update button width dynamically when the parent resizes """
        self.width = event.width
        self.coords(self.button_rect, 0, 0, self.width, self.winfo_height())

        text_x_position = self.width * 0.45 if self.color_preview else self.width // 2
        self.coords(self.button_text, text_x_position, self.winfo_height() // 2)

        if self.color_preview:
            preview_radius = self.winfo_height() // 3
            preview_x = self.width - preview_radius - 10
            preview_y = self.winfo_height() // 2

            self.coords(
                self.color_circle,
                preview_x - preview_radius, preview_y - preview_radius,
                preview_x + preview_radius, preview_y + preview_radius
            )

    def on_hover(self, event):
        """ Change color on hover """
        self.itemconfig(self.button_rect, fill=self.hover_bg)

    def on_leave(self, event):
        """ Reset to default color when mouse leaves """
        self.itemconfig(self.button_rect, fill=self.default_bg)

    def on_click(self, event):
        """ Change color when button is clicked """
        self.itemconfig(self.button_rect, fill=self.click_bg)

    def on_release(self, event):
        """ Restore hover color after click """
        self.itemconfig(self.button_rect, fill=self.hover_bg)

    def on_button_press(self, event):
        """ Execute command if provided """
        if self.command:
            self.command()

    def update_preview_color(self, new_color):
        """ Update the color preview circle """
        if self.color_preview:
            self.preview_color = new_color
            self.itemconfig(self.color_circle, fill=new_color)

    def on_focus_in(self, event):
        """Highlight border when focused via keyboard."""
        self.configure(highlightbackground="#2D8BFF")

    def on_focus_out(self, event):
        """Reset border when focus leaves."""
        self.configure(highlightbackground="#0E0F10")

    def on_key_activate(self, event):
        """Activate button via keyboard."""
        self.on_click(event)
        self.after(80, lambda: self.on_release(event))
        if self.command:
            self.command()
