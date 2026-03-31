#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>

void stevenson_arce_dither(uint8_t *image, unsigned width, unsigned height, unsigned channels, uint8_t threshold) {
    // Stevenson-Arce diffusion matrix
    int8_t sa_matrix[12][2] = {
        {2, 0}, {3, 0}, {-2, 1}, {1, 1}, {-3, 2}, {-1, 2},
        {1, 2}, {3, 2}, {-2, 3}, {1, 3}, {0, 4}, {2, 4}
    };

    float sa_weights[12] = {32.0 / 200, 12.0 / 200, 12.0 / 200, 26.0 / 200,
                             12.0 / 200, 26.0 / 200, 12.0 / 200, 12.0 / 200,
                             12.0 / 200, 26.0 / 200, 12.0 / 200, 12.0 / 200};

    for (unsigned y = 0; y < height; y++) {
        for (unsigned x = 0; x < width; x++) {
            for (unsigned c = 0; c < channels; c++) {
                uint8_t *pixel = &image[(y * width + x) * channels + c];
                int old_pixel = *pixel;
                int new_pixel = old_pixel < threshold ? 0 : 255;
                *pixel = new_pixel;
                int quant_error = old_pixel - new_pixel;

                for (int i = 0; i < 12; i++) {
                    int nx = x + sa_matrix[i][0];
                    int ny = y + sa_matrix[i][1];

                    if (nx >= 0 && nx < (int)width && ny >= 0 && ny < (int)height) {
                        uint8_t *neighbor = &image[(ny * width + nx) * channels + c];
                        *neighbor = (uint8_t)fmax(0, fmin(255, *neighbor + quant_error * sa_weights[i]));
                    }
                }
            }
        }
    }
}

static PyObject *dither_stevenson_arce(PyObject *self, PyObject *args) {
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

    stevenson_arce_dither(image_data, width, height, 4, threshold);

    PyObject *result = PyBytes_FromStringAndSize((char *)image_data, data_len);
    free(image_data);
    return result;
}

static PyMethodDef StevensonArceMethods[] = {
    {"dither", dither_stevenson_arce, METH_VARARGS, "Apply Stevenson-Arce dithering to a PNG image."},
    {NULL, NULL, 0, NULL}
};

static struct PyModuleDef stevenson_arce_module = {
    PyModuleDef_HEAD_INIT,
    "stevenson_arce",
    "Module for applying Stevenson-Arce dithering to PNG images.",
    -1,
    StevensonArceMethods
};

PyMODINIT_FUNC PyInit_stevenson_arce(void) {
    return PyModule_Create(&stevenson_arce_module);
}
