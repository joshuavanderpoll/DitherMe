# pylint: disable=line-too-long, unused-argument, no-member, missing-module-docstring, missing-class-docstring, missing-function-docstring, broad-exception-caught
import os
import sys
import tkinter as tk
from tkinter import filedialog, colorchooser, messagebox
import mimetypes
from PIL import Image, ImageTk, ImageSequence, ImageDraw
from algorithms import (
    floydsteinberg, false_floydsteinberg, sierra, sierra_lite, sierra_two_row,
    atkinson, burkes, stucki, jarvis_judice_ninke, bayer_2x2, bayer_4x4,
    bayer_8x8, clustered_dot_4x4, checkered_small, checkered_medium,
    checkered_large, stevenson_arce, knoll, lattice_boltzmann,
)
from processor import process_frame
from ui.slider import Slider
from ui.button import Button
from ui.progress_bar import ProgressBar

APP_BG = "#0E0F10"
CONTAINER_BG = "#161719"


class DitherMe:
    def __init__(self, root, startup_file=None):
        self.root = root
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

        self.selected_foreground = "#FFFFFF"
        self.selected_background = "#000000"
        self.checkerboard_bg_tk = None

        self.algorithms = {
            "Floyd-Steinberg":      floydsteinberg,
            "False Floyd-Steinberg": false_floydsteinberg,
            "Sierra":               sierra,
            "Sierra Lite":          sierra_lite,
            "Sierra Two-Row":       sierra_two_row,
            "Atkinson":             atkinson,
            "Burkes":               burkes,
            "Stucki":               stucki,
            "Jarvis-Judice & Ninke": jarvis_judice_ninke,
            "Stevenson-Arce":       stevenson_arce,
            "Knoll":                knoll,
            "Bayer 2x2":            bayer_2x2,
            "Bayer 4x4":            bayer_4x4,
            "Bayer 8x8":            bayer_8x8,
            "Clustered Dot 4x4":    clustered_dot_4x4,
            "Lattice-Boltzmann":    lattice_boltzmann,
            "Checkered Small":      checkered_small,
            "Checkered Medium":     checkered_medium,
            "Checkered Large":      checkered_large,
        }

        self._build_layout()
        self._build_menubar()

        self.update_canvas_size()

        if startup_file and os.path.exists(startup_file):
            self.upload_image(startup_file)

    def _build_layout(self):
        self.frame_right = tk.Frame(self.root, width=300, bg=CONTAINER_BG)
        self.frame_right.pack(side=tk.RIGHT, fill=tk.Y)
        self.frame_right.pack_propagate(False)

        self.frame_left = tk.Frame(self.root, bg=CONTAINER_BG)
        self.frame_left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        Button(self.frame_right, "Upload Image/GIF", command=self.upload_image).pack(pady=10, padx=10)

        self.selected_algorithm = tk.StringVar(value="Floyd-Steinberg")
        self.algorithm_dropdown = tk.OptionMenu(
            self.frame_right, self.selected_algorithm, *self.algorithms.keys(),
            command=self.update_image,
        )
        self.algorithm_dropdown.config(
            bg=CONTAINER_BG, fg="white", activebackground="#22242A",
            activeforeground="white", highlightthickness=0, relief=tk.FLAT,
        )
        self.algorithm_dropdown["menu"].config(
            bg=CONTAINER_BG, fg="white", activebackground="#22242A", activeforeground="white",
        )
        self.algorithm_dropdown.pack(pady=10, padx=10, fill=tk.X)

        self.sliders = {}
        self.default_values = {
            "scale": 100, "contrast": 1.0, "midtones": 1.0, "highlights": 1.0,
            "blur": 0, "pixelation": 1, "noise": 0, "threshold": 128,
        }

        self.is_greyscale = tk.BooleanVar(value=True)
        tk.Checkbutton(
            self.frame_right, text="Greyscale", variable=self.is_greyscale,
            bg=CONTAINER_BG, fg="white", activebackground=CONTAINER_BG,
            activeforeground="white", selectcolor=CONTAINER_BG,
            command=self.update_image,
        ).pack(pady=5, padx=10, anchor="w")

        self._add_slider("Scale (%)",  "scale",      1,    100,  100,  True)
        self._add_slider("Contrast",   "contrast",   0.5,  3.0,  1.0,  0.1)
        self._add_slider("Midtones",   "midtones",   0.5,  3.0,  1.0,  0.1)
        self._add_slider("Highlights", "highlights", 0.5,  3.0,  1.0,  0.1)
        self._add_slider("Blur",       "blur",       0,    10,   0,    0.1)
        self._add_slider("Pixelation", "pixelation", 1,    20,   1)
        self._add_slider("Noise",      "noise",      0,    100,  0)
        self._add_slider("Threshold",  "threshold",  0,    255,  128)

        self.foreground_btn = Button(self.frame_right, "Select Foreground Color", command=self.pick_foreground, color_preview=True)
        self.foreground_btn.update_preview_color(self.selected_foreground)
        self.foreground_btn.pack(pady=5, padx=10)
        self._add_slider("Foreground Opacity", "foreground_opacity", 0, 255, 255)

        self.background_btn = Button(self.frame_right, "Select Background Color", command=self.pick_background, color_preview=True)
        self.background_btn.update_preview_color(self.selected_background)
        self.background_btn.pack(pady=5, padx=10)
        self._add_slider("Background Opacity", "background_opacity", 0, 255, 255)

        self.image_container = tk.Frame(self.frame_left, bg=CONTAINER_BG, relief=tk.RIDGE)
        self.image_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.canvas_image = tk.Canvas(self.image_container, bg="black", highlightthickness=0)
        self.canvas_image.pack(expand=True, fill=tk.BOTH)
        self.canvas_image.bind("<Configure>", self.on_canvas_resize)
        self.canvas_image.bind("<ButtonPress-1>", self.on_pan_start)
        self.canvas_image.bind("<B1-Motion>", self.on_pan_move)
        self.canvas_image.bind("<ButtonRelease-1>", self.on_pan_end)
        self.canvas_image.bind("<MouseWheel>", self.on_mouse_wheel)
        self.canvas_image.bind("<Button-4>", self.on_mouse_wheel_linux)
        self.canvas_image.bind("<Button-5>", self.on_mouse_wheel_linux)
        self.canvas_image.bind("<Double-Button-1>", self.reset_view)

        self.frame_bottom = tk.Frame(self.frame_left, bg=CONTAINER_BG)
        self.frame_bottom.pack(pady=10)

        view_menu = tk.OptionMenu(self.frame_bottom, self.view_mode, "After", "Split", command=self.on_view_mode_change)
        view_menu.config(
            bg=CONTAINER_BG, fg="white", activebackground="#22242A",
            activeforeground="white", highlightthickness=0, relief=tk.FLAT,
        )
        view_menu["menu"].config(bg=CONTAINER_BG, fg="white", activebackground="#22242A", activeforeground="white")
        view_menu.pack(side=tk.LEFT, padx=5)

        self.play_btn = Button(self.frame_bottom, "Play GIF", command=self.play_gif)
        self.play_btn.pack(side=tk.LEFT, padx=5)
        self.play_btn.pack_forget()

        self.stop_btn = Button(self.frame_bottom, "Stop GIF", command=self.stop_gif)
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        self.stop_btn.pack_forget()

        self.progress_bar = ProgressBar(self.frame_right, height=20, bg_color=CONTAINER_BG, fg_color="#2D8BFF", border_color=CONTAINER_BG)

    def _build_menubar(self):
        mod_label = "⌘" if sys.platform == "darwin" else "Ctrl"
        mod_event = "Command" if sys.platform == "darwin" else "Control"

        menubar = tk.Menu(self.root)
        file_menu = tk.Menu(menubar, tearoff=False)
        file_menu.add_command(label=f"Upload…\t{mod_label}+O", command=self.upload_image)
        file_menu.add_command(label=f"Export…\t{mod_label}+E", command=self.export_image)
        file_menu.add_separator()
        file_menu.add_command(label=f"Reset Options\t{mod_label}+R", command=self.reset_options)
        file_menu.add_separator()
        file_menu.add_command(label=f"Quit DitherMe\t{mod_label}+Q", command=self.root.quit)
        menubar.add_cascade(label="File", menu=file_menu)

        self.root.config(menu=menubar)
        self.root.bind_all(f"<{mod_event}-o>", lambda e: self.upload_image())
        self.root.bind_all(f"<{mod_event}-e>", lambda e: self.export_image())
        self.root.bind_all(f"<{mod_event}-r>", lambda e: self.reset_options())
        self.root.bind_all(f"<{mod_event}-q>", lambda e: self.root.quit())

    def _add_slider(self, label, key, from_, to, default, resolution=1):
        self.sliders[key] = Slider(
            self.frame_right, label,
            min_val=from_, max_val=to, default_val=default,
            command=lambda v: self.update_image(),
            resolution=resolution,
        )

    def _get_settings(self):
        return {
            "scale":              self.sliders["scale"].get_value(),
            "contrast":           self.sliders["contrast"].get_value(),
            "midtones":           self.sliders["midtones"].get_value(),
            "highlights":         self.sliders["highlights"].get_value(),
            "blur":               self.sliders["blur"].get_value(),
            "pixelation":         self.sliders["pixelation"].get_value(),
            "noise":              self.sliders["noise"].get_value(),
            "threshold":          self.sliders["threshold"].get_value(),
            "algorithm":          self.selected_algorithm.get(),
            "greyscale":          self.is_greyscale.get(),
            "foreground":         self.selected_foreground,
            "background":         self.selected_background,
            "foreground_opacity": self.sliders["foreground_opacity"].get_value(),
            "background_opacity": self.sliders["background_opacity"].get_value(),
        }

    def pick_foreground(self):
        color = colorchooser.askcolor(title="Choose Foreground Color")[1]
        if color:
            self.selected_foreground = color
            self.foreground_btn.update_preview_color(color)
            self.update_image()

    def pick_background(self):
        color = colorchooser.askcolor(title="Choose Background Color")[1]
        if color:
            self.selected_background = color
            self.background_btn.update_preview_color(color)
            self.update_image()

    def reset_options(self):
        for key, value in self.default_values.items():
            self.sliders[key].set_value(value)
        self.selected_foreground = "#FFFFFF"
        self.selected_background = "#000000"
        self.foreground_btn.update_preview_color(self.selected_foreground)
        self.background_btn.update_preview_color(self.selected_background)
        self.update_image()

    def upload_image(self, file_path=None):
        if not file_path:
            file_path = filedialog.askopenfilename(
                title="Select an image or GIF",
                filetypes=[
                    ("Image files", "*.png *.jpg *.jpeg *.gif *.webp *.bmp *.tiff"),
                    ("All files", "*.*"),
                ],
            )

        if not file_path or not os.path.exists(file_path):
            return

        mime_type, _ = mimetypes.guess_type(file_path)
        if not mime_type or not mime_type.startswith("image/"):
            messagebox.showerror("Invalid File", "Please select a valid image file (PNG, JPG, GIF, WEBP, BMP, TIFF).")
            return

        self.root.title(f"DitherMe - {os.path.basename(file_path)}")
        self.is_gif = mime_type == "image/gif"
        self._update_gif_controls()
        self.image = Image.open(file_path)

        if self.is_gif:
            self.gif_durations = [f.info.get("duration", 100) for f in ImageSequence.Iterator(self.image)]
            self.gif_frames = [f.convert("RGBA") for f in ImageSequence.Iterator(self.image)]
            self.processed_gif_frames = [None] * len(self.gif_frames)
            for i in range(min(self.preprocessed_frames, len(self.gif_frames))):
                self.processed_gif_frames[i] = process_frame(self.gif_frames[i], self.algorithms, self._get_settings())
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

    def update_image(self, _=None):
        if self.is_gif and self.gif_frames:
            self.processed_gif_frames = [None] * len(self.gif_frames)
            for i in range(min(self.preprocessed_frames, len(self.gif_frames))):
                self.processed_gif_frames[i] = process_frame(self.gif_frames[i], self.algorithms, self._get_settings())
            self.current_frame_index = 0
            self._redraw_current()
        elif self.image:
            self.processed_image = process_frame(self.image, self.algorithms, self._get_settings())
            self._redraw_current()

    def _update_gif_controls(self):
        if self.is_gif:
            if not self.play_btn.winfo_ismapped():
                self.play_btn.pack(side=tk.LEFT, padx=5)
                self.stop_btn.pack(side=tk.LEFT, padx=5)
        else:
            self.playing = False
            self.play_btn.pack_forget()
            self.stop_btn.pack_forget()

    def update_canvas_size(self):
        if not self.original_width or not self.original_height:
            return
        max_w, max_h = 500, 500
        ratio = self.original_width / self.original_height
        if self.original_width > max_w or self.original_height > max_h:
            if ratio > 1:
                self.current_width = max_w
                self.current_height = int(max_w / ratio)
            else:
                self.current_height = max_h
                self.current_width = int(max_h * ratio)
        else:
            self.current_width, self.current_height = self.original_width, self.original_height

    def on_canvas_resize(self, event):
        self.canvas_width = max(1, event.width)
        self.canvas_height = max(1, event.height)
        bg = self._make_checkerboard(self.canvas_width, self.canvas_height)
        self.checkerboard_bg_tk = ImageTk.PhotoImage(bg)
        if self._bg_item_id is None:
            self._bg_item_id = self.canvas_image.create_image(0, 0, anchor=tk.NW, image=self.checkerboard_bg_tk)
        else:
            self.canvas_image.itemconfig(self._bg_item_id, image=self.checkerboard_bg_tk)
            self.canvas_image.coords(self._bg_item_id, 0, 0)
        self._redraw_current()

    def on_view_mode_change(self, *_):
        self._redraw_current()

    def _make_checkerboard(self, width, height, box_size=10):
        img = Image.new("RGB", (width, height), "#BFBFBF")
        draw = ImageDraw.Draw(img)
        for y in range(0, height, box_size * 2):
            for x in range(0, width, box_size * 2):
                draw.rectangle([x, y, x + box_size, y + box_size], fill="#E0E0E0")
                draw.rectangle([x + box_size, y + box_size, x + box_size * 2, y + box_size * 2], fill="#E0E0E0")
        return img

    def _get_current_frames(self):
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
        self.display_image(self._build_view_image(orig, proc))

    def _build_view_image(self, orig, proc):
        if orig is None and proc is None:
            return None
        orig = (orig or proc).convert("RGBA")
        proc = (proc or orig).convert("RGBA")

        img_w, img_h = self.original_width, self.original_height
        orig = orig.resize((img_w, img_h), Image.LANCZOS)
        proc = proc.resize((img_w, img_h), Image.LANCZOS)

        if self.view_mode.get() != "Split":
            return proc

        self.split_ratio = max(0.05, min(0.95, self.split_ratio))
        sx = max(0, min(img_w, int(self.split_ratio * img_w)))

        result = Image.new("RGBA", (img_w, img_h))
        if sx > 0:
            result.paste(orig.crop((0, 0, sx, img_h)), (0, 0))
        if sx < img_w:
            result.paste(proc.crop((sx, 0, img_w, img_h)), (sx, 0))

        draw = ImageDraw.Draw(result)
        draw.line([(sx, 0), (sx, img_h)], fill=(255, 0, 0, 255), width=3)
        r = 6
        draw.ellipse((sx - r, 0, sx + r, 2 * r), fill=(255, 0, 0, 255))
        draw.ellipse((sx - r, img_h - 2 * r, sx + r, img_h), fill=(255, 0, 0, 255))
        return result

    def display_image(self, img):
        if img is None:
            return
        scale = max(self.min_zoom, min(self.max_zoom, self.zoom))
        disp_w = max(1, int(self.current_width * scale))
        disp_h = max(1, int(self.current_height * scale))
        img_tk = ImageTk.PhotoImage(img.resize((disp_w, disp_h), Image.LANCZOS).convert("RGBA"))

        canvas_w = self.canvas_image.winfo_width() or self.current_width
        canvas_h = self.canvas_image.winfo_height() or self.current_height
        cx = canvas_w // 2 + self.pan_x
        cy = canvas_h // 2 + self.pan_y

        self._display_w = disp_w
        self._display_h = disp_h
        self._display_cx = cx
        self._display_cy = cy

        if self._image_item_id is None:
            self._image_item_id = self.canvas_image.create_image(cx, cy, image=img_tk)
        else:
            self.canvas_image.itemconfig(self._image_item_id, image=img_tk)
            self.canvas_image.coords(self._image_item_id, cx, cy)

        # keep reference — Tkinter GC's PhotoImage if not stored on the widget
        self.canvas_image.image = img_tk

    def set_zoom(self, new_zoom):
        new_zoom = max(self.min_zoom, min(self.max_zoom, new_zoom))
        if abs(new_zoom - self.zoom) < 1e-3:
            return
        self.zoom = new_zoom
        self._redraw_current()

    def on_mouse_wheel(self, event):
        self.set_zoom(self.zoom * (1.1 if event.delta > 0 else 1 / 1.1))

    def on_mouse_wheel_linux(self, event):
        self.set_zoom(self.zoom * (1.1 if event.num == 4 else 1 / 1.1))

    def reset_view(self, event=None):
        self.zoom = 1.0
        self.pan_x = 0
        self.pan_y = 0
        self._redraw_current()

    def on_pan_start(self, event):
        self._drag_start = (event.x, event.y)
        self._dragging_divider = False
        if self.view_mode.get() == "Split" and self._display_w and self._display_cx is not None:
            divider_x = self._display_cx - self._display_w / 2 + self.split_ratio * self._display_w
            if abs(event.x - divider_x) <= 12:
                self._dragging_divider = True

    def on_pan_move(self, event):
        if self._image_item_id is None:
            return
        if self._dragging_divider and self.view_mode.get() == "Split" and self._display_w:
            left_edge = self._display_cx - self._display_w / 2
            self.split_ratio = max(0.05, min(0.95, (event.x - left_edge) / self._display_w))
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
        self._drag_start = None
        self._dragging_divider = False

    def play_gif(self):
        self.playing = True
        self.animate()

    def stop_gif(self):
        self.playing = False

    def animate(self):
        if not self.playing or not self.is_gif:
            return
        if self.current_frame_index >= len(self.gif_frames):
            self.current_frame_index = 0
        # lazy-process frame on first access during playback
        if self.processed_gif_frames[self.current_frame_index] is None:
            self.processed_gif_frames[self.current_frame_index] = process_frame(
                self.gif_frames[self.current_frame_index], self.algorithms, self._get_settings()
            )
        self._redraw_current()
        duration = self.gif_durations[self.current_frame_index]
        self.current_frame_index = (self.current_frame_index + 1) % len(self.gif_frames)
        self.root.after(duration, self.animate)

    def export_image(self):
        if not self.processed_image and not any(self.processed_gif_frames):
            return

        if self.is_gif:
            filetypes = [("GIF files", "*.gif"), ("PNG files", "*.png")]
        else:
            filetypes = [
                ("PNG files", "*.png"), ("JPEG files", "*.jpeg"),
                ("WebP files", "*.webp"), ("TIFF files", "*.tiff"),
                ("BMP files", "*.bmp"), ("ICO files", "*.ico"),
            ]

        file_path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=filetypes)
        if not file_path:
            return

        if self.is_gif:
            if not self.gif_frames:
                return
            self.progress_bar.set_progress(0)
            self._export_gif_step(file_path, 0, len(self.gif_frames))
        else:
            self._export_still(file_path)

    def _export_gif_step(self, file_path, frame_index, total_frames):
        if self.processed_gif_frames[frame_index] is None:
            self.processed_gif_frames[frame_index] = process_frame(
                self.gif_frames[frame_index], self.algorithms, self._get_settings()
            )
        self.progress_bar.set_progress((frame_index + 1) / total_frames)
        if frame_index + 1 < total_frames:
            self.root.after(1, self._export_gif_step, file_path, frame_index + 1, total_frames)
        else:
            self._finish_gif_export(file_path)

    def _finish_gif_export(self, file_path):
        frames = [f.convert("RGBA") for f in self.processed_gif_frames if f is not None]
        if not frames:
            self.progress_bar.set_progress(0)
            messagebox.showerror("Export Error", "No frames available to export.")
            return
        frames[0].save(
            file_path, save_all=True, append_images=frames[1:],
            loop=0, duration=self.gif_durations[:len(frames)],
            transparency=255, disposal=2,
        )
        self.progress_bar.set_progress(0)
        messagebox.showinfo("Export Successful", "GIF exported successfully.")

    def _export_still(self, file_path):
        img = self.processed_image or self.image
        if img is None:
            return

        fmt_map = {
            ".png": "PNG", ".jpg": "JPEG", ".jpeg": "JPEG",
            ".webp": "WEBP", ".tif": "TIFF", ".tiff": "TIFF",
            ".bmp": "BMP", ".ico": "ICO",
        }
        fmt = fmt_map.get(os.path.splitext(file_path)[1].lower(), "PNG")

        self.progress_bar.set_progress(1)
        self.root.update()
        try:
            if fmt == "ICO":
                # ICO must be ≤ 256×256
                ico = img.convert("RGBA")
                if ico.width > 256 or ico.height > 256:
                    ico.thumbnail((256, 256), Image.LANCZOS)
                ico.save(file_path, format="ICO")
            else:
                img.save(file_path, format=fmt)
            messagebox.showinfo("Export Successful", f"Image exported as {fmt}.")
        except Exception as exc:
            messagebox.showerror("Export Error", f"Failed to export image:\n{exc}")
        finally:
            self.progress_bar.set_progress(0)
