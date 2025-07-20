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
time.sleep(0.1)
canable.read_until()
print("port_closed ", canable.port)
print("")

data_write = b"00112233445566778899AABBCCDDEEFF"
data_write = b"B00000000F" + data_write + data_write + data_write + data_write + b"\r"
data_write = data_write + data_write
data_write = data_write + data_write
data_write = data_write + data_write
data_write = data_write + data_write

tx_len = 0
rx_len = 0
tx_cnt = 0
rx_cnt = 0

flag_tx = True

tick_1s = int(round(time.time() * 1000)) + 1000

while True:
    if flag_tx:
        canable.write(data_write)
        tx_len += len(data_write)
        tx_cnt += int(len(data_write) / 139)

    data_read = canable.read_all()
    rx_len += len(data_read)
    for byte in data_read:
        if bytes([byte]) == b"\r" or bytes([byte]) == b"\a":
            rx_cnt += 1

    ms = int(round(time.time() * 1000))
    if ms > tick_1s and not flag_tx:
        tick_1s = ms + 1000
        
        print('tx speed:', tx_len / 1000, 'kB/s\t', tx_len * 8 / 1000, 'kbits/s')
        print('rx speed:', rx_len / 1000, 'kB/s\t', rx_len * 8 / 1000, 'kbits/s')
        print('message loss:', tx_cnt - rx_cnt, " / ", tx_cnt)
        print('')
        tx_len = 0
        rx_len = 0
        tx_cnt = 0
        rx_cnt = 0
        
        flag_tx = True
    
        if check_key_thread.is_alive() == False:
            break
    elif ms > tick_1s and flag_tx:
        tick_1s = ms + 1000
        flag_tx = False

canable.read_all()
canable.close()

