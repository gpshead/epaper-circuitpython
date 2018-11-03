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

"""A monochrome bitmap to represent display frame buffers."""

import array


class MonoBitmap:
    """A monochrome bitmap stored compactly.

    Attributes:
      bit_buf: The raw bitmap buffer bytearray.  Do not resize!
      fast_in: Input array to pass to set_pixel_fast.  Do not modify.
      width: The width.  Do not modify.
      height: The height.  Do not modify.

    Usage:
      hidden_cat = MonoBitmap(204, 112)
      hidden_cat.set_pixel(42, 23, 0)
      epd.display_frame_buf(hidden_cat.bit_buf)
    """
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self._bit_buf = bytearray(width * height // 8)

        # (&bit_buf, width, y)
        self.fast_in = array.array('i', [-1, width, 0])
        store_addr(self.fast_in, self._bit_buf)

    @property
    def bit_buf(self):
        return self._bit_buf

    def set_pixel(self, x: int, y: int, value: bool) -> None:
        #assert self.width > x >= 0
        #assert self.height > y >= 0
        binary_idx = self.width * y + x
        #byte_idx, bit_no = divmod(binary_idx, 8)
        #bit_no = 7 - bit_no  # The EPD's bit order.
        byte_idx = binary_idx >> 3
        bit_no = 7 - (binary_idx & 7)
        if value:
            self.bit_buf[byte_idx] |= (1 << bit_no)
        else:
            self.bit_buf[byte_idx] &= ~(1 << bit_no)

    # r0 must be the self.fast_in array (&bit_buf, width, y)
    # r1 is the x coordinate
    # r2 is the value to set for the pixel
    # No bounds checking is performed!
    @staticmethod
    @micropython.asm_thumb
    def set_pixel_fast(r0, r1, r2):
        # r0 <- inputs array
        # r1 <- x
        # r2 <- value
        ldr(r3, [r0, 0])  # r3 <- address of bit_buf
        ldr(r5, [r0, 4])  # r5 <- width
        ldr(r6, [r0, 8])  # r6 <- y
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
        and_(r2, r7)  # r2 <- value &= 1  (sets the eq zero flag)
        beq(CLEAR_BIT)
        orr(r4, r6)  # r4 |= (1 << bit_no)
        b(STORE)
        label(CLEAR_BIT)
        bic(r4, r6)  # r4 &= ~(1 << bit_no)  # Nice instruction!
        label(STORE)
        strb(r4, [r3, 0])


# This utility function really belongs somewhere else.
@micropython.asm_thumb
def store_addr(r0, r1):
    """Store r1 into r0[0].  Good for getting &thing into a buffer."""
    str(r1, [r0, 0])
