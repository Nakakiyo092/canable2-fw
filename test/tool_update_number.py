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

        if (self.dut.print_on):
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

        if (self.dut.print_on):
            self.print_slcan_data("R", rx_data)
        
        return rx_data


    def test_N_command(self):
        self.dut.print_on = True
        # Check response to N
        self.dut.send(b"N\r")
        rx_data = self.dut.receive()
        #self.assertGreaterEqual(len(rx_data), len(b"NA123\r"))
        #self.assertEqual(rx_data[0], b"NA123\r"[0])

        # Update serial number
        self.dut.send(b"NAB01\r")
        time.sleep(0.1)         # Extra wait for flash update
        self.assertEqual(self.dut.receive(), b"\r")

        # Check serial number after reset


if __name__ == "__main__":
    unittest.main()
