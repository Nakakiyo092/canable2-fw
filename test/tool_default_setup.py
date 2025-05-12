#!/usr/bin/env python3

import unittest

import time
from device_under_test import DeviceUnderTest


class SlcanTestCase(unittest.TestCase):

    print_on: bool
    dut: DeviceUnderTest

    def setUp(self):
        self.dut = DeviceUnderTest()
        self.dut.open()
        self.dut.setup()


    def tearDown(self):
        # close serial
        self.dut.close()
        

    def test_Q_command(self):
        #self.dut.print_on = True

        # Bit rate
        self.dut.send(b"S4\r")
        self.assertEqual(self.dut.receive(), b"\r")
        self.dut.send(b"Y2\r")
        self.assertEqual(self.dut.receive(), b"\r")

        # Timestamp
        self.dut.send(b"Z0\r")
        self.assertEqual(self.dut.receive(), b"\r")

        # Filter
        self.dut.send(b"W2\r")
        self.assertEqual(self.dut.receive(), b"\r")

        self.dut.send(b"M00000000\r")
        self.assertEqual(self.dut.receive(), b"\r")

        self.dut.send(b"mFFFFFFFF\r")       # mFFFFFFFF -> Pass all
        self.assertEqual(self.dut.receive(), b"\r")

        # Open port
        self.dut.send(b"O\r")
        self.assertEqual(self.dut.receive(), b"\r")

        # Mode
        self.dut.send(b"Q0\r")
        self.assertEqual(self.dut.receive(), b"\r")

        # Close port
        self.dut.send(b"C\r")
        self.assertEqual(self.dut.receive(), b"\r")


    def test_N_command(self):
        #self.dut.print_on = True

        # Check response to N
        self.dut.send(b"N\r")
        rx_data = self.dut.receive()

        # Update serial number
        self.dut.send(b"NAB01\r")
        time.sleep(0.1)         # Extra wait for flash update
        self.assertEqual(self.dut.receive(), b"\r")


if __name__ == "__main__":
    unittest.main()
