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

        # FIXME unable to send DLC > 8
        tx_data = b"r03F8\r"
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

        # FIXME unable to send DLC > 8
        tx_data = b"R0137FEC88\r"
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

        # FIXME unable to send DLC > 8
        tx_data = b"r03F8\r"
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

        # FIXME unable to send DLC > 8
        tx_data = b"R0137FEC88\r"
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


    def test_timestamp(self):
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

        sleep_time_ms = 15 * 1000
        time.sleep(sleep_time_ms / 1000)

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

        # Proving 2% accuracy. 300ms should be acceptable for USB latency.
        self.assertLess(abs(sleep_time_ms - diff_time_ms), 300)

        self.send(b"C\r")
        self.assertEqual(self.receive(), b"\r")


if __name__ == "__main__":
    unittest.main()
