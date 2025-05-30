#!/usr/bin/env python3

import unittest

import time
from device_under_test import DeviceUnderTest


# NOTE: This test needs to be done with CAN high and low shorted.
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


    def test_short(self):
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

        # check bus off
        self.dut.send(b"O\r")
        self.assertEqual(self.dut.receive(), b"\r")
        self.dut.send(b"F\r")
        self.assertEqual(self.dut.receive(), b"F00\r")
        self.dut.send(b"f\r")
        self.assertEqual(self.dut.receive(), b"f: node_sts=ER_ACTV, last_err_code=NONE, err_cnt_tx_rx=[0x00, 0x00], est_bus_load_percent=00\r")
        self.dut.send(b"t0000\r")
        self.assertEqual(self.dut.receive(), b"z\r")
        time.sleep(0.1)     # wait for bus off ( > 1ms * 255 / 8)
        self.dut.send(b"F\r")
        self.assertEqual(self.dut.receive(), b"FA4\r")  # BEI + EPI + EI
        time.sleep(0.1)
        self.dut.send(b"F\r")
        self.assertEqual(self.dut.receive(), b"F00\r")  # check clear
        self.dut.send(b"f\r")
        self.assertEqual(self.dut.receive(), b"f: node_sts=BUS_OFF, last_err_code=BIT0, err_cnt_tx_rx=[0xF8, 0x00], est_bus_load_percent=00\r")

        # cannot send frame during bus off
        for cmd in cmd_send_std:
            self.dut.send(cmd + b"03F0\r")
            self.assertEqual(self.dut.receive(), b"\a")
        for cmd in cmd_send_ext:
            self.dut.send(cmd + b"0137FEC80\r")
            self.assertEqual(self.dut.receive(), b"\a")

        self.dut.send(b"C\r")
        self.assertEqual(self.dut.receive(), b"\r")

        self.dut.send(b"=\r")
        self.assertEqual(self.dut.receive(), b"\r")
        
        # check recovering from bus off
        for cmd in cmd_send_std:
            self.dut.send(cmd + b"03F0\r")
            self.assertEqual(self.dut.receive(), b"z\r" + cmd + b"03F0\r")
        for cmd in cmd_send_ext:
            self.dut.send(cmd + b"0137FEC80\r")
            self.assertEqual(self.dut.receive(), b"Z\r" + cmd + b"0137FEC80\r")

        self.dut.send(b"C\r")
        self.assertEqual(self.dut.receive(), b"\r")


    def test_error_bus_off_only(self):
        #self.dut.print_on = True
        self.dut.send(b"-0\r")  # Disable auto retransmission
        self.assertEqual(self.dut.receive(), b"\r")
        self.dut.send(b"O\r")
        self.assertEqual(self.dut.receive(), b"\r")
        self.dut.send(b"F\r")
        self.assertEqual(self.dut.receive(), b"F00\r")
        self.dut.send(b"f\r")
        self.assertEqual(self.dut.receive(), b"f: node_sts=ER_ACTV, last_err_code=NONE, err_cnt_tx_rx=[0x00, 0x00], est_bus_load_percent=00\r")

        # One BIT0 error makes error passive event from REC = 0.
        # Not sure if this behavior of HAL is intensional.
        # TODO; Need to check data sheet

        for i in range(0, 1):
            self.dut.send(b"t0000\r")
            self.assertEqual(self.dut.receive(), b"z\r")
        time.sleep(0.2)     # wait for a while ( > 1ms * 1)
        self.dut.send(b"F\r")
        self.assertEqual(self.dut.receive(), b"FA4\r")  # BEI + EPI + EI
        self.dut.send(b"F\r")
        self.assertEqual(self.dut.receive(), b"F00\r")  # check error clear
        self.dut.send(b"f\r")
        self.assertEqual(self.dut.receive(), b"f: node_sts=ER_PSSV, last_err_code=BIT0, err_cnt_tx_rx=[0x88, 0x00], est_bus_load_percent=00\r")

        for i in range(0, 14):
            self.dut.send(b"t0000\r")
            self.assertEqual(self.dut.receive(), b"z\r")
        time.sleep(0.2)     # wait for a while ( > 1ms * 14)
        self.dut.send(b"F\r")
        self.assertEqual(self.dut.receive(), b"F80\r")
        self.dut.send(b"F\r")
        self.assertEqual(self.dut.receive(), b"F00\r")  # check error clear
        self.dut.send(b"f\r")
        self.assertEqual(self.dut.receive(), b"f: node_sts=ER_PSSV, last_err_code=BIT0, err_cnt_tx_rx=[0xF8, 0x00], est_bus_load_percent=00\r")

        for i in range(0, 1):
            self.dut.send(b"t0000\r")
            self.assertEqual(self.dut.receive(), b"z\r")
        time.sleep(0.2)     # wait for a while ( > 1ms * 1)
        self.dut.send(b"F\r")
        self.assertEqual(self.dut.receive(), b"F84\r")  # BEI + EI  bus off transition creates error warning. same as SJA1000
        self.dut.send(b"F\r")
        self.assertEqual(self.dut.receive(), b"F00\r")  # check error clear
        self.dut.send(b"f\r")
        self.assertEqual(self.dut.receive(), b"f: node_sts=BUS_OFF, last_err_code=BIT0, err_cnt_tx_rx=[0xF8, 0x00], est_bus_load_percent=00\r")

        self.dut.send(b"C\r")
        self.assertEqual(self.dut.receive(), b"\r")
        self.dut.send(b"-1\r")  # Enable auto retransmission
        self.assertEqual(self.dut.receive(), b"\r")
        

if __name__ == "__main__":
    unittest.main()
