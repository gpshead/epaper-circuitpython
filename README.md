# e-Paper Display driver code for Circuitpython with a fractal demo

An e-Paper display library for Circuitpython (a Micropython variant) with a
demo that draws a Julia or Mandlebrot fractal on the display.

# Hardware and Software Requirements

This code was written and tested on an Adafruit Metro M4 running
Circuitpython 3.0.

The e-Paper displays are the monochrome SPI varities from Waveshare.
Six digital I/O pins are required.

## Supported e-Paper Displays

* The monochrome 2.7" Waveshare e-Paper display module
(no hardware partial update support, ~6 seconds to update).
* The monochrome 2.9" Waveshare e-Paper display module (these have partial
update support and take ~1-2 seconds to update).

Based on my reading I *suspect* the interfaces for two of those cover all of
the monochrome SPI connected Waveshare display types but others have not yet
been tested.

Three color displays are not yet supported.

## Connections

This library assumes the jumper on the displays remains in 8-bit mode with a
dedicated data/command (DC) pin which is how the ones I purchased were shipped.

1. Digital input for Busy.
1. Digital output for Reset.
1. Digital output for Chip Select.
1. Digital output for SPI MOSI.
1. Digital output for SPI CLK
1. Digital output for Data / Command.

By default the `epdif` code uses the hardware SPI bus for SPI MOSI and SPI CLK.

# Licenses

Apache 2.0 for top level code.  The `third_party/` tree contains code from
other sources which carries its own licenses.  In particular the Waveshare code
has a MIT style license on it so the ported code retains that license.

# Disclaimer

This not an official Google product.
