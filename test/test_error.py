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
        self.canable = serial.Serial('/dev/ttyACM0', timeout=1, write_timeout=1)

        # clear buffer
        self.send(b"\r\r\r")
        self.receive()

        # reset to default status
        self.send(b"C\r")
        self.receive()
        self.send(b"S4\r")
        self.receive()
        self.send(b"Y2\r")
        self.receive()
        self.send(b"Z0\r")
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


    def test_in_all_modes(self):
        # confirm command is not active in closed mode
        self.send(b"F\r")
        self.assertEqual(self.receive(), b"\a")

        # confirm no error in normal mode
        self.send(b"O\r")
        self.assertEqual(self.receive(), b"\r")
        self.send(b"F\r")
        self.assertEqual(self.receive(), b"F00\r")
        self.send(b"C\r")
        self.assertEqual(self.receive(), b"\r")

        # confirm command is not active in closed mode
        self.send(b"F\r")
        self.assertEqual(self.receive(), b"\a")

        # confirm no error in silent mode
        self.send(b"L\r")
        self.assertEqual(self.receive(), b"\r")
        self.send(b"F\r")
        self.assertEqual(self.receive(), b"F00\r")
        self.send(b"C\r")
        self.assertEqual(self.receive(), b"\r")

        # confirm command is not active in closed mode
        self.send(b"F\r")
        self.assertEqual(self.receive(), b"\a")


    def test_usb_tx_overflow(self):
        # check response to shortest SEND in CAN normal mode
        self.send(b"O\r")
        self.assertEqual(self.receive(), b"\r")

        # confirm no error
        self.send(b"F\r")
        self.assertEqual(self.receive(), b"F00\r")

        # send a lot of command without receiving data (depends on PC env.)
        for i in range(0, 300):
            self.send(b"V\r")
            time.sleep(0.05)

        # recieve all reply
        rx_data = self.receive()
        rx_data = self.receive()    # just to make sure

        # print reply
        #rx_data = rx_data.replace(b"\r", b"[CR]\n")
        #print(rx_data.decode())
        
        # TODO count reply

        # check error
        self.send(b"F\r")
        self.assertEqual(self.receive(), b"F01\r")

        # check error clear
        self.send(b"F\r")
        self.assertEqual(self.receive(), b"F00\r")

        self.send(b"C\r")
        self.assertEqual(self.receive(), b"\r")


    def test_can_rx_overflow(self):
        # check response in CAN loopback mode
        self.send(b"=\r")
        self.assertEqual(self.receive(), b"\r")

        # confirm no error
        self.send(b"F\r")
        self.assertEqual(self.receive(), b"F00\r")

        # the buffer can store as least 400 messages (10240 / 24)
        for i in range(0, 400):
            self.send(b"t03F80011223344556677\r")
            time.sleep(0.1)    # TODO: Why does it take so long?

        # recieve all reply
        rx_data = self.receive()
        rx_data = self.receive()    # just to make sure

        # confirm no error
        self.send(b"F\r")
        self.assertEqual(self.receive(), b"F00\r")

        # the buffer can not store 800 messages (depends on PC env.)
        for i in range(0, 800):
            self.send(b"t03F80011223344556677\r")
            time.sleep(0.02)

        # recieve all reply
        rx_data = self.receive()
        rx_data = self.receive()    # just to make sure

        # check error
        self.send(b"F\r")
        self.assertEqual(self.receive(), b"F01\r")

        # check error clear
        self.send(b"F\r")
        self.assertEqual(self.receive(), b"F00\r")

        self.send(b"C\r")
        self.assertEqual(self.receive(), b"\r")


    def test_can_tx_overflow(self):
        # check response in CAN normal mode
        self.send(b"O\r")
        self.assertEqual(self.receive(), b"\r")

        # confirm no error
        self.send(b"F\r")
        self.assertEqual(self.receive(), b"F00\r")

        # the buffer can store as least 64 messages
        for i in range(0, 64):
            self.send(b"t03F0\r")
            self.assertEqual(self.receive(), b"z\r")

        # confirm no error
        self.send(b"F\r")
        self.assertEqual(self.receive(), b"F00\r")

        # the buffer can not store additional 64 messages
        for i in range(0, 64):
            self.send(b"t03F0\r")
            self.receive()

        # check error
        self.send(b"F\r")
        self.assertEqual(self.receive(), b"F02\r")

        # the buffer can not store anymore messages
        for i in range(0, 64):
            self.send(b"t03F0\r")
            self.assertEqual(self.receive(), b"\a")

        # check error
        self.send(b"F\r")
        self.assertEqual(self.receive(), b"F02\r")

        # check error clear
        self.send(b"F\r")
        self.assertEqual(self.receive(), b"F00\r")

        self.send(b"C\r")
        self.assertEqual(self.receive(), b"\r")


if __name__ == "__main__":
    unittest.main()
