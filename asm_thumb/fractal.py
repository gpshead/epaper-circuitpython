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
import struct
import time

from . import monobitmap


MAX_ITERATIONS_PLUS_1 = 40 + 1


# Avoiding the builtin abs lookup in the loop is ~10% faster.
# Avoiding the builtin range lookup gains another ~3%.
def _fractal_iterate(c, z=0, _abs=abs, _range=range) -> int:
    for n in _range(MAX_ITERATIONS_PLUS_1):
        z = z * z + c
        if _abs(z) > 2:
            return n
    return -1


# Data must be passed in via an array as micropython.asm_thumb doesn't
# support float arguments or more than three integer register inputs.
#
# Inputs:
#   Constant inputs:
#     0 [0x00]. &MonoBitmap.bit_buf (addr/int)
#     1 [0x04]. width (int)
#     2 [0x08]. julia or mandlebrot iteration? (bool true=julia)
#     3 [0x0c]. scale (float)
#     4 [0x10]. center_x (float)
#     5 [0x14]. center_y (float)
#     6 [0x18]. julia_c real (float)
#     7 [0x1c]. julia_c imag (float)
#     8 [0x20]. max_iterations (int)
#   Variants:
#     - y
#
# r0: &buffer containing the above 32-bit values.
# r1: y
@micropython.asm_thumb
def _xloop_iterate_and_set_pixels(r0, r1):
    # scaled_y_j: float = (y*scale - center_y)*1j
    vldr(s10, [r0, 0x0c])   # REG: s10 <- scale
    vmov(s20, r1)           # REG: s20 <- y (int), free REG r1
    vcvt_f32_s32(s11, s20)  # REG: s11 <- y (float)
    vldr(s15, [r0, 0x10])   # REG: s15 <- center_x
    vldr(s12, [r0, 0x14])   # REG: s12 <- center_y
    vmul(s13, s11, s10)
    vsub(s12, s13, s12)     # REG: s12 <- scaled_y_j (c_imag)
    # for x in range(width):
    mov(r1, 0)              # REG: r1 <- x
    label(X_RANGE_START)
    #     c: complex = x*scale - center_x + scaled_y_j
    vmov(s13, r1)
    vcvt_f32_s32(s13, s13)  # REG: s13 <- x
    vmul(s14, s13, s10)
    vsub(s14, s14, s15)     # REG: s14 <- (c_real)

    #     if use_julia:
    ldr(r7, [r0, 0x08])   # REG: r7 <- use_julia (sets branch flags)
    beq(MANDLEBROT)
    #         v: int = iterate(julia_c, c)  # Julia
    # iterate c= parameter.
    vldr(s0, [r0, 0x18])   # REG: s0 <- julia_c real
    vldr(s1, [r0, 0x1c])   # REG: s1 <- julia_c imag
    # iterate z= parameter.
    vmov(r7, s14)
    vmov(s5, r7)           # REG: s5 <- c_real
    vmov(r7, s12)
    vmov(s3, r7)           # REG: s3 <- c_imag
    b(CALL_ITERATE)

    #     else:
    label(MANDLEBROT)
    #         v: int = iterate(c, 0)  # Mandlebrot
    # iterate c= parameter.
    vmov(r7, s14)
    vmov(s0, r7)           # REG: s0 <- c_real
    vmov(r7, s12)
    vmov(s1, r7)           # REG: s1 <- c_imag
    # iterate z= parameter.
    mov(r7, 0)
    vmov(s5, r7)           # REG: s5 <- 0
    vmov(s3, r7)           # REG: s3 <- 0

    label(CALL_ITERATE)
    # Input: s0, s1, s5, s3
    # Output: r0
    push({r0, r1})
    bl(FRACTAL_ITERATE)
    #     set_pixel(x, y, v)
    # Inputs: r0 (array), r1 (x), r2 (value), s20 (y)
    # set_pixel_fast v= parameter is the result of iterate
    mov(r2, r0)
    # set_pixel_fast array and x= parameters are our r0 and r1.
    # from before we called iterate.
    pop({r0, r1})
    bl(SET_PIXEL)

    ldr(r7, [r0, 0x04])   # REG: r7 <- width
    add(r1, 1)  # x += 1
    cmp(r1, r7)  # if x < width, repeat the loop
    blt(X_RANGE_START)
    b(RETURN)

    ####
    label(FRACTAL_ITERATE)
    ldr(r6, [r0, 0x20])  # MAX_ITERATIONS
    mov(r4, 2)
    vmov(s4, r4)
    vcvt_f32_s32(s4, s4)  # s4 = 2.0; @asm_thumb doesn't do arm float immediates.
    # for n in range(MAX_ITERATIONS_PLUS_1):
    mov(r0, 0)  # r0 = n; current iteration number
    label(FI_LOOP)
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
    bgt(FI_END)  # return n
    add(r0, 1)
    cmp(r0, r6)
    ble(FI_LOOP)
    mov(r0, 1)  # return -1
    neg(r0, r0)
    label(FI_END)  # return value is already in r0
    bx(lr)
    #### end FRACTAL_ITERATE()

    ####
    label(SET_PIXEL)
    ldr(r3, [r0, 0x00])  # r3 <- address of bit_buf
    ldr(r5, [r0, 0x04])  # r5 <- width
    vmov(r6, s20)  # r6 <- y (we stashed it here up top)
    mul(r5, r6)  # r5 <- width * y
    add(r4, r1, r5)  # r4 <- binary_idx (width * y + x)
    mov(r5, r4)  # r5 <- binary_idx
    mov(r7, 3)
    lsr(r4, r7)  # r4 <- byte_idx
    mov(r7, 7)
    and_(r5, r7)
    sub(r5, r7, r5)  # r5 <- bit_no
    mov(r6, 1)
    lsl(r6, r5)  # r6 <- (1 << bit_no)
    add(r3, r3, r4)  # r1 <- &bit_buf[byte_idx]
    ldrb(r4, [r3, 0])  # r4 <- bit_buf[byte_idx]
    mov(r7, 1)
    and_(r2, r7)  # r2 <- value &= 1  (sets branch flags)
    beq(SPF_CLEAR_BIT)
    orr(r4, r6)  # r4 |= (1 << bit_no)
    b(SPF_STORE)
    label(SPF_CLEAR_BIT)
    bic(r4, r6)  # r4 &= ~(1 << bit_no)  # Nice instruction!
    label(SPF_STORE)
    strb(r4, [r3, 0])
    bx(lr)
    #### end SET_PIXEL

    label(RETURN)


# Created based on looking up how others have written Mandlebrot and Julia
# fractal computations in Python.  Well known algorithms.  Python's
# built-in complex number support makes them easy to express in code.
#  https://en.wikipedia.org/wiki/Mandelbrot_set#Computer_drawings
#  https://en.wikipedia.org/wiki/Julia_set#Pseudocode
#  https://github.com/ActiveState/code/blob/master/recipes/Python/579143_Mandelbrot_Set_made_simple/recipe-579143.py
#  https://github.com/ActiveState/code/blob/master/recipes/Python/577120_Julia_fractals/recipe-577120.py
#  http://0pointer.de/blog/projects/mandelbrot.html
def get_fractal(width: int, height: int, use_julia: bool = True) -> monobitmap.MonoBitmap:
    scale = 1/(width/1.5)
    if use_julia:
        center_x, center_y = 1.15, 1.6  # Julia
    else:
        center_x, center_y = 2.2, 1.5  # Mandlebrot

    fractal = monobitmap.MonoBitmap(width, height)
    julia_c = 0.3+0.6j  # Only load the complex constant once.

    xloop_params = array.array('i', (0,)*9)
    monobitmap.store_addr(xloop_params, fractal.bit_buf)
    xloop_params[1] = width
    xloop_params[2] = use_julia  # True: Julia, False: Mandlebrot
    struct.pack_into('fffff', xloop_params, 0x0c,
                     scale, center_x, center_y,
                     julia_c.real, julia_c.imag)
    xloop_params[8] = MAX_ITERATIONS_PLUS_1 - 1

    # Make these local
    compute_row_and_set_pixels = _xloop_iterate_and_set_pixels
    monotonic = time.monotonic

    start_time = monotonic()
    for y in range(height):
        compute_row_and_set_pixels(xloop_params, y)
        print('*', end='')
    end_time = monotonic()
    print('\nComputation took', end_time - start_time, 'seconds.')
    return fractal

