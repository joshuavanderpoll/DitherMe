import os
import sys
import tkinter as tk
from tkinter import filedialog, colorchooser
from PIL import Image, ImageTk, ImageEnhance, ImageFilter, ImageSequence
import numpy as np

class DitherMe:
    def __init__(self, root, startup_file=None):
        self.root = root
        self.root.title("DitherMe")
        self.root.geometry("700x700")
        self.root.resizable(False, False)

        # Main Layout: Image Left, Sliders Right
        self.frame_left = tk.Frame(root)
        self.frame_left.pack(side=tk.LEFT, padx=10, pady=10)

        self.frame_right = tk.Frame(root)
        self.frame_right.pack(side=tk.RIGHT, padx=10, pady=10)

        # Upload Button
        self.upload_btn = tk.Button(self.frame_right, text="Upload Image/GIF", command=self.upload_image)
        self.upload_btn.pack(pady=10)

        # Dictionary to store sliders
        self.sliders = {}
        self.default_values = {
            "scale": 100, "contrast": 1.0, "midtones": 1.0, "highlights": 1.0,
            "blur": 0, "pixelation": 1, "noise": 0
        }

        # Sliders
        self.add_slider("Scale (%)", "scale", 1, 100, 100, self.update_image)
        self.add_slider("Contrast", "contrast", 0.5, 3.0, 1.0, self.update_image, 0.1)
        self.add_slider("Midtones", "midtones", 0.5, 3.0, 1.0, self.update_image, 0.1)
        self.add_slider("Highlights", "highlights", 0.5, 3.0, 1.0, self.update_image, 0.1)
        self.add_slider("Blur", "blur", 0, 10, 0, self.update_image, 0.1)
        self.add_slider("Pixelation", "pixelation", 1, 20, 1, self.update_image)
        self.add_slider("Noise", "noise", 0, 100, 0, self.update_image)

        # Color Picker Buttons
        self.selected_foreground = (255, 255, 255)  # Default white for bright pixels
        self.selected_background = (0, 0, 0)  # Default black for dark pixels

        self.foreground_btn = tk.Button(self.frame_right, text="Select Foreground Color", command=self.pick_foreground)
        self.foreground_btn.pack(pady=5)

        self.background_btn = tk.Button(self.frame_right, text="Select Background Color", command=self.pick_background)
        self.background_btn.pack(pady=5)

        # Reset Options Button
        self.reset_btn = tk.Button(self.frame_right, text="Reset Options", command=self.reset_options)
        self.reset_btn.pack(pady=10)

        # Canvas for the main image
        self.canvas_image = tk.Canvas(self.frame_left, width=300, height=300, bg="black")
        self.canvas_image.pack()

        # Play/Stop Buttons Below Image
        self.frame_bottom = tk.Frame(self.frame_left)
        self.frame_bottom.pack(pady=10)

        self.play_btn = tk.Button(self.frame_bottom, text="Play GIF", command=self.play_gif, state=tk.DISABLED)
        self.play_btn.pack(side=tk.LEFT, padx=5)
        self.stop_btn = tk.Button(self.frame_bottom, text="Stop GIF", command=self.stop_gif, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=5)

        # Export Button
        self.export_btn = tk.Button(self.frame_right, text="Export Image", command=self.export_image)
        self.export_btn.pack(pady=10)

        # Image attributes
        self.image = None
        self.processed_image = None
        self.is_gif = False
        self.gif_frames = []
        self.processed_gif_frames = []
        self.current_frame_index = 0
        self.playing = False

        self.original_width = 200
        self.original_height = 200
        self.current_width = 200 
        self.current_height = 200

        if startup_file:
            self.open_image(startup_file)


    def add_slider(self, label, key, from_, to, default, command, resolution=1):
        """ Helper function to add sliders dynamically """
        lbl = tk.Label(self.frame_right, text=label)
        lbl.pack()
        slider = tk.Scale(self.frame_right, from_=from_, to=to, resolution=resolution, orient=tk.HORIZONTAL, command=command)
        slider.set(default)
        slider.pack()
        self.sliders[key] = slider  # Store slider in dictionary

    def pick_foreground(self):
        """ Open color picker for bright (white) pixels """
        color_code = colorchooser.askcolor(title="Choose Foreground Color")[0]
        if color_code:
            self.selected_foreground = tuple(int(c) for c in color_code)  # Store as RGB tuple
            self.update_image()

    def pick_background(self):
        """ Open color picker for dark (black) pixels """
        color_code = colorchooser.askcolor(title="Choose Background Color")[0]
        if color_code:
            self.selected_background = tuple(int(c) for c in color_code)  # Store as RGB tuple
            self.update_image()

    def reset_options(self):
        """ Reset all sliders and colors to their default values """
        for key, value in self.default_values.items():
            self.sliders[key].set(value)

        self.selected_foreground = (255, 255, 255)  # Reset to white
        self.selected_background = (0, 0, 0)  # Reset to black

        self.update_image()

    def open_image(self, file_path: str):
        """ Load and process the image """
        if os.path.exists(file_path):
            self.image = Image.open(file_path)
            self.is_gif = file_path.lower().endswith(".gif")

            if self.is_gif:
                self.gif_durations = [frame.info.get("duration", 100) for frame in ImageSequence.Iterator(self.image)]
                self.gif_frames = [frame.convert("RGB") for frame in ImageSequence.Iterator(self.image)]
                self.processed_gif_frames = self.gif_frames.copy()
                self.play_btn.config(state=tk.NORMAL)
                self.stop_btn.config(state=tk.NORMAL)
            else:
                self.image = self.image.convert("RGB")
                self.processed_image = self.image.copy()
                self.play_btn.config(state=tk.DISABLED)
                self.stop_btn.config(state=tk.DISABLED)

            # Store original image size
            self.original_width, self.original_height = self.image.size
            self.current_width, self.current_height = self.original_width, self.original_height

            # Update canvas to match the image aspect ratio
            self.update_canvas_size()
            self.update_image()

    def upload_image(self):
        file_path = filedialog.askopenfilename()

        if file_path:
            self.image = Image.open(file_path)
            self.is_gif = file_path.lower().endswith(".gif")

            if self.is_gif:
                self.gif_durations = [frame.info.get("duration", 100) for frame in ImageSequence.Iterator(self.image)]
                self.gif_frames = [frame.convert("RGB") for frame in ImageSequence.Iterator(self.image)]
                self.processed_gif_frames = self.gif_frames.copy()
                self.play_btn.config(state=tk.NORMAL)
                self.stop_btn.config(state=tk.NORMAL)
            else:
                self.image = self.image.convert("RGB")
                self.processed_image = self.image.copy()
                self.play_btn.config(state=tk.DISABLED)
                self.stop_btn.config(state=tk.DISABLED)

            # Store original image size
            self.original_width, self.original_height = self.image.size
            self.current_width, self.current_height = self.original_width, self.original_height

            # Update canvas to match the image aspect ratio
            self.update_canvas_size()
            self.update_image()
            
    def update_canvas_size(self):
        """ Resize the canvas to match the image's aspect ratio within a max size. """
        max_width, max_height = 500, 500  # Maximum size for preview window
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

        # Resize the canvas to fit the new dimensions
        self.canvas_image.config(width=self.current_width, height=self.current_height)
        self.canvas_image.pack()

    def update_image(self, _=None):
        """ Update and apply effects to the image or GIF frames """
        if self.is_gif:
            self.processed_gif_frames = [self.process_frame(frame) for frame in self.gif_frames]
            self.display_image(self.processed_gif_frames[0])
        elif self.image:
            self.processed_image = self.process_frame(self.image)

            self.update_canvas_size()
            self.display_image(self.processed_image)

    def process_frame(self, img):
        """ Process a single frame or static image """
        scale_factor = self.sliders["scale"].get() / 100
        new_size = (int(img.width * scale_factor), int(img.height * scale_factor))
        img = img.resize(new_size)

        contrast_factor = self.sliders["contrast"].get()
        img = ImageEnhance.Contrast(img).enhance(contrast_factor)

        midtones_factor = self.sliders["midtones"].get()
        img = img.point(lambda p: (p / 255) ** (1 / midtones_factor) * 255)

        highlights_factor = self.sliders["highlights"].get()
        img = img.point(lambda p: min(255, p * highlights_factor))

        blur_amount = self.sliders["blur"].get()
        if blur_amount > 0:
            img = img.filter(ImageFilter.GaussianBlur(blur_amount))

        pixel_size = self.sliders["pixelation"].get()
        if pixel_size > 1:
            img = img.resize((img.width // pixel_size, img.height // pixel_size), Image.NEAREST)
            img = img.resize((img.width * pixel_size, img.height * pixel_size), Image.NEAREST)

        img = self.apply_noise(img)
        return self.apply_dithering(img)

    def apply_noise(self, img):
        """ Apply noise to the image """
        noise_level = self.sliders["noise"].get()
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
        """ Display the image on the canvas """
        img = img.resize((self.current_width, self.current_height), Image.LANCZOS)
        img_tk = ImageTk.PhotoImage(img)
        self.canvas_image.create_image(self.current_width // 2, self.current_height // 2, image=img_tk)
        self.canvas_image.image = img_tk

    def play_gif(self):
        """ Play the GIF animation """
        self.playing = True
        self.animate()

    def stop_gif(self):
        """ Stop the GIF animation """
        self.playing = False

    def animate(self):
        """ Loop through frames """
        if self.playing and self.is_gif:
            self.current_frame_index = (self.current_frame_index + 1) % len(self.processed_gif_frames)
            self.display_image(self.processed_gif_frames[self.current_frame_index])
            self.root.after(100, self.animate)

    def export_image(self):
        """ Save the processed image or GIF """
        if not self.processed_image and not self.processed_gif_frames:
            return  # No image to save

        filetypes = [("GIF files", "*.gif"), ("PNG files", "*.png"), ("JPEG files", "*.jpg")] if self.is_gif else [("PNG files", "*.png"), ("JPEG files", "*.jpg")]
        file_path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=filetypes)

        if file_path:
            if self.is_gif:
                # Save as animated GIF
                self.processed_gif_frames[0].save(
                    file_path, save_all=True, append_images=self.processed_gif_frames[1:], loop=0, duration=self.gif_durations
                )
            else:
                # Save single processed image
                self.processed_image.save(file_path)

if __name__ == "__main__":
    startup_file = None

    if len(sys.argv) > 1:
        startup_file = sys.argv[1]

    root = tk.Tk()
    app = DitherMe(root, startup_file)
    root.mainloop()
