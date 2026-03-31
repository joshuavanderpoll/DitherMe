""" Setup script for the algorithms. """

import os
import sys
from setuptools import setup, Extension, find_packages

# Define project directory
PROJECT_DIR = os.path.abspath(os.path.dirname(__file__))

# Determine include and library directories
include_dirs = []
library_dirs = []
libraries = []

# Shared source files
shared_sources = []

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
    "knoll", 
    "stevenson_arce",

    # Ordered dithering
    "bayer_2x2", 
    "bayer_4x4", 
    "bayer_8x8", 
    "clustered_dot_4x4",
    "lattice_boltzmann",

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
        libraries=libraries,
        include_dirs=include_dirs,
        library_dirs=library_dirs,
        extra_compile_args=["-O2"],  # Optimize for performance
    )

# Create all extensions dynamically
extensions = [make_extension(name) for name in dither_algorithms]

# Setup configuration
setup(
    name="algorithms",
    version="1.0.0",
    description="The package providing C-coded dithering algorithms for DitherMe.",
    ext_modules=extensions,
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python",
        "Programming Language :: C",
        "Operating System :: OS Independent",
    ],
)
