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


class MonoBitmap:
    """A monochrome bitmap stored compactly.

    Attributes:
      bit_buf: The raw bitmap buffer bytearray.  Do not resize!
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
        self.bit_buf = bytearray(width * height // 8)

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
