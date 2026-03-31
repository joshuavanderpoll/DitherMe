#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>


void false_floyd_steinberg_dither(uint8_t *image, unsigned width, unsigned height, unsigned channels, uint8_t threshold) {
    for (unsigned y = 0; y < height; y++) {
        for (unsigned x = 0; x < width; x++) {
            for (unsigned c = 0; c < channels; c++) {
                uint8_t *pixel = &image[(y * width + x) * channels + c];
                int old_pixel = *pixel;
                int new_pixel = old_pixel < threshold ? 0 : 255;
                *pixel = new_pixel;
                int quant_error = old_pixel - new_pixel;

                // Spread error only to one adjacent pixel (right or bottom)
                if (x + 1 < width) { // Right pixel
                    uint8_t *right_pixel = &image[(y * width + (x + 1)) * channels + c];
                    *right_pixel = (uint8_t)fmax(0, fmin(255, *right_pixel + quant_error * 0.5));
                }
                if (y + 1 < height) { // Bottom pixel
                    uint8_t *bottom_pixel = &image[((y + 1) * width + x) * channels + c];
                    *bottom_pixel = (uint8_t)fmax(0, fmin(255, *bottom_pixel + quant_error * 0.5));
                }
            }
        }
    }
}

static PyObject *dither_false_floydsteinberg(PyObject *self, PyObject *args) {
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

    false_floyd_steinberg_dither(image_data, width, height, 4, threshold);

    PyObject *result = PyBytes_FromStringAndSize((char *)image_data, data_len);
    free(image_data);
    return result;
}

static PyMethodDef FalseFloydsteinbergMethods[] = {
    {"dither", dither_false_floydsteinberg, METH_VARARGS, "Apply a false Floyd–Steinberg dithering to a PNG image."},
    {NULL, NULL, 0, NULL}
};

static struct PyModuleDef falsefloydsteinbergmodule = {
    PyModuleDef_HEAD_INIT,
    "falsefloydsteinberg",
    "Module for applying a false version of Floyd–Steinberg dithering to PNG images.",
    -1,
    FalseFloydsteinbergMethods
};

PyMODINIT_FUNC PyInit_false_floydsteinberg(void) {
    return PyModule_Create(&falsefloydsteinbergmodule);
}