#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <png.h>
#include "image_utils.h"

static const uint8_t BAYER_8x8[8][8] = {
    {  0, 32,  8, 40,  2, 34, 10, 42 },
    { 48, 16, 56, 24, 50, 18, 58, 26 },
    { 12, 44,  4, 36, 14, 46,  6, 38 },
    { 60, 28, 52, 20, 62, 30, 54, 22 },
    {  3, 35, 11, 43,  1, 33,  9, 41 },
    { 51, 19, 59, 27, 49, 17, 57, 25 },
    { 15, 47,  7, 39, 13, 45,  5, 37 },
    { 63, 31, 55, 23, 61, 29, 53, 21 }
};

void ordered_dither_bayer_8x8(uint8_t *image, unsigned width, unsigned height, unsigned channels) {
    for (unsigned y = 0; y < height; y++) {
        for (unsigned x = 0; x < width; x++) {
            for (unsigned c = 0; c < channels; c++) {
                uint8_t *pixel = &image[(y * width + x) * channels + c];
                uint8_t threshold = (BAYER_8x8[y % 8][x % 8] * 255) / 64;
                *pixel = (*pixel > threshold) ? 255 : 0;
            }
        }
    }
}

static PyObject *dither_bayer_8x8(PyObject *self, PyObject *args) {
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

    ordered_dither_bayer_8x8(image_data, width, height, 4);

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

static PyMethodDef Bayer8x8Methods[] = {
    {"dither", dither_bayer_8x8, METH_VARARGS, "Apply 8x8 Bayer dithering to a PNG image."},
    {NULL, NULL, 0, NULL}
};

static struct PyModuleDef bayer8x8module = {
    PyModuleDef_HEAD_INIT,
    "bayer_8x8",
    "Module for applying 8x8 Bayer ordered dithering to PNG images.",
    -1,
    Bayer8x8Methods
};

PyMODINIT_FUNC PyInit_bayer_8x8(void) {
    return PyModule_Create(&bayer8x8module);
}
