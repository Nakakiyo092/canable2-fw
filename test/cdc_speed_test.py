#!/usr/bin/env python3

import argparse
import serial
import time
import threading

def get_argparser():
    parser = argparse.ArgumentParser(
        description="Test USB CDC throughput. Press 'q' + [ENTER] to quit."
    )
    parser.add_argument(
        "devicename",
        type=str,
        help="device name like COM9 or /dev/ttyACM0 (required)"
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "-r", "--rx", 
        action="store_true",
        help="test receiving speed (device -> host)"
    )
    group.add_argument(
        "-t", "--tx", 
        action="store_true",
        help="test transmitting speed (host -> device)"
    )
    parser.add_argument(
        "-d", "--duration",
        type=int,
        default=1,
        help="time to test in seconds"
    )
    parser.add_argument(
        "-c", "--chunk-size",
        type=int,
        default=1,
        help="chunk size for each transmission"
    )
    return parser


def check_key():
    while True:
        if input() == 'q':
            print("quit now")
            break


def make_data_to_write(mode: str, chunk_size: int) -> bytes:
    if mode == "tx":
        single_msg = b"00112233445566778899AABBCCDDEEFF"
        single_msg = b"B00000000F" + single_msg + single_msg + single_msg + single_msg + b"\r"
    else:
        single_msg = b"v\r"

    data_write = b""
    for _ in range(0, chunk_size):
        data_write = data_write + single_msg

    return data_write


def main():
    argparser = get_argparser()
    args = argparser.parse_args()

    try:
        device = serial.Serial(args.devicename, timeout=1, write_timeout=1)
    except Exception as e:
        print("ERROR: Could not open device ", args.devicename)
        print(e)
        return

    check_key_thread = threading.Thread(target=check_key)
    check_key_thread.start()

    device.write(b"O\r")
    time.sleep(0.1)
    device.read_all()
    print("port_open ", device.port)
    device.write(b"V\r")
    time.sleep(0.1)
    print(device.read_all().decode())
    device.write(b"v\r")
    time.sleep(0.1)
    print(device.read_all().decode())
    device.write(b"N\r")
    time.sleep(0.1)
    print(device.read_all().decode())
    print("")

    data_write = make_data_to_write("tx" if args.tx else "rx", args.chunk_size)

    tx_len = 0
    rx_len = 0
    tx_cnt = 0
    rx_cnt = 0

    flag_tx = True

    tick_next = int(round(time.time() * 1000)) + 1000 * args.duration

    while True:
        if flag_tx:
            device.write(data_write)
            tx_len += len(data_write)
            tx_cnt += args.chunk_size

        data_read = device.read_all()
        rx_len += len(data_read)
        for byte in data_read:
            if bytes([byte]) == b"\r" or bytes([byte]) == b"\a":
                rx_cnt += 1

        ms = int(round(time.time() * 1000))
        if ms > tick_next and not flag_tx:
            tx_speed = tx_len / 1000 / args.duration
            rx_speed = rx_len / 1000 / args.duration
            print("tx speed: ", f"{tx_speed:8.2f}", "kB/s\t", f"{tx_speed * 8:8.2f}", "kbits/s")
            print("rx speed: ", f"{rx_speed:8.2f}", "kB/s\t", f"{rx_speed * 8:8.2f}", "kbits/s")
            print("message loss: ", tx_cnt - rx_cnt, " / ", tx_cnt)
            print("")
            #device.write(b"F\r")
            #time.sleep(0.1)
            print("device status: ", device.read_all().decode())
            #device.write(b"f\r")
            #time.sleep(0.1)
            #print(device.read_all().decode())
            device.write(b"?\r")
            time.sleep(0.1)
            print(device.read_all().decode())
            print("")

            tx_len = 0
            rx_len = 0
            tx_cnt = 0
            rx_cnt = 0
            
            ms = int(round(time.time() * 1000))
            tick_next = ms + 1000 * args.duration
            flag_tx = True
        
            if check_key_thread.is_alive() == False:
                break
        elif ms > tick_next and flag_tx:
            tick_next = ms + 1000 
            flag_tx = False

    device.read_all()
    device.close()


if __name__ == "__main__":
    main()
