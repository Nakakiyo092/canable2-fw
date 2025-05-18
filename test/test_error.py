#!/usr/bin/env python3

import unittest

import time
from device_under_test import DeviceUnderTest


class ErrorTestCase(unittest.TestCase):

    print_on: bool
    dut: DeviceUnderTest

    def setUp(self):
        self.dut = DeviceUnderTest()
        self.dut.open()
        self.dut.setup()


    def tearDown(self):
        # close serial
        self.dut.close()


    def test_error_passive(self):
        #self.dut.print_on = True
        self.dut.send(b"=\r")
        self.assertEqual(self.dut.receive(), b"\r")

        # check no error
        self.dut.send(b"F\r")
        self.assertEqual(self.dut.receive(), b"F00\r")
        self.dut.send(b"t0000\r")
        self.assertEqual(self.dut.receive(), b"z\rt0000\r")
        time.sleep(0.2)     # wait for error passive ( > 1ms * 128)
        self.dut.send(b"F\r")
        self.assertEqual(self.dut.receive(), b"F00\r")
        self.dut.send(b"C\r")
        self.assertEqual(self.dut.receive(), b"\r")

        # check error passive
        self.dut.send(b"O\r")
        self.assertEqual(self.dut.receive(), b"\r")
        self.dut.send(b"F\r")
        self.assertEqual(self.dut.receive(), b"F00\r")
        self.dut.send(b"t0000\r")
        self.assertEqual(self.dut.receive(), b"z\r")
        time.sleep(0.2)     # wait for error passive ( > 1ms * 128)
        self.dut.send(b"F\r")
        self.assertEqual(self.dut.receive(), b"FA4\r")  # BEI & EPI & EI
        self.dut.send(b"F\r")
        self.assertEqual(self.dut.receive(), b"F00\r")  # Check cleared
        self.dut.send(b"C\r")
        self.assertEqual(self.dut.receive(), b"\r")


    def test_cdc_tx_overflow(self):
        # check response to shortest SEND in CAN normal mode
        self.dut.send(b"O\r")
        self.assertEqual(self.dut.receive(), b"\r")

        # confirm no error
        self.dut.send(b"F\r")
        self.assertEqual(self.dut.receive(), b"F00\r")

        # send a lot of command without receiving data (amount depends on PC env.)
        for i in range(0, 400):
            self.dut.send(b"v\r")
            time.sleep(0.001)

        # recieve all reply
        rx_data = self.dut.receive()

        # check error
        self.dut.send(b"F\r")
        self.assertEqual(self.dut.receive(), b"F01\r")  # CAN Rx Full (because this overflow is caused typically by too many can frame)

        # check error clear
        self.dut.send(b"F\r")
        self.assertEqual(self.dut.receive(), b"F00\r")

        self.dut.send(b"C\r")
        self.assertEqual(self.dut.receive(), b"\r")


    def test_can_rx_overflow(self):
        # check response in CAN loopback mode
        self.dut.send(b"=\r")
        self.assertEqual(self.dut.receive(), b"\r")

        # confirm no error
        self.dut.send(b"F\r")
        self.assertEqual(self.dut.receive(), b"F00\r")

        # the buffer can store as least 180 messages (4096 / 24)
        for i in range(0, 180):
            self.dut.send(b"t03F80011223344556677\r")
            time.sleep(0.001)

        # recieve all reply
        rx_data = self.dut.receive()
        rx_data = self.dut.receive()    # just to make sure

        # confirm no error
        self.dut.send(b"F\r")
        self.assertEqual(self.dut.receive(), b"F00\r")

        # the buffer can not store 800 messages (amount depends on PC env.)
        for i in range(0, 800):
            self.dut.send(b"t03F80011223344556677\r")
            time.sleep(0.001)

        # recieve all reply
        rx_data = self.dut.receive()
        rx_data = self.dut.receive()    # just to make sure

        # check error
        self.dut.send(b"F\r")
        self.assertEqual(self.dut.receive(), b"F01\r")  # CAN Rx Full

        # check error clear
        self.dut.send(b"F\r")
        self.assertEqual(self.dut.receive(), b"F00\r")

        self.dut.send(b"C\r")
        self.assertEqual(self.dut.receive(), b"\r")


    def test_can_tx_overflow(self):
        # check response in CAN normal mode
        self.dut.send(b"O\r")
        self.assertEqual(self.dut.receive(), b"\r")

        # confirm no error
        self.dut.send(b"F\r")
        self.assertEqual(self.dut.receive(), b"F00\r")

        # the buffer can store as least 64 messages
        for i in range(0, 64):
            self.dut.send(b"t03F0\r")
            self.assertEqual(self.dut.receive(), b"z\r")

        # confirm no overflow
        self.dut.send(b"F\r")
        self.assertEqual(self.dut.receive(), b"FA4\r")  # BEI & EPI & EI

        # the buffer can not store additional 64 messages
        for i in range(0, 64):
            self.dut.send(b"t03F0\r")
            self.dut.receive()

        # check error
        self.dut.send(b"F\r")
        self.assertEqual(self.dut.receive(), b"F02\r")  # CAN Tx Full

        # the buffer can not store anymore messages
        for i in range(0, 64):
            self.dut.send(b"t03F0\r")
            self.assertEqual(self.dut.receive(), b"\a")

        # check error
        self.dut.send(b"F\r")
        self.assertEqual(self.dut.receive(), b"F02\r")

        # check error clear
        self.dut.send(b"F\r")
        self.assertEqual(self.dut.receive(), b"F00\r")

        self.dut.send(b"C\r")
        self.assertEqual(self.dut.receive(), b"\r")


if __name__ == "__main__":
    unittest.main()
