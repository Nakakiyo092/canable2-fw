#!/usr/bin/env python3

import unittest

import time
import serial


class LoopbackTestCase(unittest.TestCase):

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

        # DO NOT RESET!
        

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


    def test_serial(self):
        self.send(b"N\r")
        self.assertEqual(self.receive(), b"NA123\r")


    def test_timestamp(self):
        cmd_send_std = (b"r", b"t", b"d", b"b")
        cmd_send_ext = (b"R", b"T", b"D", b"B")

        #self.print_on = True

        # check timestamp on in CAN loopback mode
        self.send(b"C\r")
        self.receive()
        self.send(b"=\r")
        self.assertEqual(self.receive(), b"\r")

        for cmd in cmd_send_std:
            self.send(cmd + b"03F0\r")
            rx_data = self.receive()
            self.assertEqual(len(rx_data), len(b"z\r" + cmd + b"03F0TTTTE\r"))
            self.assertEqual(rx_data[:len(b"z\r" + cmd + b"03F0")], b"z\r" + cmd + b"03F0")

        # Not work due to filter
        #for cmd in cmd_send_ext:
        #    self.send(cmd + b"0137FEC80\r")
        #    rx_data = self.receive()
        #    self.assertEqual(len(rx_data), len(b"Z\r" + cmd + b"0137FEC80TTTT\r"))
        #    self.assertEqual(rx_data[:len(b"Z\r" + cmd + b"0137FEC80")], b"Z\r" + cmd + b"0137FEC80")

        self.send(b"C\r")
        self.assertEqual(self.receive(), b"\r")


    def test_filter(self):
        cmd_send_std = (b"r", b"t", b"d", b"b")
        cmd_send_ext = (b"R", b"T", b"D", b"B")

        #self.print_on = True

        #self.print_on = True
        #elf.send(b"?\r")
        #self.receive()
        #self.print_on = False       

        # check pass 0x03F in CAN loopback mode
        self.send(b"C\r")
        self.receive()
        self.send(b"=\r")
        self.assertEqual(self.receive(), b"\r")

        for cmd in cmd_send_std:
            self.send(cmd + b"03F0\r")
            rx_data = self.receive()
            self.assertEqual(len(rx_data), len(b"z\r" + cmd + b"03F0TTTTE\r"))
            self.assertEqual(rx_data[0:-6], b"z\r" + cmd + b"03F0")
            self.send(cmd + b"7C00\r")
            self.assertEqual(self.receive(), b"z\r")
            self.send(cmd + b"43F0\r")
            self.assertEqual(self.receive(), b"z\r")
            self.send(cmd + b"03E0\r")
            self.assertEqual(self.receive(), b"z\r")

        for cmd in cmd_send_ext:
            self.send(cmd + b"0000003F0\r")
            rx_data = self.receive()
            self.assertEqual(len(rx_data), len(b"Z\r" + cmd + b"0000003F0TTTTE\r"))
            self.assertEqual(rx_data[0:-6], b"Z\r" + cmd + b"0000003F0")
            self.send(cmd + b"000007C00\r")
            self.assertEqual(self.receive(), b"Z\r")
            self.send(cmd + b"0137FEC80\r")
            self.assertEqual(self.receive(), b"Z\r")
            self.send(cmd + b"1EC801370\r")
            self.assertEqual(self.receive(), b"Z\r")

        self.send(b"C\r")
        self.assertEqual(self.receive(), b"\r")

    # TODO: How to check bitrates?


if __name__ == "__main__":
    unittest.main()
