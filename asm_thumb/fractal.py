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

import array
import time

from . import monobitmap


MAX_ITERATIONS_1 = 40 + 1


# Avoiding the builtin abs lookup in the loop is ~10% faster.
# Avoiding the builtin range lookup gains another ~3%.
def _fractal_iterate(c, z=0, _abs=abs, _range=range) -> int:
    for n in _range(MAX_ITERATIONS_1):
        z = z * z + c
        if _abs(z) > 2:
            return n
    return -1


# Data must be passed in via an array as micropython.asm_thumb doesn't
# support float arguments.
# r0 must be a pointer to an array of four 32-bit floats
# representing our c and z complex numbers:  [cr, cj, zr, zj]
@micropython.asm_thumb
def _fractal_iterate_fast(r0) -> int:
    mov(r5, r0)
    vldr(s0, [r5, 0])  # cr real
    vldr(s1, [r5, 4])  # cj imaginary
    vldr(s5, [r5, 8])  # zr real
    vldr(s3, [r5, 12])  # zj imaginary
    mov(r6, 41)  # MAX_ITERATIONS+1
    mov(r4, 2)
    vmov(s4, r4)
    vcvt_f32_s32(s4, s4)  # s4 = 2.0; @asm_thumb doesn't do arm float immediates.
    # for n in range(MAX_ITERATIONS_1):
    mov(r0, 0)  # r0 = n; current iteration number
    label(LOOP)
    vmov(r2, s5)  # start with zr real in s2.  The loop
    vmov(s2, r2)  # always begins/ends/cycles with it in s5.
    # complex z = z * z + c
    vmul(s6, s2, s2)
    vmul(s7, s3, s3)
    vsub(s5, s6, s7) # z = z*z  real part (zr^2 - zj^2)  [into a NEW reg]
    vmul(s6, s2, s3)
    vadd(s3, s6, s6) # z = z*z  imaginary part (zr*zj + zr*zj)
    # REG: s5 is the new zr real
    # REG: s3 is (still) zj imaginary
    vadd(s5, s5, s0) # zr += cr  real part
    vadd(s3, s3, s1) # zj += cj  imaginary part
    # complex abs(z)
    vmul(s6, s5, s5)  # zr^2
    vmul(s7, s3, s3)  # zj^2
    vadd(s6, s6, s7)
    vsqrt(s6, s6)  # sqrt(zr^2 + zj^2)
    # if abs(z) > 2
    vcmp(s6, s4)
    vmrs(APSR_nzcv, FPSCR)
    bgt(END)  # return n
    add(r0, 1)
    cmp(r0, r6)
    blt(LOOP)
    mov(r0, 0)  # return -1
    sub(r0, 1)
    label(END)  # return value is already in r0
    # expose state for debugging purposes:
#    vstr(s6, [r5, 0])  # abs(z)
#    vstr(s4, [r5, 4])  # 2.0
#    vstr(s5, [r5, 8])  # zr real
#    vstr(s3, [r5, 12])  # zj imaginary


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
    set_pixel_fast = fractal.set_pixel_fast  # faster name lookup
    set_pixel_fast_input = fractal.fast_in
    if _fractal_iterate_fast:
        # Extra space in asm_float_in is for debugging.
        asm_float_in = array.array('f', (0,0,0,0,0,0,0,0))
        def iterate(c, z=0j) -> int:
            c = complex(c)
            z = complex(z)
            asm_float_in[0] = c.real
            asm_float_in[1] = c.imag
            asm_float_in[2] = z.real
            asm_float_in[3] = z.imag
            return _fractal_iterate_fast(asm_float_in)
        print('Using asm_thumb _fractal_iterate and set_pixel.')
    else:
        iterate = _fractal_iterate
    julia_c = 0.3+0.6j  # Only load the complex constant once.

    start_time = time.monotonic()
    for y in range(height):
        set_pixel_fast_input[2] = y
        scaled_y_j_m_cx = (y*scale - center_y)*1j - center_x
        for x in range(width):
            c = x*scale + scaled_y_j_m_cx
            if use_julia:
                n = iterate(julia_c, c)  # Julia
            else:
                n = iterate(c)  # Mandlebrot

            set_pixel_fast(set_pixel_fast_input, x, n & 1)

        print('*', end='')
    print()
    print('Computation took', time.monotonic() - start_time, 'seconds.')
    return fractal

