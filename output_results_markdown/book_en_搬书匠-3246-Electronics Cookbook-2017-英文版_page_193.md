![Circuit diagram showing high-side switching using an NPN BJT (Q1) driving a PNP BJT (Q2). The GPIO pin connects to the base of Q1 through resistor R1. Q1's emitter is connected to GND. Q1's collector connects to the base of Q2 through resistor R2. Q2's emitter is connected to +V. Q2's collector is connected to the LOAD, which is connected to GND.]()![](_page_0_Picture_0.jpeg)

Figure 11-4. High-side Switching with an NPN BJT Driving a PNP BJT

Low-side switching (Recipe 11.1) is the most common and simplest arrangement, and unless you have a good reason such as the need for one end of the load to be connected to ground, you should use low-side switching.

## See Also

For a discussion of NPN and PNP bipolar transistors, see Recipe 5.1.

GPIO ports and their output logic are described in Recipe 10.7.

You will find an example of switching with a transistor using an Arduino in Recipe 11.6 and for a Raspberry Pi in Recipe 11.7.

For switching using a MOSFET, see Recipe 11.3.

## 11.3 Switch Much More Power

### Problem

You want to allow a GPIO pin to control more power than it otherwise could, but a BJT isn't enough.

### Solution

You can use a MOSFET as an electronic switch. Use the transistor in a *common-source* arrangement. Figure 11-5 shows the schematic for this circuit. Along with Recipe 11.1, you will find yourself using this circuit a lot.

This type of switching is called “low-side” switching because the transistor acts as a switch between the low voltage of GND and the load.

If the GPIO pin is high (3.3V or 5V) and exceeds the gate-threshold voltage of the MOSFET, the MOSFET will turn on, allowing current to flow from +V through the load to GND.