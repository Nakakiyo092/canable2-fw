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
        # DO NOT SETUP!


    def tearDown(self):
        # close serial
        self.dut.close()


    def test_serial(self):
        self.dut.send(b"N\r")
        self.assertEqual(self.dut.receive(), b"NA123\r")


    def test_timestamp(self):
        cmd_send_std = (b"r", b"t", b"d", b"b")
        cmd_send_ext = (b"R", b"T", b"D", b"B")

        #self.dut.print_on = True

        # check timestamp on in CAN loopback mode
        self.dut.send(b"C\r")
        self.dut.receive()
        self.dut.send(b"=\r")
        self.assertEqual(self.dut.receive(), b"\r")

        for cmd in cmd_send_std:
            self.dut.send(cmd + b"03F0\r")
            rx_data = self.dut.receive()
            if cmd == b"r" or cmd == b"t":
                self.assertEqual(len(rx_data), len(b"z\r" + cmd + b"03F0TTTT\r"))
                self.assertEqual(rx_data[:len(b"z\r" + cmd + b"03F0")], b"z\r" + cmd + b"03F0")
            else:
                self.assertEqual(len(rx_data), len(b"z\r" + cmd + b"03F0TTTTE\r"))
                self.assertEqual(rx_data[:len(b"z\r" + cmd + b"03F0")], b"z\r" + cmd + b"03F0")

        # Not work due to filter
        #for cmd in cmd_send_ext:
        #    self.dut.send(cmd + b"0137FEC80\r")
        #    rx_data = self.dut.receive()
        #    self.assertEqual(len(rx_data), len(b"Z\r" + cmd + b"0137FEC80TTTT\r"))
        #    self.assertEqual(rx_data[:len(b"Z\r" + cmd + b"0137FEC80")], b"Z\r" + cmd + b"0137FEC80")

        self.dut.send(b"C\r")
        self.assertEqual(self.dut.receive(), b"\r")


    def test_filter(self):
        cmd_send_std = (b"r", b"t", b"d", b"b")
        cmd_send_ext = (b"R", b"T", b"D", b"B")

        #self.dut.print_on = True

        #self.dut.print_on = True
        #elf.send(b"?\r")
        #self.dut.receive()
        #self.dut.print_on = False       

        # check pass 0x03F in CAN loopback mode
        self.dut.send(b"C\r")
        self.dut.receive()
        self.dut.send(b"=\r")
        self.assertEqual(self.dut.receive(), b"\r")

        for cmd in cmd_send_std:
            self.dut.send(cmd + b"03F0\r")
            rx_data = self.dut.receive()
            if cmd == b"r" or cmd == b"t":
                self.assertEqual(len(rx_data), len(b"z\r" + cmd + b"03F0TTTT\r"))
                self.assertEqual(rx_data[0:-5], b"z\r" + cmd + b"03F0")
            else:
                self.assertEqual(len(rx_data), len(b"z\r" + cmd + b"03F0TTTTE\r"))
                self.assertEqual(rx_data[0:-6], b"z\r" + cmd + b"03F0")
            self.dut.send(cmd + b"7C00\r")
            self.assertEqual(self.dut.receive(), b"z\r")
            self.dut.send(cmd + b"43F0\r")
            self.assertEqual(self.dut.receive(), b"z\r")
            self.dut.send(cmd + b"03E0\r")
            self.assertEqual(self.dut.receive(), b"z\r")

        for cmd in cmd_send_ext:
            self.dut.send(cmd + b"0000003F0\r")
            rx_data = self.dut.receive()
            if cmd == b"R" or cmd == b"T":
                self.assertEqual(len(rx_data), len(b"Z\r" + cmd + b"0000003F0TTTT\r"))
                self.assertEqual(rx_data[0:-5], b"Z\r" + cmd + b"0000003F0")
            else:
                self.assertEqual(len(rx_data), len(b"Z\r" + cmd + b"0000003F0TTTTE\r"))
                self.assertEqual(rx_data[0:-6], b"Z\r" + cmd + b"0000003F0")
            self.dut.send(cmd + b"000007C00\r")
            self.assertEqual(self.dut.receive(), b"Z\r")
            self.dut.send(cmd + b"0137FEC80\r")
            self.assertEqual(self.dut.receive(), b"Z\r")
            self.dut.send(cmd + b"1EC801370\r")
            self.assertEqual(self.dut.receive(), b"Z\r")

        self.dut.send(b"C\r")
        self.assertEqual(self.dut.receive(), b"\r")


if __name__ == "__main__":
    unittest.main()
