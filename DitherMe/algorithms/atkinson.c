#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <png.h>
#include "image_utils.h"

void atkinson_dither(uint8_t *image, unsigned width, unsigned height, unsigned channels, uint8_t threshold) {
    int8_t atkinson_matrix[6][2] = {
        {1, 0},  {2, 0},  // Right neighbors
        {-1, 1}, {0, 1},  {1, 1},  // Bottom row neighbors
        {0, 2}   // Bottom-bottom neighbor
    };

    float atkinson_weight = 1.0 / 8.0;  // Each neighbor gets 1/8 of the error

    for (unsigned y = 0; y < height; y++) {
        for (unsigned x = 0; x < width; x++) {
            for (unsigned c = 0; c < channels; c++) {
                uint8_t *pixel = &image[(y * width + x) * channels + c];
                int old_pixel = *pixel;
                int new_pixel = old_pixel < threshold ? 0 : 255;
                *pixel = new_pixel;
                int quant_error = (old_pixel - new_pixel) * atkinson_weight;

                for (int i = 0; i < 6; i++) {
                    int nx = x + atkinson_matrix[i][0];
                    int ny = y + atkinson_matrix[i][1];

                    if (nx >= 0 && nx < (int)width && ny >= 0 && ny < (int)height) {
                        uint8_t *neighbor = &image[(ny * width + nx) * channels + c];
                        *neighbor = (uint8_t)fmax(0, fmin(255, *neighbor + quant_error));
                    }
                }
            }
        }
    }
}

static PyObject *dither_atkinson(PyObject *self, PyObject *args) {
    Py_buffer input_buffer;
    unsigned int width, height;
    int threshold_arg = 128;
    if (!PyArg_ParseTuple(args, "y*IIi", &input_buffer, &width, &height, &threshold_arg)) {
        return NULL;
    }
    uint8_t threshold = (uint8_t)(threshold_arg < 0 ? 0 : threshold_arg > 255 ? 255 : threshold_arg);

    Py_ssize_t data_len = input_buffer.len;
    uint8_t *image_data = (uint8_t *)malloc(data_len);
    if (!image_data) {
        PyBuffer_Release(&input_buffer);
        PyErr_NoMemory();
        return NULL;
    }
    memcpy(image_data, input_buffer.buf, data_len);
    PyBuffer_Release(&input_buffer);

    atkinson_dither(image_data, width, height, 4, threshold);

    PyObject *result = PyBytes_FromStringAndSize((char *)image_data, data_len);
    free(image_data);
    return result;
}

static PyMethodDef AtkinsonMethods[] = {
    {"dither", dither_atkinson, METH_VARARGS, "Apply Atkinson dithering to a PNG image."},
    {NULL, NULL, 0, NULL}
};

static struct PyModuleDef atkinsonmodule = {
    PyModuleDef_HEAD_INIT,
    "atkinson",
    "Module for applying Atkinson dithering to PNG images.",
    -1,
    AtkinsonMethods
};

PyMODINIT_FUNC PyInit_atkinson(void) {
    return PyModule_Create(&atkinsonmodule);
}
