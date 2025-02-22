#include <png.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>

uint8_t *decode_png(const uint8_t *input, size_t input_size, unsigned *width, unsigned *height) {
    png_image image;
    memset(&image, 0, sizeof(image));
    image.version = PNG_IMAGE_VERSION;

    if (!png_image_begin_read_from_memory(&image, input, input_size)) {
        return NULL;
    }

    image.format = PNG_FORMAT_RGBA;

    uint8_t *buffer = (uint8_t *)malloc(PNG_IMAGE_SIZE(image));
    if (!buffer) {
        return NULL;
    }

    if (!png_image_finish_read(&image, NULL, buffer, 0, NULL)) {
        free(buffer);
        return NULL;
    }

    *width = image.width;
    *height = image.height;
    return buffer;
}

uint8_t *encode_png(uint8_t *image_data, unsigned width, unsigned height, size_t *output_size) {
    png_image image;
    memset(&image, 0, sizeof(image));
    image.version = PNG_IMAGE_VERSION;
    image.width = width;
    image.height = height;
    image.format = PNG_FORMAT_RGBA;

    uint8_t *output = NULL;
    *output_size = 0;

    png_image_write_to_memory(&image, NULL, output_size, 0, image_data, 0, NULL);
    if (*output_size == 0) {
        return NULL;
    }

    output = (uint8_t *)malloc(*output_size);
    if (!output) {
        return NULL;
    }

    if (!png_image_write_to_memory(&image, output, output_size, 0, image_data, 0, NULL)) {
        free(output);
        return NULL;
    }

    return output;
}
