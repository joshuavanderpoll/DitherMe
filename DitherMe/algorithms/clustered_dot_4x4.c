#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <png.h>
#include "image_utils.h"

static const uint8_t CLUSTERED_DOT_4x4[4][4] = {
    {12,  5,  6, 13},
    { 4,  0,  1,  7},
    {11,  3,  2,  8},
    {15, 10,  9, 14}
};

void ordered_dither_clustered_dot_4x4(uint8_t *image, unsigned width, unsigned height, unsigned channels, int threshold_bias) {
    for (unsigned y = 0; y < height; y++) {
        for (unsigned x = 0; x < width; x++) {
            for (unsigned c = 0; c < channels; c++) {
                uint8_t *pixel = &image[(y * width + x) * channels + c];
                uint8_t matrix_threshold = (CLUSTERED_DOT_4x4[y % 4][x % 4] * 255) / 16;
                int adjusted = (int)*pixel + threshold_bias;
                adjusted = adjusted < 0 ? 0 : (adjusted > 255 ? 255 : adjusted);
                *pixel = ((uint8_t)adjusted > matrix_threshold) ? 255 : 0;
            }
        }
    }
}

static PyObject *dither_clustered_dot_4x4(PyObject *self, PyObject *args) {
    Py_buffer input_buffer;
    int threshold_arg = 128;
    if (!PyArg_ParseTuple(args, "y*i", &input_buffer, &threshold_arg)) {
        return NULL;
    }
    int threshold_bias = threshold_arg - 128;

    unsigned width, height;
    uint8_t *image_data = decode_png((uint8_t *)input_buffer.buf, input_buffer.len, &width, &height);
    if (!image_data) {
        PyErr_SetString(PyExc_RuntimeError, "Failed to decode PNG");
        PyBuffer_Release(&input_buffer);
        return NULL;
    }

    ordered_dither_clustered_dot_4x4(image_data, width, height, 4, threshold_bias);

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

static PyMethodDef ClusteredDot4x4Methods[] = {
    {"dither", dither_clustered_dot_4x4, METH_VARARGS, "Apply 4x4 Clustered Dot dithering to a PNG image."},
    {NULL, NULL, 0, NULL}
};

static struct PyModuleDef clustereddot4x4module = {
    PyModuleDef_HEAD_INIT,
    "clustered_dot_4x4",
    "Module for applying 4x4 Clustered Dot ordered dithering to PNG images.",
    -1,
    ClusteredDot4x4Methods
};

PyMODINIT_FUNC PyInit_clustered_dot_4x4(void) {
    return PyModule_Create(&clustereddot4x4module);
}
