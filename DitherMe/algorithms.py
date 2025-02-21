""" Dithering algorithms used by DitherMe. """
# pylint: disable=line-too-long, unused-variable, no-member

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
                        np_img[ny, nx] = np.clip(np_img[ny, nx], 0.0, 1.0)  # Fix overflow issue

        return Image.fromarray((np_img * 255).astype(np.uint8)).convert("1")


class CheckeredDither(DitherAlgorithm):
    """Base class for checkered dithers with different sizes."""
    def __init__(self, size):
        self.size = size

    def apply_dither(self, img):
        img = img.convert("L")
        np_img = np.array(img, dtype=np.float32) / 255.0
        height, width = np_img.shape
        for y in range(height):
            for x in range(width):
                if ((y // self.size) + (x // self.size)) % 2 == 0:
                    np_img[y, x] = 1 if np_img[y, x] > 0.5 else 0
                else:
                    np_img[y, x] = 0
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


class Bayer(DitherAlgorithm):
    """Implements Bayer-ordered dithering."""

    def apply_dither(self, img):
        img = img.convert("L")
        bayer_matrix = np.array([[0, 2], [3, 1]]) / 4.0
        np_img = np.array(img, dtype=np.float32) / 255.0
        height, width = np_img.shape
        for y in range(height):
            for x in range(width):
                threshold = bayer_matrix[y % 2, x % 2]
                np_img[y, x] = 1 if np_img[y, x] > threshold else 0
        return Image.fromarray((np_img * 255).astype(np.uint8)).convert("1")


class Bayer4x4(DitherAlgorithm):
    """Implements 4x4 Bayer ordered dithering."""

    def apply_dither(self, img):
        img = img.convert("L")
        bayer_matrix = np.array([
            [ 0,  8,  2, 10],
            [12,  4, 14,  6],
            [ 3, 11,  1,  9],
            [15,  7, 13,  5]
        ]) / 16.0

        np_img = np.array(img, dtype=np.float32) / 255.0
        height, width = np_img.shape

        for y in range(height):
            for x in range(width):
                threshold = bayer_matrix[y % 4, x % 4]
                np_img[y, x] = 1 if np_img[y, x] > threshold else 0

        return Image.fromarray((np_img * 255).astype(np.uint8)).convert("1")


class Bayer8x8(DitherAlgorithm):
    """Implements 8x8 Bayer ordered dithering."""

    def apply_dither(self, img):
        img = img.convert("L")
        bayer_matrix = np.array([
            [ 0, 32,  8, 40,  2, 34, 10, 42],
            [48, 16, 56, 24, 50, 18, 58, 26],
            [12, 44,  4, 36, 14, 46,  6, 38],
            [60, 28, 52, 20, 62, 30, 54, 22],
            [ 3, 35, 11, 43,  1, 33,  9, 41],
            [51, 19, 59, 27, 49, 17, 57, 25],
            [15, 47,  7, 39, 13, 45,  5, 37],
            [63, 31, 55, 23, 61, 29, 53, 21]
        ]) / 64.0

        np_img = np.array(img, dtype=np.float32) / 255.0
        height, width = np_img.shape

        for y in range(height):
            for x in range(width):
                threshold = bayer_matrix[y % 8, x % 8]
                np_img[y, x] = 1 if np_img[y, x] > threshold else 0

        return Image.fromarray((np_img * 255).astype(np.uint8)).convert("1")


class ClusteredDot4x4(DitherAlgorithm):
    """Implements 4x4 clustered dot dithering."""

    def apply_dither(self, img):
        img = img.convert("L")
        cluster_matrix = np.array([
            [ 7, 13, 11,  4],
            [12, 16, 14,  8],
            [10, 15,  9,  2],
            [ 5,  3,  6,  1]
        ]) / 16.0

        np_img = np.array(img, dtype=np.float32) / 255.0
        height, width = np_img.shape

        for y in range(height):
            for x in range(width):
                threshold = cluster_matrix[y % 4, x % 4]
                np_img[y, x] = 1 if np_img[y, x] > threshold else 0

        return Image.fromarray((np_img * 255).astype(np.uint8)).convert("1")


class Random(DitherAlgorithm):
    """Implements random-ordered dithering."""

    def apply_dither(self, img):
        img = img.convert("L")
        np_img = np.array(img, dtype=np.float32) / 255.0
        noise = np.random.rand(*np_img.shape)
        dithered = np_img > noise
        return Image.fromarray((dithered * 255).astype(np.uint8)).convert("1")


class CheckersSmall(CheckeredDither):
    """Small checkered dithering."""

    def __init__(self):
        super().__init__(size=2)


class CheckersMedium(CheckeredDither):
    """Medium checkered dithering."""

    def __init__(self):
        super().__init__(size=4)


class CheckersLarge(CheckeredDither):
    """Large checkered dithering."""

    def __init__(self):
        super().__init__(size=8)


class RadialBurst(DitherAlgorithm):
    """Implements radial burst dithering."""

    def apply_dither(self, img):
        img = img.convert("L")
        np_img = np.array(img, dtype=np.float32) / 255.0
        height, width = np_img.shape
        cy, cx = height // 2, width // 2
        for y in range(height):
            for x in range(width):
                r = np.sqrt((x - cx) ** 2 + (y - cy) ** 2)
                np_img[y, x] = 1 if np_img[y, x] > (r % 20) / 20 else 0
        return Image.fromarray((np_img * 255).astype(np.uint8)).convert("1")


class Spiral(DitherAlgorithm):
    """Implements spiral dithering."""

    def apply_dither(self, img):
        img = img.convert("L")
        np_img = np.array(img, dtype=np.float32) / 255.0
        height, width = np_img.shape
        cy, cx = height // 2, width // 2
        spiral_density = 25

        for y in range(height):
            for x in range(width):
                dx = x - cx
                dy = y - cy
                distance = np.sqrt(dx**2 + dy**2)  # Radial distance
                angle = np.arctan2(dy, dx) + (distance / spiral_density) * np.pi * 2  # More spirals

                threshold = (angle % (2 * np.pi)) / (2 * np.pi)  # Normalize to [0, 1]
                np_img[y, x] = 1 if np_img[y, x] > threshold else 0

        return Image.fromarray((np_img * 255).astype(np.uint8)).convert("1")


class Vortex(DitherAlgorithm):
    """Implements vortex dithering."""

    def apply_dither(self, img):
        img = img.convert("L")
        np_img = np.array(img, dtype=np.float32) / 255.0
        height, width = np_img.shape
        for y in range(height):
            for x in range(width):
                angle = np.arctan2(y - height // 2, x - width // 2)
                np_img[y, x] = 1 if np_img[y, x] > (angle % np.pi) / np.pi else 0
        return Image.fromarray((np_img * 255).astype(np.uint8)).convert("1")


class Diamond(DitherAlgorithm):
    """Implements diamond dithering."""

    def apply_dither(self, img):
        img = img.convert("L")
        np_img = np.array(img, dtype=np.float32) / 255.0
        height, width = np_img.shape
        for y in range(height):
            for x in range(width):
                d = abs(y - height // 2) + abs(x - width // 2)
                np_img[y, x] = 1 if np_img[y, x] > (d % 20) / 20 else 0
        return Image.fromarray((np_img * 255).astype(np.uint8)).convert("1")


class FalseFloydSteinberg(ErrorDiffusionDither):
    """Implements False Floyd-Steinberg dithering."""

    def apply_dither(self, img):
        matrix = [(0, 1, 3), (1, -1, 1), (1, 0, 1)]
        return self.distribute_error(img, matrix, 4)


class StevensonArce(ErrorDiffusionDither):
    """Implements Stevenson-Arce dithering."""

    def apply_dither(self, img):
        matrix = [(0, 2, 32),
                  (1, -3, 12), (1, -1, 26), (1, 1, 30), (1, 3, 16),
                  (2, -2, 12), (2, 0, 26), (2, 2, 12),
                  (3, -3, 5), (3, -1, 12), (3, 1, 12), (3, 3, 5)]
        return self.distribute_error(img, matrix, 200)


class Knoll(ErrorDiffusionDither):
    """Implements Knoll dithering."""

    def apply_dither(self, img):
        matrix = [(0, 1, 5), (0, 2, 3),
                  (1, -2, 2), (1, -1, 4), (1, 0, 5), (1, 1, 4), (1, 2, 2),
                  (2, -1, 3), (2, 0, 5), (2, 1, 3)]
        return self.distribute_error(img, matrix, 32)


class BlueNoise(DitherAlgorithm):
    """Implements Blue Noise dithering."""

    def apply_dither(self, img):
        img = img.convert("L")
        np_img = np.array(img, dtype=np.float32) / 255.0
        blue_noise = np.random.normal(0.5, 0.15, np_img.shape)  # Simulated blue noise
        np_img = np_img > blue_noise
        return Image.fromarray((np_img * 255).astype(np.uint8)).convert("1")


class VoidAndCluster(DitherAlgorithm):
    """Implements Void-and-Cluster dithering."""

    def apply_dither(self, img):
        img = img.convert("L")
        np_img = np.array(img, dtype=np.float32) / 255.0
        noise = np.random.rand(*np_img.shape) * 0.1
        clustered = (np_img + noise) > 0.5
        return Image.fromarray((clustered * 255).astype(np.uint8)).convert("1")
