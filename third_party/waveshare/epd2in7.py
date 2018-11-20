# ported to CircuitPython 3.0.0-beta0 by Gregory P. Smith

##
 #  @filename   :   epd2in7.py
 #  @brief      :   Implements for e-paper library
 #  @author     :   Yehui from Waveshare
 #
 #  Copyright (C) Waveshare     July 31 2017
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

# EPD2IN7 commands
PANEL_SETTING                               = 0x00
POWER_SETTING                               = 0x01
POWER_OFF                                   = 0x02
POWER_OFF_SEQUENCE_SETTING                  = 0x03
POWER_ON                                    = 0x04
POWER_ON_MEASURE                            = 0x05
BOOSTER_SOFT_START                          = 0x06
DEEP_SLEEP                                  = 0x07
DATA_START_TRANSMISSION_1                   = 0x10  # NOTE: B&W data according to datasheet
DATA_STOP                                   = 0x11
DISPLAY_REFRESH                             = 0x12
DATA_START_TRANSMISSION_2                   = 0x13  # NOTE: Red Data according to datasheet
PARTIAL_DATA_START_TRANSMISSION_1           = 0x14
PARTIAL_DATA_START_TRANSMISSION_2           = 0x15
PARTIAL_DISPLAY_REFRESH                     = 0x16
LUT_FOR_VCOM                                = 0x20
LUT_WHITE_TO_WHITE                          = 0x21
LUT_BLACK_TO_WHITE                          = 0x22
LUT_WHITE_TO_BLACK                          = 0x23
LUT_BLACK_TO_BLACK                          = 0x24
PLL_CONTROL                                 = 0x30
TEMPERATURE_SENSOR_COMMAND                  = 0x40
TEMPERATURE_SENSOR_CALIBRATION              = 0x41
TEMPERATURE_SENSOR_WRITE                    = 0x42
TEMPERATURE_SENSOR_READ                     = 0x43
VCOM_AND_DATA_INTERVAL_SETTING              = 0x50
LOW_POWER_DETECTION                         = 0x51
TCON_SETTING                                = 0x60
TCON_RESOLUTION                             = 0x61
SOURCE_AND_GATE_START_SETTING               = 0x62
GET_STATUS                                  = 0x71
AUTO_MEASURE_VCOM                           = 0x80
VCOM_VALUE                                  = 0x81
VCM_DC_SETTING_REGISTER                     = 0x82
PROGRAM_MODE                                = 0xA0
ACTIVE_PROGRAM                              = 0xA1
READ_OTP_DATA                               = 0xA2

class EPD:
    width = 176
    height = 264

    def __init__(self):
        self.reset_pin = None
        self.dc_pin = None
        self.busy_pin = None

    # TODO convert to raw bytes literals to save space / mem / import time
    lut_vcom_dc = bytes((
        0x00, 0x00,
        0x00, 0x0F, 0x0F, 0x00, 0x00, 0x05,
        0x00, 0x32, 0x32, 0x00, 0x00, 0x02,
        0x00, 0x0F, 0x0F, 0x00, 0x00, 0x05,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    ))

    # R21H
    lut_ww = bytes((
        0x50, 0x0F, 0x0F, 0x00, 0x00, 0x05,
        0x60, 0x32, 0x32, 0x00, 0x00, 0x02,
        0xA0, 0x0F, 0x0F, 0x00, 0x00, 0x05,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    ))

    # R22H    r
    lut_bw = bytes((
        0x50, 0x0F, 0x0F, 0x00, 0x00, 0x05,
        0x60, 0x32, 0x32, 0x00, 0x00, 0x02,
        0xA0, 0x0F, 0x0F, 0x00, 0x00, 0x05,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    ))

    # R24H    b
    lut_bb = bytes((
        0xA0, 0x0F, 0x0F, 0x00, 0x00, 0x05,
        0x60, 0x32, 0x32, 0x00, 0x00, 0x02,
        0x50, 0x0F, 0x0F, 0x00, 0x00, 0x05,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    ))

    # R23H    w
    lut_wb = bytes((
        0xA0, 0x0F, 0x0F, 0x00, 0x00, 0x05,
        0x60, 0x32, 0x32, 0x00, 0x00, 0x02,
        0x50, 0x0F, 0x0F, 0x00, 0x00, 0x05,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    ))


    def delay_ms(self, ms):
        time.sleep(ms / 1000.)

    def send_command(self, command):
        self.dc_pin.value = 0
        epdif.spi_transfer(command.to_bytes(1, 'big'))

    def send_data(self, data):
        self.dc_pin.value = 1
        if isinstance(data, int):
            epdif.spi_transfer(data.to_bytes(1, 'big'))
        else:
            # The EPD appears to want CS to cycle between every byte
            # so we loop doing one byte transfers.  Not efficient, but
            # it makes it work.
            for i in range(len(data)):
                epdif.spi_transfer(data[i:i+1])

    @property
    def fb_bytes(self):
        return self.width * self.height // 8

    def init(self):
        try:
            epdif.epd_io_bus_init()
        except RuntimeError:
            pass  # it avoids global io bus reinitialization.  good.
        self.reset_pin = epdif.RST_PIN
        self.dc_pin = epdif.DC_PIN
        self.busy_pin = epdif.BUSY_PIN
        # EPD hardware init start
        self.reset()
        self.send_command(POWER_SETTING)
        self.send_data(0x03)                  # VDS_EN, VDG_EN
        self.send_data(0x00)                  # VCOM_HV, VGHL_LV[1], VGHL_LV[0]
        self.send_data(0x2b)                  # VDH
        self.send_data(0x2b)                  # VDL
        self.send_data(0x09)                  # VDHR
        self.send_command(BOOSTER_SOFT_START)
        self.send_data(0x07)
        self.send_data(0x07)
        self.send_data(0x17)
        # Power optimization
        self.send_command(0xF8)
        self.send_data(0x60)
        self.send_data(0xA5)
        # Power optimization
        self.send_command(0xF8)
        self.send_data(0x89)
        self.send_data(0xA5)
        # Power optimization
        self.send_command(0xF8)
        self.send_data(0x90)
        self.send_data(0x00)
        # Power optimization
        self.send_command(0xF8)
        self.send_data(0x93)
        self.send_data(0x2A)
        # Power optimization
        self.send_command(0xF8)
        self.send_data(0xA0)
        self.send_data(0xA5)
        # Power optimization
        self.send_command(0xF8)
        self.send_data(0xA1)
        self.send_data(0x00)
        # Power optimization
        self.send_command(0xF8)
        self.send_data(0x73)
        self.send_data(0x41)
        self.send_command(PARTIAL_DISPLAY_REFRESH)
        self.send_data(0x00)
        self.send_command(POWER_ON)
        self.wait_until_idle()

        self.send_command(PANEL_SETTING)
        self.send_data(0xAF)        # KW-BF   KWR-AF    BWROTP 0f
        self.send_command(PLL_CONTROL)
        self.send_data(0x3A)        # 3A 100HZ   29 150Hz 39 200HZ    31 171HZ
        self.send_command(VCM_DC_SETTING_REGISTER)
        self.send_data(0x12)
        self.delay_ms(2)
        self.set_lut()
        # EPD hardware init end

    def wait_until_idle(self):
        while self.busy_pin.value == 0:      # 0: busy, 1: idle
            self.delay_ms(10)

    def reset(self):
        self.reset_pin.value = 0         # module reset
        self.delay_ms(200)
        self.reset_pin.value = 1
        self.delay_ms(200)

    def set_lut(self):
        assert len(self.lut_vcom_dc) == 44
        self.send_command(LUT_FOR_VCOM)               # vcom
        self.send_data(self.lut_vcom_dc)
        assert len(self.lut_ww) == 42
        self.send_command(LUT_WHITE_TO_WHITE)         # ww --
        self.send_data(self.lut_ww)
        assert len(self.lut_bw) == 42
        self.send_command(LUT_BLACK_TO_WHITE)         # bw r
        self.send_data(self.lut_bw)
        assert len(self.lut_bb) == 42
        self.send_command(LUT_WHITE_TO_BLACK)         # wb w
        self.send_data(self.lut_bb)
        assert len(self.lut_wb) == 42
        self.send_command(LUT_BLACK_TO_BLACK)         # bb b
        self.send_data(self.lut_wb)

    def clear_frame_memory(self, pattern=0xff):
        """Fill the frame memory with a pattern byte. Does not call update."""
        self.send_command(DATA_START_TRANSMISSION_2)
        self.delay_ms(2)
        row = pattern.to_bytes(1, 'big') * ((self.width + 7) // 8)
        for j in range(self.height):
            self.send_data(row)

    def display_frame(self):
        # TODO Determine if the 2.7" display can do double buffering.
        self.send_command(DISPLAY_REFRESH)
        self.wait_until_idle()

    def display_frame_buf(self, frame_buffer, fast_ghosting=None):
        """fast_ghosting ignored on the 2.7" display; it is always slow."""
        fb_bytes = self.width * self.height // 8
        assert len(frame_buffer) == fb_bytes

        # This seems to do nothing on my EPD.
        #self.send_command(DATA_START_TRANSMISSION_1)
        #self.delay_ms(2)
        #for i in range(fb_bytes):
        #    self.send_data(b'\xff')
        #self.delay_ms(2)

        # This is all that is needed on my display.
        # DATA_START_TRANSMISSION_1 seems to have no effect
        # despite a data sheet documenting it and mentioning 2
        # as being for the "Red" channel (bad datasheet...).
        self.send_command(DATA_START_TRANSMISSION_2)
        self.delay_ms(2)
        self.send_data(frame_buffer)
        self.delay_ms(2)

        self.display_frame()

    def display_bitmap(self, bitmap, fast_ghosting=False):
        """Render a MonoBitmap onto the display.

        fast_ghosting ignored on the 2.7" display; it is always slow.
        """
        self.display_frame_buf(bitmap.bit_buf, fast_ghosting=fast_ghosting)

    # After this command is transmitted, the chip would enter the deep-sleep
    # mode to save power. The deep sleep mode would return to standby by
    # hardware reset. The only one parameter is a check code, the command would
    # be executed if check code = 0xA5.
    # Use self.reset() to awaken and use self.init() to initialize.
    def sleep(self):
        self.send_command(DEEP_SLEEP)
        self.delay_ms(2)
        self.send_data(0xa5)

### END OF FILE ###
