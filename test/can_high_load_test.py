#!/usr/bin/env python3

import serial
import time
import threading

def check_key():
    while True:
        if input() == 'q':
            print("quit now")
            break

check_key_thread = threading.Thread(target=check_key)
check_key_thread.start()

#canable = serial.Serial("/dev/ttyACM0", timeout=1, write_timeout=1)
canable = serial.Serial("COM9", timeout=1, write_timeout=1)

canable.write(b"C\r")
canable.write(b"S8\r")
canable.write(b"Y5\r")
canable.write(b"=\r")
time.sleep(0.1)
canable.read_until()
print("port_closed ", canable.port)
print("")

data_write = b"00112233445566778899AABBCCDDEEFF"
data_write = b"b000F" + data_write + data_write + data_write + data_write + b"\r"

depth_max = 10
depth_cur = 0

tx_len = 0
rx_len = 0
tx_cnt = 0
rx_cnt = 0

tick_1s = int(round(time.time() * 1000)) + 1000

while True:
    if depth_cur < depth_max:
        canable.write(data_write)
        tx_len += len(data_write)
        tx_cnt += 1
        depth_cur += 1

    data_read = canable.read_all()
    rx_len += len(data_read)
    for byte in data_read:
        if bytes([byte]) == b"b":
            rx_cnt += 1
            depth_cur -= 1

    ms = int(round(time.time() * 1000))
    if ms > tick_1s:
        tick_1s = ms + 1000
        
        print('tx speed:', tx_len / 1000, 'kB/s\t', tx_len * 8 / 1000, 'kbits/s')
        print('rx speed:', rx_len / 1000, 'kB/s\t', rx_len * 8 / 1000, 'kbits/s')
        print('CAN trafic:', tx_cnt, "frames/s")
        print('')
        tx_len = 0
        rx_len = 0
        tx_cnt = 0
        rx_cnt = 0
        
        if check_key_thread.is_alive() == False:
            break

canable.read_all()
canable.close()

