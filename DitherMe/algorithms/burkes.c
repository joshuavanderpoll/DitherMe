#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <png.h>
#include "image_utils.h"

void burkes_dither(uint8_t *image, unsigned width, unsigned height, unsigned channels, uint8_t threshold) {
    // Correcting the matrix to match the error diffusion pattern
    int8_t burkes_matrix[7][2] = {
        {1, 0}, {2, 0},  // Right neighbors
        {-2, 1}, {-1, 1}, {0, 1}, {1, 1}, {2, 1}  // Bottom row neighbors
    };

    float burkes_weights[7] = {8.0 / 32, 4.0 / 32, 2.0 / 32, 4.0 / 32, 8.0 / 32, 4.0 / 32, 2.0 / 32};

    for (unsigned y = 0; y < height; y++) {
        for (unsigned x = 0; x < width; x++) {
            for (unsigned c = 0; c < channels; c++) {
                uint8_t *pixel = &image[(y * width + x) * channels + c];
                int old_pixel = *pixel;
                int new_pixel = old_pixel < threshold ? 0 : 255;
                *pixel = new_pixel;
                int quant_error = old_pixel - new_pixel;

                // Now the loop correctly iterates over 7 elements
                for (int i = 0; i < 7; i++) {
                    int nx = x + burkes_matrix[i][0];
                    int ny = y + burkes_matrix[i][1];

                    if (nx >= 0 && nx < (int)width && ny >= 0 && ny < (int)height) {
                        uint8_t *neighbor = &image[(ny * width + nx) * channels + c];
                        *neighbor = (uint8_t)fmax(0, fmin(255, *neighbor + quant_error * burkes_weights[i]));
                    }
                }
            }
        }
    }
}

static PyObject *dither_burkes(PyObject *self, PyObject *args) {
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

    burkes_dither(image_data, width, height, 4, threshold);

    PyObject *result = PyBytes_FromStringAndSize((char *)image_data, data_len);
    free(image_data);
    return result;
}

static PyMethodDef BurkesMethods[] = {
    {"dither", dither_burkes, METH_VARARGS, "Apply Burkes dithering to a PNG image."},
    {NULL, NULL, 0, NULL}
};

static struct PyModuleDef burkesmodule = {
    PyModuleDef_HEAD_INIT,
    "burkes",
    "Module for applying Burkes dithering to PNG images.",
    -1,
    BurkesMethods
};

PyMODINIT_FUNC PyInit_burkes(void) {
    return PyModule_Create(&burkesmodule);
}
