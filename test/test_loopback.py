#!/usr/bin/env python3

import unittest

import time
from device_under_test import DeviceUnderTest


class LoopbackTestCase(unittest.TestCase):

    print_on: bool
    dut: DeviceUnderTest

    def setUp(self):
        self.dut = DeviceUnderTest()
        self.dut.open()
        self.dut.setup()


    def tearDown(self):
        # close serial
        self.dut.close()


    def test_internal_loopback(self):
        cmd_send_std = (b"r", b"t", b"d", b"b")
        cmd_send_ext = (b"R", b"T", b"D", b"B")

        # check response to shortest SEND in CAN loopback mode
        self.dut.send(b"=\r")
        self.assertEqual(self.dut.receive(), b"\r")
        for cmd in cmd_send_std:
            self.dut.send(cmd + b"03F0\r")
            self.assertEqual(self.dut.receive(), b"z\r" + cmd + b"03F0\r")
        for cmd in cmd_send_ext:
            self.dut.send(cmd + b"0137FEC80\r")
            self.assertEqual(self.dut.receive(), b"Z\r" + cmd + b"0137FEC80\r")
        self.dut.send(b"C\r")
        self.assertEqual(self.dut.receive(), b"\r")

        # check response to longest SEND in CAN loopback mode
        self.dut.send(b"=\r")
        self.assertEqual(self.dut.receive(), b"\r")
        tx_data = b"r03FF\r"
        self.dut.send(tx_data)
        self.assertEqual(self.dut.receive(), b"z\r" + tx_data)
        tx_data = b"t03F80011223344556677\r"
        self.dut.send(tx_data)
        self.assertEqual(self.dut.receive(), b"z\r" + tx_data)
        tx_data = b"d03FF00112233445566778899AABBCCDDEEFF00112233445566778899AABBCCDDEEFF00112233445566778899AABBCCDDEEFF00112233445566778899AABBCCDDEEFF\r"
        self.dut.send(tx_data)
        self.assertEqual(self.dut.receive(), b"z\r" + tx_data)
        tx_data = b"b03FF00112233445566778899AABBCCDDEEFF00112233445566778899AABBCCDDEEFF00112233445566778899AABBCCDDEEFF00112233445566778899AABBCCDDEEFF\r"
        self.dut.send(tx_data)
        self.assertEqual(self.dut.receive(), b"z\r" + tx_data)
        tx_data = b"R0137FEC8F\r"
        self.dut.send(tx_data)
        self.assertEqual(self.dut.receive(), b"Z\r" + tx_data)
        tx_data = b"T0137FEC880011223344556677\r"
        self.dut.send(tx_data)
        self.assertEqual(self.dut.receive(), b"Z\r" + tx_data)
        tx_data = b"D0137FEC8F00112233445566778899AABBCCDDEEFF00112233445566778899AABBCCDDEEFF00112233445566778899AABBCCDDEEFF00112233445566778899AABBCCDDEEFF\r"
        self.dut.send(tx_data)
        self.assertEqual(self.dut.receive(), b"Z\r" + tx_data)
        tx_data = b"B0137FEC8F00112233445566778899AABBCCDDEEFF00112233445566778899AABBCCDDEEFF00112233445566778899AABBCCDDEEFF00112233445566778899AABBCCDDEEFF\r"
        self.dut.send(tx_data)
        self.assertEqual(self.dut.receive(), b"Z\r" + tx_data)
        self.dut.send(b"C\r")
        self.assertEqual(self.dut.receive(), b"\r")


    def test_external_loopback(self):
        cmd_send_std = (b"r", b"t", b"d", b"b")
        cmd_send_ext = (b"R", b"T", b"D", b"B")

        # check response to shortest SEND in CAN loopback mode
        self.dut.send(b"+\r")
        self.assertEqual(self.dut.receive(), b"\r")
        for cmd in cmd_send_std:
            self.dut.send(cmd + b"03F0\r")
            self.assertEqual(self.dut.receive(), b"z\r" + cmd + b"03F0\r")
        for cmd in cmd_send_ext:
            self.dut.send(cmd + b"0137FEC80\r")
            self.assertEqual(self.dut.receive(), b"Z\r" + cmd + b"0137FEC80\r")
        self.dut.send(b"C\r")
        self.assertEqual(self.dut.receive(), b"\r")

        # check response to longest SEND in CAN loopback mode
        self.dut.send(b"+\r")
        self.assertEqual(self.dut.receive(), b"\r")
        tx_data = b"r03FF\r"
        self.dut.send(tx_data)
        self.assertEqual(self.dut.receive(), b"z\r" + tx_data)
        tx_data = b"t03F80011223344556677\r"
        self.dut.send(tx_data)
        self.assertEqual(self.dut.receive(), b"z\r" + tx_data)
        tx_data = b"d03FF00112233445566778899AABBCCDDEEFF00112233445566778899AABBCCDDEEFF00112233445566778899AABBCCDDEEFF00112233445566778899AABBCCDDEEFF\r"
        self.dut.send(tx_data)
        self.assertEqual(self.dut.receive(), b"z\r" + tx_data)
        tx_data = b"b03FF00112233445566778899AABBCCDDEEFF00112233445566778899AABBCCDDEEFF00112233445566778899AABBCCDDEEFF00112233445566778899AABBCCDDEEFF\r"
        self.dut.send(tx_data)
        self.assertEqual(self.dut.receive(), b"z\r" + tx_data)
        tx_data = b"R0137FEC8F\r"
        self.dut.send(tx_data)
        self.assertEqual(self.dut.receive(), b"Z\r" + tx_data)
        tx_data = b"T0137FEC880011223344556677\r"
        self.dut.send(tx_data)
        self.assertEqual(self.dut.receive(), b"Z\r" + tx_data)
        tx_data = b"D0137FEC8F00112233445566778899AABBCCDDEEFF00112233445566778899AABBCCDDEEFF00112233445566778899AABBCCDDEEFF00112233445566778899AABBCCDDEEFF\r"
        self.dut.send(tx_data)
        self.assertEqual(self.dut.receive(), b"Z\r" + tx_data)
        tx_data = b"B0137FEC8F00112233445566778899AABBCCDDEEFF00112233445566778899AABBCCDDEEFF00112233445566778899AABBCCDDEEFF00112233445566778899AABBCCDDEEFF\r"
        self.dut.send(tx_data)
        self.assertEqual(self.dut.receive(), b"Z\r" + tx_data)
        self.dut.send(b"C\r")
        self.assertEqual(self.dut.receive(), b"\r")


    def test_nominal_bitrate(self):
        #self.dut.print_on = True
        # check response to SEND in every nominal bitrate
        for rate in range(0, 9):
            cmd = "S" + str(rate) + "\r"
            self.dut.send(cmd.encode())
            self.assertEqual(self.dut.receive(), b"\r")
            self.dut.send(b"=\r")
            self.assertEqual(self.dut.receive(), b"\r")
            tx_data = b"b03F80011223344556677\r"
            self.dut.send(tx_data)
            self.assertEqual(self.dut.receive(), b"z\r" + tx_data)
            self.dut.send(b"C\r")
            self.assertEqual(self.dut.receive(), b"\r")


    def test_data_bitrate(self):
        #self.dut.print_on = True
        # check response to SEND in every data bitrate
        for rate in (0, 1, 2, 4, 5, 8):    # for CANable2
        #for rate in (0, 1, 2, 3, 4, 5):    # for USB2CANFDV1
            cmd = "Y" + str(rate) + "\r"
            self.dut.send(cmd.encode())
            self.assertEqual(self.dut.receive(), b"\r")
            self.dut.send(b"=\r")
            self.assertEqual(self.dut.receive(), b"\r")
            tx_data = b"b03F80011223344556677\r"
            self.dut.send(tx_data)
            self.assertEqual(self.dut.receive(), b"z\r" + tx_data)
            self.dut.send(b"C\r")
            self.assertEqual(self.dut.receive(), b"\r")


    def test_timestamp_milli(self):
        cmd_send_std = (b"r", b"t", b"d", b"b")
        cmd_send_ext = (b"R", b"T", b"D", b"B")

        #self.dut.print_on = True

        # check timestamp off in CAN loopback mode
        self.dut.send(b"=\r")
        self.assertEqual(self.dut.receive(), b"\r")
        for cmd in cmd_send_std:
            self.dut.send(cmd + b"03F0\r")
            self.assertEqual(self.dut.receive(), b"z\r" + cmd + b"03F0\r")
        for cmd in cmd_send_ext:
            self.dut.send(cmd + b"0137FEC80\r")
            self.assertEqual(self.dut.receive(), b"Z\r" + cmd + b"0137FEC80\r")
        self.dut.send(b"C\r")
        self.assertEqual(self.dut.receive(), b"\r")

        # check timestamp on in CAN loopback mode
        self.dut.send(b"Z1\r")
        self.assertEqual(self.dut.receive(), b"\r")
        self.dut.send(b"=\r")
        self.assertEqual(self.dut.receive(), b"\r")
        for cmd in cmd_send_std:
            self.dut.send(cmd + b"03F0\r")
            rx_data = self.dut.receive()
            self.assertEqual(len(rx_data), len(b"z\r" + cmd + b"03F0TTTT\r"))
            self.assertEqual(rx_data[:len(b"z\r" + cmd + b"03F0")], b"z\r" + cmd + b"03F0")
        for cmd in cmd_send_ext:
            self.dut.send(cmd + b"0137FEC80\r")
            rx_data = self.dut.receive()
            self.assertEqual(len(rx_data), len(b"Z\r" + cmd + b"0137FEC80TTTT\r"))
            self.assertEqual(rx_data[:len(b"Z\r" + cmd + b"0137FEC80")], b"Z\r" + cmd + b"0137FEC80")
        self.dut.send(b"C\r")
        self.assertEqual(self.dut.receive(), b"\r")

        # check timestamp off in CAN loopback mode
        self.dut.send(b"Z0\r")
        self.assertEqual(self.dut.receive(), b"\r")
        self.dut.send(b"=\r")
        self.assertEqual(self.dut.receive(), b"\r")
        for cmd in cmd_send_std:
            self.dut.send(cmd + b"03F0\r")
            self.assertEqual(self.dut.receive(), b"z\r" + cmd + b"03F0\r")
        for cmd in cmd_send_ext:
            self.dut.send(cmd + b"0137FEC80\r")
            self.assertEqual(self.dut.receive(), b"Z\r" + cmd + b"0137FEC80\r")
        self.dut.send(b"C\r")
        self.assertEqual(self.dut.receive(), b"\r")

        # check timestamp accuracy in CAN loopback mode
        self.dut.send(b"Z1\r")
        self.assertEqual(self.dut.receive(), b"\r")
        self.dut.send(b"=\r")
        self.assertEqual(self.dut.receive(), b"\r")
        
        #  send first frame and get timestamp
        self.dut.send(b"t03F0\r")
        rx_data = self.dut.receive()
        self.assertEqual(len(rx_data), len(b"z\r" + b"t03F0TTTT\r"))
        self.assertEqual(rx_data[:len(b"z\r" + b"t03F0")], b"z\r" + b"t03F0")
        last_timestamp = rx_data[len(b"z\r" + b"t03F0"):len(b"z\r" + b"t03F0") + 4]
        last_time_ms = int(last_timestamp.decode(), 16)

        #  sleep for a while
        sleep_time_ms = 30 * 1000
        time.sleep(sleep_time_ms / 1000.0)

        #  send second frame and get timestamp
        self.dut.send(b"t03F0\r")
        rx_data = self.dut.receive()
        self.assertEqual(len(rx_data), len(b"z\r" + b"t03F0TTTT\r"))
        self.assertEqual(rx_data[:len(b"z\r" + b"t03F0")], b"z\r" + b"t03F0")
        crnt_timestamp = rx_data[len(b"z\r" + b"t03F0"):len(b"z\r" + b"t03F0") + 4]
        crnt_time_ms = int(crnt_timestamp.decode(), 16)
        if crnt_time_ms > last_time_ms:
            diff_time_ms = crnt_time_ms - last_time_ms
        else:
            diff_time_ms = (60000 + crnt_time_ms) - last_time_ms

        # Proving 2% accuracy. 600ms should be acceptable for USB latency.
        self.assertLess(abs(sleep_time_ms - diff_time_ms), 600)
        self.dut.send(b"C\r")
        self.assertEqual(self.dut.receive(), b"\r")


    def test_timestamp_micro(self):
        cmd_send_std = (b"r", b"t", b"d", b"b")
        cmd_send_ext = (b"R", b"T", b"D", b"B")

        #self.dut.print_on = True

        # check timestamp off in CAN loopback mode
        self.dut.send(b"=\r")
        self.assertEqual(self.dut.receive(), b"\r")
        for cmd in cmd_send_std:
            self.dut.send(cmd + b"03F0\r")
            self.assertEqual(self.dut.receive(), b"z\r" + cmd + b"03F0\r")
        for cmd in cmd_send_ext:
            self.dut.send(cmd + b"0137FEC80\r")
            self.assertEqual(self.dut.receive(), b"Z\r" + cmd + b"0137FEC80\r")
        self.dut.send(b"C\r")
        self.assertEqual(self.dut.receive(), b"\r")

        # check timestamp on in CAN loopback mode
        self.dut.send(b"Z2\r")
        self.assertEqual(self.dut.receive(), b"\r")
        self.dut.send(b"=\r")
        self.assertEqual(self.dut.receive(), b"\r")
        for cmd in cmd_send_std:
            self.dut.send(cmd + b"03F0\r")
            rx_data = self.dut.receive()
            self.assertEqual(len(rx_data), len(b"z\r" + cmd + b"03F0TTTTTTTT\r"))
            self.assertEqual(rx_data[:len(b"z\r" + cmd + b"03F0")], b"z\r" + cmd + b"03F0")
        for cmd in cmd_send_ext:
            self.dut.send(cmd + b"0137FEC80\r")
            rx_data = self.dut.receive()
            self.assertEqual(len(rx_data), len(b"Z\r" + cmd + b"0137FEC80TTTTTTTT\r"))
            self.assertEqual(rx_data[:len(b"Z\r" + cmd + b"0137FEC80")], b"Z\r" + cmd + b"0137FEC80")
        self.dut.send(b"C\r")
        self.assertEqual(self.dut.receive(), b"\r")

        # check timestamp off in CAN loopback mode
        self.dut.send(b"Z0\r")
        self.assertEqual(self.dut.receive(), b"\r")
        self.dut.send(b"=\r")
        self.assertEqual(self.dut.receive(), b"\r")
        for cmd in cmd_send_std:
            self.dut.send(cmd + b"03F0\r")
            self.assertEqual(self.dut.receive(), b"z\r" + cmd + b"03F0\r")
        for cmd in cmd_send_ext:
            self.dut.send(cmd + b"0137FEC80\r")
            self.assertEqual(self.dut.receive(), b"Z\r" + cmd + b"0137FEC80\r")
        self.dut.send(b"C\r")
        self.assertEqual(self.dut.receive(), b"\r")

        # check timestamp accuracy in CAN loopback mode
        self.dut.send(b"Z2\r")
        self.assertEqual(self.dut.receive(), b"\r")
        self.dut.send(b"=\r")
        self.assertEqual(self.dut.receive(), b"\r")

        #  send first frame and get timestamp
        self.dut.send(b"t03F0\r")
        rx_data = self.dut.receive()
        self.assertEqual(len(rx_data), len(b"z\r" + b"t03F0TTTTTTTT\r"))
        self.assertEqual(rx_data[:len(b"z\r" + b"t03F0")], b"z\r" + b"t03F0")
        last_timestamp = rx_data[len(b"z\r" + b"t03F0"):len(b"z\r" + b"t03F0") + 8]
        last_time_us = int(last_timestamp.decode(), 16)

        #  sleep for a while
        sleep_time_us = 30 * 1000 * 1000
        time.sleep(sleep_time_us / 1000.0 / 1000.0)

        #  send second frame and get timestamp
        self.dut.send(b"t03F0\r")
        rx_data = self.dut.receive()
        self.assertEqual(len(rx_data), len(b"z\r" + b"t03F0TTTTTTTT\r"))
        self.assertEqual(rx_data[:len(b"z\r" + b"t03F0")], b"z\r" + b"t03F0")
        crnt_timestamp = rx_data[len(b"z\r" + b"t03F0"):len(b"z\r" + b"t03F0") + 8]
        crnt_time_us = int(crnt_timestamp.decode(), 16)
        if crnt_time_us > last_time_us:
            diff_time_us = crnt_time_us - last_time_us
        else:
            diff_time_us = (3600000000 + crnt_time_us) - last_time_us

        # Proving 2% accuracy. 600ms should be acceptable for USB latency.
        self.assertLess(abs(sleep_time_us - diff_time_us), 600 * 1000)
        self.dut.send(b"C\r")
        self.assertEqual(self.dut.receive(), b"\r")


    def test_timestamp_same_stamp(self):
        #self.dut.print_on = True

        # check timestamp on in CAN loopback mode
        self.dut.send(b"z2003\r")
        self.assertEqual(self.dut.receive(), b"\r")
        self.dut.send(b"=\r")
        self.assertEqual(self.dut.receive(), b"\r")
        self.dut.send(b"t03F0\r")
        rx_data = self.dut.receive()
        self.assertEqual(len(rx_data), len(b"\r" + b"zt03F0TTTTTTTT\r" + b"t03F0TTTTTTTT\r"))
        if rx_data[1] == b"z"[0]:
            tx_timestamp = rx_data[len(b"\rzt03F0"):len(b"\rzt03F0") + 8]
        else:
            tx_timestamp = rx_data[len(b"\rt03F0TTTTTTTT\rzt03F0"):len(b"\rt03F0TTTTTTTT\rzt03F0") + 8]
        if rx_data[1] == b"z"[0]:
            rx_timestamp = rx_data[len(b"\rzt03F0TTTTTTTT\rt03F0"):len(b"\rzt03F0TTTTTTTT\rt03F0") + 8]
        else:
            rx_timestamp = rx_data[len(b"\rt03F0"):len(b"\rt03F0") + 8]
        self.assertEqual(tx_timestamp, rx_timestamp)
        self.dut.send(b"C\r")
        self.assertEqual(self.dut.receive(), b"\r")


    def test_timestamp_consistency(self):
        #self.dut.print_on = True

        # Compare timestamp for a Z[CR] command and for a received CAN frame
        self.dut.send(b"S8\r")
        self.assertEqual(self.dut.receive(), b"\r")
        self.dut.send(b"z2001\r")
        self.assertEqual(self.dut.receive(), b"\r")
        self.dut.send(b"=\r")
        self.assertEqual(self.dut.receive(), b"\r")
        self.dut.send(b"Z\rt03F0\r")
        rx_data = self.dut.receive() + self.dut.receive()
        last_timestamp = rx_data[len(b"Z"):len(b"Z") + 8]
        last_time_us = int(last_timestamp.decode(), 16)
        crnt_timestamp = rx_data[len(b"ZXXXXXXXX\rz\rt03F0"):len(b"ZXXXXXXXX\rz\rt03F0") + 8]
        crnt_time_us = int(crnt_timestamp.decode(), 16)
        if crnt_time_us > last_time_us:
            diff_time_us = crnt_time_us - last_time_us
        else:
            diff_time_us = (3600000000 + crnt_time_us) - last_time_us

        # Difference should be less than time to send the frame (~50us) + main loop cycle (~100us)
        self.assertLess(diff_time_us, 200)
        self.dut.send(b"C\r")
        self.assertEqual(self.dut.receive(), b"\r")


    def test_timestamp_accuracy_milli(self):
        #self.dut.print_on = True

        # check timestamp on in CAN loopback mode
        self.dut.send(b"Z1\r")
        self.assertEqual(self.dut.receive(), b"\r")
        self.dut.send(b"S0\r")
        self.assertEqual(self.dut.receive(), b"\r")
        self.dut.send(b"Y1\r")
        self.assertEqual(self.dut.receive(), b"\r")
        self.dut.send(b"=\r")
        self.assertEqual(self.dut.receive(), b"\r")


        # test frame number 1 * 1 ~ 5ms
        tx_frame = b"t55585555555555555555"
        self.dut.send(tx_frame + b"\r" + tx_frame + b"\r")
        time.sleep(0.1)
        rx_data = self.dut.receive()
        self.assertEqual(len(rx_data), 2 * (len(b"z\r") + len(tx_frame) + len(b"TTTT\r")))

        pos = 2 * len(b"z\r") + len(tx_frame)
        timestamp_1st = rx_data[pos : pos + 4]

        pos = 2 * len(b"z\r") + len(tx_frame) + len(b"TTTT\r") + len(tx_frame)
        timestamp_2nd = rx_data[pos : pos + 4]

        time_exp_us = (int(timestamp_1st, 16) * 1000 + (47 + 8 * 8 + 1) * 100) % 60000000   # 1 stuff bits?
        self.assertLess(abs(time_exp_us - int(timestamp_2nd, 16) * 1000), 1000)


        # test frame number 2 * 1 ~ 5ms
        tx_frame = b"B1555555585555555555555555"
        self.dut.send(tx_frame + b"\r" + tx_frame + b"\r")
        time.sleep(0.1)
        rx_data = self.dut.receive()
        self.assertEqual(len(rx_data), 2 * (len(b"Z\r") + len(tx_frame) + len(b"TTTT\r")))

        pos = 2 * len(b"Z\r") + len(tx_frame)
        timestamp_1st = rx_data[pos : pos + 4]

        pos = 2 * len(b"Z\r") + len(tx_frame) + len(b"TTTT\r") + len(tx_frame)
        timestamp_2nd = rx_data[pos : pos + 4]

        time_exp_us = (int(timestamp_1st, 16) * 1000 + 49 * 100 + 8 * 8 + 26 + 7) % 60000000   # 7 stuff bits?
        self.assertLess(abs(time_exp_us - int(timestamp_2nd, 16) * 1000), 1000)


        # close port
        self.dut.send(b"C\r")
        self.assertEqual(self.dut.receive(), b"\r")


    def test_timestamp_accuracy_micro(self):
        #self.dut.print_on = True

        # check timestamp on in CAN loopback mode
        self.dut.send(b"Z2\r")
        self.assertEqual(self.dut.receive(), b"\r")
        self.dut.send(b"S0\r")
        self.assertEqual(self.dut.receive(), b"\r")
        self.dut.send(b"Y1\r")
        self.assertEqual(self.dut.receive(), b"\r")
        self.dut.send(b"=\r")
        self.assertEqual(self.dut.receive(), b"\r")


        # test frame number 1 * 1 ~ 5ms
        tx_frame = b"t55585555555555555555"
        self.dut.send(tx_frame + b"\r" + tx_frame + b"\r")
        time.sleep(0.1)
        rx_data = self.dut.receive()
        self.assertEqual(len(rx_data), 2 * (len(b"z\r") + len(tx_frame) + len(b"TTTTTTTT\r")))

        pos = 2 * len(b"z\r") + len(tx_frame)
        timestamp_1st = rx_data[pos : pos + 8]

        pos = 2 * len(b"z\r") + len(tx_frame) + len(b"TTTTTTTT\r") + len(tx_frame)
        timestamp_2nd = rx_data[pos : pos + 8]

        time_exp_us = (int(timestamp_1st, 16) + (47 + 8 * 8 + 1) * 100) % 3600000000   # 1 stuff bits?
        self.assertEqual(time_exp_us, int(timestamp_2nd, 16))


        # test frame number 2 * 1 ~ 5ms
        tx_frame = b"B1555555585555555555555555"
        self.dut.send(tx_frame + b"\r" + tx_frame + b"\r")
        time.sleep(0.1)
        rx_data = self.dut.receive()
        self.assertEqual(len(rx_data), 2 * (len(b"Z\r") + len(tx_frame) + len(b"TTTTTTTT\r")))

        pos = 2 * len(b"Z\r") + len(tx_frame)
        timestamp_1st = rx_data[pos : pos + 8]

        pos = 2 * len(b"Z\r") + len(tx_frame) + len(b"TTTTTTTT\r") + len(tx_frame)
        timestamp_2nd = rx_data[pos : pos + 8]

        time_exp_us = (int(timestamp_1st, 16) + 49 * 100 + 8 * 8 + 26 + 7) % 3600000000   # 7 stuff bits?
        self.assertEqual(time_exp_us, int(timestamp_2nd, 16))


        # test frame number 1 * 20 ~ 100ms
        tx_frame = b"t55585555555555555555"
        for i in range(0, 20):
            self.dut.send(tx_frame + b"\r")
        time.sleep(0.5)
        rx_data = self.dut.receive()
        self.assertEqual(len(rx_data), 20 * (len(b"z\r") + len(tx_frame) + len(b"TTTTTTTT\r")))

        rx_data = rx_data.replace(b"z\r", b"")

        pos = len(tx_frame)
        timestamp_1st = rx_data[pos : pos + 8]

        pos = 19 * (len(tx_frame) + len(b"TTTTTTTT\r")) + len(tx_frame)
        timestamp_2nd = rx_data[pos : pos + 8]

        time_exp_us = (int(timestamp_1st, 16) + 19 * (47 + 8 * 8 + 1) * 100) % 3600000000   # 1 stuff bits?
        self.assertEqual(time_exp_us, int(timestamp_2nd, 16))


        # test frame number 2 * 20 ~ 100ms
        tx_frame = b"B1555555585555555555555555"
        for i in range(0, 20):
            self.dut.send(tx_frame + b"\r")
        time.sleep(0.5)
        rx_data = self.dut.receive()
        self.assertEqual(len(rx_data), 20 * (len(b"Z\r") + len(tx_frame) + len(b"TTTTTTTT\r")))

        rx_data = rx_data.replace(b"Z\r", b"")

        pos = len(tx_frame)
        timestamp_1st = rx_data[pos : pos + 8]

        pos = 19 * (len(tx_frame) + len(b"TTTTTTTT\r")) + len(tx_frame)
        timestamp_2nd = rx_data[pos : pos + 8]

        time_exp_us = (int(timestamp_1st, 16) + 19 * (49 * 100 + 8 * 8 + 26 + 7)) % 3600000000   # 7 stuff bits?
        self.assertEqual(time_exp_us, int(timestamp_2nd, 16))


        # close port
        self.dut.send(b"C\r")
        self.assertEqual(self.dut.receive(), b"\r")


    def test_tx_off_rx_on(self):
        cmd_send_std = (b"r", b"t", b"d", b"b")
        cmd_send_ext = (b"R", b"T", b"D", b"B")

        #self.dut.print_on = True

        # check tx event on in CAN loopback mode
        self.dut.send(b"z0001\r")
        self.assertEqual(self.dut.receive(), b"\r")
        self.dut.send(b"=\r")
        self.assertEqual(self.dut.receive(), b"\r")
        for cmd in cmd_send_std:
            self.dut.send(cmd + b"03F0\r")
            self.assertEqual(self.dut.receive(), b"z\r" + cmd + b"03F0\r")
        for cmd in cmd_send_ext:
            self.dut.send(cmd + b"0137FEC80\r")
            self.assertEqual(self.dut.receive(), b"Z\r" + cmd + b"0137FEC80\r")
        self.dut.send(b"C\r")
        self.assertEqual(self.dut.receive(), b"\r")


    def test_tx_on_rx_off(self):
        cmd_send_std = (b"r", b"t", b"d", b"b")
        cmd_send_ext = (b"R", b"T", b"D", b"B")

        #self.dut.print_on = True

        # check tx event on in CAN loopback mode
        self.dut.send(b"z0002\r")
        self.assertEqual(self.dut.receive(), b"\r")
        self.dut.send(b"=\r")
        self.assertEqual(self.dut.receive(), b"\r")
        for cmd in cmd_send_std:
            self.dut.send(cmd + b"03F0\r")
            self.assertEqual(self.dut.receive(), b"\r" + b"z" + cmd + b"03F0\r")
        for cmd in cmd_send_ext:
            self.dut.send(cmd + b"0137FEC80\r")
            self.assertEqual(self.dut.receive(), b"\r" + b"Z" + cmd + b"0137FEC80\r")
        self.dut.send(b"C\r")
        self.assertEqual(self.dut.receive(), b"\r")


    def test_esi_on(self):
        cmd_send_std = (b"r", b"t", b"d", b"b")
        cmd_send_ext = (b"R", b"T", b"D", b"B")

        #self.dut.print_on = True

        # check tx event on in CAN loopback mode
        self.dut.send(b"z0013\r")
        self.assertEqual(self.dut.receive(), b"\r")
        self.dut.send(b"=\r")
        self.assertEqual(self.dut.receive(), b"\r")
        for cmd in cmd_send_std:
            self.dut.send(cmd + b"03F0\r")
            if cmd == b"r" or cmd == b"t":
                rx_data = self.dut.receive()
                self.assertEqual(len(rx_data), len(b"\r" + b"z" + cmd + b"03F0\r" + cmd + b"03F0\r"))
                if rx_data[1] == b"z"[0]:
                    self.assertEqual(rx_data, b"\r" + b"z" + cmd + b"03F0\r" + cmd + b"03F0\r")
                else:
                    self.assertEqual(rx_data, b"\r" + cmd + b"03F0\r" + b"z" + cmd + b"03F0\r")
            else:
                rx_data = self.dut.receive()
                self.assertEqual(len(rx_data), len(b"\r" + b"z" + cmd + b"03F00\r" + cmd + b"03F00\r"))
                if rx_data[1] == b"z"[0]:
                    self.assertEqual(rx_data, b"\r" + b"z" + cmd + b"03F00\r" + cmd + b"03F00\r")
                else:
                    self.assertEqual(rx_data, b"\r" + cmd + b"03F00\r" + b"z" + cmd + b"03F00\r")
        for cmd in cmd_send_ext:
            self.dut.send(cmd + b"0137FEC80\r")
            if cmd == b"R" or cmd == b"T":
                rx_data = self.dut.receive()
                self.assertEqual(len(rx_data), len(b"\r" + b"Z" + cmd + b"0137FEC80\r" + cmd + b"0137FEC80\r"))
                if rx_data[1] == b"Z"[0]:
                    self.assertEqual(rx_data, b"\r" + b"Z" + cmd + b"0137FEC80\r" + cmd + b"0137FEC80\r")
                else:
                    self.assertEqual(rx_data, b"\r" + cmd + b"0137FEC80\r" + b"Z" + cmd + b"0137FEC80\r")
            else:
                rx_data = self.dut.receive()
                self.assertEqual(len(rx_data), len(b"\r" + b"Z" + cmd + b"0137FEC800\r" + cmd + b"0137FEC800\r"))
                if rx_data[1] == b"Z"[0]:
                    self.assertEqual(rx_data, b"\r" + b"Z" + cmd + b"0137FEC800\r" + cmd + b"0137FEC800\r")
                else:
                    self.assertEqual(rx_data, b"\r" + cmd + b"0137FEC800\r" + b"Z" + cmd + b"0137FEC800\r")
        self.dut.send(b"C\r")
        self.assertEqual(self.dut.receive(), b"\r")


    def test_filter_basic(self):
        cmd_send_std = (b"r", b"t", b"d", b"b")
        cmd_send_ext = (b"R", b"T", b"D", b"B")

        #self.dut.print_on = True

        # check pass all (default) in CAN loopback mode
        self.dut.send(b"=\r")
        self.assertEqual(self.dut.receive(), b"\r")
        for cmd in cmd_send_std:
            self.dut.send(cmd + b"03F0\r")
            self.assertEqual(self.dut.receive(), b"z\r" + cmd + b"03F0\r")
            self.dut.send(cmd + b"7C00\r")
            self.assertEqual(self.dut.receive(), b"z\r" + cmd + b"7C00\r")
        for cmd in cmd_send_ext:
            self.dut.send(cmd + b"0000003F0\r")
            self.assertEqual(self.dut.receive(), b"Z\r" + cmd + b"0000003F0\r")
            self.dut.send(cmd + b"000007C00\r")
            self.assertEqual(self.dut.receive(), b"Z\r" + cmd + b"000007C00\r")
            self.dut.send(cmd + b"0137FEC80\r")
            self.assertEqual(self.dut.receive(), b"Z\r" + cmd + b"0137FEC80\r")
            self.dut.send(cmd + b"1EC801370\r")
            self.assertEqual(self.dut.receive(), b"Z\r" + cmd + b"1EC801370\r")
        self.dut.send(b"C\r")
        self.assertEqual(self.dut.receive(), b"\r")

        # check pass 0x03F in CAN loopback mode
        self.dut.send(b"M0000003F\r")
        self.assertEqual(self.dut.receive(), b"\r")
        self.dut.send(b"mFFFFF800\r")
        self.assertEqual(self.dut.receive(), b"\r")
        self.dut.send(b"=\r")
        self.assertEqual(self.dut.receive(), b"\r")
        for cmd in cmd_send_std:
            self.dut.send(cmd + b"03F0\r")
            self.assertEqual(self.dut.receive(), b"z\r" + cmd + b"03F0\r")
            self.dut.send(cmd + b"7C00\r")
            self.assertEqual(self.dut.receive(), b"z\r")
        for cmd in cmd_send_ext:
            self.dut.send(cmd + b"0000003F0\r")
            self.assertEqual(self.dut.receive(), b"Z\r" + cmd + b"0000003F0\r")
            self.dut.send(cmd + b"000007C00\r")
            self.assertEqual(self.dut.receive(), b"Z\r")
            self.dut.send(cmd + b"0137FEC80\r")
            self.assertEqual(self.dut.receive(), b"Z\r")
            self.dut.send(cmd + b"1EC801370\r")
            self.assertEqual(self.dut.receive(), b"Z\r")
        self.dut.send(b"C\r")
        self.assertEqual(self.dut.receive(), b"\r")

        # check pass 0x0137FEC8 (0x6C8) in CAN loopback mode
        self.dut.send(b"M0137FEC8\r")
        self.assertEqual(self.dut.receive(), b"\r")
        self.dut.send(b"mE0000000\r")
        self.assertEqual(self.dut.receive(), b"\r")
        self.dut.send(b"=\r")
        self.assertEqual(self.dut.receive(), b"\r")
        for cmd in cmd_send_std:
            self.dut.send(cmd + b"03F0\r")
            self.assertEqual(self.dut.receive(), b"z\r")
            self.dut.send(cmd + b"7C00\r")
            self.assertEqual(self.dut.receive(), b"z\r")
            self.dut.send(cmd + b"6C80\r")
            self.assertEqual(self.dut.receive(), b"z\r" + cmd + b"6C80\r")
        for cmd in cmd_send_ext:
            self.dut.send(cmd + b"0000003F0\r")
            self.assertEqual(self.dut.receive(), b"Z\r")
            self.dut.send(cmd + b"000007C00\r")
            self.assertEqual(self.dut.receive(), b"Z\r")
            self.dut.send(cmd + b"0137FEC80\r")
            self.assertEqual(self.dut.receive(), b"Z\r" + cmd + b"0137FEC80\r")
            self.dut.send(cmd + b"1EC801370\r")
            self.assertEqual(self.dut.receive(), b"Z\r")
        self.dut.send(b"C\r")
        self.assertEqual(self.dut.receive(), b"\r")

        # check pass STD ID 0x03F in CAN loopback mode
        self.dut.send(b"M8000003F\r")
        self.assertEqual(self.dut.receive(), b"\r")
        self.dut.send(b"m00000000\r")
        self.assertEqual(self.dut.receive(), b"\r")
        self.dut.send(b"=\r")
        self.assertEqual(self.dut.receive(), b"\r")
        for cmd in cmd_send_std:
            self.dut.send(cmd + b"03F0\r")
            self.assertEqual(self.dut.receive(), b"z\r" + cmd + b"03F0\r")
            self.dut.send(cmd + b"7C00\r")
            self.assertEqual(self.dut.receive(), b"z\r")
        for cmd in cmd_send_ext:
            self.dut.send(cmd + b"0000003F0\r")
            self.assertEqual(self.dut.receive(), b"Z\r")
            self.dut.send(cmd + b"000007C00\r")
            self.assertEqual(self.dut.receive(), b"Z\r")
            self.dut.send(cmd + b"0137FEC80\r")
            self.assertEqual(self.dut.receive(), b"Z\r")
            self.dut.send(cmd + b"1EC801370\r")
            self.assertEqual(self.dut.receive(), b"Z\r")
        self.dut.send(b"C\r")
        self.assertEqual(self.dut.receive(), b"\r")

        # check pass EXT ID 0x0137FEC8 in CAN loopback mode
        self.dut.send(b"M0137FEC8\r")
        self.assertEqual(self.dut.receive(), b"\r")
        self.dut.send(b"m00000000\r")
        self.assertEqual(self.dut.receive(), b"\r")
        self.dut.send(b"=\r")
        self.assertEqual(self.dut.receive(), b"\r")
        for cmd in cmd_send_std:
            self.dut.send(cmd + b"03F0\r")
            self.assertEqual(self.dut.receive(), b"z\r")
            self.dut.send(cmd + b"7C00\r")
            self.assertEqual(self.dut.receive(), b"z\r")
            self.dut.send(cmd + b"6C80\r")
            self.assertEqual(self.dut.receive(), b"z\r")
        for cmd in cmd_send_ext:
            self.dut.send(cmd + b"0000003F0\r")
            self.assertEqual(self.dut.receive(), b"Z\r")
            self.dut.send(cmd + b"000007C00\r")
            self.assertEqual(self.dut.receive(), b"Z\r")
            self.dut.send(cmd + b"0137FEC80\r")
            self.assertEqual(self.dut.receive(), b"Z\r" + cmd + b"0137FEC80\r")
            self.dut.send(cmd + b"1EC801370\r")
            self.assertEqual(self.dut.receive(), b"Z\r")
        self.dut.send(b"C\r")
        self.assertEqual(self.dut.receive(), b"\r")
        

    def test_filter_every_bits(self):
        # receive std
        self.dut.send(b"M80000000\r")
        self.assertEqual(self.dut.receive(), b"\r")
        self.dut.send(b"m00000000\r")
        self.assertEqual(self.dut.receive(), b"\r")
        self.dut.send(b"=\r")
        self.assertEqual(self.dut.receive(), b"\r")
        self.dut.send(b"t0000\r")
        self.assertEqual(self.dut.receive(), b"z\r" + b"t0000\r")
        for idx in range(0, 11):
            self.dut.send(b"t" + (f'{(1 << idx):03X}').encode() + b"0\r")
            self.assertEqual(self.dut.receive(), b"z\r")
        self.dut.send(b"T000000000\r")
        self.assertEqual(self.dut.receive(), b"Z\r")
        for idx in range(0, 29):
            self.dut.send(b"T" + (f'{(1 << idx):08X}').encode() + b"0\r")
            self.assertEqual(self.dut.receive(), b"Z\r")
        self.dut.send(b"C\r")
        self.assertEqual(self.dut.receive(), b"\r")

        # receive ext
        self.dut.send(b"M00000000\r")
        self.assertEqual(self.dut.receive(), b"\r")
        self.dut.send(b"m00000000\r")
        self.assertEqual(self.dut.receive(), b"\r")
        self.dut.send(b"=\r")
        self.assertEqual(self.dut.receive(), b"\r")
        self.dut.send(b"t0000\r")
        self.assertEqual(self.dut.receive(), b"z\r")
        for idx in range(0, 11):
            self.dut.send(b"t" + (f'{(1 << idx):03X}').encode() + b"0\r")
            self.assertEqual(self.dut.receive(), b"z\r")
        self.dut.send(b"T000000000\r")
        self.assertEqual(self.dut.receive(), b"Z\r" + b"T000000000\r")
        for idx in range(0, 29):
            self.dut.send(b"T" + (f'{(1 << idx):08X}').encode() + b"0\r")
            self.assertEqual(self.dut.receive(), b"Z\r")
        self.dut.send(b"C\r")
        self.assertEqual(self.dut.receive(), b"\r")

        # receive both
        self.dut.send(b"M00000000\r")
        self.assertEqual(self.dut.receive(), b"\r")
        self.dut.send(b"m80000000\r")
        self.assertEqual(self.dut.receive(), b"\r")
        self.dut.send(b"=\r")
        self.assertEqual(self.dut.receive(), b"\r")
        self.dut.send(b"t0000\r")
        self.assertEqual(self.dut.receive(), b"z\r" + b"t0000\r")
        for idx in range(0, 11):
            self.dut.send(b"t" + (f'{(1 << idx):03X}').encode() + b"0\r")
            self.assertEqual(self.dut.receive(), b"z\r")
        self.dut.send(b"T000000000\r")
        self.assertEqual(self.dut.receive(), b"Z\r" + b"T000000000\r")
        for idx in range(0, 29):
            self.dut.send(b"T" + (f'{(1 << idx):08X}').encode() + b"0\r")
            self.assertEqual(self.dut.receive(), b"Z\r")
        self.dut.send(b"C\r")
        self.assertEqual(self.dut.receive(), b"\r")

        # check consistency
        self.dut.send(b"m80000000\r")
        self.assertEqual(self.dut.receive(), b"\r")
        self.dut.send(b"M00000000\r")
        self.assertEqual(self.dut.receive(), b"\r")
        self.dut.send(b"=\r")
        self.assertEqual(self.dut.receive(), b"\r")
        self.dut.send(b"t0000\r")
        self.assertEqual(self.dut.receive(), b"z\r" + b"t0000\r")
        for idx in range(0, 11):
            self.dut.send(b"t" + (f'{(1 << idx):03X}').encode() + b"0\r")
            self.assertEqual(self.dut.receive(), b"z\r")
        self.dut.send(b"T000000000\r")
        self.assertEqual(self.dut.receive(), b"Z\r" + b"T000000000\r")
        for idx in range(0, 29):
            self.dut.send(b"T" + (f'{(1 << idx):08X}').encode() + b"0\r")
            self.assertEqual(self.dut.receive(), b"Z\r")
        self.dut.send(b"C\r")
        self.assertEqual(self.dut.receive(), b"\r")


    def test_can_rx_buffer(self):
        rx_data_exp = b""
        # check response in CAN loopback mode
        self.dut.send(b"=\r")
        self.assertEqual(self.dut.receive(), b"\r")

        # the buffer can store as least 180 messages (4096 / 22)
        for i in range(0, 180):
            tx_data = b"t03F8001122334455" + format(i, "04X").encode() + b"\r"
            self.dut.send(tx_data)
            rx_data_exp += b"z\r" + tx_data
            time.sleep(0.001)

        # check all reply
        rx_data = self.dut.receive()
        self.assertEqual(rx_data, rx_data_exp)

        self.dut.send(b"F\r")
        self.assertEqual(self.dut.receive(), b"F00\r")
        self.dut.send(b"C\r")
        self.assertEqual(self.dut.receive(), b"\r")


    def test_can_tx_buffer(self):
        #self.dut.print_on = True
        rx_data_exp = b""
        # check response in CAN loopback mode
        self.dut.send(b"S0\r")  # take ~10ms to send one frame
        self.assertEqual(self.dut.receive(), b"\r")
        self.dut.send(b"=\r")
        self.assertEqual(self.dut.receive(), b"\r")

        # the buffer can store as least 64 messages
        for i in range(0, 64):
            tx_data = b"t03F8001122334455" + format(i, "04X").encode() + b"\r"
            self.dut.send(tx_data)
            rx_data_exp += tx_data
            time.sleep(0.001)

        # check all reply
        rx_data = self.dut.receive()
        rx_data += self.dut.receive()    # just to make sure (need time to tx all)
        rx_data = rx_data.replace(b"z\r", b"")
        self.assertEqual(rx_data, rx_data_exp)

        self.dut.send(b"F\r")
        self.assertEqual(self.dut.receive(), b"F00\r")
        self.dut.send(b"C\r")
        self.assertEqual(self.dut.receive(), b"\r")


    def test_can_tx_event_buffer(self):
        #self.dut.print_on = True
        rx_data_exp = b""
        # check response in CAN loopback mode
        self.dut.send(b"z0002\r")  # no rx, tx event only
        self.assertEqual(self.dut.receive(), b"\r")
        self.dut.send(b"=\r")
        self.assertEqual(self.dut.receive(), b"\r")

        # the buffer can store as least 180 messages (4096 / 22)
        for i in range(0, 180):
            tx_data = b"t03F8001122334455" + format(i, "04X").encode() + b"\r"
            self.dut.send(tx_data)
            rx_data_exp += b"\r" + b"z" + tx_data
            time.sleep(0.001)

        # check all reply
        rx_data = self.dut.receive()
        self.assertEqual(rx_data, rx_data_exp)

        self.dut.send(b"F\r")
        self.assertEqual(self.dut.receive(), b"F00\r")
        self.dut.send(b"C\r")
        self.assertEqual(self.dut.receive(), b"\r")


    def test_high_rx_frame_rate(self):
        #self.dut.print_on = True
        rx_data_exp = b""
        # check response in CAN loopback mode
        self.dut.send(b"S8\r")
        self.assertEqual(self.dut.receive(), b"\r")
        self.dut.send(b"Y5\r")
        self.assertEqual(self.dut.receive(), b"\r")
        self.dut.send(b"z0001\r")
        self.assertEqual(self.dut.receive(), b"\r")
        self.dut.send(b"=\r")
        self.assertEqual(self.dut.receive(), b"\r")

        # the buffer can store as least 180 messages (4096 / 22)
        for i in range(0, 180):
            tx_data = b"r" + format(i, "03X").encode() + b"0\r"
            self.dut.send(tx_data)
            rx_data_exp += b"z\r" + tx_data
            time.sleep(0.001)

        # check all reply
        rx_data = self.dut.receive()
        self.assertEqual(rx_data, rx_data_exp)

        self.dut.send(b"F\r")
        self.assertEqual(self.dut.receive(), b"F00\r")
        self.dut.send(b"C\r")
        self.assertEqual(self.dut.receive(), b"\r")


    def test_high_tx_frame_rate(self):
        #self.dut.print_on = True
        rx_data_exp = b""
        # check response in CAN loopback mode
        self.dut.send(b"S8\r")
        self.assertEqual(self.dut.receive(), b"\r")
        self.dut.send(b"Y5\r")
        self.assertEqual(self.dut.receive(), b"\r")
        self.dut.send(b"z0002\r")
        self.assertEqual(self.dut.receive(), b"\r")
        self.dut.send(b"=\r")
        self.assertEqual(self.dut.receive(), b"\r")

        # the buffer can store as least 180 messages (4096 / 22)
        for i in range(0, 180):
            tx_data = b"r" + format(i, "03X").encode() + b"0\r"
            self.dut.send(tx_data)
            rx_data_exp += b"\r" + b"z" + tx_data
            time.sleep(0.001)

        # check all reply
        rx_data = self.dut.receive()
        self.assertEqual(rx_data, rx_data_exp)

        self.dut.send(b"F\r")
        self.assertEqual(self.dut.receive(), b"F00\r")
        self.dut.send(b"C\r")
        self.assertEqual(self.dut.receive(), b"\r")


    def test_bus_load(self):
        #self.dut.print_on = True
        rx_data_exp = b""
        # check response in CAN loopback mode
        self.dut.send(b"S0\r")
        self.assertEqual(self.dut.receive(), b"\r")
        self.dut.send(b"z0000\r")
        self.assertEqual(self.dut.receive(), b"\r")
        self.dut.send(b"=\r")
        self.assertEqual(self.dut.receive(), b"\r")

        tx_data = b"t55585555555555555555\r"    # 112bit * 0.1ms = 11.2ms
        for i in range(0, 4):
            tx_data = tx_data + tx_data    # 11.2ms * 16 = 179.2ms

        # 0% mode (prove 10% accuracy)
        time.sleep(1)
        rx_data = self.dut.receive()
        self.dut.send(b"f\r")
        rx_data = self.dut.receive()
        self.assertEqual(len(rx_data), 93)        
        self.assertGreaterEqual(int(rx_data[90:92], 10), 0)
        self.assertLessEqual(int(rx_data[90:92], 10), 0)

        # 18% mode (prove 10% accuracy)
        time.sleep(0.5)
        self.dut.send(tx_data)
        time.sleep(1)
        self.dut.send(tx_data)
        time.sleep(0.5)
        rx_data = self.dut.receive()
        self.dut.send(b"f\r")
        rx_data = self.dut.receive()
        self.assertEqual(len(rx_data), 93)
        self.assertGreaterEqual(int(rx_data[90:92], 10), 8)
        self.assertLessEqual(int(rx_data[90:92], 10), 28)

        # 36% mode (prove 10% accuracy)
        tx_data = tx_data + tx_data
        time.sleep(0.5)
        self.dut.send(tx_data)
        time.sleep(1)
        self.dut.send(tx_data)
        time.sleep(0.5)
        rx_data = self.dut.receive()
        self.dut.send(b"f\r")
        rx_data = self.dut.receive()
        self.assertEqual(len(rx_data), 93)
        self.assertGreaterEqual(int(rx_data[90:92], 10), 26)
        self.assertLessEqual(int(rx_data[90:92], 10), 46)

        # 72% mode (prove 10% accuracy)
        tx_data = tx_data + tx_data
        time.sleep(0.5)
        self.dut.send(tx_data)
        time.sleep(1)
        self.dut.send(tx_data)
        time.sleep(0.5)
        rx_data = self.dut.receive()
        self.dut.send(b"f\r")
        rx_data = self.dut.receive()
        self.assertEqual(len(rx_data), 93)
        self.assertGreaterEqual(int(rx_data[90:92], 10), 62)
        self.assertLessEqual(int(rx_data[90:92], 10), 82)

        self.dut.send(b"C\r")
        self.assertEqual(self.dut.receive(), b"\r")


if __name__ == "__main__":
    unittest.main()
