#!/usr/bin/env python3

import unittest

import time
import serial

# NOTE: This test needs to be done with CAN high and low shorted
class ShortTestCase(unittest.TestCase):

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
        self.send(b"W2\r")
        self.receive()
        self.send(b"M00000000\r")
        self.receive()
        self.send(b"mFFFFFFFF\r")
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


    def test_short(self):
        self.print_on = True
        # ensure no error counter
        self.send(b"C\r")
        self.receive()
        self.send(b"=\r")
        self.assertEqual(self.receive(), b"\r")
        #self.print_on = False
        #for idx in range(0, 200):
        #    self.send(b"t0000\r")
        #    self.assertEqual(self.receive(), b"z\rt0000\r")
        #self.print_on = True

        # check no error
        self.send(b"F\r")
        self.assertEqual(self.receive(), b"F00\r")
        self.send(b"f\r")
        self.assertEqual(self.receive(), b"f00000000\r")

        # check bus off
        self.send(b"C\r")
        self.assertEqual(self.receive(), b"\r")
        self.send(b"O\r")
        self.assertEqual(self.receive(), b"\r")
        self.send(b"F\r")
        self.assertEqual(self.receive(), b"F00\r")
        self.send(b"f\r")
        self.assertEqual(self.receive(), b"f00000000\r")
        self.send(b"t0000\r")
        self.assertEqual(self.receive(), b"z\r")
        time.sleep(0.2)     # wait for error passive ( > 1ms * 128)
        self.send(b"F\r")
        self.assertEqual(self.receive(), b"F00\r")
        self.send(b"f\r")
        self.assertEqual(self.receive(), b"f0003F800\r")    # one more error (+8) will cause overflow
        time.sleep(0.2)
        self.send(b"F\r")
        self.assertEqual(self.receive(), b"F00\r")
        self.send(b"f\r")
        self.assertEqual(self.receive(), b"f0003F800\r")    # no self reset
        self.send(b"t0000\r")
        self.assertEqual(self.receive(), b"z\r")
        self.send(b"C\r")
        self.assertEqual(self.receive(), b"\r")


if __name__ == "__main__":
    unittest.main()
