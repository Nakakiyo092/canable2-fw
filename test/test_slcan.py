#!/usr/bin/env python3

import unittest

import time
import serial


class SlcanTestCase(unittest.TestCase):

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


    def test_V_command(self):
        # check response to V
        self.send(b"V\r")
        rx_data = self.receive()
        self.assertGreaterEqual(len(rx_data), len(b"V1013\r"))
        self.assertEqual(rx_data[0], b"V1013\r"[0])


    def test_N_command(self):
        #self.print_on = True
        # check response to N
        self.send(b"N\r")
        rx_data = self.receive()
        self.assertGreaterEqual(len(rx_data), len(b"NA123\r"))
        self.assertEqual(rx_data[0], b"NA123\r"[0])


    def test_blank_command(self):
        # check response to [CR]
        self.send(b"\r")
        self.assertEqual(self.receive(), b"\r")


    def test_error_command(self):
        # check response to [BELL]
        self.send(b"\a")
        self.assertEqual(self.receive(), b"")      # message incomplete without [CR]

        self.send(b"\r")
        self.assertEqual(self.receive(), b"\a")


    def test_open_close_command(self):
        # check response to C and O
        self.send(b"C\r")
        self.assertEqual(self.receive(), b"\a")
        self.send(b"O\r")
        self.assertEqual(self.receive(), b"\r")
        self.send(b"O\r")
        self.assertEqual(self.receive(), b"\a")
        self.send(b"C\r")
        self.assertEqual(self.receive(), b"\r")

        # check response to C and L
        self.send(b"C\r")
        self.assertEqual(self.receive(), b"\a")
        self.send(b"L\r")
        self.assertEqual(self.receive(), b"\r")
        self.send(b"L\r")
        self.assertEqual(self.receive(), b"\a")
        self.send(b"C\r")
        self.assertEqual(self.receive(), b"\r")

        # check response to O and L
        self.send(b"C\r")
        self.assertEqual(self.receive(), b"\a")
        self.send(b"O\r")
        self.assertEqual(self.receive(), b"\r")
        self.send(b"L\r")
        self.assertEqual(self.receive(), b"\a")
        self.send(b"C\r")
        self.assertEqual(self.receive(), b"\r")
        self.send(b"L\r")
        self.assertEqual(self.receive(), b"\r")
        self.send(b"O\r")
        self.assertEqual(self.receive(), b"\a")
        self.send(b"C\r")
        self.assertEqual(self.receive(), b"\r")


    def test_S_command(self):
        # check response to S with CAN port closed
        for idx in range(0, 10):
            cmd = "S" + str(idx) + "\r"
            self.send(cmd.encode())
            self.assertEqual(self.receive(), b"\r")

        # check response to S in CAN normal mode
        self.send(b"O\r")
        self.assertEqual(self.receive(), b"\r")

        for idx in range(0, 10):
            cmd = "S" + str(idx) + "\r"
            self.send(cmd.encode())
            self.assertEqual(self.receive(), b"\a")

        self.send(b"C\r")
        self.assertEqual(self.receive(), b"\r")

        # check response to S in CAN silent mode
        self.send(b"L\r")
        self.assertEqual(self.receive(), b"\r")

        for idx in range(0, 10):
            cmd = "S" + str(idx) + "\r"
            self.send(cmd.encode())
            self.assertEqual(self.receive(), b"\a")

        self.send(b"C\r")
        self.assertEqual(self.receive(), b"\r")

        # invalid format
        cmd = "S" + "\r"
        self.send(cmd.encode())
        self.assertEqual(self.receive(), b"\a")


    def test_Y_command(self):
        # check response to Y with CAN port closed
        for idx in range(0, 10):
            cmd = "Y" + str(idx) + "\r"
            self.send(cmd.encode())
            if idx in (0, 1, 2, 4, 5):
                self.assertEqual(self.receive(), b"\r")
            else:
                self.assertEqual(self.receive(), b"\a")

        # check response to Y in CAN normal mode
        self.send(b"O\r")
        self.assertEqual(self.receive(), b"\r")

        for idx in range(0, 10):
            cmd = "Y" + str(idx) + "\r"
            self.send(cmd.encode())
            self.assertEqual(self.receive(), b"\a")

        self.send(b"C\r")
        self.assertEqual(self.receive(), b"\r")

        # check response to Y in CAN silent mode
        self.send(b"L\r")
        self.assertEqual(self.receive(), b"\r")

        for idx in range(0, 10):
            cmd = "Y" + str(idx) + "\r"
            self.send(cmd.encode())
            self.assertEqual(self.receive(), b"\a")

        self.send(b"C\r")
        self.assertEqual(self.receive(), b"\r")

        # invalid format
        cmd = "Y" + "\r"
        self.send(cmd.encode())
        self.assertEqual(self.receive(), b"\a")


    def test_Z_command(self):
        # check response to Z with CAN port closed
        for idx in range(0, 10):
            cmd = "Z" + str(idx) + "\r"
            self.send(cmd.encode())
            if idx in (0, 1):
                self.assertEqual(self.receive(), b"\r")
            else:
                self.assertEqual(self.receive(), b"\a")

        # check response to Z in CAN normal mode
        self.send(b"O\r")
        self.assertEqual(self.receive(), b"\r")

        for idx in range(0, 10):
            cmd = "Z" + str(idx) + "\r"
            self.send(cmd.encode())
            self.assertEqual(self.receive(), b"\a")

        self.send(b"C\r")
        self.assertEqual(self.receive(), b"\r")

        # check response to Z in CAN silent mode
        self.send(b"L\r")
        self.assertEqual(self.receive(), b"\r")

        for idx in range(0, 10):
            cmd = "Z" + str(idx) + "\r"
            self.send(cmd.encode())
            self.assertEqual(self.receive(), b"\a")

        self.send(b"C\r")
        self.assertEqual(self.receive(), b"\r")

        # invalid format
        cmd = "Z" + "\r"
        self.send(cmd.encode())
        self.assertEqual(self.receive(), b"\a")


    def test_send_command(self):
        cmd_send_std = (b"r", b"t", b"d", b"b")
        cmd_send_ext = (b"R", b"T", b"D", b"B")

        # check response to SEND with CAN port closed
        for cmd in cmd_send_std:
            self.send(cmd + b"03F0\r")
            self.assertEqual(self.receive(), b"\a")

        for cmd in cmd_send_ext:
            self.send(cmd + b"0137FEC80\r")
            self.assertEqual(self.receive(), b"\a")

        # check response to shortest SEND in CAN normal mode
        self.send(b"O\r")
        self.assertEqual(self.receive(), b"\r")

        for cmd in cmd_send_std:
            self.send(cmd + b"03F0\r")
            self.assertEqual(self.receive(), b"z\r")

        for cmd in cmd_send_ext:
            self.send(cmd + b"0137FEC80\r")
            self.assertEqual(self.receive(), b"Z\r")

        self.send(b"C\r")
        self.assertEqual(self.receive(), b"\r")

        # check response to longest SEND in CAN normal mode
        self.send(b"O\r")
        self.assertEqual(self.receive(), b"\r")

        # FIXME unable to send DLC > 8
        self.send(b"r03F8\r")
        self.assertEqual(self.receive(), b"z\r")
        self.send(b"t03F80011223344556677\r")
        self.assertEqual(self.receive(), b"z\r")
        self.send(b"d03FF00112233445566778899AABBCCDDEEFF00112233445566778899AABBCCDDEEFF00112233445566778899AABBCCDDEEFF00112233445566778899AABBCCDDEEFF\r")
        self.assertEqual(self.receive(), b"z\r")
        self.send(b"b03FF00112233445566778899AABBCCDDEEFF00112233445566778899AABBCCDDEEFF00112233445566778899AABBCCDDEEFF00112233445566778899AABBCCDDEEFF\r")
        self.assertEqual(self.receive(), b"z\r")

        # FIXME unable to send DLC > 8
        self.send(b"R0137FEC88\r")
        self.assertEqual(self.receive(), b"Z\r")
        self.send(b"T0137FEC880011223344556677\r")
        self.assertEqual(self.receive(), b"Z\r")
        self.send(b"D0137FEC8F00112233445566778899AABBCCDDEEFF00112233445566778899AABBCCDDEEFF00112233445566778899AABBCCDDEEFF00112233445566778899AABBCCDDEEFF\r")
        self.assertEqual(self.receive(), b"Z\r")
        self.send(b"B0137FEC8F00112233445566778899AABBCCDDEEFF00112233445566778899AABBCCDDEEFF00112233445566778899AABBCCDDEEFF00112233445566778899AABBCCDDEEFF\r")
        self.assertEqual(self.receive(), b"Z\r")

        self.send(b"C\r")
        self.assertEqual(self.receive(), b"\r")

        # check response to SEND in CAN silent mode
        self.send(b"L\r")
        self.assertEqual(self.receive(), b"\r")

        for cmd in cmd_send_std:
            self.send(cmd + b"03F0\r")
            self.assertEqual(self.receive(), b"\a")

        for cmd in cmd_send_ext:
            self.send(cmd + b"0137FEC80\r")
            self.assertEqual(self.receive(), b"\a")

        self.send(b"C\r")
        self.assertEqual(self.receive(), b"\r")

        # check response to too short command in CAN normal mode
        self.send(b"O\r")
        self.assertEqual(self.receive(), b"\r")

        for cmd in cmd_send_std:
            self.send(cmd + b"03F\r")
            self.assertEqual(self.receive(), b"\a")

        for cmd in cmd_send_std:
            self.send(cmd + b"03F1\r")
            if cmd == b"r":
                self.assertEqual(self.receive(), b"z\r")
            elif cmd == b"R":
                self.assertEqual(self.receive(), b"Z\r")
            else:
                self.assertEqual(self.receive(), b"\a")

        for cmd in cmd_send_ext:
            self.send(cmd + b"0137FEC8\r")
            self.assertEqual(self.receive(), b"\a")

        for cmd in cmd_send_ext:
            self.send(cmd + b"0137FEC81\r")
            if cmd == b"r":
                self.assertEqual(self.receive(), b"z\r")
            elif cmd == b"R":
                self.assertEqual(self.receive(), b"Z\r")
            else:
                self.assertEqual(self.receive(), b"\a")

        self.send(b"C\r")
        self.assertEqual(self.receive(), b"\r")

        # check response to invalid command in CAN normal mode
        self.send(b"O\r")
        self.assertEqual(self.receive(), b"\r")

        for cmd in cmd_send_std:
            self.send(cmd + b"03FG\r")
            self.assertEqual(self.receive(), b"\a")

        for cmd in cmd_send_ext:
            self.send(cmd + b"0137FEC8G\r")
            self.assertEqual(self.receive(), b"\a")

        self.send(b"C\r")
        self.assertEqual(self.receive(), b"\r")

        # check response to out of range command in CAN normal mode
        self.send(b"O\r")
        self.assertEqual(self.receive(), b"\r")

        self.send(b"r8000\r")
        #self.assertEqual(self.receive(), b"\a")
        # FIXME no check for invalid id
        self.receive()
        self.send(b"t8000\r")
        #self.assertEqual(self.receive(), b"\a")
        # FIXME
        self.receive()
        self.send(b"t03F9001122334455667788\r")
        #self.assertEqual(self.receive(), b"\a")
        # FIXME
        self.receive()
        self.send(b"d8000\r")
        #self.assertEqual(self.receive(), b"\a")
        # FIXME
        self.receive()
        self.send(b"b8000\r")
        #self.assertEqual(self.receive(), b"\a")
        # FIXME
        self.receive()

        self.send(b"R200000000\r")
        #self.assertEqual(self.receive(), b"\a")
        # FIXME
        self.receive()
        self.send(b"T200000000\r")
        #self.assertEqual(self.receive(), b"\a")
        # FIXME
        self.receive()
        self.send(b"T03F9001122334455667788\r")
        #self.assertEqual(self.receive(), b"\a")
        # FIXME
        self.receive()
        self.send(b"D200000000\r")
        #self.assertEqual(self.receive(), b"\a")
        # FIXME
        self.receive()
        self.send(b"B200000000\r")
        #self.assertEqual(self.receive(), b"\a")
        # FIXME
        self.receive()

        self.send(b"C\r")
        self.assertEqual(self.receive(), b"\r")


if __name__ == "__main__":
    unittest.main()
