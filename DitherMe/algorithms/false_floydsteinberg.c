#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <png.h>
#include "image_utils.h"


void false_floyd_steinberg_dither(uint8_t *image, unsigned width, unsigned height, unsigned channels) {
    for (unsigned y = 0; y < height; y++) {
        for (unsigned x = 0; x < width; x++) {
            for (unsigned c = 0; c < channels; c++) {
                uint8_t *pixel = &image[(y * width + x) * channels + c];
                int old_pixel = *pixel;
                int new_pixel = old_pixel < 128 ? 0 : 255;
                *pixel = new_pixel;
                int quant_error = old_pixel - new_pixel;

                // Spread error only to one adjacent pixel (right or bottom)
                if (x + 1 < width) { // Right pixel
                    uint8_t *right_pixel = &image[(y * width + (x + 1)) * channels + c];
                    *right_pixel = (uint8_t)fmax(0, fmin(255, *right_pixel + quant_error * 0.5));
                }
                if (y + 1 < height) { // Bottom pixel
                    uint8_t *bottom_pixel = &image[((y + 1) * width + x) * channels + c];
                    *bottom_pixel = (uint8_t)fmax(0, fmin(255, *bottom_pixel + quant_error * 0.5));
                }
            }
        }
    }
}

static PyObject *dither_false_floydsteinberg(PyObject *self, PyObject *args) {
    Py_buffer input_buffer;
    if (!PyArg_ParseTuple(args, "y*", &input_buffer)) {
        return NULL;
    }

    unsigned width, height;
    uint8_t *image_data = decode_png((uint8_t *)input_buffer.buf, input_buffer.len, &width, &height);
    if (!image_data) {
        PyErr_SetString(PyExc_RuntimeError, "Failed to decode PNG");
        return NULL;
    }

    false_floyd_steinberg_dither(image_data, width, height, 4);

    size_t output_size;
    uint8_t *output_data = encode_png(image_data, width, height, &output_size);
    free(image_data);

    if (!output_data) {
        PyErr_SetString(PyExc_RuntimeError, "Failed to encode PNG");
        return NULL;
    }

    PyObject *result = PyBytes_FromStringAndSize((char *)output_data, output_size);
    free(output_data);
    return result;
}

static PyMethodDef FalseFloydsteinbergMethods[] = {
    {"dither", dither_false_floydsteinberg, METH_VARARGS, "Apply a false Floyd–Steinberg dithering to a PNG image."},
    {NULL, NULL, 0, NULL}
};

static struct PyModuleDef falsefloydsteinbergmodule = {
    PyModuleDef_HEAD_INIT,
    "falsefloydsteinberg",
    "Module for applying a false version of Floyd–Steinberg dithering to PNG images.",
    -1,
    FalseFloydsteinbergMethods
};

PyMODINIT_FUNC PyInit_false_floydsteinberg(void) {
    return PyModule_Create(&falsefloydsteinbergmodule);
}