#!/usr/bin/env python3

import unittest

import time
import serial


class SlcanTestCase(unittest.TestCase):

    print_on: bool
    canable: serial

    def setUp(self):
        # initialize
        self.print_on = False
        
        # connect to canable
        # device name should be changed
        self.canable = serial.Serial('/dev/ttyACM0', timeout=1, write_timeout=1)

        # clear buffer
        self.send(b"\r\r\r")
        self.receive()

        # reset to default status
        self.send(b"C\r")
        self.receive()


    def tearDown(self):
        # close serial
        self.canable.close()


    def print_slcan_data(self, dir: chr, data: bytes):
        datar = data
        datar = datar.replace(b"\r", b"[CR]")
        datar = datar.replace(b"\a", b"[BELL]")
        if dir == "t" or dir == "T":
            print("")
            print("<<< ", datar.decode())
        else:
            print("")
            print(">>> ", datar.decode())


    def send(self, tx_data: bytes):
        self.canable.write(tx_data)

        if (self.print_on):
            self.print_slcan_data("T", tx_data)


    def receive(self) -> bytes:
        rx_data = b""
        cycle = 0.02    # sec
        timeout = 1     # sec
        for i in range(0, int(timeout / cycle)):
            time.sleep(cycle)
            tmp = self.canable.read_all()
            rx_data = rx_data + tmp
            if len(tmp) == 0 and len(rx_data) != 0:
                break

        if (self.print_on):
            self.print_slcan_data("R", rx_data)
        
        return rx_data


    def test_Q_command(self):
        self.print_on = True

        # Timestamp
        self.send(b"z1013\r")
        self.assertEqual(self.receive(), b"\r")

        # Filter
        self.send(b"W2\r")
        self.assertEqual(self.receive(), b"\r")

        self.send(b"M00000000\r")
        self.assertEqual(self.receive(), b"\r")

        self.send(b"mFFFFFFFF\r")       # mFFFFFFFF -> Pass all
        self.assertEqual(self.receive(), b"\r")

        # Open port
        self.send(b"O\r")
        self.assertEqual(self.receive(), b"\r")

        # Mode
        self.send(b"Q1\r")
        self.assertEqual(self.receive(), b"\r")

        # Close port
        self.send(b"C\r")
        self.assertEqual(self.receive(), b"\r")

        # check serial number after reset


if __name__ == "__main__":
    unittest.main()
