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


    def test_internal_loopback(self):
        cmd_send_std = (b"r", b"t", b"d", b"b")
        cmd_send_ext = (b"R", b"T", b"D", b"B")

        # check response to shortest SEND in CAN loopback mode
        self.send(b"=\r")
        self.assertEqual(self.receive(), b"\r")

        for cmd in cmd_send_std:
            self.send(cmd + b"03F0\r")
            self.assertEqual(self.receive(), b"z\r" + cmd + b"03F0\r")

        for cmd in cmd_send_ext:
            self.send(cmd + b"0137FEC80\r")
            self.assertEqual(self.receive(), b"Z\r" + cmd + b"0137FEC80\r")

        self.send(b"C\r")
        self.assertEqual(self.receive(), b"\r")

        # check response to longest SEND in CAN loopback mode
        self.send(b"=\r")
        self.assertEqual(self.receive(), b"\r")

        tx_data = b"r03FF\r"
        self.send(tx_data)
        self.assertEqual(self.receive(), b"z\r" + tx_data)

        tx_data = b"t03F80011223344556677\r"
        self.send(tx_data)
        self.assertEqual(self.receive(), b"z\r" + tx_data)
        tx_data = b"d03FF00112233445566778899AABBCCDDEEFF00112233445566778899AABBCCDDEEFF00112233445566778899AABBCCDDEEFF00112233445566778899AABBCCDDEEFF\r"
        self.send(tx_data)
        self.assertEqual(self.receive(), b"z\r" + tx_data)
        tx_data = b"b03FF00112233445566778899AABBCCDDEEFF00112233445566778899AABBCCDDEEFF00112233445566778899AABBCCDDEEFF00112233445566778899AABBCCDDEEFF\r"
        self.send(tx_data)
        self.assertEqual(self.receive(), b"z\r" + tx_data)

        tx_data = b"R0137FEC8F\r"
        self.send(tx_data)
        self.assertEqual(self.receive(), b"Z\r" + tx_data)

        tx_data = b"T0137FEC880011223344556677\r"
        self.send(tx_data)
        self.assertEqual(self.receive(), b"Z\r" + tx_data)
        tx_data = b"D0137FEC8F00112233445566778899AABBCCDDEEFF00112233445566778899AABBCCDDEEFF00112233445566778899AABBCCDDEEFF00112233445566778899AABBCCDDEEFF\r"
        self.send(tx_data)
        self.assertEqual(self.receive(), b"Z\r" + tx_data)
        tx_data = b"B0137FEC8F00112233445566778899AABBCCDDEEFF00112233445566778899AABBCCDDEEFF00112233445566778899AABBCCDDEEFF00112233445566778899AABBCCDDEEFF\r"
        self.send(tx_data)
        self.assertEqual(self.receive(), b"Z\r" + tx_data)

        self.send(b"C\r")
        self.assertEqual(self.receive(), b"\r")


    def test_external_loopback(self):
        cmd_send_std = (b"r", b"t", b"d", b"b")
        cmd_send_ext = (b"R", b"T", b"D", b"B")

        # check response to shortest SEND in CAN loopback mode
        self.send(b"+\r")
        self.assertEqual(self.receive(), b"\r")

        for cmd in cmd_send_std:
            self.send(cmd + b"03F0\r")
            self.assertEqual(self.receive(), b"z\r" + cmd + b"03F0\r")

        for cmd in cmd_send_ext:
            self.send(cmd + b"0137FEC80\r")
            self.assertEqual(self.receive(), b"Z\r" + cmd + b"0137FEC80\r")

        self.send(b"C\r")
        self.assertEqual(self.receive(), b"\r")

        # check response to longest SEND in CAN loopback mode
        self.send(b"+\r")
        self.assertEqual(self.receive(), b"\r")

        tx_data = b"r03FF\r"
        self.send(tx_data)
        self.assertEqual(self.receive(), b"z\r" + tx_data)

        tx_data = b"t03F80011223344556677\r"
        self.send(tx_data)
        self.assertEqual(self.receive(), b"z\r" + tx_data)
        tx_data = b"d03FF00112233445566778899AABBCCDDEEFF00112233445566778899AABBCCDDEEFF00112233445566778899AABBCCDDEEFF00112233445566778899AABBCCDDEEFF\r"
        self.send(tx_data)
        self.assertEqual(self.receive(), b"z\r" + tx_data)
        tx_data = b"b03FF00112233445566778899AABBCCDDEEFF00112233445566778899AABBCCDDEEFF00112233445566778899AABBCCDDEEFF00112233445566778899AABBCCDDEEFF\r"
        self.send(tx_data)
        self.assertEqual(self.receive(), b"z\r" + tx_data)

        tx_data = b"R0137FEC8F\r"
        self.send(tx_data)
        self.assertEqual(self.receive(), b"Z\r" + tx_data)

        tx_data = b"T0137FEC880011223344556677\r"
        self.send(tx_data)
        self.assertEqual(self.receive(), b"Z\r" + tx_data)
        tx_data = b"D0137FEC8F00112233445566778899AABBCCDDEEFF00112233445566778899AABBCCDDEEFF00112233445566778899AABBCCDDEEFF00112233445566778899AABBCCDDEEFF\r"
        self.send(tx_data)
        self.assertEqual(self.receive(), b"Z\r" + tx_data)
        tx_data = b"B0137FEC8F00112233445566778899AABBCCDDEEFF00112233445566778899AABBCCDDEEFF00112233445566778899AABBCCDDEEFF00112233445566778899AABBCCDDEEFF\r"
        self.send(tx_data)
        self.assertEqual(self.receive(), b"Z\r" + tx_data)

        self.send(b"C\r")
        self.assertEqual(self.receive(), b"\r")


    def test_nominal_bitrate(self):
        #self.print_on = True
        # check response to SEND in every nominal bitrate
        for rate in range(0, 9):
            cmd = "S" + str(rate) + "\r"
            self.send(cmd.encode())
            self.assertEqual(self.receive(), b"\r")
            self.send(b"=\r")
            self.assertEqual(self.receive(), b"\r")
            tx_data = b"b03F80011223344556677\r"
            self.send(tx_data)
            self.assertEqual(self.receive(), b"z\r" + tx_data)
            self.send(b"C\r")
            self.assertEqual(self.receive(), b"\r")


    def test_data_bitrate(self):
        # check response to SEND in every data bitrate
        for rate in (0, 1, 2, 4, 5, 8):
            cmd = "Y" + str(rate) + "\r"
            self.send(cmd.encode())
            self.assertEqual(self.receive(), b"\r")
            self.send(b"=\r")
            self.assertEqual(self.receive(), b"\r")
            tx_data = b"b03F80011223344556677\r"
            self.send(tx_data)
            self.assertEqual(self.receive(), b"z\r" + tx_data)
            self.send(b"C\r")
            self.assertEqual(self.receive(), b"\r")


    def test_timestamp_milli(self):
        cmd_send_std = (b"r", b"t", b"d", b"b")
        cmd_send_ext = (b"R", b"T", b"D", b"B")

        #self.print_on = True

        # check timestamp off in CAN loopback mode
        self.send(b"=\r")
        self.assertEqual(self.receive(), b"\r")

        for cmd in cmd_send_std:
            self.send(cmd + b"03F0\r")
            self.assertEqual(self.receive(), b"z\r" + cmd + b"03F0\r")

        for cmd in cmd_send_ext:
            self.send(cmd + b"0137FEC80\r")
            self.assertEqual(self.receive(), b"Z\r" + cmd + b"0137FEC80\r")

        self.send(b"C\r")
        self.assertEqual(self.receive(), b"\r")

        # check timestamp on in CAN loopback mode
        self.send(b"Z1\r")
        self.assertEqual(self.receive(), b"\r")

        self.send(b"=\r")
        self.assertEqual(self.receive(), b"\r")

        for cmd in cmd_send_std:
            self.send(cmd + b"03F0\r")
            rx_data = self.receive()
            self.assertEqual(len(rx_data), len(b"z\r" + cmd + b"03F0TTTT\r"))
            self.assertEqual(rx_data[:len(b"z\r" + cmd + b"03F0")], b"z\r" + cmd + b"03F0")

        for cmd in cmd_send_ext:
            self.send(cmd + b"0137FEC80\r")
            rx_data = self.receive()
            self.assertEqual(len(rx_data), len(b"Z\r" + cmd + b"0137FEC80TTTT\r"))
            self.assertEqual(rx_data[:len(b"Z\r" + cmd + b"0137FEC80")], b"Z\r" + cmd + b"0137FEC80")

        self.send(b"C\r")
        self.assertEqual(self.receive(), b"\r")

        # check timestamp off in CAN loopback mode
        self.send(b"Z0\r")
        self.assertEqual(self.receive(), b"\r")

        self.send(b"=\r")
        self.assertEqual(self.receive(), b"\r")

        for cmd in cmd_send_std:
            self.send(cmd + b"03F0\r")
            self.assertEqual(self.receive(), b"z\r" + cmd + b"03F0\r")

        for cmd in cmd_send_ext:
            self.send(cmd + b"0137FEC80\r")
            self.assertEqual(self.receive(), b"Z\r" + cmd + b"0137FEC80\r")

        self.send(b"C\r")
        self.assertEqual(self.receive(), b"\r")

        # check timestamp accuracy in CAN loopback mode
        self.send(b"Z1\r")
        self.assertEqual(self.receive(), b"\r")

        self.send(b"=\r")
        self.assertEqual(self.receive(), b"\r")

        self.send(b"t03F0\r")
        rx_data = self.receive()
        self.assertEqual(len(rx_data), len(b"z\r" + b"t03F0TTTT\r"))
        self.assertEqual(rx_data[:len(b"z\r" + b"t03F0")], b"z\r" + b"t03F0")

        last_timestamp = rx_data[len(b"z\r" + b"t03F0"):len(b"z\r" + b"t03F0") + 4]
        last_time_ms = int(last_timestamp.decode(), 16)

        #print("time: ", last_time_ms)

        sleep_time_ms = 30 * 1000
        time.sleep(sleep_time_ms / 1000.0)

        self.send(b"t03F0\r")
        rx_data = self.receive()
        self.assertEqual(len(rx_data), len(b"z\r" + b"t03F0TTTT\r"))
        self.assertEqual(rx_data[:len(b"z\r" + b"t03F0")], b"z\r" + b"t03F0")

        crnt_timestamp = rx_data[len(b"z\r" + b"t03F0"):len(b"z\r" + b"t03F0") + 4]
        crnt_time_ms = int(crnt_timestamp.decode(), 16)

        #print("time: ", crnt_time_ms)

        if crnt_time_ms > last_time_ms:
            diff_time_ms = crnt_time_ms - last_time_ms
        else:
            diff_time_ms = (60000 + crnt_time_ms) - last_time_ms

        # Proving 2% accuracy. 600ms should be acceptable for USB latency.
        self.assertLess(abs(sleep_time_ms - diff_time_ms), 600)

        self.send(b"C\r")
        self.assertEqual(self.receive(), b"\r")


    def test_timestamp_micro(self):
        cmd_send_std = (b"r", b"t", b"d", b"b")
        cmd_send_ext = (b"R", b"T", b"D", b"B")

        #self.print_on = True

        # check timestamp off in CAN loopback mode
        self.send(b"=\r")
        self.assertEqual(self.receive(), b"\r")

        #self.print_on = True
        #self.send(b"?\r")
        #self.receive()
        #self.print_on = False

        for cmd in cmd_send_std:
            self.send(cmd + b"03F0\r")
            self.assertEqual(self.receive(), b"z\r" + cmd + b"03F0\r")

        for cmd in cmd_send_ext:
            self.send(cmd + b"0137FEC80\r")
            self.assertEqual(self.receive(), b"Z\r" + cmd + b"0137FEC80\r")

        self.send(b"C\r")
        self.assertEqual(self.receive(), b"\r")

        # check timestamp on in CAN loopback mode
        self.send(b"Z2\r")
        self.assertEqual(self.receive(), b"\r")

        self.send(b"=\r")
        self.assertEqual(self.receive(), b"\r")

        for cmd in cmd_send_std:
            self.send(cmd + b"03F0\r")
            rx_data = self.receive()
            self.assertEqual(len(rx_data), len(b"z\r" + cmd + b"03F0TTTTTTTT\r"))
            self.assertEqual(rx_data[:len(b"z\r" + cmd + b"03F0")], b"z\r" + cmd + b"03F0")

        for cmd in cmd_send_ext:
            self.send(cmd + b"0137FEC80\r")
            rx_data = self.receive()
            self.assertEqual(len(rx_data), len(b"Z\r" + cmd + b"0137FEC80TTTTTTTT\r"))
            self.assertEqual(rx_data[:len(b"Z\r" + cmd + b"0137FEC80")], b"Z\r" + cmd + b"0137FEC80")

        self.send(b"C\r")
        self.assertEqual(self.receive(), b"\r")

        # check timestamp off in CAN loopback mode
        self.send(b"Z0\r")
        self.assertEqual(self.receive(), b"\r")

        self.send(b"=\r")
        self.assertEqual(self.receive(), b"\r")

        for cmd in cmd_send_std:
            self.send(cmd + b"03F0\r")
            self.assertEqual(self.receive(), b"z\r" + cmd + b"03F0\r")

        for cmd in cmd_send_ext:
            self.send(cmd + b"0137FEC80\r")
            self.assertEqual(self.receive(), b"Z\r" + cmd + b"0137FEC80\r")

        self.send(b"C\r")
        self.assertEqual(self.receive(), b"\r")

        # check timestamp accuracy in CAN loopback mode
        self.send(b"Z2\r")
        self.assertEqual(self.receive(), b"\r")

        self.send(b"=\r")
        self.assertEqual(self.receive(), b"\r")

        self.send(b"t03F0\r")
        rx_data = self.receive()
        self.assertEqual(len(rx_data), len(b"z\r" + b"t03F0TTTTTTTT\r"))
        self.assertEqual(rx_data[:len(b"z\r" + b"t03F0")], b"z\r" + b"t03F0")

        last_timestamp = rx_data[len(b"z\r" + b"t03F0"):len(b"z\r" + b"t03F0") + 8]
        last_time_us = int(last_timestamp.decode(), 16)

        #print("time: ", last_time_us)

        sleep_time_us = 30 * 1000 * 1000
        time.sleep(sleep_time_us / 1000.0 / 1000.0)

        self.send(b"t03F0\r")
        rx_data = self.receive()
        self.assertEqual(len(rx_data), len(b"z\r" + b"t03F0TTTTTTTT\r"))
        self.assertEqual(rx_data[:len(b"z\r" + b"t03F0")], b"z\r" + b"t03F0")

        crnt_timestamp = rx_data[len(b"z\r" + b"t03F0"):len(b"z\r" + b"t03F0") + 8]
        crnt_time_us = int(crnt_timestamp.decode(), 16)

        #print("time: ", crnt_time_us)

        if crnt_time_us > last_time_us:
            diff_time_us = crnt_time_us - last_time_us
        else:
            diff_time_us = (0x100000000 + crnt_time_us) - last_time_us

        # Proving 2% accuracy. 600ms should be acceptable for USB latency.
        self.assertLess(abs(sleep_time_us - diff_time_us), 600 * 1000)

        #self.print_on = True
        #self.send(b"?\r")
        #self.receive()
        #self.print_on = False

        self.send(b"C\r")
        self.assertEqual(self.receive(), b"\r")


    def test_timestamp_same_stamp(self):
        #self.print_on = True

        # check timestamp on in CAN loopback mode
        self.send(b"z2003\r")
        self.assertEqual(self.receive(), b"\r")
        self.send(b"=\r")
        self.assertEqual(self.receive(), b"\r")

        self.print_on = True
        self.send(b"?\r")
        self.receive()
        self.print_on = False

        self.print_on = True
        self.send(b"?\r")
        self.receive()
        self.print_on = False

        self.send(b"t03F0\r")
        rx_data = self.receive()
        self.assertEqual(len(rx_data), len(b"zt03F0TTTTTTTT\r" + b"t03F0TTTTTTTT\r"))

        if rx_data[0] == b"z"[0]:
            tx_timestamp = rx_data[len(b"zt03F0"):len(b"zt03F0") + 8]
        else:
            tx_timestamp = rx_data[len(b"t03F0TTTTTTTT\rzt03F0"):len(b"t03F0TTTTTTTT\rzt03F0") + 8]

        if rx_data[0] == b"z"[0]:
            rx_timestamp = rx_data[len(b"zt03F0TTTTTTTT\rt03F0"):len(b"zt03F0TTTTTTTT\rt03F0") + 8]
        else:
            rx_timestamp = rx_data[len(b"t03F0"):len(b"t03F0") + 8]

        self.assertEqual(tx_timestamp, rx_timestamp)

        self.print_on = True
        self.send(b"?\r")
        self.receive()
        self.print_on = False

        self.send(b"C\r")
        self.assertEqual(self.receive(), b"\r")


    def test_tx_off_rx_on(self):
        cmd_send_std = (b"r", b"t", b"d", b"b")
        cmd_send_ext = (b"R", b"T", b"D", b"B")

        #self.print_on = True

        # check tx event on in CAN loopback mode
        self.send(b"z0001\r")
        self.assertEqual(self.receive(), b"\r")
        self.send(b"=\r")
        self.assertEqual(self.receive(), b"\r")

        for cmd in cmd_send_std:
            self.send(cmd + b"03F0\r")
            self.assertEqual(self.receive(), b"z\r" + cmd + b"03F0\r")

        for cmd in cmd_send_ext:
            self.send(cmd + b"0137FEC80\r")
            self.assertEqual(self.receive(), b"Z\r" + cmd + b"0137FEC80\r")

        self.send(b"C\r")
        self.assertEqual(self.receive(), b"\r")


    def test_tx_on_rx_off(self):
        cmd_send_std = (b"r", b"t", b"d", b"b")
        cmd_send_ext = (b"R", b"T", b"D", b"B")

        #self.print_on = True

        # check tx event on in CAN loopback mode
        self.send(b"z0002\r")
        self.assertEqual(self.receive(), b"\r")
        self.send(b"=\r")
        self.assertEqual(self.receive(), b"\r")

        for cmd in cmd_send_std:
            self.send(cmd + b"03F0\r")
            self.assertEqual(self.receive(), b"z" + cmd + b"03F0\r")

        for cmd in cmd_send_ext:
            self.send(cmd + b"0137FEC80\r")
            self.assertEqual(self.receive(), b"Z" + cmd + b"0137FEC80\r")

        self.send(b"C\r")
        self.assertEqual(self.receive(), b"\r")


    def test_esi_on(self):
        cmd_send_std = (b"r", b"t", b"d", b"b")
        cmd_send_ext = (b"R", b"T", b"D", b"B")

        #self.print_on = True

        # check tx event on in CAN loopback mode
        self.send(b"z0013\r")
        self.assertEqual(self.receive(), b"\r")
        self.send(b"=\r")
        self.assertEqual(self.receive(), b"\r")

        for cmd in cmd_send_std:
            self.send(cmd + b"03F0\r")
            if cmd == b"r" or cmd == b"t":
                rx_data = self.receive()
                self.assertEqual(len(rx_data), len(b"z" + cmd + b"03F0\r" + cmd + b"03F0\r"))
                if rx_data[0] == b"z"[0]:
                    self.assertEqual(rx_data, b"z" + cmd + b"03F0\r" + cmd + b"03F0\r")
                else:
                    self.assertEqual(rx_data, cmd + b"03F0\r" + b"z" + cmd + b"03F0\r")
            else:
                rx_data = self.receive()
                self.assertEqual(len(rx_data), len(b"z" + cmd + b"03F00\r" + cmd + b"03F00\r"))
                if rx_data[0] == b"z"[0]:
                    self.assertEqual(rx_data, b"z" + cmd + b"03F00\r" + cmd + b"03F00\r")
                else:
                    self.assertEqual(rx_data, cmd + b"03F00\r" + b"z" + cmd + b"03F00\r")

        for cmd in cmd_send_ext:
            self.send(cmd + b"0137FEC80\r")
            if cmd == b"R" or cmd == b"T":
                rx_data = self.receive()
                self.assertEqual(len(rx_data), len(b"Z" + cmd + b"0137FEC80\r" + cmd + b"0137FEC80\r"))
                if rx_data[0] == b"Z"[0]:
                    self.assertEqual(rx_data, b"Z" + cmd + b"0137FEC80\r" + cmd + b"0137FEC80\r")
                else:
                    self.assertEqual(rx_data, cmd + b"0137FEC80\r" + b"Z" + cmd + b"0137FEC80\r")
            else:
                rx_data = self.receive()
                self.assertEqual(len(rx_data), len(b"Z" + cmd + b"0137FEC800\r" + cmd + b"0137FEC800\r"))
                if rx_data[0] == b"Z"[0]:
                    self.assertEqual(rx_data, b"Z" + cmd + b"0137FEC800\r" + cmd + b"0137FEC800\r")
                else:
                    self.assertEqual(rx_data, cmd + b"0137FEC800\r" + b"Z" + cmd + b"0137FEC800\r")

        self.send(b"C\r")
        self.assertEqual(self.receive(), b"\r")


    def test_filter_basic(self):
        cmd_send_std = (b"r", b"t", b"d", b"b")
        cmd_send_ext = (b"R", b"T", b"D", b"B")

        #self.print_on = True

        # check pass all in CAN loopback mode
        self.send(b"=\r")
        self.assertEqual(self.receive(), b"\r")

        for cmd in cmd_send_std:
            self.send(cmd + b"03F0\r")
            self.assertEqual(self.receive(), b"z\r" + cmd + b"03F0\r")
            self.send(cmd + b"7C00\r")
            self.assertEqual(self.receive(), b"z\r" + cmd + b"7C00\r")

        for cmd in cmd_send_ext:
            self.send(cmd + b"0000003F0\r")
            self.assertEqual(self.receive(), b"Z\r" + cmd + b"0000003F0\r")
            self.send(cmd + b"000007C00\r")
            self.assertEqual(self.receive(), b"Z\r" + cmd + b"000007C00\r")
            self.send(cmd + b"0137FEC80\r")
            self.assertEqual(self.receive(), b"Z\r" + cmd + b"0137FEC80\r")
            self.send(cmd + b"1EC801370\r")
            self.assertEqual(self.receive(), b"Z\r" + cmd + b"1EC801370\r")

        self.send(b"C\r")
        self.assertEqual(self.receive(), b"\r")

        # check pass 0x03F in CAN loopback mode
        self.send(b"M0000003F\r")
        self.assertEqual(self.receive(), b"\r")
        self.send(b"mFFFFF800\r")
        self.assertEqual(self.receive(), b"\r")

        self.send(b"=\r")
        self.assertEqual(self.receive(), b"\r")

        for cmd in cmd_send_std:
            self.send(cmd + b"03F0\r")
            self.assertEqual(self.receive(), b"z\r" + cmd + b"03F0\r")
            self.send(cmd + b"7C00\r")
            self.assertEqual(self.receive(), b"z\r")

        for cmd in cmd_send_ext:
            self.send(cmd + b"0000003F0\r")
            self.assertEqual(self.receive(), b"Z\r" + cmd + b"0000003F0\r")
            self.send(cmd + b"000007C00\r")
            self.assertEqual(self.receive(), b"Z\r")
            self.send(cmd + b"0137FEC80\r")
            self.assertEqual(self.receive(), b"Z\r")
            self.send(cmd + b"1EC801370\r")
            self.assertEqual(self.receive(), b"Z\r")

        self.send(b"C\r")
        self.assertEqual(self.receive(), b"\r")

        # check pass 0x0137FEC8 in CAN loopback mode
        self.send(b"M0137FEC8\r")
        self.assertEqual(self.receive(), b"\r")
        self.send(b"mE0000000\r")
        self.assertEqual(self.receive(), b"\r")

        self.send(b"=\r")
        self.assertEqual(self.receive(), b"\r")

        for cmd in cmd_send_std:
            self.send(cmd + b"03F0\r")
            #self.assertEqual(self.receive(), b"z\r")
            self.receive()
            self.send(cmd + b"7C00\r")
            #self.assertEqual(self.receive(), b"z\r")
            self.receive()

        for cmd in cmd_send_ext:
            self.send(cmd + b"0000003F0\r")
            #self.assertEqual(self.receive(), b"Z\r")
            self.receive()
            self.send(cmd + b"000007C00\r")
            #self.assertEqual(self.receive(), b"Z\r")
            self.receive()
            self.send(cmd + b"0137FEC80\r")
            #self.assertEqual(self.receive(), b"Z\r")
            self.receive()
            self.send(cmd + b"1EC801370\r")
            #self.assertEqual(self.receive(), b"Z\r" + cmd + b"1EC801370\r")
            self.receive()

        self.send(b"C\r")
        self.assertEqual(self.receive(), b"\r")
        

    def test_filter_every_bits(self):
        # receive std
        self.send(b"M80000000\r")
        self.assertEqual(self.receive(), b"\r")
        self.send(b"m00000000\r")
        self.assertEqual(self.receive(), b"\r")

        self.send(b"=\r")
        self.assertEqual(self.receive(), b"\r")

        self.send(b"t0000\r")
        self.assertEqual(self.receive(), b"z\r" + b"t0000\r")
        for idx in range(0, 11):
            self.send(b"t" + (f'{(1 << idx):03X}').encode() + b"0\r")
            self.assertEqual(self.receive(), b"z\r")
        self.send(b"T000000000\r")
        self.assertEqual(self.receive(), b"Z\r")
        for idx in range(0, 29):
            self.send(b"T" + (f'{(1 << idx):08X}').encode() + b"0\r")
            self.assertEqual(self.receive(), b"Z\r")

        self.send(b"C\r")
        self.assertEqual(self.receive(), b"\r")

        # receive ext
        self.send(b"M00000000\r")
        self.assertEqual(self.receive(), b"\r")
        self.send(b"m00000000\r")
        self.assertEqual(self.receive(), b"\r")

        self.send(b"=\r")
        self.assertEqual(self.receive(), b"\r")

        self.send(b"t0000\r")
        self.assertEqual(self.receive(), b"z\r")
        for idx in range(0, 11):
            self.send(b"t" + (f'{(1 << idx):03X}').encode() + b"0\r")
            self.assertEqual(self.receive(), b"z\r")
        self.send(b"T000000000\r")
        self.assertEqual(self.receive(), b"Z\r" + b"T000000000\r")
        for idx in range(0, 29):
            self.send(b"T" + (f'{(1 << idx):08X}').encode() + b"0\r")
            self.assertEqual(self.receive(), b"Z\r")

        self.send(b"C\r")
        self.assertEqual(self.receive(), b"\r")

        # receive both
        self.send(b"M00000000\r")
        self.assertEqual(self.receive(), b"\r")
        self.send(b"m80000000\r")
        self.assertEqual(self.receive(), b"\r")

        self.send(b"=\r")
        self.assertEqual(self.receive(), b"\r")

        self.send(b"t0000\r")
        self.assertEqual(self.receive(), b"z\r" + b"t0000\r")
        for idx in range(0, 11):
            self.send(b"t" + (f'{(1 << idx):03X}').encode() + b"0\r")
            self.assertEqual(self.receive(), b"z\r")
        self.send(b"T000000000\r")
        self.assertEqual(self.receive(), b"Z\r" + b"T000000000\r")
        for idx in range(0, 29):
            self.send(b"T" + (f'{(1 << idx):08X}').encode() + b"0\r")
            self.assertEqual(self.receive(), b"Z\r")

        self.send(b"C\r")
        self.assertEqual(self.receive(), b"\r")

        # check consistency
        self.send(b"m80000000\r")
        self.assertEqual(self.receive(), b"\r")
        self.send(b"M00000000\r")
        self.assertEqual(self.receive(), b"\r")

        self.send(b"=\r")
        self.assertEqual(self.receive(), b"\r")

        self.send(b"t0000\r")
        self.assertEqual(self.receive(), b"z\r" + b"t0000\r")
        for idx in range(0, 11):
            self.send(b"t" + (f'{(1 << idx):03X}').encode() + b"0\r")
            self.assertEqual(self.receive(), b"z\r")
        self.send(b"T000000000\r")
        self.assertEqual(self.receive(), b"Z\r" + b"T000000000\r")
        for idx in range(0, 29):
            self.send(b"T" + (f'{(1 << idx):08X}').encode() + b"0\r")
            self.assertEqual(self.receive(), b"Z\r")

        self.send(b"C\r")
        self.assertEqual(self.receive(), b"\r")


    def test_can_rx_buffer(self):
        rx_data_exp = b""
        # check response in CAN loopback mode
        self.send(b"=\r")
        self.assertEqual(self.receive(), b"\r")

        # the buffer can store as least 400 messages (10240 / 22)
        for i in range(0, 400):
            tx_data = b"t03F8001122334455" + format(i, "04X").encode() + b"\r"
            self.send(tx_data)
            rx_data_exp += b"z\r" + tx_data
            time.sleep(0.001)

        # check all reply
        rx_data = self.receive()
        self.assertEqual(rx_data, rx_data_exp)

        # check cycle time
        #self.print_on = True
        self.send(b"?\r")
        self.receive()
        #self.print_on = False       

        self.send(b"C\r")
        self.assertEqual(self.receive(), b"\r")


    def test_can_tx_buffer(self):
        rx_data_exp = b""
        # check response in CAN loopback mode
        self.send(b"S0\r")  # take ~10ms to send one frame
        self.assertEqual(self.receive(), b"\r")
        self.send(b"=\r")
        self.assertEqual(self.receive(), b"\r")

        # the buffer can store as least 64 messages
        for i in range(0, 64):
            tx_data = b"t03F8001122334455" + format(i, "04X").encode() + b"\r"
            self.send(tx_data)
            rx_data_exp += tx_data

        # check all reply
        rx_data = self.receive()
        rx_data += self.receive()    # just to make sure (need time to tx all)
        rx_data = rx_data.replace(b"z\r", b"")
        self.assertEqual(rx_data, rx_data_exp)

        self.send(b"C\r")
        self.assertEqual(self.receive(), b"\r")


if __name__ == "__main__":
    unittest.main()
