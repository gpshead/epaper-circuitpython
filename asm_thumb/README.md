# ARM Assembly CircuitPython Fractal Optimizations

This package is where the fun continues... when originally writing
the code, I was happy in the "Yay, it works!" sense, but wasn't
satisfied with the speed _and_ wanted to get my hands dirty with
some of the fancier Micropython features and learn some ARM assembly.

A microcontroller running at 10x-25x the clock speed of my old PCjr
should have no trouble spitting out fractals in the blink of an eye,
made even easier as the M4 has floating point hardware!
Challenge accepted, lets give it a whirl.

## Prerequisite: Build a custom CircuitPython (!)

To use any code in this subdirectory you will need to make a custom
build of CircuitPython 3 for this and flash it to your device.  My
circuitpython tree is in git repo hell at the moment but I believe the
main thing to do before building is to set `MICROPY_EMIT_INLINE_THUMB`
to `(1)` in `ports/atmel-samd/mpconfigport.h`.

With that you can build a `@micropython.asm_thumb` enabled interpreter
and install it in your M4.

TODO: Update this section with modern instructions on how to do this
build and flashing the next time I update that tree.

# Resulting Performance

Using the `third_party.waveshare.epd2in7` display size (176x264) on my Adafruit
Metro M4 Express (120Mhz SAMD51J19) under CircuitPython 3.0 I observed this
Julia fractal computation performance.

## Original optimized pure Python code

23.9 seconds

## `fractal_iterate()` implemented using `asm_thumb`

12.4 seconds

# Future work

MicroPython has other intermediate optimization levels available that
do not entail writing native assembly code.  I want to explore those.
