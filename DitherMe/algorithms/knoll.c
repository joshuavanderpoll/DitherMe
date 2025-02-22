#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <png.h>
#include "image_utils.h"

void knoll_dither(uint8_t *image, unsigned width, unsigned height, unsigned channels) {
    // Knoll diffusion matrix (5x5)
    int8_t knoll_matrix[24][2] = {
        {1, 0}, {2, 0}, {3, 0}, {4, 0},  // Right neighbors
        {-1, 1}, {0, 1}, {1, 1}, {2, 1}, {3, 1}, {4, 1},  // Next row
        {-2, 2}, {-1, 2}, {0, 2}, {1, 2}, {2, 2}, {3, 2}, {4, 2},  // Row 3
        {-3, 3}, {-2, 3}, {-1, 3}, {0, 3}, {1, 3}, {2, 3}, {3, 3}  // Row 4
    };

    float knoll_weights[24] = {12.0 / 136, 10.0 / 136, 7.0 / 136, 5.0 / 136,
                                12.0 / 136, 12.0 / 136, 8.0 / 136, 5.0 / 136, 3.0 / 136, 0.0,
                                10.0 / 136, 8.0 / 136, 5.0 / 136, 3.0 / 136, 2.0 / 136, 0.0, 0.0,
                                7.0 / 136, 5.0 / 136, 3.0 / 136, 2.0 / 136, 1.0 / 136, 0.0, 0.0};

    for (unsigned y = 0; y < height; y++) {
        for (unsigned x = 0; x < width; x++) {
            for (unsigned c = 0; c < channels; c++) {
                uint8_t *pixel = &image[(y * width + x) * channels + c];
                int old_pixel = *pixel;
                int new_pixel = old_pixel < 128 ? 0 : 255;
                *pixel = new_pixel;
                int quant_error = old_pixel - new_pixel;

                for (int i = 0; i < 24; i++) {
                    int nx = x + knoll_matrix[i][0];
                    int ny = y + knoll_matrix[i][1];

                    if (nx >= 0 && nx < (int)width && ny >= 0 && ny < (int)height) {
                        uint8_t *neighbor = &image[(ny * width + nx) * channels + c];
                        *neighbor = (uint8_t)fmax(0, fmin(255, *neighbor + quant_error * knoll_weights[i]));
                    }
                }
            }
        }
    }
}

static PyObject *dither_knoll(PyObject *self, PyObject *args) {
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

    knoll_dither(image_data, width, height, 4);

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

static PyMethodDef KnollMethods[] = {
    {"dither", dither_knoll, METH_VARARGS, "Apply Knoll dithering to a PNG image."},
    {NULL, NULL, 0, NULL}
};

static struct PyModuleDef knoll_module = {
    PyModuleDef_HEAD_INIT,
    "knoll",
    "Module for applying Knoll dithering to PNG images.",
    -1,
    KnollMethods
};

PyMODINIT_FUNC PyInit_knoll(void) {
    return PyModule_Create(&knoll_module);
}
