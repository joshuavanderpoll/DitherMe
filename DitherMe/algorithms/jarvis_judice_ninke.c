#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <png.h>
#include "image_utils.h"

void jarvis_judice_ninke_dither(uint8_t *image, unsigned width, unsigned height, unsigned channels) {
    int8_t jjn_matrix[12][2] = {
        {1, 0}, {2, 0},   // Right neighbors
        {-2, 1}, {-1, 1}, {0, 1}, {1, 1}, {2, 1},  // First below row
        {-2, 2}, {-1, 2}, {0, 2}, {1, 2}, {2, 2}   // Second below row
    };

    float jjn_weights[12] = {
        7.0 / 48, 5.0 / 48,
        3.0 / 48, 5.0 / 48, 7.0 / 48, 5.0 / 48, 3.0 / 48,
        1.0 / 48, 3.0 / 48, 5.0 / 48, 3.0 / 48, 1.0 / 48
    };

    for (unsigned y = 0; y < height; y++) {
        for (unsigned x = 0; x < width; x++) {
            for (unsigned c = 0; c < channels; c++) {
                uint8_t *pixel = &image[(y * width + x) * channels + c];
                int old_pixel = *pixel;
                int new_pixel = old_pixel < 128 ? 0 : 255;
                *pixel = new_pixel;
                int quant_error = old_pixel - new_pixel;

                for (int i = 0; i < 12; i++) {
                    int nx = x + jjn_matrix[i][0];
                    int ny = y + jjn_matrix[i][1];

                    if (nx >= 0 && nx < (int)width && ny >= 0 && ny < (int)height) {
                        uint8_t *neighbor = &image[(ny * width + nx) * channels + c];
                        *neighbor = (uint8_t)fmax(0, fmin(255, *neighbor + quant_error * jjn_weights[i]));
                    }
                }
            }
        }
    }
}

static PyObject *dither_jarvis_judice_ninke(PyObject *self, PyObject *args) {
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

    jarvis_judice_ninke_dither(image_data, width, height, 4);

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

static PyMethodDef JarvisJudiceNinkeMethods[] = {
    {"dither", dither_jarvis_judice_ninke, METH_VARARGS, "Apply Jarvis, Judice & Ninke dithering to a PNG image."},
    {NULL, NULL, 0, NULL}
};

static struct PyModuleDef jarvisjudiceninkemodule = {
    PyModuleDef_HEAD_INIT,
    "jarvis_judice_ninke",
    "Module for applying Jarvis, Judice & Ninke dithering to PNG images.",
    -1,
    JarvisJudiceNinkeMethods
};

PyMODINIT_FUNC PyInit_jarvis_judice_ninke(void) {
    return PyModule_Create(&jarvisjudiceninkemodule);
}
