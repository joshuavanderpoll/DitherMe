#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <png.h>
#include "image_utils.h"

void sierra_dither(uint8_t *image, unsigned width, unsigned height, unsigned channels) {
    int8_t sierra_matrix[6][2] = {
        {1, 0},  {2, 0},  // Right neighbors
        {-2, 1}, {-1, 1}, {0, 1}, {1, 1}  // Bottom row neighbors
    };

    float sierra_weights[6] = {5.0 / 32, 3.0 / 32, 2.0 / 32, 4.0 / 32, 5.0 / 32, 4.0 / 32};

    for (unsigned y = 0; y < height; y++) {
        for (unsigned x = 0; x < width; x++) {
            for (unsigned c = 0; c < channels; c++) {
                uint8_t *pixel = &image[(y * width + x) * channels + c];
                int old_pixel = *pixel;
                int new_pixel = old_pixel < 128 ? 0 : 255;
                *pixel = new_pixel;
                int quant_error = old_pixel - new_pixel;

                for (int i = 0; i < 6; i++) {
                    int nx = x + sierra_matrix[i][0];
                    int ny = y + sierra_matrix[i][1];

                    if (nx >= 0 && nx < (int)width && ny >= 0 && ny < (int)height) {
                        uint8_t *neighbor = &image[(ny * width + nx) * channels + c];
                        *neighbor = (uint8_t)fmax(0, fmin(255, *neighbor + quant_error * sierra_weights[i]));
                    }
                }
            }
        }
    }
}

static PyObject *dither_sierra(PyObject *self, PyObject *args) {
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

    sierra_dither(image_data, width, height, 4);

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

static PyMethodDef SierraMethods[] = {
    {"dither", dither_sierra, METH_VARARGS, "Apply Original Sierra dithering to a PNG image."},
    {NULL, NULL, 0, NULL}
};

static struct PyModuleDef sierramodule = {
    PyModuleDef_HEAD_INIT,
    "sierra",
    "Module for applying Original Sierra dithering to PNG images.",
    -1,
    SierraMethods
};

PyMODINIT_FUNC PyInit_sierra(void) {
    return PyModule_Create(&sierramodule);
}
