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
from DitherMe.algorithms import floydsteinberg, false_floydsteinberg, sierra, sierra_lite, sierra_two_row, atkinson, burkes, stucki, jarvis_judice_ninke, bayer_2x2, bayer_4x4, bayer_8x8, clustered_dot_4x4, checkered_small, checkered_medium, checkered_large


class DitherMe:
    """ Main application class for DitherMe. """

    def __init__(self, main_root, startup_file=None):
        self.root = main_root
        self.root.title("DitherMe")
        self.root.geometry("1110x775")
        self.root.configure(bg="#1A1A23")

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
            # "Stevenson-Arce": ,
            # "Knoll": ,

            # # Ordered Dithering
            "Bayer 2x2": bayer_2x2,
            "Bayer 4x4": bayer_4x4,
            "Bayer 8x8": bayer_8x8,
            "Clustered Dot 4x4": clustered_dot_4x4,
            # "Lattice-Boltzmann": ,

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
        self.frame_right = tk.Frame(self.root, width=300, bg="#2A2B35")
        self.frame_right.pack(side=tk.RIGHT, fill=tk.Y)
        self.frame_right.pack_propagate(False)

        # Main content
        self.frame_left = tk.Frame(self.root, bg="#1A1A23")
        self.frame_left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Upload Button
        self.upload_btn = Button(self.frame_right, "Upload Image/GIF", command=self.upload_image)
        self.upload_btn.pack(pady=10, padx=10)

        # Algorithm Dropdown
        self.selected_algorithm = tk.StringVar(value="Floyd-Steinberg")
        self.algorithm_dropdown = tk.OptionMenu(self.frame_right, self.selected_algorithm, *self.algorithms.keys(), command=self.update_image)
        self.algorithm_dropdown.pack(pady=10, padx=10, fill=tk.X)

        # Dictionary to store sliders
        self.sliders = {}
        self.default_values = {
            "scale": 100, "contrast": 1.0, "midtones": 1.0, "highlights": 1.0,
            "blur": 0, "pixelation": 1, "noise": 0
        }

        # Greyscale Checkbox
        self.is_greyscale = tk.BooleanVar(value=True)  # Default is checked (True)
        self.greyscale_checkbox = tk.Checkbutton(self.frame_right, text="Greyscale", variable=self.is_greyscale, bg="#2A2B35", fg="white", selectcolor="#2A2B35", command=self.update_image)
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
        self.image_container = tk.Frame(self.frame_left, bg="#2A2B35", relief=tk.RIDGE)
        self.image_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Canvas for main image
        self.canvas_image = tk.Canvas(self.image_container, bg="black", highlightthickness=0)
        self.canvas_image.pack(expand=True)

        # Play/Stop Buttons
        self.frame_bottom = tk.Frame(self.frame_left, bg="#1A1A23")
        self.frame_bottom.pack(pady=10)

        self.play_btn = Button(self.frame_bottom, "Play GIF", command=self.play_gif)
        self.play_btn.pack(side=tk.LEFT, padx=5)

        self.stop_btn = Button(self.frame_bottom, "Stop GIF", command=self.stop_gif)
        self.stop_btn.pack(side=tk.LEFT, padx=5)

        # Export Button
        self.export_btn = Button(self.frame_right, "Export Image", command=self.export_image)
        self.export_btn.pack(pady=10, padx=10)

        # Progress Bar
        self.progress_bar = ProgressBar(self.frame_right, height=20, bg_color="#1A1A23", fg_color="#006CE8", border_color="#1A1A23")

        # Image attributes
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
            file_path = filedialog.askopenfilename()

        if file_path and os.path.exists(file_path):
            mime_type, _ = mimetypes.guess_type(file_path)

            if not mime_type.startswith("image/"):
                tk.messagebox.showerror("Invalid File", "Please select a valid image file (PNG, JPG, GIF, WEBP, BMP, TIFF).")
                return

            self.is_gif = mime_type == "image/gif"
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
            self.update_canvas_size()
            self.update_image()


    def update_canvas_size(self):
        """ Update the canvas size based on the image dimensions. """

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

        # Generate checkerboard background
        self.checkerboard_bg = self.create_checkerboard(self.current_width, self.current_height)
        self.checkerboard_bg_tk = ImageTk.PhotoImage(self.checkerboard_bg)

        # Resize canvas to fit image
        self.canvas_image.config(width=self.current_width, height=self.current_height)
        self.canvas_image.pack()

        # Display checkerboard as background
        self.canvas_image.create_image(0, 0, anchor=tk.NW, image=self.checkerboard_bg_tk)


    def update_image(self, algorithm=None):
        """ Update the displayed image based on the current settings. """

        if self.is_gif:
            self.processed_gif_frames = [self.process_frame(frame) for frame in self.gif_frames]

            # Reset to first frame
            self.current_frame_index = 0
            self.display_image(self.processed_gif_frames[0])
        elif self.image:
            self.processed_image = self.process_frame(self.image)
            self.display_image(self.processed_image)


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

        img = img.resize((self.current_width, self.current_height), Image.LANCZOS)

        # Composite over checkerboard
        composite = Image.alpha_composite(self.checkerboard_bg.convert("RGBA"), img.convert("RGBA"))

        # Convert to Tkinter format and display
        img_tk = ImageTk.PhotoImage(composite)
        self.canvas_image.create_image(self.current_width // 2, self.current_height // 2, image=img_tk)
        self.canvas_image.image = img_tk


    def create_checkerboard(self, width, height, box_size=10):
        """ Create a checkerboard pattern as a background. """

        pattern = Image.new("RGB", (width, height), "#BFBFBF")  # Light gray base

        draw = ImageDraw.Draw(pattern)
        for y in range(0, height, box_size * 2):
            for x in range(0, width, box_size * 2):
                draw.rectangle([x, y, x + box_size, y + box_size], fill="#E0E0E0")  # Lighter box
                draw.rectangle([x + box_size, y + box_size, x + box_size * 2, y + box_size * 2], fill="#E0E0E0")

        return pattern


    def play_gif(self):
        """ Play the GIF animation """

        self.playing = True
        self.animate()


    def stop_gif(self):
        """ Stop the GIF animation """

        self.playing = False


    def animate(self):
        """ Animate the GIF frames """

        if self.playing and self.is_gif:
            if self.current_frame_index >= len(self.gif_frames):
                self.current_frame_index = 0

            # Process the frame lazily if it hasn't been processed yet
            if self.processed_gif_frames[self.current_frame_index] is None:
                self.processed_gif_frames[self.current_frame_index] = self.process_frame(self.gif_frames[self.current_frame_index])

            self.display_image(self.processed_gif_frames[self.current_frame_index])
            self.current_frame_index = (self.current_frame_index + 1) % len(self.gif_frames)

            frame_duration = self.gif_durations[self.current_frame_index]
            self.root.after(frame_duration, self.animate)


    def export_image(self):
        """ Export the image to a file. """

        if not self.processed_image and not self.processed_gif_frames:
            return  # No image to save

        filetypes = [("PNG files", "*.png"), ("JPEG files", "*.jpg")] if not self.is_gif else [("GIF files", "*.gif"), ("PNG files", "*.png")]
        file_path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=filetypes)

        if file_path:
            if self.is_gif:
                # Process remaining frames before exporting
                total_frames = len(self.gif_frames)
                self.progress_bar.set_progress(0)

                for i in range(total_frames):
                    if self.processed_gif_frames[i] is None:
                        self.processed_gif_frames[i] = self.process_frame(self.gif_frames[i])

                    # Update progress bar
                    self.progress_bar.set_progress((i + 1) / total_frames)
                    self.root.update()

                processed_frames = [frame.convert("RGBA") for frame in self.processed_gif_frames if frame is not None]

                if processed_frames:  # Check if we have any frames to save
                    processed_frames[0].save(
                        file_path,
                        save_all=True,
                        append_images=processed_frames[1:],
                        loop=0,
                        duration=self.gif_durations[:len(processed_frames)],  # Match durations to frames
                        transparency=255,
                        disposal=2
                    )

                    # Reset progress bar after export
                    self.progress_bar.set_progress(0)
                    tk.messagebox.showinfo("Export Successful", "The GIF has been successfully exported.")
                else:
                    tk.messagebox.showerror("Export Error", "No frames available to export.")
            else:
                self.progress_bar.set_progress(1)
                self.root.update()
                self.processed_image.save(file_path, format="PNG")
                self.progress_bar.set_progress(0)
                tk.messagebox.showinfo("Export Successful", "The image has been successfully exported.")


if __name__ == "__main__":
    ARGV_FILE = None

    if len(sys.argv) > 1:
        ARGV_FILE = sys.argv[1]

    root = tk.Tk()
    app = DitherMe(root, ARGV_FILE)
    root.mainloop()
