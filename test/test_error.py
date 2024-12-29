#!/usr/bin/env python3

import unittest

import time
import serial


class ErrorTestCase(unittest.TestCase):

    print_on: bool
    canable: serial

    def setUp(self):
        # initialize
        self.print_on = False
        
        # connect to canable
        # device name should be changed
        self.canable = serial.Serial('/dev/ttyACM0', timeout=1)

        # clear buffer
        self.send(b"\r\r\r")
        self.receive()

        # reset to default status
        self.send(b"C\r")
        self.receive()


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
        timeout = 10    # sec
        for i in range(0, int(timeout / cycle)):
            time.sleep(cycle)
            tmp = self.canable.read_all()
            rx_data = rx_data + tmp
            if len(tmp) == 0:
                break

        if (self.print_on):
            self.print_slcan_data("R", rx_data)
        
        return rx_data


    def test_usb_tx_overflow(self):
        # send a lot of command without receiving data
        for i in range(0, 200):
            self.send(b"V\r")
            time.sleep(0.02)

        # recieve all reply
        rx_data = self.receive()

        # print reply
        rx_data = rx_data.replace(b"\r", b"[CR]\n")
        #print(rx_data.decode())
        
        # TODO count reply

        # check error
        self.send(b"F\r")
        # TODO
        #self.assertEqual(self.receive(), b"F08\r")
        self.assertEqual(self.receive(), b"\a")


    def test_can_tx_overflow(self):
        # check response to shortest SEND in CAN normal mode
        self.send(b"O\r")
        self.assertEqual(self.receive(), b"\r")

        # the buffer can store as least 64 messages
        for i in range(0, 64):
            self.send(b"t03F0\r")
            self.assertEqual(self.receive(), b"z\r")

        # the buffer can not store additional 64 messages
        for i in range(0, 64):
            self.send(b"t03F0\r")
            self.receive()

        # the buffer can not store anymore messages
        for i in range(0, 64):
            self.send(b"t03F0\r")
            self.assertEqual(self.receive(), b"\a")

        # check error
        self.send(b"F\r")
        # TODO
        #self.assertEqual(self.receive(), b"F08\r")
        self.assertEqual(self.receive(), b"\a")

        self.send(b"C\r")
        self.assertEqual(self.receive(), b"\r")


if __name__ == "__main__":
    unittest.main()
