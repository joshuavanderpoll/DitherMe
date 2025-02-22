#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <png.h>
#include "image_utils.h"

void floyd_steinberg_dither(uint8_t *image, unsigned width, unsigned height, unsigned channels) {
    int8_t fs_matrix[4][2] = {
        {1, 0},  // Right
        {-1, 1}, // Bottom-left
        {0, 1},  // Bottom
        {1, 1}   // Bottom-right
    };

    float fs_weights[4] = {7.0 / 16, 3.0 / 16, 5.0 / 16, 1.0 / 16};

    for (unsigned y = 0; y < height; y++) {
        for (unsigned x = 0; x < width; x++) {
            for (unsigned c = 0; c < channels; c++) {
                uint8_t *pixel = &image[(y * width + x) * channels + c];
                int old_pixel = *pixel;
                int new_pixel = old_pixel < 128 ? 0 : 255;
                *pixel = new_pixel;
                int quant_error = old_pixel - new_pixel;

                for (int i = 0; i < 4; i++) {
                    int nx = x + fs_matrix[i][0];
                    int ny = y + fs_matrix[i][1];

                    if (nx >= 0 && nx < (int)width && ny >= 0 && ny < (int)height) {
                        uint8_t *neighbor = &image[(ny * width + nx) * channels + c];
                        *neighbor = (uint8_t)fmax(0, fmin(255, *neighbor + quant_error * fs_weights[i]));
                    }
                }
            }
        }
    }
}

static PyObject *dither_floydsteinberg(PyObject *self, PyObject *args) {
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

    floyd_steinberg_dither(image_data, width, height, 4);

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

static PyMethodDef FloydsteinbergMethods[] = {
    {"dither", dither_floydsteinberg, METH_VARARGS, "Apply Floyd–Steinberg dithering to a PNG image."},
    {NULL, NULL, 0, NULL}
};

static struct PyModuleDef floydsteinbergmodule = {
    PyModuleDef_HEAD_INIT,
    "floydsteinberg",
    "Module for applying Floyd–Steinberg dithering to PNG images.",
    -1,
    FloydsteinbergMethods
};

PyMODINIT_FUNC PyInit_floydsteinberg(void) {
    return PyModule_Create(&floydsteinbergmodule);
}
