# Set local project directory
PROJECT_DIR := $(CURDIR)
BUILD_DIR := $(PROJECT_DIR)/build
INSTALL_DIR := $(PROJECT_DIR)/png_lib

# libpng version
LIBPNG_VERSION = 1.6.45
LIBPNG_TAR = libpng-$(LIBPNG_VERSION).tar.gz
LIBPNG_URL = https://download.sourceforge.net/libpng/$(LIBPNG_TAR)
SRC_DIR = $(BUILD_DIR)/libpng-$(LIBPNG_VERSION)

# Detect OS
UNAME_S := $(shell uname -s)

# Set platform-specific variables
ifeq ($(UNAME_S), Linux)
    NPROC := $(shell nproc)
    RM_CMD := rm -rf
    WGET_CMD := wget -c
endif

ifeq ($(UNAME_S), Darwin)  # macOS
    NPROC := $(shell sysctl -n hw.ncpu)
    RM_CMD := rm -rf
    WGET_CMD := $(shell command -v wget >/dev/null 2>&1 || brew install wget && echo wget -c)
endif

ifeq ($(OS), Windows_NT)  # Windows (MSYS2)
    NPROC := $(shell nproc)
    RM_CMD := rm -rf
    WGET_CMD := $(shell command -v wget >/dev/null 2>&1 || pacman -S --noconfirm wget && echo wget -c)
endif

all: download extract build install

download:
	@mkdir -p $(BUILD_DIR)
	@echo "Downloading libpng $(LIBPNG_VERSION)..."
	@$(WGET_CMD) $(LIBPNG_URL) -O $(BUILD_DIR)/$(LIBPNG_TAR)

extract:
	@echo "Extracting libpng..."
	@tar -xzf $(BUILD_DIR)/$(LIBPNG_TAR) -C $(BUILD_DIR)

build:
	@echo "Building libpng..."
	cd $(SRC_DIR) && ./configure --prefix=$(INSTALL_DIR) && make -j$(NPROC)

install:
	@echo "Installing libpng locally in $(INSTALL_DIR)..."
	cd $(SRC_DIR) && make install

clean:
	@echo "Cleaning up build files..."
	@$(RM_CMD) $(SRC_DIR)  # Remove extracted source folder
	@rm -f $(BUILD_DIR)/$(LIBPNG_TAR)  # Remove tarball
	@$(RM_CMD) $(INSTALL_DIR)  # Remove installation if required
	@echo "Cleanup complete."

uninstall:
	@echo "Removing local installation..."
	@$(RM_CMD) $(INSTALL_DIR)

.PHONY: all download extract build install clean uninstall
