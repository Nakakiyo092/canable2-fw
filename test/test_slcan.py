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


    def test_blank_command(self):
        # check response to [CR]
        self.dut.send(b"\r")
        self.assertEqual(self.dut.receive(), b"\r")


    def test_error_command(self):
        # check response to [BELL]
        self.dut.send(b"\a")
        self.assertEqual(self.dut.receive(), b"")      # message is incomplete without [CR]
        self.dut.send(b"\r")
        self.assertEqual(self.dut.receive(), b"\a")


    def test_V_command(self):
        # check response to V
        self.dut.send(b"V\r")
        rx_data = self.dut.receive()
        self.assertEqual(len(rx_data), len(b"V1013\r"))
        self.assertEqual(rx_data[0], b"V1013\r"[0])
        self.dut.send(b"V0\r")
        self.assertEqual(self.dut.receive(), b"\a")


    def test_v_command(self):
        self.dut.send(b"v\r")
        rx_data = self.dut.receive()
        self.assertGreaterEqual(len(rx_data), len(b"v\r"))
        self.assertEqual(rx_data[0], b"v\r"[0])
        self.dut.send(b"v0\r")
        self.assertEqual(self.dut.receive(), b"\a")


    def test_I_command(self):
        self.dut.send(b"I\r")
        rx_data = self.dut.receive()
        self.assertEqual(len(rx_data), len(b"I20A0\r"))
        self.assertEqual(rx_data[0], b"I20A0\r"[0])
        self.dut.send(b"I0\r")
        self.assertEqual(self.dut.receive(), b"\a")


    def test_i_command(self):
        self.dut.send(b"i\r")
        rx_data = self.dut.receive()
        self.assertGreaterEqual(len(rx_data), len(b"i\r"))
        self.assertEqual(rx_data[0], b"i\r"[0])
        self.dut.send(b"i0\r")
        self.assertEqual(self.dut.receive(), b"\a")


    def test_N_command(self):
        #self.dut.print_on = True
        # check response to N
        self.dut.send(b"N\r")
        rx_data = self.dut.receive()
        self.assertEqual(len(rx_data), len(b"NA123\r"))
        self.assertEqual(rx_data[0], b"NA123\r"[0])
        self.dut.send(b"NA123\r")
        self.assertEqual(self.dut.receive(), b"\r")
        self.dut.send(b"N0\r")
        self.assertEqual(self.dut.receive(), b"\a")
        self.dut.send(b"NA12\r")
        self.assertEqual(self.dut.receive(), b"\a")
        self.dut.send(b"NA1230\r")
        self.assertEqual(self.dut.receive(), b"\a")


    def test_open_close_command(self):
        # check response to C and O
        self.dut.send(b"C\r")
        self.assertEqual(self.dut.receive(), b"\a")
        self.dut.send(b"O\r")
        self.assertEqual(self.dut.receive(), b"\r")
        self.dut.send(b"O\r")
        self.assertEqual(self.dut.receive(), b"\a")
        self.dut.send(b"C\r")
        self.assertEqual(self.dut.receive(), b"\r")

        # check response to C and L
        self.dut.send(b"C\r")
        self.assertEqual(self.dut.receive(), b"\a")
        self.dut.send(b"L\r")
        self.assertEqual(self.dut.receive(), b"\r")
        self.dut.send(b"L\r")
        self.assertEqual(self.dut.receive(), b"\a")
        self.dut.send(b"C\r")
        self.assertEqual(self.dut.receive(), b"\r")

        # check response to O and L
        self.dut.send(b"C\r")
        self.assertEqual(self.dut.receive(), b"\a")
        self.dut.send(b"O\r")
        self.assertEqual(self.dut.receive(), b"\r")
        self.dut.send(b"L\r")
        self.assertEqual(self.dut.receive(), b"\a")
        self.dut.send(b"C\r")
        self.assertEqual(self.dut.receive(), b"\r")
        self.dut.send(b"L\r")
        self.assertEqual(self.dut.receive(), b"\r")
        self.dut.send(b"O\r")
        self.assertEqual(self.dut.receive(), b"\a")
        self.dut.send(b"C\r")
        self.assertEqual(self.dut.receive(), b"\r")

        # invalid format
        self.dut.send(b"O0\r")
        self.assertEqual(self.dut.receive(), b"\a")
        self.dut.send(b"L0\r")
        self.assertEqual(self.dut.receive(), b"\a")
        self.dut.send(b"C0\r")
        self.assertEqual(self.dut.receive(), b"\a")


    def test_S_command(self):
        # check response to S with CAN port closed
        for idx in range(0, 10):
            cmd = "S" + str(idx) + "\r"
            self.dut.send(cmd.encode())
            if idx <= 8:
                self.assertEqual(self.dut.receive(), b"\r")
            else:
                self.assertEqual(self.dut.receive(), b"\a")

        # check response to S in CAN normal mode
        self.dut.send(b"O\r")
        self.assertEqual(self.dut.receive(), b"\r")
        for idx in range(0, 10):
            cmd = "S" + str(idx) + "\r"
            self.dut.send(cmd.encode())
            self.assertEqual(self.dut.receive(), b"\a")
        self.dut.send(b"C\r")
        self.assertEqual(self.dut.receive(), b"\r")

        # check response to S in CAN silent mode
        self.dut.send(b"L\r")
        self.assertEqual(self.dut.receive(), b"\r")
        for idx in range(0, 10):
            cmd = "S" + str(idx) + "\r"
            self.dut.send(cmd.encode())
            self.assertEqual(self.dut.receive(), b"\a")
        self.dut.send(b"C\r")
        self.assertEqual(self.dut.receive(), b"\r")

        # invalid format
        self.dut.send(b"S\r")
        self.assertEqual(self.dut.receive(), b"\a")
        self.dut.send(b"S00\r")
        self.assertEqual(self.dut.receive(), b"\a")
        self.dut.send(b"SG\r")
        self.assertEqual(self.dut.receive(), b"\a")


    def test_s_command(self):
        # check response with CAN port closed
        self.dut.send(b"s10460908\r")
        #self.dut.send(b"s010046009008\r")  # extension for future use?
        self.assertEqual(self.dut.receive(), b"\r")

        # check response in CAN normal mode
        self.dut.send(b"O\r")
        self.assertEqual(self.dut.receive(), b"\r")
        self.dut.send(b"s10460908\r")
        self.assertEqual(self.dut.receive(), b"\a")
        self.dut.send(b"C\r")
        self.assertEqual(self.dut.receive(), b"\r")

        # check response in CAN silent mode
        self.dut.send(b"L\r")
        self.assertEqual(self.dut.receive(), b"\r")
        self.dut.send(b"s10460908\r")
        self.assertEqual(self.dut.receive(), b"\a")
        self.dut.send(b"C\r")
        self.assertEqual(self.dut.receive(), b"\r")

        # within range
        self.dut.send(b"s01010101\r")
        self.assertEqual(self.dut.receive(), b"\r")
        self.dut.send(b"sFFFF8080\r")
        self.assertEqual(self.dut.receive(), b"\r")
        
        # our of range
        self.dut.send(b"s00460908\r")
        self.assertEqual(self.dut.receive(), b"\a")
        #self.dut.send(b"sFF460908\r")
        #self.assertEqual(self.dut.receive(), b"\a")
        self.dut.send(b"s10000908\r")
        self.assertEqual(self.dut.receive(), b"\a")
        #self.dut.send(b"s10FF0908\r")
        #self.assertEqual(self.dut.receive(), b"\a")
        self.dut.send(b"s10460008\r")
        self.assertEqual(self.dut.receive(), b"\a")
        self.dut.send(b"s10468108\r")
        self.assertEqual(self.dut.receive(), b"\a")
        self.dut.send(b"s10460900\r")
        self.assertEqual(self.dut.receive(), b"\a")
        self.dut.send(b"s10460981\r")
        self.assertEqual(self.dut.receive(), b"\a")

        # invalid format
        self.dut.send(b"s1046090\r")
        self.assertEqual(self.dut.receive(), b"\a")
        self.dut.send(b"s104609080\r")
        self.assertEqual(self.dut.receive(), b"\a")
        self.dut.send(b"s0G460908\r")
        self.assertEqual(self.dut.receive(), b"\a")


    def test_Y_command(self):
        # check response to Y with CAN port closed
        for idx in range(0, 10):
            cmd = "Y" + str(idx) + "\r"
            self.dut.send(cmd.encode())
            if idx in (0, 1, 2, 4, 5, 8):    # for CANable2
            #if idx in (0, 1, 2, 3, 4, 5):    # for USB2CANFDV1
                self.assertEqual(self.dut.receive(), b"\r")
            else:
                self.assertEqual(self.dut.receive(), b"\a")

        # check response to Y in CAN normal mode
        self.dut.send(b"O\r")
        self.assertEqual(self.dut.receive(), b"\r")
        for idx in range(0, 10):
            cmd = "Y" + str(idx) + "\r"
            self.dut.send(cmd.encode())
            self.assertEqual(self.dut.receive(), b"\a")
        self.dut.send(b"C\r")
        self.assertEqual(self.dut.receive(), b"\r")

        # check response to Y in CAN silent mode
        self.dut.send(b"L\r")
        self.assertEqual(self.dut.receive(), b"\r")
        for idx in range(0, 10):
            cmd = "Y" + str(idx) + "\r"
            self.dut.send(cmd.encode())
            self.assertEqual(self.dut.receive(), b"\a")
        self.dut.send(b"C\r")
        self.assertEqual(self.dut.receive(), b"\r")

        # invalid format
        self.dut.send(b"Y\r")
        self.assertEqual(self.dut.receive(), b"\a")
        self.dut.send(b"Y00\r")
        self.assertEqual(self.dut.receive(), b"\a")
        self.dut.send(b"YG\r")
        self.assertEqual(self.dut.receive(), b"\a")


    def test_y_command(self):
        # check response with CAN port closed
        self.dut.send(b"y021E0908\r")
        self.assertEqual(self.dut.receive(), b"\r")

        # check response in CAN normal mode
        self.dut.send(b"O\r")
        self.assertEqual(self.dut.receive(), b"\r")
        self.dut.send(b"y021E0908\r")
        self.assertEqual(self.dut.receive(), b"\a")
        self.dut.send(b"C\r")
        self.assertEqual(self.dut.receive(), b"\r")

        # check response in CAN silent mode
        self.dut.send(b"L\r")
        self.assertEqual(self.dut.receive(), b"\r")
        self.dut.send(b"y021E0908\r")
        self.assertEqual(self.dut.receive(), b"\a")
        self.dut.send(b"C\r")
        self.assertEqual(self.dut.receive(), b"\r")

        # within range
        self.dut.send(b"y01010101\r")
        self.assertEqual(self.dut.receive(), b"\r")
        self.dut.send(b"y20201010\r")
        self.assertEqual(self.dut.receive(), b"\r")
        
        # our of range
        self.dut.send(b"y001E0908\r")
        self.assertEqual(self.dut.receive(), b"\a")
        self.dut.send(b"y211E0908\r")
        self.assertEqual(self.dut.receive(), b"\a")
        self.dut.send(b"y02000908\r")
        self.assertEqual(self.dut.receive(), b"\a")
        self.dut.send(b"y02210908\r")
        self.assertEqual(self.dut.receive(), b"\a")
        self.dut.send(b"y021E0008\r")
        self.assertEqual(self.dut.receive(), b"\a")
        self.dut.send(b"y021E1108\r")
        self.assertEqual(self.dut.receive(), b"\a")
        self.dut.send(b"y021E0900\r")
        self.assertEqual(self.dut.receive(), b"\a")
        self.dut.send(b"y021E0911\r")
        self.assertEqual(self.dut.receive(), b"\a")

        # invalid format
        self.dut.send(b"y021E090\r")
        self.assertEqual(self.dut.receive(), b"\a")
        self.dut.send(b"y021E09080\r")
        self.assertEqual(self.dut.receive(), b"\a")
        self.dut.send(b"y0G1E0908\r")
        self.assertEqual(self.dut.receive(), b"\a")


    def test_Z_command(self):
        # Without option
        # check response to Z with timestamp disabled
        self.dut.send(b"Z0\r")
        self.assertEqual(self.dut.receive(), b"\r")
        self.dut.send(b"Z\r")
        self.assertEqual(self.dut.receive(), b"\a")

        # check response to Z with ms timestamp
        self.dut.send(b"Z1\r")
        self.assertEqual(self.dut.receive(), b"\r")
        self.dut.send(b"Z\r")
        rx_data = self.dut.receive()
        self.assertEqual(len(rx_data), len(b"Zxxxx\r"))
        self.assertEqual(rx_data[0], b"Zxxxx\r"[0])

        # check response to Z with us timestamp
        self.dut.send(b"Z2\r")
        self.assertEqual(self.dut.receive(), b"\r")
        self.dut.send(b"Z\r")
        rx_data = self.dut.receive()
        self.assertEqual(len(rx_data), len(b"Zxxxxxxxx\r"))
        self.assertEqual(rx_data[0], b"Zxxxxxxxx\r"[0])

        # With option
        # check response to Z with CAN port closed
        for idx in range(0, 10):
            cmd = "Z" + str(idx) + "\r"
            self.dut.send(cmd.encode())
            if idx in range(0, 3):
                self.assertEqual(self.dut.receive(), b"\r")
            else:
                self.assertEqual(self.dut.receive(), b"\a")

        # check response to Z in CAN normal mode
        self.dut.send(b"O\r")
        self.assertEqual(self.dut.receive(), b"\r")
        for idx in range(0, 10):
            cmd = "Z" + str(idx) + "\r"
            self.dut.send(cmd.encode())
            self.assertEqual(self.dut.receive(), b"\a")
        self.dut.send(b"C\r")
        self.assertEqual(self.dut.receive(), b"\r")

        # check response to Z in CAN silent mode
        self.dut.send(b"L\r")
        self.assertEqual(self.dut.receive(), b"\r")
        for idx in range(0, 10):
            cmd = "Z" + str(idx) + "\r"
            self.dut.send(cmd.encode())
            self.assertEqual(self.dut.receive(), b"\a")
        self.dut.send(b"C\r")
        self.assertEqual(self.dut.receive(), b"\r")

        # invalid format
        self.dut.send(b"Z00\r")
        self.assertEqual(self.dut.receive(), b"\a")
        self.dut.send(b"ZG\r")
        self.assertEqual(self.dut.receive(), b"\a")


    def test_z_command(self):
        # check response with CAN port closed
        for idx in range(0, 10):
            cmd = "z" + str(idx) + "000\r"
            self.dut.send(cmd.encode())
            if idx in range(0, 3):
                self.assertEqual(self.dut.receive(), b"\r")
            else:
                self.assertEqual(self.dut.receive(), b"\a")

        # check response in CAN normal mode
        self.dut.send(b"O\r")
        self.assertEqual(self.dut.receive(), b"\r")
        for idx in range(0, 10):
            cmd = "z" + str(idx) + "000\r"
            self.dut.send(cmd.encode())
            self.assertEqual(self.dut.receive(), b"\a")
        self.dut.send(b"C\r")
        self.assertEqual(self.dut.receive(), b"\r")

        # check response in CAN silent mode
        self.dut.send(b"L\r")
        self.assertEqual(self.dut.receive(), b"\r")
        for idx in range(0, 10):
            cmd = "z" + str(idx) + "000\r"
            self.dut.send(cmd.encode())
            self.assertEqual(self.dut.receive(), b"\a")
        self.dut.send(b"C\r")
        self.assertEqual(self.dut.receive(), b"\r")

        # invalid format
        self.dut.send(b"z000\r")
        self.assertEqual(self.dut.receive(), b"\a")
        self.dut.send(b"z00000\r")
        self.assertEqual(self.dut.receive(), b"\a")
        self.dut.send(b"zG000\r")
        self.assertEqual(self.dut.receive(), b"\a")


    def test_F_command(self):
        # check response with CAN port closed
        self.dut.send(b"F\r")
        self.assertEqual(self.dut.receive(), b"\a")

        # check response in CAN normal mode
        self.dut.send(b"O\r")
        self.assertEqual(self.dut.receive(), b"\r")
        self.dut.send(b"F\r")
        self.assertEqual(self.dut.receive(), b"F00\r")
        self.dut.send(b"C\r")
        self.assertEqual(self.dut.receive(), b"\r")

        # check response in CAN silent mode
        self.dut.send(b"L\r")
        self.assertEqual(self.dut.receive(), b"\r")
        self.dut.send(b"F\r")
        self.assertEqual(self.dut.receive(), b"F00\r")
        self.dut.send(b"C\r")
        self.assertEqual(self.dut.receive(), b"\r")

        # invalid format
        self.dut.send(b"O\r")
        self.assertEqual(self.dut.receive(), b"\r")
        self.dut.send(b"F0\r")
        self.assertEqual(self.dut.receive(), b"\a")
        self.dut.send(b"C\r")
        self.assertEqual(self.dut.receive(), b"\r")


    def test_f_command(self):
        # check response with CAN port closed
        self.dut.send(b"f\r")
        self.assertEqual(self.dut.receive(), b"\a")

        # check response in CAN normal mode
        self.dut.send(b"O\r")
        self.assertEqual(self.dut.receive(), b"\r")
        self.dut.send(b"f\r")
        rx_data = self.dut.receive()
        self.assertGreaterEqual(len(rx_data), len(b"f\r"))
        self.assertEqual(rx_data[0], b"f\r"[0])
        self.dut.send(b"C\r")
        self.assertEqual(self.dut.receive(), b"\r")

        # check response in CAN silent mode
        self.dut.send(b"L\r")
        self.assertEqual(self.dut.receive(), b"\r")
        self.dut.send(b"f\r")
        rx_data = self.dut.receive()
        self.assertGreaterEqual(len(rx_data), len(b"f\r"))
        self.assertEqual(rx_data[0], b"f\r"[0])
        self.dut.send(b"C\r")
        self.assertEqual(self.dut.receive(), b"\r")

        # invalid format
        self.dut.send(b"O\r")
        self.assertEqual(self.dut.receive(), b"\r")
        self.dut.send(b"f0\r")
        self.assertEqual(self.dut.receive(), b"\a")
        self.dut.send(b"C\r")
        self.assertEqual(self.dut.receive(), b"\r")


    def test_W_command(self):
        # check response with CAN port closed
        for idx in range(0, 10):
            cmd = "W" + str(idx) + "\r"
            self.dut.send(cmd.encode())
            if idx == 2:
                self.assertEqual(self.dut.receive(), b"\r")
            else:
                self.assertEqual(self.dut.receive(), b"\a")

        # check response in CAN normal mode
        self.dut.send(b"O\r")
        self.assertEqual(self.dut.receive(), b"\r")
        for idx in range(0, 10):
            cmd = "W" + str(idx) + "\r"
            self.dut.send(cmd.encode())
            self.assertEqual(self.dut.receive(), b"\a")
        self.dut.send(b"C\r")
        self.assertEqual(self.dut.receive(), b"\r")

        # check response in CAN silent mode
        self.dut.send(b"L\r")
        self.assertEqual(self.dut.receive(), b"\r")
        for idx in range(0, 10):
            cmd = "W" + str(idx) + "\r"
            self.dut.send(cmd.encode())
            self.assertEqual(self.dut.receive(), b"\a")
        self.dut.send(b"C\r")
        self.assertEqual(self.dut.receive(), b"\r")

        # invalid format
        self.dut.send(b"W\r")
        self.assertEqual(self.dut.receive(), b"\a")
        self.dut.send(b"W00\r")
        self.assertEqual(self.dut.receive(), b"\a")
        self.dut.send(b"WG\r")
        self.assertEqual(self.dut.receive(), b"\a")


    def test_M_command(self):
        # check response with CAN port closed
        self.dut.send(b"M00000000\r")
        self.assertEqual(self.dut.receive(), b"\r")
        self.dut.send(b"MFFFFFFFF\r")
        self.assertEqual(self.dut.receive(), b"\r")

        # check response in CAN normal mode
        self.dut.send(b"O\r")
        self.assertEqual(self.dut.receive(), b"\r")
        self.dut.send(b"M00000000\r")
        self.assertEqual(self.dut.receive(), b"\a")
        self.dut.send(b"MFFFFFFFF\r")
        self.assertEqual(self.dut.receive(), b"\a")
        self.dut.send(b"C\r")
        self.assertEqual(self.dut.receive(), b"\r")

        # check response in CAN silent mode
        self.dut.send(b"L\r")
        self.assertEqual(self.dut.receive(), b"\r")
        self.dut.send(b"M00000000\r")
        self.assertEqual(self.dut.receive(), b"\a")
        self.dut.send(b"MFFFFFFFF\r")
        self.assertEqual(self.dut.receive(), b"\a")
        self.dut.send(b"C\r")
        self.assertEqual(self.dut.receive(), b"\r")

        # invalid format
        self.dut.send(b"M0000000\r")
        self.assertEqual(self.dut.receive(), b"\a")
        self.dut.send(b"M000000000\r")
        self.assertEqual(self.dut.receive(), b"\a")
        self.dut.send(b"M0000000G\r")
        self.assertEqual(self.dut.receive(), b"\a")


    def test_m_command(self):
        # check response with CAN port closed
        self.dut.send(b"m00000000\r")
        self.assertEqual(self.dut.receive(), b"\r")
        self.dut.send(b"mFFFFFFFF\r")
        self.assertEqual(self.dut.receive(), b"\r")

        # check response in CAN normal mode
        self.dut.send(b"O\r")
        self.assertEqual(self.dut.receive(), b"\r")
        self.dut.send(b"m00000000\r")
        self.assertEqual(self.dut.receive(), b"\a")
        self.dut.send(b"mFFFFFFFF\r")
        self.assertEqual(self.dut.receive(), b"\a")
        self.dut.send(b"C\r")
        self.assertEqual(self.dut.receive(), b"\r")

        # check response in CAN silent mode
        self.dut.send(b"L\r")
        self.assertEqual(self.dut.receive(), b"\r")
        self.dut.send(b"m00000000\r")
        self.assertEqual(self.dut.receive(), b"\a")
        self.dut.send(b"mFFFFFFFF\r")
        self.assertEqual(self.dut.receive(), b"\a")
        self.dut.send(b"C\r")
        self.assertEqual(self.dut.receive(), b"\r")

        # invalid format
        self.dut.send(b"m0000000\r")
        self.assertEqual(self.dut.receive(), b"\a")
        self.dut.send(b"m000000000\r")
        self.assertEqual(self.dut.receive(), b"\a")
        self.dut.send(b"m0000000G\r")
        self.assertEqual(self.dut.receive(), b"\a")


    def test_Q_command(self):
        # check response to Q with CAN port closed
        for idx in range(0, 10):
            cmd = "Q" + str(idx) + "\r"
            self.dut.send(cmd.encode())
            self.assertEqual(self.dut.receive(), b"\a")

        # check response to Q in CAN normal mode
        self.dut.send(b"O\r")
        self.assertEqual(self.dut.receive(), b"\r")
        for idx in range(0, 10):
            cmd = "Q" + str(idx) + "\r"
            self.dut.send(cmd.encode())
            if idx in (0, 1, 2):
                self.assertEqual(self.dut.receive(), b"\r")
            else:
                self.assertEqual(self.dut.receive(), b"\a")
        self.dut.send(b"C\r")
        self.assertEqual(self.dut.receive(), b"\r")

        # check response to Q in CAN silent mode
        self.dut.send(b"L\r")
        self.assertEqual(self.dut.receive(), b"\r")
        for idx in range(0, 10):
            cmd = "Q" + str(idx) + "\r"
            self.dut.send(cmd.encode())
            if idx in (0, 1, 2):
                self.assertEqual(self.dut.receive(), b"\r")
            else:
                self.assertEqual(self.dut.receive(), b"\a")
        self.dut.send(b"C\r")
        self.assertEqual(self.dut.receive(), b"\r")

        # invalid format
        self.dut.send(b"O\r")
        self.assertEqual(self.dut.receive(), b"\r")
        self.dut.send(b"Q\r")
        self.assertEqual(self.dut.receive(), b"\a")
        self.dut.send(b"Q00\r")
        self.assertEqual(self.dut.receive(), b"\a")
        self.dut.send(b"QG\r")
        self.assertEqual(self.dut.receive(), b"\a")
        self.dut.send(b"C\r")
        self.assertEqual(self.dut.receive(), b"\r")


    def test_send_command(self):
        cmd_send_std = (b"r", b"t", b"d", b"b")
        cmd_send_ext = (b"R", b"T", b"D", b"B")

        # check response to SEND with CAN port closed
        for cmd in cmd_send_std:
            self.dut.send(cmd + b"03F0\r")
            self.assertEqual(self.dut.receive(), b"\a")
        for cmd in cmd_send_ext:
            self.dut.send(cmd + b"0137FEC80\r")
            self.assertEqual(self.dut.receive(), b"\a")

        # check response to SEND in CAN normal mode
        self.dut.send(b"O\r")
        self.assertEqual(self.dut.receive(), b"\r")
        for cmd in cmd_send_std:
            self.dut.send(cmd + b"03F0\r")
            self.assertEqual(self.dut.receive(), b"z\r")
        for cmd in cmd_send_ext:
            self.dut.send(cmd + b"0137FEC80\r")
            self.assertEqual(self.dut.receive(), b"Z\r")
        self.dut.send(b"C\r")
        self.assertEqual(self.dut.receive(), b"\r")

        # check response to minimum/shortest SEND in CAN normal mode
        self.dut.send(b"O\r")
        self.assertEqual(self.dut.receive(), b"\r")
        self.dut.send(b"r0000\r")
        self.assertEqual(self.dut.receive(), b"z\r")
        self.dut.send(b"t0000\r")
        self.assertEqual(self.dut.receive(), b"z\r")
        self.dut.send(b"d0000\r")
        self.assertEqual(self.dut.receive(), b"z\r")
        self.dut.send(b"b0000\r")
        self.assertEqual(self.dut.receive(), b"z\r")
        self.dut.send(b"R000000000\r")
        self.assertEqual(self.dut.receive(), b"Z\r")
        self.dut.send(b"T000000000\r")
        self.assertEqual(self.dut.receive(), b"Z\r")
        self.dut.send(b"D000000000\r")
        self.assertEqual(self.dut.receive(), b"Z\r")
        self.dut.send(b"B000000000\r")
        self.assertEqual(self.dut.receive(), b"Z\r")
        self.dut.send(b"C\r")
        self.assertEqual(self.dut.receive(), b"\r")

        # check response to maximum/longest SEND in CAN normal mode
        self.dut.send(b"O\r")
        self.assertEqual(self.dut.receive(), b"\r")
        self.dut.send(b"r7FFF\r")
        self.assertEqual(self.dut.receive(), b"z\r")
        self.dut.send(b"t7FF80011223344556677\r")
        self.assertEqual(self.dut.receive(), b"z\r")
        self.dut.send(b"d7FFF00112233445566778899AABBCCDDEEFF00112233445566778899AABBCCDDEEFF00112233445566778899AABBCCDDEEFF00112233445566778899AABBCCDDEEFF\r")
        self.assertEqual(self.dut.receive(), b"z\r")
        self.dut.send(b"b7FFF00112233445566778899AABBCCDDEEFF00112233445566778899AABBCCDDEEFF00112233445566778899AABBCCDDEEFF00112233445566778899AABBCCDDEEFF\r")
        self.assertEqual(self.dut.receive(), b"z\r")
        self.dut.send(b"R1FFFFFFFF\r")
        self.assertEqual(self.dut.receive(), b"Z\r")
        self.dut.send(b"T1FFFFFFF80011223344556677\r")
        self.assertEqual(self.dut.receive(), b"Z\r")
        self.dut.send(b"D1FFFFFFFF00112233445566778899AABBCCDDEEFF00112233445566778899AABBCCDDEEFF00112233445566778899AABBCCDDEEFF00112233445566778899AABBCCDDEEFF\r")
        self.assertEqual(self.dut.receive(), b"Z\r")
        self.dut.send(b"B1FFFFFFFF00112233445566778899AABBCCDDEEFF00112233445566778899AABBCCDDEEFF00112233445566778899AABBCCDDEEFF00112233445566778899AABBCCDDEEFF\r")
        self.assertEqual(self.dut.receive(), b"Z\r")
        self.dut.send(b"C\r")
        self.assertEqual(self.dut.receive(), b"\r")

        # check response to SEND in CAN silent mode
        self.dut.send(b"L\r")
        self.assertEqual(self.dut.receive(), b"\r")
        for cmd in cmd_send_std:
            self.dut.send(cmd + b"03F0\r")
            self.assertEqual(self.dut.receive(), b"\a")
        for cmd in cmd_send_ext:
            self.dut.send(cmd + b"0137FEC80\r")
            self.assertEqual(self.dut.receive(), b"\a")
        self.dut.send(b"C\r")
        self.assertEqual(self.dut.receive(), b"\r")

        # check response to too short command in CAN normal mode
        self.dut.send(b"O\r")
        self.assertEqual(self.dut.receive(), b"\r")
        for cmd in cmd_send_std:
            self.dut.send(cmd + b"03F\r")
            self.assertEqual(self.dut.receive(), b"\a")
        for cmd in cmd_send_std:
            self.dut.send(cmd + b"03F10\r")
            self.assertEqual(self.dut.receive(), b"\a")
        for cmd in cmd_send_ext:
            self.dut.send(cmd + b"0137FEC8\r")
            self.assertEqual(self.dut.receive(), b"\a")
        for cmd in cmd_send_ext:
            self.dut.send(cmd + b"0137FEC810\r")
            self.assertEqual(self.dut.receive(), b"\a")
        self.dut.send(b"C\r")
        self.assertEqual(self.dut.receive(), b"\r")

        # check response to too long command in CAN normal mode
        self.dut.send(b"O\r")
        self.assertEqual(self.dut.receive(), b"\r")
        for cmd in cmd_send_std:
            self.dut.send(cmd + b"03F00\r")
            self.assertEqual(self.dut.receive(), b"\a")
        for cmd in cmd_send_ext:
            self.dut.send(cmd + b"0137FEC800\r")
            self.assertEqual(self.dut.receive(), b"\a")
        self.dut.send(b"C\r")
        self.assertEqual(self.dut.receive(), b"\r")

        # check response to invalid command in CAN normal mode
        self.dut.send(b"O\r")
        self.assertEqual(self.dut.receive(), b"\r")
        for cmd in cmd_send_std:
            self.dut.send(cmd + b"03FG\r")
            self.assertEqual(self.dut.receive(), b"\a")
        for cmd in cmd_send_ext:
            self.dut.send(cmd + b"0137FEC8G\r")
            self.assertEqual(self.dut.receive(), b"\a")
        self.dut.send(b"C\r")
        self.assertEqual(self.dut.receive(), b"\r")

        # check response to out of range command in CAN normal mode
        self.dut.send(b"O\r")
        self.assertEqual(self.dut.receive(), b"\r")
        self.dut.send(b"r8000\r")
        self.assertEqual(self.dut.receive(), b"\a")
        self.dut.send(b"t8000\r")
        self.assertEqual(self.dut.receive(), b"\a")
        self.dut.send(b"t03F9001122334455667788\r")
        self.assertEqual(self.dut.receive(), b"\a")
        self.dut.send(b"d8000\r")
        self.assertEqual(self.dut.receive(), b"\a")
        self.dut.send(b"d03F9001122334455667788\r")
        self.assertEqual(self.dut.receive(), b"\a")
        self.dut.send(b"b8000\r")
        self.assertEqual(self.dut.receive(), b"\a")
        self.dut.send(b"b03F9001122334455667788\r")
        self.assertEqual(self.dut.receive(), b"\a")
        self.dut.send(b"R200000000\r")
        self.assertEqual(self.dut.receive(), b"\a")
        self.dut.send(b"T200000000\r")
        self.assertEqual(self.dut.receive(), b"\a")
        self.dut.send(b"T03F9001122334455667788\r")
        self.assertEqual(self.dut.receive(), b"\a")
        self.dut.send(b"D200000000\r")
        self.assertEqual(self.dut.receive(), b"\a")
        #self.dut.send(b"D0137FEC89001122334455667788\r")
        #self.assertEqual(self.dut.receive(), b"\a")
        self.dut.send(b"B200000000\r")
        self.assertEqual(self.dut.receive(), b"\a")
        #self.dut.send(b"B0137FEC89001122334455667788\r")
        #self.assertEqual(self.dut.receive(), b"\a")
        self.dut.send(b"C\r")
        self.assertEqual(self.dut.receive(), b"\r")


if __name__ == "__main__":
    unittest.main()
