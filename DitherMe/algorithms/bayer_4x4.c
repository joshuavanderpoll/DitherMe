#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <png.h>
#include "image_utils.h"

static const uint8_t BAYER_4x4[4][4] = {
    {0, 8, 2, 10},
    {12, 4, 14, 6},
    {3, 11, 1, 9},
    {15, 7, 13, 5}
};

void ordered_dither_bayer_4x4(uint8_t *image, unsigned width, unsigned height, unsigned channels) {
    for (unsigned y = 0; y < height; y++) {
        for (unsigned x = 0; x < width; x++) {
            for (unsigned c = 0; c < channels; c++) {
                uint8_t *pixel = &image[(y * width + x) * channels + c];
                uint8_t threshold = (BAYER_4x4[y % 4][x % 4] * 255) / 16;
                *pixel = (*pixel > threshold) ? 255 : 0;
            }
        }
    }
}

static PyObject *dither_bayer_4x4(PyObject *self, PyObject *args) {
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

    ordered_dither_bayer_4x4(image_data, width, height, 4);

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

static PyMethodDef Bayer4x4Methods[] = {
    {"dither", dither_bayer_4x4, METH_VARARGS, "Apply 4x4 Bayer dithering to a PNG image."},
    {NULL, NULL, 0, NULL}
};

static struct PyModuleDef bayer4x4module = {
    PyModuleDef_HEAD_INIT,
    "bayer_4x4",
    "Module for applying 4x4 Bayer ordered dithering to PNG images.",
    -1,
    Bayer4x4Methods
};

PyMODINIT_FUNC PyInit_bayer_4x4(void) {
    return PyModule_Create(&bayer4x4module);
}
