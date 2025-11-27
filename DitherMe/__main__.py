""" DitherMe application """
# pylint: disable=line-too-long, unused-argument, no-member

import os
import io
import sys
import tkinter as tk
from tkinter import filedialog, colorchooser
import mimetypes
from PIL import Image, ImageTk, ImageEnhance, ImageFilter, ImageSequence, ImageDraw, ImageColor
import numpy as np

from ui.slider import Slider
from ui.button import Button
from ui.progress_bar import ProgressBar
from algorithms import floydsteinberg, false_floydsteinberg, sierra, sierra_lite, sierra_two_row, atkinson, burkes, stucki, jarvis_judice_ninke, bayer_2x2, bayer_4x4, bayer_8x8, clustered_dot_4x4, checkered_small, checkered_medium, checkered_large, stevenson_arce, knoll, lattice_boltzmann


APP_BG = "#0E0F10"
CONTAINER_BG = "#161719"


class DitherMe:
    """ Main application class for DitherMe. """

    def __init__(self, main_root, startup_file=None):
        self.root = main_root
        self.root.title("DitherMe")
        self.root.geometry("1110x775")
        self.root.configure(bg=APP_BG)

        self.image = None
        self.processed_image = None
        self.is_gif = False
        self.gif_frames = []
        self.gif_durations = []
        self.processed_gif_frames = []
        self.current_frame_index = 0
        self.playing = False
        self.preprocessed_frames = 5

        self.original_width = 200
        self.original_height = 200
        self.current_width = 200
        self.current_height = 200

        self.zoom = 1.0
        self.min_zoom = 0.25
        self.max_zoom = 8.0
        self.pan_x = 0
        self.pan_y = 0
        self._drag_start = None

        self.canvas_width = 500
        self.canvas_height = 500
        self._bg_item_id = None
        self._image_item_id = None

        self.view_mode = tk.StringVar(value="After")
        self.split_ratio = 0.5
        self._dragging_divider = False
        
        self._display_w = None
        self._display_h = None
        self._display_cx = None
        self._display_cy = None

        self.algorithms = {
            # Error Diffusion Dithering
            "Floyd-Steinberg": floydsteinberg,
            "False Floyd-Steinberg": false_floydsteinberg,
            "Sierra": sierra,
            "Sierra Lite": sierra_lite,
            "Sierra Two-Row": sierra_two_row,
            "Atkinson": atkinson,
            "Burkes": burkes,
            "Stucki": stucki,
            "Jarvis-Judice & Ninke": jarvis_judice_ninke,
            "Stevenson-Arce": stevenson_arce,
            "Knoll": knoll,

            # # Ordered Dithering
            "Bayer 2x2": bayer_2x2,
            "Bayer 4x4": bayer_4x4,
            "Bayer 8x8": bayer_8x8,
            "Clustered Dot 4x4": clustered_dot_4x4,
            "Lattice-Boltzmann": lattice_boltzmann,

            # Noise-Based Dithering
            # "Random": ,
            # "Blue Noise": ,
            # "Void-and-Cluster": ,

            # # Checkered Dithering
            "Checkered Small": checkered_small,
            "Checkered Medium": checkered_medium,
            "Checkered Large": checkered_large,

            # Artistic Dithering
            # "Radial Burst": ,
            # "Vortex": ,
            # "Diamond": ,
            # "Spiral": ,
        }

        # Sidebar
        self.frame_right = tk.Frame(self.root, width=300, bg=CONTAINER_BG)
        self.frame_right.pack(side=tk.RIGHT, fill=tk.Y)
        self.frame_right.pack_propagate(False)

        # Main content
        self.frame_left = tk.Frame(self.root, bg=CONTAINER_BG)
        self.frame_left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Upload Button
        self.upload_btn = Button(self.frame_right, "Upload Image/GIF", command=self.upload_image)
        self.upload_btn.pack(pady=10, padx=10)

        # Algorithm Dropdown
        self.selected_algorithm = tk.StringVar(value="Floyd-Steinberg")
        self.algorithm_dropdown = tk.OptionMenu(self.frame_right, self.selected_algorithm, *self.algorithms.keys(), command=self.update_image)
        self.algorithm_dropdown.config(
            bg=CONTAINER_BG,
            fg="white",
            activebackground="#22242A",
            activeforeground="white",
            highlightthickness=0,
            relief=tk.FLAT
        )
        self.algorithm_dropdown["menu"].config(
            bg=CONTAINER_BG,
            fg="white",
            activebackground="#22242A",
            activeforeground="white"
        )
        self.algorithm_dropdown.pack(pady=10, padx=10, fill=tk.X)

        # Dictionary to store sliders
        self.sliders = {}
        self.default_values = {
            "scale": 100, "contrast": 1.0, "midtones": 1.0, "highlights": 1.0,
            "blur": 0, "pixelation": 1, "noise": 0
        }

        # Greyscale Checkbox
        self.is_greyscale = tk.BooleanVar(value=True) 
        self.greyscale_checkbox = tk.Checkbutton(
            self.frame_right,
            text="Greyscale",
            variable=self.is_greyscale,
            bg=CONTAINER_BG,
            fg="white",
            activebackground=CONTAINER_BG,
            activeforeground="white",
            selectcolor=CONTAINER_BG,
            command=self.update_image
        )
        self.greyscale_checkbox.pack(pady=5, padx=10, anchor="w")

        # Sliders
        self.add_slider("Scale (%)", "scale", 1, 100, 100, self.update_image, True)
        self.add_slider("Contrast", "contrast", 0.5, 3.0, 1.0, self.update_image, 0.1)
        self.add_slider("Midtones", "midtones", 0.5, 3.0, 1.0, self.update_image, 0.1)
        self.add_slider("Highlights", "highlights", 0.5, 3.0, 1.0, self.update_image, 0.1)
        self.add_slider("Blur", "blur", 0, 10, 0, self.update_image, 0.1)
        self.add_slider("Pixelation", "pixelation", 1, 20, 1, self.update_image)
        self.add_slider("Noise", "noise", 0, 100, 0, self.update_image)

        # Foreground and Background color initialization
        self.selected_foreground = "#FFFFFF"  # Default to white
        self.selected_background = "#000000"  # Default to black

        # Foreground color picker
        self.foreground_btn = Button(self.frame_right, "Select Foreground Color", command=self.pick_foreground, color_preview=True)
        self.foreground_btn.update_preview_color(self.selected_foreground)
        self.foreground_btn.pack(pady=5, padx=10)
        self.add_slider("Foreground Opacity", "foreground_opacity", 0, 255, 255, self.update_image)

        # Background color picker
        self.background_btn = Button(self.frame_right, "Select Background Color", command=self.pick_background, color_preview=True)
        self.background_btn.update_preview_color(self.selected_background)
        self.background_btn.pack(pady=5, padx=10)
        self.add_slider("Background Opacity", "background_opacity", 0, 255, 255, self.update_image)

        # Reset Options Button
        self.reset_btn = Button(self.frame_right, "Reset Options", command=self.reset_options)
        self.reset_btn.pack(pady=10, padx=10)

        # Container for Image Preview
        self.image_container = tk.Frame(self.frame_left, bg=CONTAINER_BG, relief=tk.RIDGE)
        self.image_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Canvas for main image
        self.canvas_image = tk.Canvas(self.image_container, bg="black", highlightthickness=0)
        self.canvas_image.pack(expand=True, fill=tk.BOTH)

        # Resize handler: keep checkerboard full size
        self.canvas_image.bind("<Configure>", self.on_canvas_resize)

        # Zoom & pan bindings
        self.canvas_image.bind("<ButtonPress-1>", self.on_pan_start)
        self.canvas_image.bind("<B1-Motion>", self.on_pan_move)
        self.canvas_image.bind("<ButtonRelease-1>", self.on_pan_end)

        # Scroll-wheel zoom (Windows/macOS)
        self.canvas_image.bind("<MouseWheel>", self.on_mouse_wheel)
        # Scroll-wheel zoom (Linux)
        self.canvas_image.bind("<Button-4>", self.on_mouse_wheel_linux)
        self.canvas_image.bind("<Button-5>", self.on_mouse_wheel_linux)

        # Double click to reset view
        self.canvas_image.bind("<Double-Button-1>", self.reset_view)

        # Play/Stop Buttons
        self.frame_bottom = tk.Frame(self.frame_left, bg=CONTAINER_BG)
        self.frame_bottom.pack(pady=10)

        self.view_mode_menu = tk.OptionMenu(
            self.frame_bottom,
            self.view_mode,
            "After",
            "Split",
            command=self.on_view_mode_change
        )
        self.view_mode_menu.config(
            bg=CONTAINER_BG,
            fg="white",
            activebackground="#22242A",
            activeforeground="white",
            highlightthickness=0,
            relief=tk.FLAT
        )
        self.view_mode_menu["menu"].config(
            bg=CONTAINER_BG,
            fg="white",
            activebackground="#22242A",
            activeforeground="white"
        )
        self.view_mode_menu.pack(side=tk.LEFT, padx=5)

        self.play_btn = Button(self.frame_bottom, "Play GIF", command=self.play_gif)
        self.play_btn.pack(side=tk.LEFT, padx=5)
        self.play_btn.pack_forget()

        self.stop_btn = Button(self.frame_bottom, "Stop GIF", command=self.stop_gif)
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        self.stop_btn.pack_forget()

        # Export Button
        self.export_btn = Button(self.frame_right, "Export Image", command=self.export_image)
        self.export_btn.pack(pady=10, padx=10)

        # Progress Bar
        self.progress_bar = ProgressBar(
            self.frame_right,
            height=20,
            bg_color=CONTAINER_BG,
            fg_color="#2D8BFF",
            border_color=CONTAINER_BG
        )

        self.update_canvas_size()

        if startup_file and os.path.exists(startup_file):
            self.upload_image(startup_file)


    def add_slider(self, label, key, from_, to, default, command, resolution=1):
        """ Add a slider UI item. """

        slider = Slider(self.frame_right, label, min_val=from_, max_val=to, default_val=default, command=lambda v: command(), resolution=resolution)
        self.sliders[key] = slider


    def pick_foreground(self):
        """ Open color picker for foreground color. """

        color_code = colorchooser.askcolor(title="Choose Foreground Color")[1]
        if color_code:
            self.selected_foreground = color_code
            self.foreground_btn.update_preview_color(color_code)
            self.update_image()


    def pick_background(self):
        """ Open color picker for background color. """

        color_code = colorchooser.askcolor(title="Choose Background Color")[1]
        if color_code:
            self.selected_background = color_code
            self.background_btn.update_preview_color(color_code)
            self.update_image()


    def reset_options(self):
        """ Reset all options to default values. """

        for key, value in self.default_values.items():
            self.sliders[key].set_value(value)

        self.selected_foreground = "#FFFFFF"
        self.selected_background = "#000000"
        self.foreground_btn.update_preview_color(self.selected_foreground)
        self.background_btn.update_preview_color(self.selected_background)

        self.update_image()


    def upload_image(self, file_path=None):
        """ Open a file dialog to upload an image. """

        if not file_path:
            filetypes = [
                ("Image files", "*.png *.jpg *.jpeg *.gif *.webp *.bmp *.tiff"),
                ("All files", "*.*"),
            ]
            file_path = filedialog.askopenfilename(
                title="Select an image or GIF",
                filetypes=filetypes
            )

        if file_path and os.path.exists(file_path):
            mime_type, _ = mimetypes.guess_type(file_path)

            if not mime_type or not mime_type.startswith("image/"):
                tk.messagebox.showerror(
                    "Invalid File",
                    "Please select a valid image file (PNG, JPG, GIF, WEBP, BMP, TIFF)."
                )
                return

            self.root.title(f"DitherMe - {os.path.basename(file_path)}")
            self.is_gif = mime_type == "image/gif"
            self.update_gif_controls()
            self.image = Image.open(file_path)

            if self.is_gif:
                self.gif_durations = [frame.info.get("duration", 100) for frame in ImageSequence.Iterator(self.image)]
                self.gif_frames = [frame.convert("RGBA") for frame in ImageSequence.Iterator(self.image)]
                self.processed_gif_frames = [None] * len(self.gif_frames)  # Lazy processing placeholder

                # Process only a few frames at first
                for i in range(min(self.preprocessed_frames, len(self.gif_frames))):
                    self.processed_gif_frames[i] = self.process_frame(self.gif_frames[i])

            else:
                self.image = self.image.convert("RGBA")
                self.processed_image = self.image.copy()

            self.original_width, self.original_height = self.image.size
            self.zoom = 1.0
            self.pan_x = 0
            self.pan_y = 0
            self._drag_start = None
            self.update_canvas_size()
            self.update_image()


    def update_gif_controls(self):
        """Show or hide GIF controls based on whether the current file is a GIF."""
        if self.is_gif:
            if not self.play_btn.winfo_ismapped():
                self.play_btn.pack(side=tk.LEFT, padx=5)
                self.stop_btn.pack(side=tk.LEFT, padx=5)
        else:
            self.playing = False
            self.play_btn.pack_forget()
            self.stop_btn.pack_forget()


    def update_canvas_size(self):
        """ Update the canvas size """

        if not self.original_width or not self.original_height:
            return

        max_width, max_height = 500, 500
        aspect_ratio = self.original_width / self.original_height

        if self.original_width > max_width or self.original_height > max_height:
            if aspect_ratio > 1:
                self.current_width = max_width
                self.current_height = int(max_width / aspect_ratio)
            else:
                self.current_height = max_height
                self.current_width = int(max_height * aspect_ratio)
        else:
            self.current_width, self.current_height = self.original_width, self.original_height


    def create_checkerboard(self, width, height, box_size=10):
        """ Create a checkerboard pattern as a background. """

        pattern = Image.new("RGB", (width, height), "#BFBFBF")

        draw = ImageDraw.Draw(pattern)
        for y in range(0, height, box_size * 2):
            for x in range(0, width, box_size * 2):
                draw.rectangle([x, y, x + box_size, y + box_size], fill="#E0E0E0")
                draw.rectangle([x + box_size, y + box_size, x + box_size * 2, y + box_size * 2], fill="#E0E0E0")

        return pattern
    
    
    def on_view_mode_change(self, *_):
        """Als de view mode verandert (After/Split), teken direct opnieuw."""
        self._redraw_current()


    def on_canvas_resize(self, event):
        """Make checkerboard fill the entire canvas whenever it resizes."""
        self.canvas_width = max(1, event.width)
        self.canvas_height = max(1, event.height)

        # Generate checkerboard at canvas size
        self.checkerboard_bg = self.create_checkerboard(self.canvas_width, self.canvas_height)
        self.checkerboard_bg_tk = ImageTk.PhotoImage(self.checkerboard_bg)

        if self._bg_item_id is None:
            # Draw background once, at the very back
            self._bg_item_id = self.canvas_image.create_image(
                0, 0,
                anchor=tk.NW,
                image=self.checkerboard_bg_tk,
            )
        else:
            # Update existing background image
            self.canvas_image.itemconfig(self._bg_item_id, image=self.checkerboard_bg_tk)
            self.canvas_image.coords(self._bg_item_id, 0, 0)

        # Optionally re-center the current image on resize
        self._redraw_current()


    def update_image(self, algorithm=None):
        """ Update the displayed image based on the current settings. """

        if self.is_gif and self.gif_frames:
            # Clear all cached processed frames
            self.processed_gif_frames = [None] * len(self.gif_frames)

            # Preprocess only a small number of frames for a fast preview
            for i in range(min(self.preprocessed_frames, len(self.gif_frames))):
                self.processed_gif_frames[i] = self.process_frame(self.gif_frames[i])

            # Reset to first frame
            self.current_frame_index = 0
            self._redraw_current()

        elif self.image:
            self.processed_image = self.process_frame(self.image)
            self._redraw_current()


    def process_frame(self, img):
        """ Process an image frame """

        # Ensure image is in RGB mode
        img_rgb = img.convert("RGB")

        # Get scale factor (percent-based)
        scale_factor = self.sliders["scale"].get_value() / 100.0

        # Resize image
        new_size = (max(1, int(img.width * scale_factor)), max(1, int(img.height * scale_factor)))
        img_resized = img_rgb.resize(new_size, Image.LANCZOS)

        # Convert to grayscale if selected
        if self.is_greyscale.get():
            img_converted = img_resized.convert("L")
        else:
            img_converted = img_resized

        # Apply contrast adjustment
        contrast_factor = self.sliders["contrast"].get_value()
        img_converted = ImageEnhance.Contrast(img_converted).enhance(contrast_factor)

        # Apply midtones and highlights correction
        midtone_factor = self.sliders["midtones"].get_value()
        highlight_factor = self.sliders["highlights"].get_value()

        np_img = np.array(img_converted, dtype=np.float32) / 255.0
        np_img = np_img ** (1 / midtone_factor)  # Adjust midtones
        np_img = np.clip(np_img * highlight_factor, 0, 1)  # Adjust highlights
        img_converted = Image.fromarray((np_img * 255).astype(np.uint8))

        # Apply blur
        blur_amount = self.sliders["blur"].get_value()
        if blur_amount > 0:
            img_converted = img_converted.filter(ImageFilter.GaussianBlur(blur_amount))

        # Apply pixelation
        pixelation_factor = self.sliders["pixelation"].get_value()
        if pixelation_factor > 1:
            img_converted = img_converted.resize((img_converted.width // pixelation_factor, img_converted.height // pixelation_factor), Image.NEAREST)
            img_converted = img_converted.resize((img_converted.width * pixelation_factor, img_converted.height * pixelation_factor), Image.NEAREST)

        # Apply noise
        img_converted = self.apply_noise(img_converted)

        # Convert image to bytes
        img_byte_arr = io.BytesIO()
        img_converted.save(img_byte_arr, format="PNG")
        img_bytes = img_byte_arr.getvalue()

        # Apply dithering algorithm
        dither_algorithm = self.algorithms[self.selected_algorithm.get()]
        dithered_bytes = dither_algorithm.dither(img_bytes)
        dithered_img = Image.open(io.BytesIO(dithered_bytes)).convert("L" if self.is_greyscale.get() else "RGB")

        # If greyscale mode is enabled, apply foreground/background colors
        if self.is_greyscale.get():
            np_dithered = np.array(dithered_img)

            # Get foreground and background colors
            fg_color = ImageColor.getrgb(self.selected_foreground)
            bg_color = ImageColor.getrgb(self.selected_background)

            # Get opacity values (0-255)
            fg_opacity = self.sliders["foreground_opacity"].get_value() / 255.0
            bg_opacity = self.sliders["background_opacity"].get_value() / 255.0

            # Convert to RGBA
            np_colored = np.zeros((*np_dithered.shape, 4), dtype=np.uint8)  # 4 channels (RGBA)

            # Apply colors with opacity blending
            np_colored[np_dithered < 128] = [*bg_color, int(bg_opacity * 255)]  # Dark pixels -> Background
            np_colored[np_dithered >= 128] = [*fg_color, int(fg_opacity * 255)]  # Light pixels -> Foreground

            # Convert back to PIL image
            final_image = Image.fromarray(np_colored, mode="RGBA")
        else:
            # Keep dithered image as is if not in greyscale mode
            final_image = dithered_img

        # Resize to original size for display
        final_image = final_image.resize((self.original_width, self.original_height), Image.NEAREST)

        return final_image


    def apply_noise(self, img):
        """ Apply noise to the image """

        noise_level = self.sliders["noise"].get_value()
        if noise_level == 0:
            return img  # No noise applied

        np_img = np.array(img)
        noise = np.random.randint(-noise_level, noise_level, np_img.shape, dtype=np.int16)
        np_img = np.clip(np_img + noise, 0, 255).astype(np.uint8)

        return Image.fromarray(np_img)


    def display_image(self, img):
        """ Display the image on the canvas. """
        if img is None:
            return

        base_w, base_h = self.current_width, self.current_height
        scale = max(self.min_zoom, min(self.max_zoom, self.zoom))
        disp_w = max(1, int(base_w * scale))
        disp_h = max(1, int(base_h * scale))
        img_resized = img.resize((disp_w, disp_h), Image.LANCZOS)
        img_tk = ImageTk.PhotoImage(img_resized.convert("RGBA"))

        # Canvas center (we want to keep it centered + pan offset)
        canvas_w = self.canvas_image.winfo_width() or base_w
        canvas_h = self.canvas_image.winfo_height() or base_h
        center_x = canvas_w // 2 + self.pan_x
        center_y = canvas_h // 2 + self.pan_y

        self._display_w = disp_w
        self._display_h = disp_h
        self._display_cx = center_x
        self._display_cy = center_y

        if self._image_item_id is None:
            # First time: create the item
            self._image_item_id = self.canvas_image.create_image(center_x, center_y, image=img_tk)
        else:
            # Update existing item (faster than recreating)
            self.canvas_image.itemconfig(self._image_item_id, image=img_tk)
            self.canvas_image.coords(self._image_item_id, center_x, center_y)

        # Keep reference so it doesn't get GC'd
        self.canvas_image.image = img_tk


    def _get_current_frames(self):
        """Return (original_frame, processed_frame) for current still or GIF."""
        if self.is_gif and self.gif_frames:
            orig = self.gif_frames[self.current_frame_index]
            proc = self.processed_gif_frames[self.current_frame_index]
            if proc is None:
                proc = orig
        else:
            orig = self.image
            proc = self.processed_image if self.processed_image is not None else orig
        return orig, proc

    def _redraw_current(self):
        orig, proc = self._get_current_frames()
        view_img = self.build_view_image(orig, proc)
        self.display_image(view_img)


    def build_view_image(self, orig, proc):
        """Bouw het beeld op basis van huidige view mode (After/Split)."""
        if orig is None and proc is None:
            return None

        if orig is None:
            orig = proc
        if proc is None:
            proc = orig

        orig = orig.convert("RGBA")
        proc = proc.convert("RGBA")

        W, H = self.original_width, self.original_height
        orig = orig.resize((W, H), Image.LANCZOS)
        proc = proc.resize((W, H), Image.LANCZOS)

        mode = self.view_mode.get()

        if mode == "Split":
            min_ratio = 0.05
            max_ratio = 0.95
            self.split_ratio = max(min_ratio, min(max_ratio, self.split_ratio))

            split_x = int(self.split_ratio * W)
            split_x = max(0, min(W, split_x))

            result = Image.new("RGBA", (W, H))

            if split_x > 0:
                left = orig.crop((0, 0, split_x, H))
                result.paste(left, (0, 0))

            if split_x < W:
                right = proc.crop((split_x, 0, W, H))
                result.paste(right, (split_x, 0))

            if 0 <= split_x < W:
                draw = ImageDraw.Draw(result)
                draw.line([(split_x, 0), (split_x, H)], fill=(255, 0, 0, 255), width=3)
                r = 6 
                draw.ellipse(
                    (split_x - r, 0, split_x + r, 2 * r),
                    fill=(255, 0, 0, 255)
                )
                draw.ellipse(
                    (split_x - r, H - 2 * r, split_x + r, H),
                    fill=(255, 0, 0, 255)
                )

            return result

        return proc


    def create_checkerboard(self, width, height, box_size=10):
        """ Create a checkerboard pattern as a background. """

        pattern = Image.new("RGB", (width, height), "#BFBFBF")

        draw = ImageDraw.Draw(pattern)
        for y in range(0, height, box_size * 2):
            for x in range(0, width, box_size * 2):
                draw.rectangle([x, y, x + box_size, y + box_size], fill="#E0E0E0")
                draw.rectangle([x + box_size, y + box_size, x + box_size * 2, y + box_size * 2], fill="#E0E0E0")

        return pattern


    def play_gif(self):
        """ Play the GIF animation """

        self.playing = True
        self.animate()


    def stop_gif(self):
        """ Stop the GIF animation """

        self.playing = False


    def set_zoom(self, new_zoom: float):
        """Set zoom level and refresh view."""
        new_zoom = max(self.min_zoom, min(self.max_zoom, new_zoom))
        if abs(new_zoom - self.zoom) < 1e-3:
            return

        self.zoom = new_zoom
        self._redraw_current()


    def on_mouse_wheel(self, event):
        """Zoom in/out with the mouse wheel (Windows/macOS)."""
        factor = 1.1 if event.delta > 0 else 1 / 1.1
        self.set_zoom(self.zoom * factor)


    def on_mouse_wheel_linux(self, event):
        """Zoom in/out with the mouse wheel (Linux Button-4/5)."""
        factor = 1.1 if event.num == 4 else 1 / 1.1
        self.set_zoom(self.zoom * factor)


    def reset_view(self, event=None):
        """Reset zoom & pan to default (center image)."""
        self.zoom = 1.0
        self.pan_x = 0
        self.pan_y = 0
        self._redraw_current()


    def on_pan_start(self, event):
        """Start panning (left mouse button) of divider drag in Split mode."""
        self._drag_start = (event.x, event.y)
        self._dragging_divider = False

        if self.view_mode.get() == "Split" and self._display_w and self._display_cx is not None:
            left_edge = self._display_cx - self._display_w / 2
            divider_x = left_edge + self.split_ratio * self._display_w

            if abs(event.x - divider_x) <= 12:
                self._dragging_divider = True


    def on_pan_move(self, event):
        """Pan while dragging, of de divider verschuiven in Split mode."""
        if self._image_item_id is None:
            return

        if self._dragging_divider and self.view_mode.get() == "Split" and self._display_w and self._display_cx is not None:
            left_edge = self._display_cx - self._display_w / 2
            rel_x = event.x - left_edge

            if self._display_w > 0:
                min_ratio = 0.05
                max_ratio = 0.95
                raw_ratio = rel_x / self._display_w
                self.split_ratio = max(min_ratio, min(max_ratio, raw_ratio))
                self._redraw_current()

            return

        if self._drag_start is None:
            return

        dx = event.x - self._drag_start[0]
        dy = event.y - self._drag_start[1]
        self._drag_start = (event.x, event.y)
        self.canvas_image.move(self._image_item_id, dx, dy)
        self.pan_x += dx
        self.pan_y += dy


    def on_pan_end(self, event):
        """End panning of divider drag."""
        self._drag_start = None
        self._dragging_divider = False


    def animate(self):
        """ Animate the GIF frames """

        if self.playing and self.is_gif:
            if self.current_frame_index >= len(self.gif_frames):
                self.current_frame_index = 0

            # Process the frame lazily if it hasn't been processed yet
            if self.processed_gif_frames[self.current_frame_index] is None:
                self.processed_gif_frames[self.current_frame_index] = self.process_frame(self.gif_frames[self.current_frame_index])

            self._redraw_current()

            frame_duration = self.gif_durations[self.current_frame_index]
            self.current_frame_index = (self.current_frame_index + 1) % len(self.gif_frames)

            self.root.after(frame_duration, self.animate)


    def export_image(self):
        """Export the image or GIF to a file, supporting multiple formats."""

        if not self.processed_image and not self.processed_gif_frames:
            return
        
        if self.is_gif:
            filetypes = [
                ("GIF files (*.gif)", "*.gif"),
                ("PNG files (*.png)", "*.png"),
            ]
        else:
            filetypes = [
                ("PNG files (*.png)", "*.png"),
                ("JPEG files (*.jpeg)", "*.jpeg"),
                ("WebP files (*.webp)", "*.webp"),
                ("TIFF files (*.tiff)", "*.tiff"),
                ("BMP files (*.bmp)", "*.bmp"),
                ("ICO files (*.ico)", "*.ico"),
            ]

        file_path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=filetypes,
        )

        if not file_path:
            return

        if self.is_gif:
            total_frames = len(self.gif_frames)
            if total_frames == 0:
                return

            self.progress_bar.set_progress(0)

            for i in range(total_frames):
                if self.processed_gif_frames[i] is None:
                    self.processed_gif_frames[i] = self.process_frame(self.gif_frames[i])

                # Update progress bar
                self.progress_bar.set_progress((i + 1) / total_frames)
                self.root.update()

            processed_frames = [frame.convert("RGBA") for frame in self.processed_gif_frames if frame is not None]

            if processed_frames:
                processed_frames[0].save(
                    file_path,
                    save_all=True,
                    append_images=processed_frames[1:],
                    loop=0,
                    duration=self.gif_durations[:len(processed_frames)],
                    transparency=255,
                    disposal=2,
                )

                self.progress_bar.set_progress(0)
                tk.messagebox.showinfo("Export Successful", "The GIF has been successfully exported.")
            else:
                tk.messagebox.showerror("Export Error", "No frames available to export.")

        else:
            img_to_save = self.processed_image or self.image
            if img_to_save is None:
                return

            ext = os.path.splitext(file_path)[1].lower()

            fmt_map = {
                ".png": "PNG",
                ".jpg": "JPEG",
                ".jpeg": "JPEG",
                ".webp": "WEBP",
                ".tif": "TIFF",
                ".tiff": "TIFF",
                ".bmp": "BMP",
                ".ico": "ICO",
            }
            fmt = fmt_map.get(ext, "PNG")

            self.progress_bar.set_progress(1)
            self.root.update()

            try:
                if fmt == "ICO":
                    # ICO: must be <= 256x256, Windows-style icon
                    
                    ico_img = img_to_save.convert("RGBA")
                    if ico_img.width > 256 or ico_img.height > 256:
                        ico_img = ico_img.copy()
                        ico_img.thumbnail((256, 256), Image.LANCZOS)
                    ico_img.save(file_path, format="ICO")
                else:
                    img_to_save.save(file_path, format=fmt)

                tk.messagebox.showinfo(
                    "Export Successful",
                    f"The image has been successfully exported as {fmt}."
                )
            except Exception as exc:
                tk.messagebox.showerror(
                    "Export Error",
                    f"Failed to export image:\n{exc}"
                )
            finally:
                self.progress_bar.set_progress(0)


if __name__ == "__main__":
    ARGV_FILE = None

    if len(sys.argv) > 1:
        ARGV_FILE = sys.argv[1]

    root = tk.Tk()
    app = DitherMe(root, ARGV_FILE)
    root.mainloop()
