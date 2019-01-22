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

import board
import digitalio
import random
import time

#from third_party.waveshare import color_epd2in13 as connected_epd
from third_party.waveshare import epd2in7 as connected_epd
#from third_party.waveshare import epd2in9 as connected_epd
#from third_party.waveshare import epd2in13 as connected_epd

try:
    # Optimized version - requires a custom CircuitPython build.
    from asm_thumb import fractal
    from asm_thumb import monobitmap
    HAVE_ASM = True
except (ImportError, SyntaxError):
    import fractal
    import monobitmap
    HAVE_ASM = False


def sample_keys():
    """Yields four bools representing the button press state on the 2.7" EPD.
    
    The 2.7 inch EPD rpi hat has four push buttons connected to RPI hat pins.

    Follow the traces to see which pins those are and wire them up to digital
    inputs D2 through D5 on your CircuitPython device.  A button press grounds
    the pin.

    This function samples them all and yields four bools for each button.
    """
    DigitalInOut = digitalio.DigitalInOut
    Pull = digitalio.Pull
    with DigitalInOut(board.D2) as key1, DigitalInOut(board.D3) as key2, \
            DigitalInOut(board.D4) as key3, DigitalInOut(board.D5) as key4:
        key1.switch_to_input(Pull.UP)
        key2.switch_to_input(Pull.UP)
        key3.switch_to_input(Pull.UP)
        key4.switch_to_input(Pull.UP)
        for k in (key1, key2, key3, key4):
            yield not k.value  # False is pressed


class StatusLED:
    """A simple interface to the onboard pixel."""

    def __init__(self):
        if hasattr(board, 'NEOPIXEL'):
            import neopixel
            self._led = neopixel.NeoPixel(board.NEOPIXEL, 1)
            self._led.brightness = 1/16
        elif hasattr(board, 'APA102_MOSI'):
            import adafruit_dotstar
            self._led = adafruit_dotstar.DotStar(
                board.APA102_SCK, board.APA102_MOSI, 1)
            self._led.brightness = 0.7
        else:
            self._led = [None]

    def off(self):
        self._led[0] = b'\0\0\0'

    def busy(self):
        self._led[0] = b'\x50\x10\0'

    def ready(self):
        self._led[0] = b'\x10\x50\0' if HAVE_ASM else b'\x10\0\x70'


def main():
    led = StatusLED()
    led.busy()

    epd = connected_epd.EPD()
    print("Initializing display...")
    epd.init()
    if HAVE_ASM:
      print("@micropython.asm_thumb implementation loaded.")
    else:
      print("Pure Python implementation loaded.")

    keys = [1,]  # Print message on start.
    while True:
        if any(keys):
            led.ready()
            print("Awaiting key1-key4 button press.")
        keys = list(sample_keys())
        if any(keys):
            led.busy()

        if keys[0]:
            print("Computing Mandlebrot fractal.")
            fractal_image = fractal.get_fractal(epd.width, epd.height,
                                                use_julia=False)
            print("Displaying.")
            if getattr(epd, 'colors', 2) > 2:
                epd.display_frames(None, fractal_image.bit_buf)
            else:
                epd.display_bitmap(fractal_image, fast_ghosting=True)
            del fractal_image
        elif keys[1]:
            print("Setting display to white.")
            epd.clear_frame_memory(0xff)
            epd.display_frame()
        elif keys[2]:
            raw_framebuf = bytearray(epd.fb_bytes)
            for pos in range(len(raw_framebuf)):
                raw_framebuf[pos] = random.randint(0, 256)
            print("Displaying random framebuf.")
            if getattr(epd, 'colors', 2) <= 2:
                epd.display_frame_buf(raw_framebuf, fast_ghosting=True)
            else:
                raw_framebuf2 = bytearray(epd.fb_bytes)
                for pos in range(len(raw_framebuf2)):
                    raw_framebuf2[pos] = random.randint(0, 256)
                epd.display_frames(raw_framebuf, raw_framebuf2)
                del raw_framebuf2
            del raw_framebuf
        elif keys[3]:
            print("Computing Julia fractal.")
            fractal_image = fractal.get_fractal(epd.width, epd.height,
                                                use_julia=True)
            print("Displaying.")
            if getattr(epd, 'colors', 2) > 2:
                epd.display_frames(fractal_image.bit_buf, None)
            else:
                epd.display_bitmap(fractal_image, fast_ghosting=True)
            del fractal_image
        else:
            # This effectively debounces the keys, we merely sample them
            # rather than treat a state change as an interrupt.  If a key
            # is not pressed for this duration it may not be noticed.
            time.sleep(0.05)  # short time between polling.

    print("Done.")


if __name__ == '__main__':
    main()
