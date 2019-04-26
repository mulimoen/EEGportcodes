#! /usr/bin/env python3
import serial
import sys
import time
import queue
import threading
from collections import namedtuple


class PortCodeHandler:
    """
    PortCodeHandler sends bits over the wire, allowing portcodes to be sent
    from the display computer to the recording computer for EEG trials.

    To prevent locking the computer for synchronisation to take place,
    a worker thread is spawned to handle the portcodes.

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

        self.queue = queue.Queue(maxsize=10)

        if not emulate_on_fail:
            self.ser = serial.Serial(portname)
            self.worker = PortCodePinger(self.queue, self.ser)
            self.worker.start()
            return

        try:
            self.ser = serial.Serial(portname)
        except serial.serialutil.SerialException:
            print("Could not open device {}".format(portname) + "\n"
                  "No portcodes will be sent, but they will" +
                  " be emulated on stdout", file=sys.stderr)
            self.ser = None

        self.queue = queue.Queue(maxsize=10)
        self.worker = PortCodePinger(self.queue, self.ser)
        self.worker.start()

    def close(self):
        """
        Closes the handler
        """
        self.queue.put_nowait("quit")
        self.worker.join()
        if self.ser is not None:
            self.ser.close()

    def send_portcode(self, code):
        """
        :param code: integer with the combination of bits

        The bits will be sent over the wire. The usual would be to
        send a power of two for a single bit
        code = (1, 2, 4, 8, 16, 32, 64, 128)
        Send 0 to reset the portcodes

        The bits will be reset back to 0 as soon as possible,
        as the EEG uses triggers. This methods assumes the EEG
        is placed in TRIGGER HIGH mode.
        """
        code = int(code)
        if not 0 <= code <= 255:
            self.close()
            raise ValueError("Code must be within 0 <= code <= 255")
        self.queue.put_nowait(code)

    def clear(self):
        """
        Clears all bits on the wire
        """

        self.queue.put_nowait(0)


class PortCodePinger(threading.Thread):
    def __init__(self, queue, ser):
        threading.Thread.__init__(self)
        self.queue = queue
        self.ser = ser
        self.SYNC_TIME = 0.01  # [s]

    def run(self):
        BitSet = namedtuple("BitSet", ["time_started", "code"])
        current_codes = []

        def get_code(current_codes):
            num = 0
            for i in current_codes:
                num |= i.code
            return num

        def send_code(code):
            if self.ser is not None:
                self.ser.write(bytearray([code]))
                self.ser.flush()
            else:
                print("PORTCODE EMULATE, code is [{0:3}/{0:08b}]".format(code))

        def update_codes(current_codes):
            """ Must be called after send_codes """
            timenow = time.monotonic()
            new_codes = []
            for i in current_codes:
                if i.time_started is None:  # First time code was sent
                    new_codes.append(BitSet(time.monotonic(), i.code))
                    continue
                dt = timenow - i.time_started
                if (dt < self.SYNC_TIME):
                    new_codes.append(i)
            current_codes[:] = new_codes

        def flush(current_codes):
            while len(current_codes) > 0:
                # Waiting until all codes has been transmitted,
                # reset signals don't matter (only rising edge)
                update_codes(current_codes)

            if self.ser is not None:
                self.ser.write(bytearray([0]))
                self.ser.flush()
                time.sleep(self.SYNC_TIME)

        flush(current_codes)
        current_code = 0
        print("Initialized worker thread")

        while True:
            if len(current_codes) == 0:
                # No signal on the wire, can wait until new signal
                task = self.queue.get()
            else:  # Signal needs to be flushed, only check for new
                if self.queue.empty():
                    task = None
                else:
                    task = self.queue.get_nowait()
            if task is not None:
                if task == "quit":
                    flush(current_codes)
                    return
                if task == 0:
                    flush(current_codes)
                    new_code = 0
                code = task
                current_codes.append(BitSet(None, code))

            new_code = get_code(current_codes)
            if new_code != current_code:
                send_code(new_code)
                current_code = new_code
            update_codes(current_codes)


def test_portcodes():
    handle = PortCodeHandler()

    handle.send_portcode(1)
    time.sleep(0.5)
    handle.send_portcode(4)
    handle.send_portcode(8)
    time.sleep(0.5)
    handle.send_portcode(1)
    time.sleep(0.5)
    handle.send_portcode(255)
    time.sleep(0.5)
    handle.send_portcode(2)
    handle.close()


if __name__ == "__main__":
    test_portcodes()
