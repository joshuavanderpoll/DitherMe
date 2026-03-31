#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <png.h>
#include "image_utils.h"

// Apply a medium checkerboard dithering pattern (2x2 blocks)
void checkered_dither(uint8_t *image, unsigned width, unsigned height, unsigned channels, uint8_t threshold) {
    uint8_t low_t  = (uint8_t)((uint16_t)threshold * 2 / 3);
    uint8_t high_t = (uint8_t)((uint16_t)threshold * 4 / 3 > 255 ? 255 : (uint16_t)threshold * 4 / 3);
    for (unsigned y = 0; y < height; y++) {
        for (unsigned x = 0; x < width; x++) {
            uint8_t *pixel = &image[(y * width + x) * channels];

            uint8_t brightness = (uint8_t)(0.299 * pixel[0] + 0.587 * pixel[1] + 0.114 * pixel[2]);

            uint8_t pixel_threshold = (((x / 2) + (y / 2)) % 2 == 0) ? low_t : high_t;
            uint8_t new_pixel = (brightness < pixel_threshold) ? 0 : 255;

            for (unsigned c = 0; c < 3; c++) {
                pixel[c] = new_pixel;
            }
        }
    }
}

// Python wrapper
static PyObject *dither_checkered(PyObject *self, PyObject *args) {
    Py_buffer input_buffer;
    int threshold_arg = 128;
    if (!PyArg_ParseTuple(args, "y*i", &input_buffer, &threshold_arg)) {
        return NULL;
    }
    uint8_t threshold = (uint8_t)(threshold_arg < 0 ? 0 : threshold_arg > 255 ? 255 : threshold_arg);

    unsigned width, height;
    uint8_t *image_data = decode_png((uint8_t *)input_buffer.buf, input_buffer.len, &width, &height);
    if (!image_data) {
        PyErr_SetString(PyExc_RuntimeError, "Failed to decode PNG");
        PyBuffer_Release(&input_buffer);
        return NULL;
    }

    checkered_dither(image_data, width, height, 4, threshold);

    size_t output_size;
    uint8_t *output_data = encode_png(image_data, width, height, &output_size);
    free(image_data);

    if (!output_data) {
        PyErr_SetString(PyExc_RuntimeError, "Failed to encode PNG");
        PyBuffer_Release(&input_buffer);
        return NULL;
    }

    PyObject *result = PyBytes_FromStringAndSize((char *)output_data, output_size);
    free(output_data);
    PyBuffer_Release(&input_buffer);
    return result;
}

static PyMethodDef CheckeredMethods[] = {
    {"dither", dither_checkered, METH_VARARGS, "Apply a medium checkerboard dithering to a PNG image."},
    {NULL, NULL, 0, NULL}
};

static struct PyModuleDef checkeredmodule = {
    PyModuleDef_HEAD_INIT,
    "checkered_medium",
    "Medium checkerboard dithering module.",
    -1,
    CheckeredMethods
};

PyMODINIT_FUNC PyInit_checkered_medium(void) {
    return PyModule_Create(&checkeredmodule);
}
