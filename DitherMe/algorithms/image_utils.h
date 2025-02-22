#ifndef IMAGE_UTILS_H
#define IMAGE_UTILS_H

#include <stdint.h>
#include <stdlib.h>

uint8_t *decode_png(const uint8_t *input, size_t input_size, unsigned *width, unsigned *height);
uint8_t *encode_png(uint8_t *image_data, unsigned width, unsigned height, size_t *output_size);

#endif
