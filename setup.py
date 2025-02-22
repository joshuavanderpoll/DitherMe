""" Setup script for the algorithms. """

import os
from setuptools import setup, Extension, find_packages

# Define project directory
PROJECT_DIR = os.path.abspath(os.path.dirname(__file__))
PNG_LIB_PATH = os.path.join(PROJECT_DIR, "png_lib")

# Include and library directories
include_dirs = [os.path.join(PNG_LIB_PATH, "include")]
library_dirs = [os.path.join(PNG_LIB_PATH, "lib")]

# Shared source files
shared_sources = ["DitherMe/algorithms/image_utils.c"]

# List of dithering algorithms
dither_algorithms = [
    # Error diffusion dithering
    "floydsteinberg",
    "false_floydsteinberg",
    "sierra",
    "sierra_lite",
    "sierra_two_row",
    "atkinson",
    "burkes",
    "stucki",
    "jarvis_judice_ninke",

    # Ordered dithering
    "bayer_2x2", 
    "bayer_4x4", 
    "bayer_8x8", 
    "clustered_dot_4x4",

    # Checkered dithering
    "checkered_small",
    "checkered_medium",
    "checkered_large",
]

# Function to create extension modules
def make_extension(name):
    """ Create an extension module for the given algorithm. """

    return Extension(
        f"DitherMe.algorithms.{name}",
        sources=[f"DitherMe/algorithms/{name}.c"] + shared_sources,
        libraries=["png"],
        include_dirs=include_dirs,
        library_dirs=library_dirs,
        extra_compile_args=["-O2"],  # Optimize for performance
    )

# Create all extensions dynamically
extensions = [make_extension(name) for name in dither_algorithms]

# Check if libpng is available
if not os.path.exists(os.path.join(PNG_LIB_PATH, "lib", "libpng.a")):
    print("Warning: libpng not found. Make sure libpng is installed in 'png_lib'.")

# Setup configuration
setup(
    name="algorithms",
    version="1.0.0",
    description="The package providing C-coded dithering algorithms for DitherMe.",
    ext_modules=extensions,
    packages=find_packages(),  # Automatically find all packages
    classifiers=[
        "Programming Language :: Python",
        "Programming Language :: C",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
