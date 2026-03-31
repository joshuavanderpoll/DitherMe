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

void ordered_dither_bayer_8x8(uint8_t *image, unsigned width, unsigned height, unsigned channels, int threshold_bias) {
    for (unsigned y = 0; y < height; y++) {
        for (unsigned x = 0; x < width; x++) {
            for (unsigned c = 0; c < channels; c++) {
                uint8_t *pixel = &image[(y * width + x) * channels + c];
                uint8_t matrix_threshold = (BAYER_8x8[y % 8][x % 8] * 255) / 64;
                int adjusted = (int)*pixel + threshold_bias;
                adjusted = adjusted < 0 ? 0 : (adjusted > 255 ? 255 : adjusted);
                *pixel = ((uint8_t)adjusted > matrix_threshold) ? 255 : 0;
            }
        }
    }
}

static PyObject *dither_bayer_8x8(PyObject *self, PyObject *args) {
    Py_buffer input_buffer;
    unsigned int width, height;
    int threshold_arg = 128;
    if (!PyArg_ParseTuple(args, "y*IIi", &input_buffer, &width, &height, &threshold_arg)) {
        return NULL;
    }
    int threshold_bias = threshold_arg - 128;

    Py_ssize_t data_len = input_buffer.len;
    uint8_t *image_data = (uint8_t *)malloc(data_len);
    if (!image_data) {
        PyBuffer_Release(&input_buffer);
        PyErr_NoMemory();
        return NULL;
    }
    memcpy(image_data, input_buffer.buf, data_len);
    PyBuffer_Release(&input_buffer);

    ordered_dither_bayer_8x8(image_data, width, height, 4, threshold_bias);

    PyObject *result = PyBytes_FromStringAndSize((char *)image_data, data_len);
    free(image_data);
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
