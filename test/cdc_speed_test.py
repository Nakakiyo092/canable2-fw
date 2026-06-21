#!/usr/bin/env python3

"""
Test USB CDC throughput for a SLCAN device.

License:
    MIT License.
    See the accompanying LICENSE file for full terms.
"""

import time

import argparse
import serial


ROUND_TRIP_TIME_SAMPLES = 5
STATS_INTERVAL_MS = 60_000


def get_argparser():
    """Get argument parser for this script."""
    parser = argparse.ArgumentParser(
        description="Test USB CDC throughput. Press [CTRL] + 'c' to quit."
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
    group.add_argument(
        "-b", "--bi", 
        action="store_true",
        help="test bidirectional speed (host <-> device)"
    )
    parser.add_argument(
        "-i", "--iteration",
        type=int,
        default=0,
        help="number of iterations to test (0 for infinite)"
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
        help="number of times the base message is repeated to form one tx chunk"
    )
    return parser


def setup_device_under_test(dev: serial.Serial, mode: str):
    """Setup device and print test information."""
    print("usb port name:", dev.port)
    print("")

    dev.write(b"\a\r\r")    # Flush the buffer
    dev.write(b"C\r")
    time.sleep(0.1)
    dev.read_all()

    dev.write(b"N\r")
    time.sleep(0.1)
    print("serial number:", dev.read_all().decode())
    dev.write(b"V\r")
    time.sleep(0.1)
    print("slcan version:", dev.read_all().decode())
    dev.write(b"v\r")
    time.sleep(0.1)
    print("detail:")
    print("   ", dev.read_all().decode())
    print("")

    if mode == "bi":
        # Setup maximum CAN speed to stress the device
        dev.write(b"S8\r")
        dev.write(b"Y5\r")
        dev.write(b"+\r")    # TODO: warning if loopback is not supported
        time.sleep(0.1)
        dev.read_all()
        print("can port status: open/loopback (1M/5Mbps)")
    else:
        print("can port status: closed")

    print("")


def cleanup_device_under_test(dev: serial.Serial):
    """Close the device cleanly at the end of the test."""
    dev.write(b"C\r")
    time.sleep(0.1)
    dev.read_all()
    dev.close()


def print_round_trip_time(dev: serial.Serial) -> int:
    """Print round-trip time.
    
    Returns average RTT in us.
    Returns -1 on error.
    """
    rtt = []
    for _ in range(0, ROUND_TRIP_TIME_SAMPLES):
        # Use perf_counter for better resolution (RTT is expected to be less than ms)
        time_start = time.perf_counter()
        dev.write(b"\r")
        dev.read_until(b"\r")
        time_end = time.perf_counter()
        rtt.append(int((time_end - time_start) * 1000 * 1000))

    print("ping:", rtt, "us")
    print("")

    if len(rtt) == 0:
        return -1

    return sum(rtt) // len(rtt)


def make_data_to_write(mode: str, chunk_size: int) -> bytes:
    """Make data to write to device."""
    if mode == "rx":
        #single_msg = b"v\r"    # Higher TX-to-RX gain (if supported by device)
        single_msg = b"V\r"    # Lower gain but widely supported
    else:
        single_msg = b"00112233445566778899AABBCCDDEEFF"
        single_msg = b"B00000000F" + single_msg * 4 + b"\r" # a frame with 64 bytes data

    data_write = b""
    for _ in range(0, chunk_size):
        data_write = data_write + single_msg

    return data_write


def count_message(data: bytes) -> int:
    """Count the number of messages in the data."""
    terminators = {ord("\r"), ord("\a")}
    return sum(byte in terminators for byte in data)


def print_speed_and_loss(stats: dict, duration: int):
    """Print the speed and message loss. The argument duration is in seconds."""
    if duration == 0:
        print("tx speed: ", "N/A")
        print("rx speed: ", "N/A")
    else:
        tx_speed = stats["tx_len"] / 1000 / duration
        rx_speed = stats["rx_len"] / 1000 / duration
        print("tx speed: ", f"{tx_speed:8.2f}", "kB/s\t", f"{tx_speed * 8:8.2f}", "kbits/s")
        print("rx speed: ", f"{rx_speed:8.2f}", "kB/s\t", f"{rx_speed * 8:8.2f}", "kbits/s")

    print("message loss: ", stats["tx_msg"] - stats["rx_msg"], " / ", stats["tx_msg"])
    print("")


def print_device_status(dev: serial.Serial):
    """Print device status information."""
    dev.write(b"F\r")
    time.sleep(0.1)
    print("device status:", dev.read_all().decode())
    print("detail:")

    dev.write(b"f\r")
    time.sleep(0.1)
    resp = dev.read_all().decode()
    if resp != "\a":
        print("   ", resp)

    dev.write(b"z\r")
    time.sleep(0.1)
    resp = dev.read_all().decode()
    if resp != "\a":
        print("   ", resp)

    print("")


def main():
    """Main function."""
    argparser = get_argparser()
    args = argparser.parse_args()

    mode = "bi" if args.bi else "tx" if args.tx else "rx"

    try:
        device = serial.Serial(args.devicename, timeout=1, write_timeout=1)
    except serial.SerialException as err:
        print("ERROR: Could not open device ", args.devicename)
        print(err)
        return

    setup_device_under_test(device, mode)
    print_round_trip_time(device)

    data_write = make_data_to_write(mode, args.chunk_size)

    stats = {
        "tx_len": 0,
        "rx_len": 0,
        "tx_msg": 0,
        "rx_msg": 0,
    }

    loop_cnt = args.iteration
    phase_tx = True
    tick_next = int(round(time.time() * 1000)) + 1000 * args.duration

    while True:
        if phase_tx:
            device.write(data_write)
            stats["tx_len"] += len(data_write)
            # For bi-directional test, tx message is counted twice to match rx count. TODO move this logic to printer
            stats["tx_msg"] += args.chunk_size if mode != "bi" else args.chunk_size * 2

        data_read = device.read_all()
        stats["rx_len"] += len(data_read)
        stats["rx_msg"] += count_message(data_read)

        ms = int(round(time.time() * 1000))
        if ms > tick_next and not phase_tx:
            print_speed_and_loss(stats, args.duration)
            print_device_status(device)

            for key in stats:
                stats[key] = 0

            ms = int(round(time.time() * 1000))
            tick_next = ms + 1000 * args.duration
            phase_tx = True

            if loop_cnt == 1:
                break

            if loop_cnt > 0:
                loop_cnt -= 1

        elif ms > tick_next and phase_tx:
            tick_next = ms + 100    # Off time to retrieve remaining data in buffer.
            phase_tx = False

    cleanup_device_under_test(device)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        # TODO close USB port cleanly
        pass
