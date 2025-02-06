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
        self.send(b"S4\r")
        self.receive()
        self.send(b"Y2\r")
        self.receive()
        self.send(b"z0001\r")
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


    def test_V_command(self):
        # check response to V
        self.send(b"V\r")
        rx_data = self.receive()
        self.assertEqual(len(rx_data), len(b"V1013\r"))
        self.assertEqual(rx_data[0], b"V1013\r"[0])
        self.send(b"V0\r")
        self.assertEqual(self.receive(), b"\a")


    def test_v_command(self):
        self.send(b"v\r")
        rx_data = self.receive()
        self.assertGreaterEqual(len(rx_data), len(b"v:\r"))
        self.assertEqual(rx_data[0], b"v:\r"[0])
        self.send(b"v0\r")
        self.assertEqual(self.receive(), b"\a")


    def test_I_command(self):
        self.send(b"I\r")
        rx_data = self.receive()
        self.assertEqual(len(rx_data), len(b"I20A0\r"))
        self.assertEqual(rx_data[0], b"I20A0\r"[0])
        self.send(b"I0\r")
        self.assertEqual(self.receive(), b"\a")


    def test_i_command(self):
        self.send(b"i\r")
        rx_data = self.receive()
        self.assertGreaterEqual(len(rx_data), len(b"i:\r"))
        self.assertEqual(rx_data[0], b"i:\r"[0])
        self.send(b"i0\r")
        self.assertEqual(self.receive(), b"\a")


    def test_N_command(self):
        #self.print_on = True
        # check response to N
        self.send(b"N\r")
        rx_data = self.receive()
        self.assertGreaterEqual(len(rx_data), len(b"NA123\r"))
        self.assertEqual(rx_data[0], b"NA123\r"[0])
        self.send(b"NA123\r")
        self.assertEqual(self.receive(), b"\r")
        self.send(b"N\r")
        self.assertEqual(self.receive(), b"NA123\r")
        self.send(b"N0\r")
        self.assertEqual(self.receive(), b"\a")
        self.send(b"NA12\r")
        self.assertEqual(self.receive(), b"\a")
        self.send(b"NA1230\r")
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

        # invalid format
        self.send(b"O0\r")
        self.assertEqual(self.receive(), b"\a")
        self.send(b"L0\r")
        self.assertEqual(self.receive(), b"\a")
        self.send(b"C0\r")
        self.assertEqual(self.receive(), b"\a")


    def test_S_command(self):
        # check response to S with CAN port closed
        for idx in range(0, 10):
            cmd = "S" + str(idx) + "\r"
            self.send(cmd.encode())
            if idx <= 8:
                self.assertEqual(self.receive(), b"\r")
            else:
                self.assertEqual(self.receive(), b"\a")

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
        self.send(b"S\r")
        self.assertEqual(self.receive(), b"\a")
        self.send(b"S00\r")
        self.assertEqual(self.receive(), b"\a")


    def test_s_command(self):
        # check response with CAN port closed
        self.send(b"s10460908\r")
        #self.send(b"s010046009008\r")  # extension for future use?
        self.assertEqual(self.receive(), b"\r")

        # check response in CAN normal mode
        self.send(b"O\r")
        self.assertEqual(self.receive(), b"\r")

        self.send(b"s10460908\r")
        self.assertEqual(self.receive(), b"\a")

        self.send(b"C\r")
        self.assertEqual(self.receive(), b"\r")

        # check response in CAN silent mode
        self.send(b"L\r")
        self.assertEqual(self.receive(), b"\r")

        self.send(b"s10460908\r")
        self.assertEqual(self.receive(), b"\a")

        self.send(b"C\r")
        self.assertEqual(self.receive(), b"\r")

        # our of range
        self.send(b"sFFFFFFFF\r")
        self.assertEqual(self.receive(), b"\a")

        # invalid format
        self.send(b"s1046090\r")
        self.assertEqual(self.receive(), b"\a")
        self.send(b"s104609080\r")
        self.assertEqual(self.receive(), b"\a")
        self.send(b"s0G460908\r")
        self.assertEqual(self.receive(), b"\a")


    def test_Y_command(self):
        # check response to Y with CAN port closed
        for idx in range(0, 10):
            cmd = "Y" + str(idx) + "\r"
            self.send(cmd.encode())
            if idx in (0, 1, 2, 4, 5, 8):
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
        self.send(b"Y\r")
        self.assertEqual(self.receive(), b"\a")
        self.send(b"Y00\r")
        self.assertEqual(self.receive(), b"\a")


    def test_y_command(self):
        # check response with CAN port closed
        self.send(b"y021E0908\r")
        self.assertEqual(self.receive(), b"\r")

        # check response in CAN normal mode
        self.send(b"O\r")
        self.assertEqual(self.receive(), b"\r")

        self.send(b"y021E0908\r")
        self.assertEqual(self.receive(), b"\a")

        self.send(b"C\r")
        self.assertEqual(self.receive(), b"\r")

        # check response in CAN silent mode
        self.send(b"L\r")
        self.assertEqual(self.receive(), b"\r")

        self.send(b"y021E0908\r")
        self.assertEqual(self.receive(), b"\a")

        self.send(b"C\r")
        self.assertEqual(self.receive(), b"\r")

        # our of range
        self.send(b"yFFFFFFFF\r")
        self.assertEqual(self.receive(), b"\a")

        # invalid format
        self.send(b"y021E090\r")
        self.assertEqual(self.receive(), b"\a")
        self.send(b"y021E09080\r")
        self.assertEqual(self.receive(), b"\a")
        self.send(b"y0G1E0908\r")
        self.assertEqual(self.receive(), b"\a")


    def test_Z_command(self):
        # check response to Z with CAN port closed
        for idx in range(0, 10):
            cmd = "Z" + str(idx) + "\r"
            self.send(cmd.encode())
            if idx in range(0, 3):
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
        self.send(b"Z\r")
        self.assertEqual(self.receive(), b"\a")
        self.send(b"Z00\r")
        self.assertEqual(self.receive(), b"\a")


    def test_z_command(self):
        # check response with CAN port closed
        for idx in range(0, 10):
            cmd = "z" + str(idx) + "000\r"
            self.send(cmd.encode())
            if idx in range(0, 3):
                self.assertEqual(self.receive(), b"\r")
            else:
                self.assertEqual(self.receive(), b"\a")

        # check response in CAN normal mode
        self.send(b"O\r")
        self.assertEqual(self.receive(), b"\r")

        for idx in range(0, 10):
            cmd = "z" + str(idx) + "000\r"
            self.send(cmd.encode())
            self.assertEqual(self.receive(), b"\a")

        self.send(b"C\r")
        self.assertEqual(self.receive(), b"\r")

        # check response in CAN silent mode
        self.send(b"L\r")
        self.assertEqual(self.receive(), b"\r")

        for idx in range(0, 10):
            cmd = "z" + str(idx) + "000\r"
            self.send(cmd.encode())
            self.assertEqual(self.receive(), b"\a")

        self.send(b"C\r")
        self.assertEqual(self.receive(), b"\r")

        # invalid format
        self.send(b"z000\r")
        self.assertEqual(self.receive(), b"\a")
        self.send(b"z00000\r")
        self.assertEqual(self.receive(), b"\a")


    def test_F_command(self):
        # check response with CAN port closed
        self.send(b"F\r")
        self.assertEqual(self.receive(), b"\a")

        # check response in CAN normal mode
        self.send(b"O\r")
        self.assertEqual(self.receive(), b"\r")

        self.send(b"F\r")
        self.assertEqual(self.receive(), b"F00\r")

        self.send(b"C\r")
        self.assertEqual(self.receive(), b"\r")

        # check response in CAN silent mode
        self.send(b"L\r")
        self.assertEqual(self.receive(), b"\r")

        self.send(b"F\r")
        self.assertEqual(self.receive(), b"F00\r")

        self.send(b"C\r")
        self.assertEqual(self.receive(), b"\r")

        # invalid format
        self.send(b"O\r")
        self.assertEqual(self.receive(), b"\r")

        self.send(b"F0\r")
        self.assertEqual(self.receive(), b"\a")

        self.send(b"C\r")
        self.assertEqual(self.receive(), b"\r")


    def test_W_command(self):
        # check response with CAN port closed
        for idx in range(0, 10):
            cmd = "W" + str(idx) + "\r"
            self.send(cmd.encode())
            if idx == 2:
                self.assertEqual(self.receive(), b"\r")
            else:
                self.assertEqual(self.receive(), b"\a")

        # check response in CAN normal mode
        self.send(b"O\r")
        self.assertEqual(self.receive(), b"\r")

        for idx in range(0, 10):
            cmd = "W" + str(idx) + "\r"
            self.send(cmd.encode())
            self.assertEqual(self.receive(), b"\a")

        self.send(b"C\r")
        self.assertEqual(self.receive(), b"\r")

        # check response in CAN silent mode
        self.send(b"L\r")
        self.assertEqual(self.receive(), b"\r")

        for idx in range(0, 10):
            cmd = "W" + str(idx) + "\r"
            self.send(cmd.encode())
            self.assertEqual(self.receive(), b"\a")

        self.send(b"C\r")
        self.assertEqual(self.receive(), b"\r")

        # invalid format
        self.send(b"W\r")
        self.assertEqual(self.receive(), b"\a")
        self.send(b"W00\r")
        self.assertEqual(self.receive(), b"\a")


    def test_M_command(self):
        # check response with CAN port closed
        cmd = "M0000003F\r"
        self.send(cmd.encode())
        self.assertEqual(self.receive(), b"\r")
        cmd = "M0137FEC8\r"
        self.send(cmd.encode())
        self.assertEqual(self.receive(), b"\r")
        cmd = "MFFFFFFFF\r"
        self.send(cmd.encode())
        self.assertEqual(self.receive(), b"\r")

        # check response in CAN normal mode
        self.send(b"O\r")
        self.assertEqual(self.receive(), b"\r")

        cmd = "M0000003F\r"
        self.send(cmd.encode())
        self.assertEqual(self.receive(), b"\a")
        cmd = "M0137FEC8\r"
        self.send(cmd.encode())
        self.assertEqual(self.receive(), b"\a")

        self.send(b"C\r")
        self.assertEqual(self.receive(), b"\r")

        # check response in CAN silent mode
        self.send(b"L\r")
        self.assertEqual(self.receive(), b"\r")

        cmd = "M0000003F\r"
        self.send(cmd.encode())
        self.assertEqual(self.receive(), b"\a")
        cmd = "M0137FEC8\r"
        self.send(cmd.encode())
        self.assertEqual(self.receive(), b"\a")

        self.send(b"C\r")
        self.assertEqual(self.receive(), b"\r")

        # invalid format
        self.send(b"M0000000\r")
        self.assertEqual(self.receive(), b"\a")
        self.send(b"M000000000\r")
        self.assertEqual(self.receive(), b"\a")
        self.send(b"M0000000G\r")
        self.assertEqual(self.receive(), b"\a")


    def test_m_command(self):
        # check response with CAN port closed
        cmd = "m0000003F\r"
        self.send(cmd.encode())
        self.assertEqual(self.receive(), b"\r")
        cmd = "m0137FEC8\r"
        self.send(cmd.encode())
        self.assertEqual(self.receive(), b"\r")
        cmd = "mFFFFFFFF\r"
        self.send(cmd.encode())
        self.assertEqual(self.receive(), b"\r")

        # check response in CAN normal mode
        self.send(b"O\r")
        self.assertEqual(self.receive(), b"\r")

        cmd = "m0000003F\r"
        self.send(cmd.encode())
        self.assertEqual(self.receive(), b"\a")
        cmd = "m0137FEC8\r"
        self.send(cmd.encode())
        self.assertEqual(self.receive(), b"\a")

        self.send(b"C\r")
        self.assertEqual(self.receive(), b"\r")

        # check response in CAN silent mode
        self.send(b"L\r")
        self.assertEqual(self.receive(), b"\r")

        cmd = "m0000003F\r"
        self.send(cmd.encode())
        self.assertEqual(self.receive(), b"\a")
        cmd = "m0137FEC8\r"
        self.send(cmd.encode())
        self.assertEqual(self.receive(), b"\a")

        self.send(b"C\r")
        self.assertEqual(self.receive(), b"\r")

        # invalid format
        self.send(b"m0000000\r")
        self.assertEqual(self.receive(), b"\a")
        self.send(b"m000000000\r")
        self.assertEqual(self.receive(), b"\a")
        self.send(b"m0000000G\r")
        self.assertEqual(self.receive(), b"\a")


    def test_Q_command(self):
        # check response to Q with CAN port closed
        for idx in range(0, 10):
            cmd = "Q" + str(idx) + "\r"
            self.send(cmd.encode())
            self.assertEqual(self.receive(), b"\a")

        # check cycle time
        #self.print_on = True
        self.send(b"?\r")
        self.receive()
        #self.print_on = False       

        # check response to Q in CAN normal mode
        self.send(b"O\r")
        self.assertEqual(self.receive(), b"\r")

        for idx in range(0, 10):
            cmd = "Q" + str(idx) + "\r"
            self.send(cmd.encode())
            if idx in (0, 1, 2):
                self.assertEqual(self.receive(), b"\r")
            else:
                self.assertEqual(self.receive(), b"\a")

        # check cycle time
        #self.print_on = True
        self.send(b"?\r")
        self.receive()
        #self.print_on = False       

        self.send(b"C\r")
        self.assertEqual(self.receive(), b"\r")

        # check response to Q in CAN silent mode
        self.send(b"L\r")
        self.assertEqual(self.receive(), b"\r")

        for idx in range(0, 10):
            cmd = "Q" + str(idx) + "\r"
            self.send(cmd.encode())
            if idx in (0, 1, 2):
                self.assertEqual(self.receive(), b"\r")
            else:
                self.assertEqual(self.receive(), b"\a")

        self.send(b"C\r")
        self.assertEqual(self.receive(), b"\r")

        # invalid format
        self.send(b"O\r")
        self.assertEqual(self.receive(), b"\r")
        self.send(b"Q\r")
        self.assertEqual(self.receive(), b"\a")
        self.send(b"Q00\r")
        self.assertEqual(self.receive(), b"\a")
        self.send(b"C\r")
        self.assertEqual(self.receive(), b"\r")


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

        self.send(b"r03FF\r")
        self.assertEqual(self.receive(), b"z\r")
        self.send(b"t03F80011223344556677\r")
        self.assertEqual(self.receive(), b"z\r")
        self.send(b"d03FF00112233445566778899AABBCCDDEEFF00112233445566778899AABBCCDDEEFF00112233445566778899AABBCCDDEEFF00112233445566778899AABBCCDDEEFF\r")
        self.assertEqual(self.receive(), b"z\r")
        self.send(b"b03FF00112233445566778899AABBCCDDEEFF00112233445566778899AABBCCDDEEFF00112233445566778899AABBCCDDEEFF00112233445566778899AABBCCDDEEFF\r")
        self.assertEqual(self.receive(), b"z\r")

        self.send(b"R0137FEC8F\r")
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

        # check response to too long command in CAN normal mode
        self.send(b"O\r")
        self.assertEqual(self.receive(), b"\r")

        for cmd in cmd_send_std:
            self.send(cmd + b"03F00\r")
            self.assertEqual(self.receive(), b"\a")

        for cmd in cmd_send_ext:
            self.send(cmd + b"0137FEC800\r")
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
        self.assertEqual(self.receive(), b"\a")
        self.send(b"t8000\r")
        self.assertEqual(self.receive(), b"\a")
        self.send(b"t03F9001122334455667788\r")
        self.assertEqual(self.receive(), b"\a")
        self.send(b"d8000\r")
        self.assertEqual(self.receive(), b"\a")
        self.send(b"b8000\r")
        self.assertEqual(self.receive(), b"\a")

        self.send(b"R200000000\r")
        self.assertEqual(self.receive(), b"\a")
        self.send(b"T200000000\r")
        self.assertEqual(self.receive(), b"\a")
        self.send(b"T03F9001122334455667788\r")
        self.assertEqual(self.receive(), b"\a")
        self.send(b"D200000000\r")
        self.assertEqual(self.receive(), b"\a")
        self.send(b"B200000000\r")
        self.assertEqual(self.receive(), b"\a")

        self.send(b"C\r")
        self.assertEqual(self.receive(), b"\r")


if __name__ == "__main__":
    unittest.main()
