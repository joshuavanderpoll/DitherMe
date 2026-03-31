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

    ordered_dither_clustered_dot_4x4(image_data, width, height, 4, threshold_bias);

    PyObject *result = PyBytes_FromStringAndSize((char *)image_data, data_len);
    free(image_data);
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
