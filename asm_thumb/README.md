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

# Performance Results

Using the `third_party.waveshare.epd2in7` display size (176x264) on my Adafruit
Metro M4 Express (120Mhz SAMD51J19) under CircuitPython 3.0 I observed this
Julia fractal computation performance.

## Original optimized pure Python code.

23.9 seconds

## + `_fractal_iterate()` implemented using asm.

12.4 seconds

## + `MonoBitmap.set_pixel` implemented using asm.

7.74 seconds

### + Removing the `use_julia` conditional.

7.5 seconds

## Reimplement the entire `for x in range(width)` loop using asm.

0.211 seconds

## + Fix the bug in the above code.

0.199 seconds - now that we are computing the correct thing.

## + Optimize the x-loop assembly code.

**0.156 seconds**!

Instructions and memory loads were moved outside of loops and the 14 cycle
`vsqrt` instruction was removed by rethinking our math needs.

## + Stop printing a `*` to the serial console every row

**0.140 seconds**

A full *170x faster* than the original optimized Python code.

## Couldn't we optimize more?

Yes.  The next obvious step would be to move the `for y in range(height)`
loop into assembly.  If we weren't already an order of magnitude faster
than the slow e-Paper displays this code was originally a demo for, that
might make sense.  For that purpose, we've already outdone ourselves. :)

# You Made This Look Too Easy a.k.a. How Hard Was This?

It wasn't easy!  I spent numerous multi-hour stretches on random evenings
or weekends in early 2018 weeks hammering this out.  I wasn't using git
to track my work at the time, though I saved various snapshots of my progress
which I used to recreate parts of my journey in this repository.

## Challenge: Debugging `@micropython.asm_thumb` Code

It is painful.  This code is ultimately native asm, you cannot simply do
the equivalent of `print()` debugging or even try things out in a REPL
as you can with normal Python code.  Despite its appearance to fit within
Python syntax, this really is just a weird looking subset of ARM Thumb
assembly.

In the earlier `_fractal_iterate` version of the code you may have noticed that
I made the `fast_in` array extra large and left some debugging code commented
out.  That was from a debugging effort where I had it export some internal
state so I could attempt to reason about what was or wasn't going right
internally.

## An Example bug fixed along the way

Fixed now, but I made commit 0d3efe94c84b84237c1e3193fe5746fa5c2eec7c with a
known issue in my x-loop assembly code.  Can you spot it?  If so, you must have
the ARM Thumb architecture reference manual memorized.  :P  It took me a very
long time to debug that one.  I only noticed it when I started playing with a
newly acquired epd2in9 display which made me actually look closely at what was
on the screen...  One row of pixels at the edge was simply wrong.  Look at
the diff to see why.  I spent many hours over many days puzzling over that.

# Future Optimization Work

MicroPython has other intermediate optimization levels available that
do not entail writing native assembly code.  I want to get a CircuitPython
build working with those enabled and explore their performance.

# Caveats

Writing native assembly is instructive (pun intended!) but extremely difficult
to maintain.  Do it to learn, but it should always be a last resort.
