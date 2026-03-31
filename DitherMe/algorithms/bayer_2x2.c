#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>

static const uint8_t BAYER_2x2[2][2] = {
    {0, 2},
    {3, 1}
};

void ordered_dither_bayer_2x2(uint8_t *image, unsigned width, unsigned height, unsigned channels, int threshold_bias) {
    for (unsigned y = 0; y < height; y++) {
        for (unsigned x = 0; x < width; x++) {
            for (unsigned c = 0; c < channels; c++) {
                uint8_t *pixel = &image[(y * width + x) * channels + c];
                uint8_t matrix_threshold = (BAYER_2x2[y % 2][x % 2] * 255) / 4;
                int adjusted = (int)*pixel + threshold_bias;
                adjusted = adjusted < 0 ? 0 : (adjusted > 255 ? 255 : adjusted);
                *pixel = ((uint8_t)adjusted > matrix_threshold) ? 255 : 0;
            }
        }
    }
}

static PyObject *dither_bayer_2x2(PyObject *self, PyObject *args) {
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

    ordered_dither_bayer_2x2(image_data, width, height, 4, threshold_bias);

    PyObject *result = PyBytes_FromStringAndSize((char *)image_data, data_len);
    free(image_data);
    return result;
}

static PyMethodDef Bayer2x2Methods[] = {
    {"dither", dither_bayer_2x2, METH_VARARGS, "Apply 2x2 Bayer dithering to a PNG image."},
    {NULL, NULL, 0, NULL}
};

static struct PyModuleDef bayer2x2module = {
    PyModuleDef_HEAD_INIT,
    "bayer_2x2",
    "Module for applying 2x2 Bayer ordered dithering to PNG images.",
    -1,
    Bayer2x2Methods
};

PyMODINIT_FUNC PyInit_bayer_2x2(void) {
    return PyModule_Create(&bayer2x2module);
}
