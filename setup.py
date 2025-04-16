""" Setup script for the algorithms. """

import os
import sys
from setuptools import setup, Extension, find_packages

# Define project directory
PROJECT_DIR = os.path.abspath(os.path.dirname(__file__))
PNG_LIB_PATH = os.path.join(PROJECT_DIR, "png_lib")

# Determine include and library directories
libraries = []
vcpkg_root = os.environ.get("VCPKG_ROOT")
if vcpkg_root and sys.platform == "win32":
    # Windows with vcpkg
    include_dirs = [os.path.join(vcpkg_root, "installed", "x64-windows", "include")]
    library_dirs = [os.path.join(vcpkg_root, "installed", "x64-windows", "lib")]
    libraries = ["libpng16"]
else:
    # macOS/Ubuntu with local png_lib or system libpng
    include_dirs = [os.path.join(PNG_LIB_PATH, "include")]
    library_dirs = [os.path.join(PNG_LIB_PATH, "lib")]
    libraries = ["png"]

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

# Check if libpng is likely available
libpng_found = False
for lib_dir in library_dirs:
    if sys.platform == "win32":
        if os.path.exists(os.path.join(lib_dir, "libpng16.lib")):
            libpng_found = True
            break
    else:
        if os.path.exists(os.path.join(lib_dir, "libpng.a")) or os.path.exists(os.path.join(lib_dir, "libpng.so")):
            libpng_found = True
            break

if not libpng_found:
    print(f"Warning: libpng not found in {library_dirs}. Make sure libpng is installed.")
    exit(1)

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
