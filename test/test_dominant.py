#!/usr/bin/env python3

import unittest

import time
from device_under_test import DeviceUnderTest


# NOTE: This test needs to be done with CAN bus fixed at dominant level.
class ShortTestCase(unittest.TestCase):

    print_on: bool
    dut: DeviceUnderTest

    def setUp(self):
        self.dut = DeviceUnderTest()
        self.dut.open()
        self.dut.setup()


    def tearDown(self):
        # close serial
        self.dut.close()


    def test_dominant(self):
        cmd_send_std = (b"r", b"t", b"d", b"b")
        cmd_send_ext = (b"R", b"T", b"D", b"B")

        #self.dut.print_on = True
        self.dut.send(b"=\r")
        self.assertEqual(self.dut.receive(), b"\r")

        # check no error
        self.dut.send(b"F\r")
        self.assertEqual(self.dut.receive(), b"F00\r")
        self.dut.send(b"f\r")
        self.assertEqual(self.dut.receive(), b"f: node_sts=ER_ACTV, last_err_code=NONE, err_cnt_tx_rx=[0x00, 0x00], est_bus_load_percent=00\r")
        self.dut.send(b"C\r")
        self.assertEqual(self.dut.receive(), b"\r")

        # check error passive
        self.dut.send(b"O\r")
        self.assertEqual(self.dut.receive(), b"\r")
        time.sleep(0.5)     # wait for error passive ( > 1ms * 128 / 1)
        self.dut.send(b"F\r")
        self.assertEqual(self.dut.receive(), b"FA4\r")  # BEI + EPI + EI
        self.dut.send(b"F\r")
        self.assertEqual(self.dut.receive(), b"F00\r")  # check error clear
        self.dut.send(b"f\r")
        self.assertEqual(self.dut.receive(), b"f: node_sts=ER_PSSV, last_err_code=FORM, err_cnt_tx_rx=[0x00, 0x80], est_bus_load_percent=00\r")

        self.dut.send(b"C\r")
        self.assertEqual(self.dut.receive(), b"\r")


if __name__ == "__main__":
    unittest.main()
