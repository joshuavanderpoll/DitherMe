import tkinter as tk
from tkinter import filedialog, colorchooser
from PIL import Image, ImageTk, ImageEnhance, ImageFilter


class DitherMe:
    def __init__(self, root):
        self.root = root
        self.root.title("DitherMe")

        # Main Layout: Image Left, Sliders Right
        self.frame_left = tk.Frame(root)
        self.frame_left.pack(side=tk.LEFT, padx=10, pady=10)

        self.frame_right = tk.Frame(root)
        self.frame_right.pack(side=tk.RIGHT, padx=10, pady=10)

        # Upload Button
        self.upload_btn = tk.Button(self.frame_right, text="Upload Image", command=self.upload_image)
        self.upload_btn.pack(pady=10)

        # Dictionary to store sliders
        self.sliders = {}

        # Sliders
        self.add_slider("Scale (%)", "scale", 10, 200, 100, self.update_image)
        self.add_slider("Contrast", "contrast", 0.5, 3.0, 1.0, self.update_image, 0.1)
        self.add_slider("Midtones", "midtones", 0.5, 3.0, 1.0, self.update_image, 0.1)
        self.add_slider("Highlights", "highlights", 0.5, 3.0, 1.0, self.update_image, 0.1)
        self.add_slider("Blur", "blur", 0, 10, 0, self.update_image, 0.1)
        self.add_slider("Pixelation", "pixelation", 1, 20, 1, self.update_image)

        # Color Picker Buttons
        self.selected_foreground = (255, 255, 255)  # Default white for bright pixels
        self.selected_background = (0, 0, 0)  # Default black for dark pixels

        self.foreground_btn = tk.Button(self.frame_right, text="Select Foreground Color", command=self.pick_foreground)
        self.foreground_btn.pack(pady=5)

        self.background_btn = tk.Button(self.frame_right, text="Select Background Color", command=self.pick_background)
        self.background_btn.pack(pady=5)

        # Canvas for the main image
        self.canvas_image = tk.Canvas(self.frame_left, width=300, height=300, bg="black")
        self.canvas_image.pack()

        self.image = None
        self.processed_image = None

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
            self.update_image()  # Update image after selection

    def pick_background(self):
        """ Open color picker for dark (black) pixels """
        color_code = colorchooser.askcolor(title="Choose Background Color")[0]
        if color_code:
            self.selected_background = tuple(int(c) for c in color_code)  # Store as RGB tuple
            self.update_image()  # Update image after selection

    def upload_image(self):
        file_path = filedialog.askopenfilename()

        if file_path:
            self.image = Image.open(file_path).convert("RGB")
            self.processed_image = self.image.copy()
            self.update_image()  # Apply settings immediately

    def update_image(self, _=None):
        if self.image:
            # Apply scale
            scale_factor = self.sliders["scale"].get() / 100
            new_size = (int(self.image.width * scale_factor), int(self.image.height * scale_factor))
            img = self.image.resize(new_size)

            # Apply contrast
            contrast_factor = self.sliders["contrast"].get()
            img = ImageEnhance.Contrast(img).enhance(contrast_factor)

            # Apply midtones (gamma correction)
            midtones_factor = self.sliders["midtones"].get()
            img = img.point(lambda p: (p / 255) ** (1 / midtones_factor) * 255)

            # Apply highlights adjustment
            highlights_factor = self.sliders["highlights"].get()
            img = img.point(lambda p: min(255, p * highlights_factor))

            # Apply blur
            blur_amount = self.sliders["blur"].get()
            if blur_amount > 0:
                img = img.filter(ImageFilter.GaussianBlur(blur_amount))

            # Apply pixelation effect
            pixel_size = self.sliders["pixelation"].get()
            if pixel_size > 1:
                img = img.resize((img.width // pixel_size, img.height // pixel_size), Image.NEAREST)
                img = img.resize((img.width * pixel_size, img.height * pixel_size), Image.NEAREST)

            # Apply dithering
            self.apply_dithering(img)

    def apply_dithering(self, img):
        """ Convert to grayscale, apply dithering, and replace white & black pixels """
        gray_image = img.convert("L")

        # Floyd-Steinberg dithering
        dithered_image = gray_image.convert("1", dither=Image.FLOYDSTEINBERG)

        # Convert back to RGB
        dithered_rgb = dithered_image.convert("RGB")

        # Replace white and black pixels with selected colors
        pixels = dithered_rgb.load()
        for y in range(dithered_rgb.height):
            for x in range(dithered_rgb.width):
                if pixels[x, y] == (255, 255, 255):  # White pixels
                    pixels[x, y] = self.selected_foreground  # Replace with chosen foreground color
                elif pixels[x, y] == (0, 0, 0):  # Black pixels
                    pixels[x, y] = self.selected_background  # Replace with chosen background color

        self.display_image(dithered_rgb)

    def display_image(self, img):
        """ Display the image on the canvas """
        img = img.resize((300, 300))  # Resize for display
        img_tk = ImageTk.PhotoImage(img)
        self.canvas_image.create_image(150, 150, image=img_tk)
        self.canvas_image.image = img_tk  # Keep reference


if __name__ == "__main__":
    root = tk.Tk()
    app = DitherMe(root)
    root.mainloop()
