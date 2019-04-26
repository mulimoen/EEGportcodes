# EEGportcodes

This program gives the user the possibility of sending trigger codes (portcodes) to to an EEG machine. This can be used in conjunction with for example BrainProducts EEG.


## Background
An EEG (Electroencephalogram) experiment often consists of two machines, a display computer and an EEG recorder, separated for latency reasons. The display computer must communicate with the EEG recorder to synchronise stimulus presentation and trigger codes. This communication can be done over the parallel port, which modern machines are not usually equpped with. The parallel port can be emulated over a serial port, and this program treats the serial port as a parallel port, only allowing one signal (byte) at a time.


## Usage
The main program ([portcode.py](portcode.py)) can be import in a program with
```python3
import PortCodeHandler

pch = PortCodeHandler()

# Stimulus, emit code:
pch.send_portcode(2)

# Do other stuff

# Signal new stimulus
pch.send_portcode(4)

# Done sending portcodes, must close the handle
pch.close()
```
A testing program can executed by running portcode.py directly. BrainProducts EEG expects the portcodes to be powers of two, which gives 8 unique signals (1, 2, 4, 8, 16, 32, 64, 128). This will show up as triggers on the EEG recordings.


## Technical details
The program spawns a background thread to read portcodes from the caller (stimulus machine) and send over the wire to the EEG recorder. Using this background thread ensures the stimulus machine does not skip a frame, while the signal will be sent properly.

The program supports sending multiple codes simultaneously, and will multiplex them, by bitwise of of the input codes. If 0 is sent, this will act as a flush, waiting until all signals have been sent before processing new codes.
