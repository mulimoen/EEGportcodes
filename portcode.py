from __future__ import print_function
import serial
import sys
import time


class PortCodeHandler:
    """
    PortCodeHandler sends bits over the wire, allowing portcodes to be sent
    from the display computer to the recording computer for EEG trials.

    Author: Magnus Ulimoen
    """

    def __init__(self, portname="COM3", emulate_on_fail=True):
        """
        :param portname: Portname to be opened

        :param emulate_on_fail: Whether to fail or emulate if portname
        can not be opened

        If portname can not be opened, the portcodes will be emulated
        by printing to stdout.
        """

        if not emulate_on_fail:
            self.ser = serial.Serial(portname)
            return

        try:
            self.ser = serial.Serial(portname)
        except serial.serialutil.SerialException:
            print("Could not open device {}".format(portname) + "\n"
                  "No portcodes will be sent, but they will" +
                  "be emulated on stdout", file=sys.stderr)
            self.ser = None

    def close(self):
        """
        Closes the serial port
        """
        if self.ser is not None:
            self.ser.close()

    def send_portcode(self, code):
        """
        :param code: integer with the combination of bits

        The bits will be sent over the wire. The usual would be to
        send a power of two for a single bit
        code = (0, 1, 2, 4, 8, 16, 32, 64, 128)

        The bits will be reset back to 0 as soon as possible,
        as the EEG uses triggers. This methods assumes the EEG
        is placed in TRIGGER HIGH mode.
        """
        code = int(code)
        if self.ser is None:
            print("PORTCODE EMULATED, code is: {}".format([code]))
            return
        self.ser.write(bytearray([code]))
        self.ser.flush()
        self.clear()

    def clear(self):
        """
        Clears all bits on the wire
        """

        if self.ser is None:
            return
        self.ser.write(bytearray([0]))
        self.ser.flush()
        time.sleep(0.01)  # Waiting 10 ms to properly synchronise with other


if __name__ == "__main__":
    print(help(PortCodeHandler))
