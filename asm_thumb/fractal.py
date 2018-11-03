# python3: CircuitPython 3.0

# Author: Gregory P. Smith (@gpshead) <greg@krypto.org>
#
# Copyright 2018 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Compute a Mandlebrot or Julia fractal into a bitmap."""

import time

import monobitmap


MAX_ITERATIONS_1 = 40 + 1


# Avoiding the builtin abs lookup in the loop is ~10% faster.
# Avoiding the builtin range lookup gains another ~3%.
def _fractal_iterate(c, z=0, _abs=abs, _range=range) -> int:
    for n in _range(MAX_ITERATIONS_1):
        z = z * z + c
        if _abs(z) > 2:
            return n
    return -1


# Created based on looking up how others have written Mandlebrot and Julia
# fractal computations in Python.  Well known algorithms.  Python's
# built-in complex number support makes them easy to express in code.
#  https://en.wikipedia.org/wiki/Mandelbrot_set#Computer_drawings
#  https://en.wikipedia.org/wiki/Julia_set#Pseudocode
#  https://github.com/ActiveState/code/blob/master/recipes/Python/579143_Mandelbrot_Set_made_simple/recipe-579143.py
#  https://github.com/ActiveState/code/blob/master/recipes/Python/577120_Julia_fractals/recipe-577120.py
#  http://0pointer.de/blog/projects/mandelbrot.html
def get_fractal(width, height, use_julia=True):
    scale = 1/(width/1.5)
    if use_julia:
        center_x, center_y = 1.15, 1.6  # Julia
    else:
        center_x, center_y = 2.2, 1.5  # Mandlebrot

    fractal = monobitmap.MonoBitmap(width, height)
    set_pixel = fractal.set_pixel  # faster name lookup
    iterate = _fractal_iterate  # faster name lookup
    julia_c = 0.3+0.6j  # Only load the complex constant once.

    start_time = time.monotonic()
    for y in range(height):
        scaled_y_j_m_cx = (y*scale - center_y)*1j - center_x
        for x in range(width):
            c = x*scale + scaled_y_j_m_cx
            if use_julia:
                n = iterate(julia_c, c)  # Julia
            else:
                n = iterate(c)  # Mandlebrot

            set_pixel(x, y, n & 1)

        print('*', end='')
    print()
    print('Computation took', time.monotonic() - start_time, 'seconds.')
    return fractal

