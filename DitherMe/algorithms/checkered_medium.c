#define PY_SSIZE_T_CLEAN
#include <Python.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>

// Apply a medium checkerboard dithering pattern (2x2 blocks)
void checkered_dither(uint8_t *image, unsigned width, unsigned height, unsigned channels, uint8_t threshold) {
    uint8_t low_t  = (uint8_t)((uint16_t)threshold * 2 / 3);
    uint8_t high_t = (uint8_t)((uint16_t)threshold * 4 / 3 > 255 ? 255 : (uint16_t)threshold * 4 / 3);
    for (unsigned y = 0; y < height; y++) {
        for (unsigned x = 0; x < width; x++) {
            uint8_t *pixel = &image[(y * width + x) * channels];

            uint8_t brightness = (uint8_t)(0.299 * pixel[0] + 0.587 * pixel[1] + 0.114 * pixel[2]);

            uint8_t pixel_threshold = (((x / 2) + (y / 2)) % 2 == 0) ? low_t : high_t;
            uint8_t new_pixel = (brightness < pixel_threshold) ? 0 : 255;

            for (unsigned c = 0; c < 3; c++) {
                pixel[c] = new_pixel;
            }
        }
    }
}

// Python wrapper
static PyObject *dither_checkered(PyObject *self, PyObject *args) {
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

    checkered_dither(image_data, width, height, 4, threshold);

    PyObject *result = PyBytes_FromStringAndSize((char *)image_data, data_len);
    free(image_data);
    return result;
}

static PyMethodDef CheckeredMethods[] = {
    {"dither", dither_checkered, METH_VARARGS, "Apply a medium checkerboard dithering to a PNG image."},
    {NULL, NULL, 0, NULL}
};

static struct PyModuleDef checkeredmodule = {
    PyModuleDef_HEAD_INIT,
    "checkered_medium",
    "Medium checkerboard dithering module.",
    -1,
    CheckeredMethods
};

PyMODINIT_FUNC PyInit_checkered_medium(void) {
    return PyModule_Create(&checkeredmodule);
}
