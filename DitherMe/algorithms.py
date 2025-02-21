""" Dithering algorithms used by DitherMe. """

import numpy as np
from PIL import Image

class DitherAlgorithm:
    """Base class for dithering modes."""

    def apply_dither(self, img):
        """Applies dithering to the input image."""

        raise NotImplementedError("Dithering mode must implement apply_dither method")

class ErrorDiffusionDither(DitherAlgorithm):
    """Base class for all error diffusion dithering algorithms."""

    def apply_dither(self, img):
        """Placeholder method to satisfy the abstract method requirement."""

        raise NotImplementedError("Subclasses should implement this method")

    def distribute_error(self, img, matrix, divisor):
        """Applies error diffusion based on the given diffusion matrix."""

        img = img.convert("L")  # Ensure grayscale
        np_img = np.array(img, dtype=np.float32) / 255.0
        height, width = np_img.shape

        for y in range(height):
            for x in range(width):
                old_pixel = np_img[y, x]
                new_pixel = 1.0 if old_pixel >= 0.5 else 0.0
                np_img[y, x] = new_pixel
                quant_error = old_pixel - new_pixel

                for dy, dx, weight in matrix:
                    ny, nx = y + dy, x + dx
                    if 0 <= ny < height and 0 <= nx < width:
                        np_img[ny, nx] += quant_error * (weight / divisor)

        return Image.fromarray((np_img * 255).astype(np.uint8)).convert("1")

class FloydSteinberg(ErrorDiffusionDither):
    """Implements Floyd-Steinberg dithering."""

    def apply_dither(self, img):
        matrix = [(0, 1, 7), (1, -1, 3), (1, 0, 5), (1, 1, 1)]
        return self.distribute_error(img, matrix, 16)
    
class Sierra(ErrorDiffusionDither):
    """Implements full Sierra dithering."""

    def apply_dither(self, img):
        matrix = [(0, 1, 5), (0, 2, 3),
                  (1, -2, 2), (1, -1, 4), (1, 0, 5), (1, 1, 4), (1, 2, 2),
                  (2, -1, 2), (2, 0, 3), (2, 1, 2)]
        return self.distribute_error(img, matrix, 32)

class TwoRowSierra(ErrorDiffusionDither):
    """Implements Two-Row Sierra dithering."""

    def apply_dither(self, img):
        matrix = [(0, 1, 4), (0, 2, 3),
                  (1, -2, 1), (1, -1, 2), (1, 0, 3), (1, 1, 2), (1, 2, 1)]
        return self.distribute_error(img, matrix, 16)

class SierraLite(ErrorDiffusionDither):
    """Implements Sierra Lite dithering."""

    def apply_dither(self, img):
        matrix = [(0, 1, 2), (1, -1, 1), (1, 0, 1)]
        return self.distribute_error(img, matrix, 4)

class Atkinson(ErrorDiffusionDither):
    """Implements Atkinson dithering."""

    def apply_dither(self, img):
        matrix = [(0, 1, 1), (0, 2, 1),
                  (1, -1, 1), (1, 0, 1), (1, 1, 1),
                  (2, 0, 1)]
        return self.distribute_error(img, matrix, 8)

class JarvisJudiceNinke(ErrorDiffusionDither):
    """Implements Jarvis, Judice & Ninke dithering."""

    def apply_dither(self, img):
        matrix = [(0, 1, 7), (0, 2, 5),
                  (1, -2, 3), (1, -1, 5), (1, 0, 7), (1, 1, 5), (1, 2, 3),
                  (2, -2, 1), (2, -1, 3), (2, 0, 5), (2, 1, 3), (2, 2, 1)]
        return self.distribute_error(img, matrix, 48)

class Stucki(ErrorDiffusionDither):
    """Implements Stucki dithering."""

    def apply_dither(self, img):
        matrix = [(0, 1, 8), (0, 2, 4),
                  (1, -2, 2), (1, -1, 4), (1, 0, 8), (1, 1, 4), (1, 2, 2),
                  (2, -2, 1), (2, -1, 2), (2, 0, 4), (2, 1, 2), (2, 2, 1)]
        return self.distribute_error(img, matrix, 42)

class Burkes(ErrorDiffusionDither):
    """Implements Burkes dithering."""

    def apply_dither(self, img):
        matrix = [(0, 1, 8), (0, 2, 4),
                  (1, -2, 2), (1, -1, 4), (1, 0, 8), (1, 1, 4), (1, 2, 2)]
        return self.distribute_error(img, matrix, 32)

class LatticeBoltzmann(DitherAlgorithm):
    """Simulates fluid-like dithering using Lattice-Boltzmann principles."""

    def apply_dither(self, img):
        img = img.convert("L")
        np_img = np.array(img, dtype=np.float32) / 255.0
        noise = np.random.rand(*np_img.shape) * 0.1
        lbm = np_img + noise
        dithered = lbm >= 0.5
        return Image.fromarray(dithered.astype(np.uint8) * 255).convert("1")
