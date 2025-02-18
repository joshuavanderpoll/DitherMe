import os
import sys
import tkinter as tk
from tkinter import filedialog, colorchooser
from PIL import Image, ImageTk, ImageColor, ImageEnhance, ImageFilter, ImageSequence, ImageDraw
import numpy as np
import mimetypes

from ui.slider import Slider
from ui.button import Button

class DitherMe:
    def __init__(self, root, startup_file=None):
        self.root = root
        self.root.title("DitherMe")
        self.root.geometry("1110x750")
        self.root.resizable(False, False)
        self.root.configure(bg="#1A1A23")

        # Sidebar
        self.frame_right = tk.Frame(root, width=300, bg="#2A2B35")
        self.frame_right.pack(side=tk.RIGHT, fill=tk.Y)
        self.frame_right.pack_propagate(False)

        # Main content
        self.frame_left = tk.Frame(root, bg="#1A1A23")
        self.frame_left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Upload Button
        self.upload_btn = Button(self.frame_right, "Upload Image/GIF", command=self.upload_image)
        self.upload_btn.pack(pady=10, padx=10)

        # Dictionary to store sliders
        self.sliders = {}
        self.default_values = {
            "scale": 100, "contrast": 1.0, "midtones": 1.0, "highlights": 1.0,
            "blur": 0, "pixelation": 1, "noise": 0
        }

        # Sliders
        self.add_slider("Scale", "scale", 1, 100, 100, self.update_image, True)
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

        # Image attributes
        self.image = None
        self.processed_image = None
        self.is_gif = False
        self.gif_frames = []
        self.processed_gif_frames = []
        self.current_frame_index = 0
        self.playing = False
        self.preprocessed_frames = 5

        self.original_width = 200
        self.original_height = 200
        self.current_width = 200
        self.current_height = 200

        self.update_canvas_size()

        if startup_file:
            self.open_image(startup_file)

    def add_slider(self, label, key, from_, to, default, command, resolution=1):
        slider = Slider(self.frame_right, label, min_val=from_, max_val=to, default_val=default, command=lambda v: command(), resolution=resolution)
        self.sliders[key] = slider

    def pick_foreground(self):
        color_code = colorchooser.askcolor(title="Choose Foreground Color")[1]
        if color_code:
            self.selected_foreground = color_code
            self.foreground_btn.update_preview_color(color_code)
            self.update_image()

    def pick_background(self):
        color_code = colorchooser.askcolor(title="Choose Background Color")[1]
        if color_code:
            self.selected_background = color_code
            self.background_btn.update_preview_color(color_code)
            self.update_image()

    def reset_options(self):
        for key, value in self.default_values.items():
            self.sliders[key].set_value(value)

        self.selected_foreground = "#FFFFFF"
        self.selected_background = "#000000"
        self.foreground_btn.update_preview_color(self.selected_foreground)
        self.background_btn.update_preview_color(self.selected_background)

        self.update_image()

    def open_image(self, file_path: str):
        if os.path.exists(file_path):
            self.upload_image(file_path)

    def upload_image(self, file_path=None):
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
                self.processed_gif_frames = []
                
                # Preprocess only the first few frames
                for i in range(min(self.preprocessed_frames, len(self.gif_frames))):
                    self.processed_gif_frames.append(self.process_frame(self.gif_frames[i]))
                
                # Rest of the frames are processed lazily
                self.processed_gif_frames.extend([None] * (len(self.gif_frames) - len(self.processed_gif_frames)))
            else:
                self.image = self.image.convert("RGBA")
                self.processed_image = self.image.copy()

            self.original_width, self.original_height = self.image.size
            self.update_canvas_size()
            self.update_image()
            
    def update_canvas_size(self):
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

    def update_image(self):
        if self.is_gif:
            # Reset all processed frames to force reprocessing with new settings
            self.processed_gif_frames = [None] * len(self.gif_frames)

            # Process the first few frames to show immediate change
            for i in range(min(self.preprocessed_frames, len(self.gif_frames))):
                self.processed_gif_frames[i] = self.process_frame(self.gif_frames[i])
            
            # If a GIF is playing, update the current frame
            if self.playing:
                self.current_frame_index = 0  # Reset to the first frame to see changes immediately
            self.display_image(self.processed_gif_frames[0])  # Display first frame with new settings
        elif self.image:
            self.processed_image = self.process_frame(self.image)
            self.display_image(self.processed_image)

    def process_frame(self, img):
        """ Process an image frame."""

        # Ensure image is in RGBA mode
        img_rgba = img.convert("RGBA")
        img_rgb, img_alpha = img_rgba.convert("RGB"), img_rgba.getchannel("A")

        # Get scale factor (percent-based)
        scale_factor = self.sliders["scale"].get_value() / 100.0

        # Resize RGB and Alpha channels separately
        new_size = (max(1, int(img.width * scale_factor)), max(1, int(img.height * scale_factor)))
        img_rgb = img_rgb.resize(new_size, Image.LANCZOS)
        img_alpha = img_alpha.resize(new_size, Image.LANCZOS)

        # Convert to grayscale for dithering
        img_gray = img_rgb.convert("L")

        # Apply contrast adjustment
        contrast_factor = self.sliders["contrast"].get_value()
        img_gray = ImageEnhance.Contrast(img_gray).enhance(contrast_factor)

        # Apply midtones and highlights correction
        midtone_factor = self.sliders["midtones"].get_value()
        highlight_factor = self.sliders["highlights"].get_value()

        np_img = np.array(img_gray, dtype=np.float32) / 255.0
        np_img = np_img ** (1 / midtone_factor)  # Adjust midtones
        np_img = np.clip(np_img * highlight_factor, 0, 1)  # Adjust highlights
        img_gray = Image.fromarray((np_img * 255).astype(np.uint8))

        # Apply blur
        blur_amount = self.sliders["blur"].get_value()
        if blur_amount > 0:
            img_gray = img_gray.filter(ImageFilter.GaussianBlur(blur_amount))

        # Apply pixelation
        pixelation_factor = self.sliders["pixelation"].get_value()
        if pixelation_factor > 1:
            img_gray = img_gray.resize((img_gray.width // pixelation_factor, img_gray.height // pixelation_factor), Image.NEAREST)
            img_gray = img_gray.resize((img_gray.width * pixelation_factor, img_gray.height * pixelation_factor), Image.NEAREST)

        # Apply noise
        img_gray = self.apply_noise(img_gray)

        # Apply dithering
        dithered_img = img_gray.convert("1", dither=Image.FLOYDSTEINBERG)
        dithered_img = dithered_img.convert("RGBA")

        # Get user-selected colors and opacity
        fg_color = np.array(ImageColor.getrgb(self.selected_foreground), dtype=np.uint8)
        bg_color = np.array(ImageColor.getrgb(self.selected_background), dtype=np.uint8)
        
        fg_opacity = self.sliders["foreground_opacity"].get_value() / 255.0  # Convert to range [0,1]
        bg_opacity = self.sliders["background_opacity"].get_value() / 255.0  # Convert to range [0,1]

        # Convert image to NumPy array
        dithered_pixels = np.array(dithered_img, dtype=np.uint8)
        alpha_pixels = np.array(img_alpha, dtype=np.uint8)

        # Create a mask for dithering (white -> foreground, black -> background)
        mask = (dithered_pixels[:, :, 0] > 128).astype(np.float32)  # White pixels (foreground)

        # Compute final blended color while preserving transparency
        blended_pixels = np.zeros_like(dithered_pixels, dtype=np.uint8)

        for i in range(3):  # Apply to R, G, B channels
            blended_pixels[:, :, i] = (
                mask * ((1 - fg_opacity) * dithered_pixels[:, :, i] + fg_opacity * fg_color[i]) +
                (1 - mask) * ((1 - bg_opacity) * dithered_pixels[:, :, i] + bg_opacity * bg_color[i])
            ).astype(np.uint8)

        # **Apply alpha blending to transparency**
        blended_pixels[:, :, 3] = (alpha_pixels * (
            mask * fg_opacity + (1 - mask) * bg_opacity
        )).astype(np.uint8)  # Preserve original transparency while respecting opacity

        # Convert back to Image
        final_image = Image.fromarray(blended_pixels, "RGBA")

        # Resize back to original size
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

    def apply_dithering(self, img):
        """ Apply dithering effect """
        gray_image = img.convert("L")
        dithered_image = gray_image.convert("1", dither=Image.FLOYDSTEINBERG)
        dithered_rgb = dithered_image.convert("RGB")

        pixels = dithered_rgb.load()
        for y in range(dithered_rgb.height):
            for x in range(dithered_rgb.width):
                if pixels[x, y] == (255, 255, 255):
                    pixels[x, y] = self.selected_foreground
                else:
                    pixels[x, y] = self.selected_background

        return dithered_rgb

    def display_image(self, img):
        img = img.resize((self.current_width, self.current_height), Image.LANCZOS)

        # Composite over checkerboard
        composite = Image.alpha_composite(self.checkerboard_bg.convert("RGBA"), img.convert("RGBA"))

        # Convert to Tkinter format and display
        img_tk = ImageTk.PhotoImage(composite)
        self.canvas_image.create_image(self.current_width // 2, self.current_height // 2, image=img_tk)
        self.canvas_image.image = img_tk

    def create_checkerboard(self, width, height, box_size=10):
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
        self.playing = False

    def animate(self):
        if self.playing and self.is_gif:
            if self.current_frame_index >= len(self.processed_gif_frames):
                self.current_frame_index = 0

            # Process frame if it hasn't been processed with the latest settings
            if self.processed_gif_frames[self.current_frame_index] is None:
                self.processed_gif_frames[self.current_frame_index] = self.process_frame(self.gif_frames[self.current_frame_index])

            self.display_image(self.processed_gif_frames[self.current_frame_index])
            self.current_frame_index = (self.current_frame_index + 1) % len(self.processed_gif_frames)
            self.root.after(100, self.animate)

    def export_image(self):
        if not self.processed_image and not self.processed_gif_frames:
            return  # No image to save

        filetypes = [("PNG files", "*.png"), ("JPEG files", "*.jpg")] if not self.is_gif else [("GIF files", "*.gif"), ("PNG files", "*.png")]
        file_path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=filetypes)

        if file_path:
            if self.is_gif:
                # Ensure all frames are processed before export
                processed_frames = []
                for frame in self.gif_frames:
                    if self.processed_gif_frames[self.gif_frames.index(frame)] is None:
                        processed_frame = self.process_frame(frame)
                        self.processed_gif_frames[self.gif_frames.index(frame)] = processed_frame
                    processed_frames.append(self.processed_gif_frames[self.gif_frames.index(frame)])

                # Convert processed GIF frames to mode 'P' (palette-based) to preserve transparency
                processed_frames = [frame.convert("RGBA") for frame in processed_frames if frame is not None]

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
                else:
                    tk.messagebox.showerror("Export Error", "No frames available to export.")
            else:
                # Save single processed image with transparency
                self.processed_image.save(file_path, format="PNG")

if __name__ == "__main__":
    startup_file = None

    if len(sys.argv) > 1:
        startup_file = sys.argv[1]

    root = tk.Tk()
    app = DitherMe(root, startup_file)
    root.mainloop()
