#!/usr/bin/env python3

import unittest

import time
from device_under_test import DeviceUnderTest


# NOTE: YOU must check LED in this test.
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


    def test_led_on(self):
        cmd_send_std = (b"r", b"t", b"d", b"b")
        cmd_send_ext = (b"R", b"T", b"D", b"B")

        # check response to shortest SEND in CAN loopback mode
        self.dut.send(b"z0000\r")
        self.assertEqual(self.dut.receive(), b"\r")
        self.dut.send(b"W2\r")
        self.assertEqual(self.dut.receive(), b"\r")
        self.dut.send(b"M00000000\r")
        self.assertEqual(self.dut.receive(), b"\r")
        self.dut.send(b"m00000000\r")       # pass 00000000x only
        self.assertEqual(self.dut.receive(), b"\r")
        self.dut.send(b"=\r")
        self.assertEqual(self.dut.receive(), b"\r")


        print("")
        print("The both LED should lit 16 times.")
        print("")

        time.sleep(2)

        for cmd in cmd_send_std:
            time.sleep(0.5)
            self.dut.send(cmd + b"03F0\r")
            self.assertEqual(self.dut.receive(), b"z\r")

        for cmd in cmd_send_ext:
            time.sleep(0.5)
            self.dut.send(cmd + b"0137FEC80\r")
            self.assertEqual(self.dut.receive(), b"Z\r")

        for cmd in cmd_send_std:
            time.sleep(0.5)
            self.dut.send(cmd + b"0000\r")
            self.assertEqual(self.dut.receive(), b"z\r")

        for cmd in cmd_send_ext:
            time.sleep(0.5)
            self.dut.send(cmd + b"000000000\r")
            self.assertEqual(self.dut.receive(), b"Z\r")

        time.sleep(2)

        self.dut.send(b"C\r")
        self.assertEqual(self.dut.receive(), b"\r")


if __name__ == "__main__":
    unittest.main()
