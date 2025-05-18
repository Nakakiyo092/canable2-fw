#!/usr/bin/env python3

import unittest

import time
from device_under_test import DeviceUnderTest


class LoopbackTestCase(unittest.TestCase):

    print_on: bool
    dut: DeviceUnderTest

    def setUp(self):
        self.dut = DeviceUnderTest()
        self.dut.open()
        self.dut.setup()


    def tearDown(self):
        # close serial
        self.dut.close()


    def test_setup(self):
        # check response to shortest SEND in CAN loopback mode
        self.dut.send(b"NA123\r")
        self.assertEqual(self.dut.receive(), b"\r")

        self.dut.send(b"z1011\r")
        self.assertEqual(self.dut.receive(), b"\r")

        self.dut.send(b"M0000003F\r")
        self.assertEqual(self.dut.receive(), b"\r")
        self.dut.send(b"mFFFFF800\r")
        self.assertEqual(self.dut.receive(), b"\r")

        self.dut.send(b"O\r")
        self.assertEqual(self.dut.receive(), b"\r")

        self.dut.send(b"Q1\r")
        self.assertEqual(self.dut.receive(), b"\r")

        self.dut.send(b"C\r")
        self.assertEqual(self.dut.receive(), b"\r")

        # update setting in RAM
        self.dut.send(b"z0000\r")
        self.assertEqual(self.dut.receive(), b"\r")

        self.dut.send(b"M00000000\r")
        self.assertEqual(self.dut.receive(), b"\r")
        self.dut.send(b"mFFFFFFFF\r")
        self.assertEqual(self.dut.receive(), b"\r")


if __name__ == "__main__":
    unittest.main()
