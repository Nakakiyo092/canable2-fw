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
        self.dut.print_on = True

        # Timestamp
        self.dut.send(b"z1013\r")
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
        self.dut.send(b"Q1\r")
        self.assertEqual(self.dut.receive(), b"\r")

        # Close port
        self.dut.send(b"C\r")
        self.assertEqual(self.dut.receive(), b"\r")

        # check serial number after reset


if __name__ == "__main__":
    unittest.main()
