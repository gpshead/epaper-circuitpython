# Ported to CircuitPython by Gregory P. Smith

##
 #  @filename   :   epd2in13b.py
 #  @brief      :   Implements for Dual-color e-paper library
 #  @author     :   Yehui from Waveshare
 #
 #  Copyright (C) Waveshare     August 15 2017
 #
 # Permission is hereby granted, free of charge, to any person obtaining a copy
 # of this software and associated documnetation files (the "Software"), to deal
 # in the Software without restriction, including without limitation the rights
 # to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 # copies of the Software, and to permit persons to  whom the Software is
 # furished to do so, subject to the following conditions:
 #
 # The above copyright notice and this permission notice shall be included in
 # all copies or substantial portions of the Software.
 #
 # THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 # IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 # FITNESS OR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 # AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 # LIABILITY WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 # OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
 # THE SOFTWARE.
 #

import time

from . import epdif

# EPD2IN13B commands
PANEL_SETTING                               = 0x00
POWER_SETTING                               = 0x01
POWER_OFF                                   = 0x02
POWER_OFF_SEQUENCE_SETTING                  = 0x03
POWER_ON                                    = 0x04
POWER_ON_MEASURE                            = 0x05
BOOSTER_SOFT_START                          = 0x06
DEEP_SLEEP                                  = 0x07
DATA_START_TRANSMISSION_1                   = 0x10  # B&W data
DATA_STOP                                   = 0x11
DISPLAY_REFRESH                             = 0x12
DATA_START_TRANSMISSION_2                   = 0x13  # tinted data
VCOM_LUT                                    = 0x20
W2W_LUT                                     = 0x21
B2W_LUT                                     = 0x22
W2B_LUT                                     = 0x23
B2B_LUT                                     = 0x24
PLL_CONTROL                                 = 0x30
TEMPERATURE_SENSOR_CALIBRATION              = 0x40
TEMPERATURE_SENSOR_SELECTION                = 0x41
TEMPERATURE_SENSOR_WRITE                    = 0x42
TEMPERATURE_SENSOR_READ                     = 0x43
VCOM_AND_DATA_INTERVAL_SETTING              = 0x50
LOW_POWER_DETECTION                         = 0x51
TCON_SETTING                                = 0x60
RESOLUTION_SETTING                          = 0x61
GET_STATUS                                  = 0x71
AUTO_MEASURE_VCOM                           = 0x80
VCOM_VALUE                                  = 0x81
VCM_DC_SETTING                              = 0x82
PARTIAL_WINDOW                              = 0x90
PARTIAL_IN                                  = 0x91
PARTIAL_OUT                                 = 0x92
PROGRAM_MODE                                = 0xA0
ACTIVE_PROGRAM                              = 0xA1
READ_OTP_DATA                               = 0xA2
POWER_SAVING                                = 0xE3

class EPD:
    width = 104
    height = 212
    colors = 3

    def __init__(self):
        self.reset_pin = epdif.RST_PIN
        self.dc_pin = epdif.DC_PIN
        self.busy_pin = epdif.BUSY_PIN

    def _delay_ms(self, ms):
        time.sleep(ms / 1000.)

    def _send_command(self, command):
        self.dc_pin.value = 0
        epdif.spi_transfer(command.to_bytes(1, 'big'))

    def _send_data(self, data):
        self.dc_pin.value = 1
        if isinstance(data, int):
            epdif.spi_transfer(data.to_bytes(1, 'big'))
        else:
            # The EPD needs CS to cycle hi between every byte so we loop doing
            # one byte transfers to cause that.  Not efficient, but it makes
            # it work.  Data sheets say needs to be at least a 60ns CS pulse.
            for i in range(len(data)):
                epdif.spi_transfer(data[i:i+1])

    @property
    def fb_bytes(self):
        return self.width * self.height // 8

    def init(self):
        try:
            epdif.epd_io_bus_init()
        except RuntimeError:
            pass  # It avoids global io bus reinitialization.  Good.
        self.reset_pin = epdif.RST_PIN
        self.dc_pin = epdif.DC_PIN
        self.busy_pin = epdif.BUSY_PIN
        self.reset()
        self._send_command(BOOSTER_SOFT_START)
        self._send_data (0x17)
        self._send_data (0x17)
        self._send_data (0x17)
        self._send_command(POWER_ON)
        self.wait_until_idle()
        self._send_command(PANEL_SETTING)
        self._send_data(0x8F)
        self._send_command(VCOM_AND_DATA_INTERVAL_SETTING)
        self._send_data(0x37)
        self._send_command(RESOLUTION_SETTING)
        self._send_data (0x68)
        self._send_data (0x00)
        self._send_data (0xD4)

    def wait_until_idle(self):
        while self.busy_pin.value == 1:      # 0: idle, 1: busy
            self._delay_ms(10)

    def reset(self):
        self.reset_pin.value = 0         # module reset
        self._delay_ms(200)
        self.reset_pin.value = 1
        self._delay_ms(200)

    def clear_frame_memory(self, pattern: int, tint_pattern: int = -1):
        self._send_command(DATA_START_TRANSMISSION_1)
        self._delay_ms(2)
        row = pattern.to_bytes(1, 'big') * ((self.width + 7) // 8)
        for j in range(self.height):
            self._send_data(row)
        if tint_pattern < 0:
            tint_pattern = pattern
        self._delay_ms(2)
        self._send_command(DATA_START_TRANSMISSION_2)
        self._delay_ms(2)
        row = tint_pattern.to_bytes(1, 'big') * ((self.width + 7) // 8)
        for j in range(self.height):
            self._send_data(row)
        self._delay_ms(2)

    # TODO An API that takes a two bits per pixel image input would be good.

    def display_frame(self):
        self.display_frames(None, None)

    def display_frames(self, frame_buffer_black, frame_buffer_red):
        # TODO: assert buffer lengths and _send_data all of it w/o loop?
        if frame_buffer_black:
            self._send_command(DATA_START_TRANSMISSION_1)
            self._delay_ms(2)
            for i in range(0, self.width * self.height / 8):
                self._send_data(frame_buffer_black[i])
            self._delay_ms(2)
        if frame_buffer_red:
            self._send_command(DATA_START_TRANSMISSION_2)
            self._delay_ms(2)
            for i in range(0, self.width * self.height / 8):
                self._send_data(frame_buffer_red[i])
            self._delay_ms(2)

        self._send_command(DISPLAY_REFRESH)
        self.wait_until_idle()

    # after this, call epd.init() to awaken the module
    def sleep(self):
        self._send_command(VCOM_AND_DATA_INTERVAL_SETTING)
        self._send_data(0x37)
        self._send_command(VCM_DC_SETTING_REGISTER)         #to solve Vcom drop
        self._send_data(0x00)
        self._send_command(POWER_SETTING)         #power setting
        self._send_data(0x02)        #gate switch to external
        self._send_data(b'\x00\x00\x00')
        self._wait_until_idle()
        self._send_command(POWER_OFF)         #power off

    # TODO: pixel and drawing functions should be put in a shared class.
    # such as MonoBitmap...  the only actual relevance to us is set_absolute_pixel
    # which describes how the bits are set per byte and that a color pixel is
    # a 0 bit (1 transparent) and a black pixel is a 1 bit (0 white) in their
    # respective frame buffers.  the color buffer is added after the b&w is drawn.

    def _set_absolute_pixel(self, frame_buffer, x: int, y: int, tinted: bool):
        """Set a pixel black or tinted in a bytearray frame buffer."""
        if (x < 0 or x >= self.width or y < 0 or y >= self.height):
            raise ValueError('x %d, y %d out of range' % (x, y))
        if tinted:
            frame_buffer[(x + y * self.width) / 8] &= ~(0x80 >> (x % 8))
        else:
            frame_buffer[(x + y * self.width) / 8] |= 0x80 >> (x % 8)

    set_pixel = _set_absolute_pixel  # I got rid of the rotation code.

    # TODO(gps): left off porting here.

    def draw_line(self, frame_buffer, x0, y0, x1, y1, tinted):
        # Bresenham algorithm
        dx = abs(x1 - x0)
        sx = 1 if x0 < x1 else -1
        dy = -abs(y1 - y0)
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        while((x0 != x1) and (y0 != y1)):
            self.set_pixel(frame_buffer, x0, y0 , tinted)
            if (2 * err >= dy):
                err += dy
                x0 += sx
            if (2 * err <= dx):
                err += dx
                y0 += sy

    def draw_horizontal_line(self, frame_buffer, x, y, width, tinted):
        for i in range(x, x + width):
            self.set_pixel(frame_buffer, i, y, tinted)

    def draw_vertical_line(self, frame_buffer, x, y, height, tinted):
        for i in range(y, y + height):
            self.set_pixel(frame_buffer, x, i, tinted)

    def draw_rectangle(self, frame_buffer, x0, y0, x1, y1, tinted):
        min_x = x0 if x1 > x0 else x1
        max_x = x1 if x1 > x0 else x0
        min_y = y0 if y1 > y0 else y1
        max_y = y1 if y1 > y0 else y0
        self.draw_horizontal_line(frame_buffer, min_x, min_y, max_x - min_x + 1, tinted)
        self.draw_horizontal_line(frame_buffer, min_x, max_y, max_x - min_x + 1, tinted)
        self.draw_vertical_line(frame_buffer, min_x, min_y, max_y - min_y + 1, tinted)
        self.draw_vertical_line(frame_buffer, max_x, min_y, max_y - min_y + 1, tinted)

    def draw_filled_rectangle(self, frame_buffer, x0, y0, x1, y1, tinted):
        min_x = x0 if x1 > x0 else x1
        max_x = x1 if x1 > x0 else x0
        min_y = y0 if y1 > y0 else y1
        max_y = y1 if y1 > y0 else y0
        for i in range(min_x, max_x + 1):
            self.draw_vertical_line(frame_buffer, i, min_y, max_y - min_y + 1, tinted)

    def draw_circle(self, frame_buffer, x, y, radius, tinted):
        # Bresenham algorithm
        x_pos = -radius
        y_pos = 0
        err = 2 - 2 * radius
        if (x >= self.width or y >= self.height):
            return
        while True:
            self.set_pixel(frame_buffer, x - x_pos, y + y_pos, tinted)
            self.set_pixel(frame_buffer, x + x_pos, y + y_pos, tinted)
            self.set_pixel(frame_buffer, x + x_pos, y - y_pos, tinted)
            self.set_pixel(frame_buffer, x - x_pos, y - y_pos, tinted)
            e2 = err
            if (e2 <= y_pos):
                y_pos += 1
                err += y_pos * 2 + 1
                if(-x_pos == y_pos and e2 <= x_pos):
                    e2 = 0
            if (e2 > x_pos):
                x_pos += 1
                err += x_pos * 2 + 1
            if x_pos > 0:
                break

    def draw_filled_circle(self, frame_buffer, x, y, radius, tinted):
        # Bresenham algorithm
        x_pos = -radius
        y_pos = 0
        err = 2 - 2 * radius
        if (x >= self.width or y >= self.height):
            return
        while True:
            self.set_pixel(frame_buffer, x - x_pos, y + y_pos, tinted)
            self.set_pixel(frame_buffer, x + x_pos, y + y_pos, tinted)
            self.set_pixel(frame_buffer, x + x_pos, y - y_pos, tinted)
            self.set_pixel(frame_buffer, x - x_pos, y - y_pos, tinted)
            self.draw_horizontal_line(frame_buffer, x + x_pos, y + y_pos, 2 * (-x_pos) + 1, tinted)
            self.draw_horizontal_line(frame_buffer, x + x_pos, y - y_pos, 2 * (-x_pos) + 1, tinted)
            e2 = err
            if (e2 <= y_pos):
                y_pos += 1
                err += y_pos * 2 + 1
                if(-x_pos == y_pos and e2 <= x_pos):
                    e2 = 0
            if (e2 > x_pos):
                x_pos  += 1
                err += x_pos * 2 + 1
            if x_pos > 0:
                break
