#!/usr/bin/env python3

"""
Collection of tests which take long time to complete.

- CAN bus error and buffer error rate (loopback as default or with receiver option)
- Demonstrate that the timestamp sentinel (firmware's last-resort defence) does
  not appear under normal operation across many samples, including long idle
  periods that cross TIM3 16-bit wrap (~65.5 ms) and the 1-hour TIM2 wrap
- Compare clock accuracy between host and device

License:
    MIT License.
    See the accompanying LICENSE file for full terms.
"""

import time
import random

import argparse
import serial


ROUND_TRIP_TIME_SAMPLES = 10
STATS_INTERVAL_MS = 60_000
TIMESTAMP_PERIOD_US = 3600_000_000
# UINT16_MAX / 2: half of the TIM3 period (~32.7 ms). Beyond this the
# host/device timestamp diff cannot be uniquely reconstructed against
# TIM3's 16-bit wrap, so the comparison loses meaning.
TIMESTAMP_DIFF_THRESHOLD_US = 0xFFFF // 2
RTT_SAFETY_MARGIN = 6   # Six sigma


def get_argparser():
    """Get argument parser for this script."""
    parser = argparse.ArgumentParser(
        description="Run collection of long time tests. Press [CTRL] + 'c' to quit."
    )
    parser.add_argument(
        "devicename",
        type=str,
        help="device name like COM9 or /dev/ttyACM0 (required)"
    )
    parser.add_argument(
        "-d", "--duration",
        type=int,
        default=1,
        help="time to test in hours"
    )
    parser.add_argument(
        "-w", "--with-receiver",
        action="store_true",
        help="run the test with another device receiving the messages"
    )
    return parser


def setup_device_under_test(dev: serial.Serial, with_receiver: bool):
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

    # Setup maximum CAN speed to stress the device
    dev.write(b"S8\r")
    dev.write(b"Y5\r")
    dev.write(b"z2002\r")
    time.sleep(0.1)
    dev.read_all()
    
    if with_receiver:
        dev.write(b"O\r")    # TODO: warning if loopback is not supported
        time.sleep(0.1)
        dev.read_all()
        print("can port status: open/normal (1M/5Mbps)")
    else:
        dev.write(b"+\r")
        time.sleep(0.1)
        dev.read_all()
        print("can port status: open/loopback (1M/5Mbps)")

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
        rtt.append(int((time_end - time_start) * 1000 * 1000))  # Convert sec to us

    print("ping:", rtt, "us")

    if len(rtt) == 0:
        return -1

    ave_rtt = sum(rtt) // len(rtt)
    if RTT_SAFETY_MARGIN * ave_rtt > TIMESTAMP_DIFF_THRESHOLD_US:
        print("WARNING: The round trip time is too large to verify the timestamp.")
    print("")

    return ave_rtt


def make_data_to_write(seq: int) -> bytes:
    """Make data to write to device, with the host-side sequence number
    embedded in the 8-byte payload.

    The seq round-trips through the device: it appears verbatim in the
    matching Tx-event (`Z`) reply, so the receive side can detect dropped
    commands (CDC Rx overrun under sustained pressure) and resync the
    host_tx_time_us_list pairing instead of letting one drop cascade
    into thousands of false comparison failures.

    Keeps the FD-BRS extended-ID frame format (`B`) so the BRS code path
    is still exercised; sustained-rate BRS data-phase stress is covered
    by can_stress_test.py, so this test only needs a single representative
    frame per iteration.
    """
    return b"B000000008" + f"{seq & 0xFFFFFFFFFFFFFFFF:016X}".encode() + b"\r"


def extract_seq_from_tx_event(msg: bytes) -> int:
    """Extract the 8-byte (16 hex chars) sequence number from the data
    portion of a Z (Tx event) message. Returns -1 if the message is
    too short to contain a seq.

    Z message layout for our frame ('B' + 8 ID + 1 DLC + 16 data + 8 ts + CR):
        msg[0]      = 'Z'
        msg[1]      = 'B'
        msg[2:10]   = ID (8 hex)
        msg[10:11]  = DLC (1 hex)
        msg[11:27]  = data (16 hex) <-- seq is here
        msg[27:35]  = timestamp (8 hex)
        msg[35]     = '\\r'
    """
    if len(msg) < 27 + 1:
        return -1
    try:
        return int(msg[11:27].decode(), 16)
    except (ValueError, UnicodeDecodeError):
        return -1


SENTINEL_US = 0xFFFFFFFF


def extract_timestamp_from_tx_event(msg: bytes) -> int:
    """Extract 4-byte us timestamp from TX event message.

    TX Event format: b'Z' + frame_data + timestamp_hex(8 chars) + b'\r'
    Returns timestamp in us (0-3,599,999,999).
    Returns -1 on parse error, SENTINEL_US if device reported the out-of-spec sentinel.
    """
    if len(msg) < len(b"ZTTTTTTTT\r") or msg[0:1] != b"Z":
        return -1

    try:
        timestamp_hex = msg[-9:-1].decode()     # Last 8 chars before '\r'
        return int(timestamp_hex, 16)
    except (ValueError, UnicodeDecodeError):
        print("ERROR: Failed to extract timestamp from message:", msg)
        return -1


def calc_timestamp_diff(ts_new: int, ts_old: int) -> int:
    """Calculate timestamp difference with 1 hour period compensation.
    
    Timestamp counter resets at 3600_000_000 us.
    Returns difference in us.
    """
    if ts_new >= ts_old:
        return ts_new - ts_old
    else:
        # Overflow occurred
        return (TIMESTAMP_PERIOD_US - ts_old) + ts_new


def print_status_check(stats: dict):
    """Print status check results."""
    print(f"status check: {stats['st_checked']} samples")
    print(f"  no error: {stats['st_no_error_count']}")
    print(f"  buffer error: {stats['st_buf_error_count']}")
    print(f"  can bus error: {stats['st_can_error_count']}")
    if stats['st_buf_error_count'] or stats['st_can_error_count']:
        print("WARNING: There was buffer or bus error which can affect timer verification.")
    print("")


def print_timestamp_verification(stats: dict):
    """Print timestamp verification results."""
    if stats["ts_verified"] == 0:
        print("timestamp verification: 0 samples (need at least 1)")
        print("")
        return
    
    avg_error = stats["ts_error_sum"] / stats["ts_verified"]
    max_error = stats["ts_error_max"]
    failure_count = stats["ts_failure_count"]
    
    print(f"timestamp comparison (host - device): {stats['ts_verified']} samples")
    print(f"  ave abs error: {avg_error:.1f} us")
    print(f"  max abs error: {max_error} us")
    print(f"  failures: {failure_count}")
    print(f"    of which >{TIMESTAMP_DIFF_THRESHOLD_US} us: {failure_count - stats['ts_sentinel_count']}")
    print(f"    of which sentinel: {stats['ts_sentinel_count']}")
    print("")


def print_clock_accuracy(stats: dict):
    """Print clock drift statistics.

    Primary numbers use time.perf_counter() (monotonic, RTT-jitter-bounded).
    Reference numbers based on time.time() are also printed; on systems with
    active NTP sync these track wall clock and the device's drift vs NTP
    becomes visible. On systems without NTP sync the two numbers agree
    within the host's free-running clock drift."""
    if stats["clock_samples"] == 0:
        print("clock accuracy: 0 samples (need at least 1)")
        print("")
        return

    print(f"clock accuracy: {stats['clock_duration'] // 1000_000} sec")
    print(f"  clock offset: {stats['clock_offset'] / 1000:.1f} ms")
    if stats['clock_duration'] > 0:
        print(f"  drift upper bound: {stats['clock_offset_upper_bound'] / stats['clock_duration'] * 1000_000:.1f} ppm")
        print(f"  drift lower bound: {stats['clock_offset_lower_bound'] / stats['clock_duration'] * 1000_000:.1f} ppm")
    else:
        print(f"  drift upper bound: N/A ppm")
        print(f"  drift lower bound: N/A ppm")

    # Reference value via time.time() (NTP-aware when NTP sync is active).
    # host_perf_vs_wall_ppm = how much perf_counter ran faster than the wall
    # clock since test start. Adding it to the perf_counter-based device drift
    # gives the device drift against the wall clock.
    wall_us = stats.get("host_walltime_elapsed_us", 0)
    perf_us = stats.get("host_perfcounter_elapsed_us", 0)
    if wall_us > 0:
        host_perf_vs_wall_ppm = (perf_us - wall_us) / wall_us * 1_000_000
        print(f"  (reference, time.time() based):")
        print(f"    host perf_counter vs wall clock: {host_perf_vs_wall_ppm:+.1f} ppm")
        if stats['clock_duration'] > 0:
            drift_us_perf = stats['clock_offset']
            drift_us_wall = drift_us_perf - (perf_us - wall_us)
            wall_ppm = drift_us_wall / wall_us * 1_000_000
            print(f"    device drift vs wall clock:      {wall_ppm:+.1f} ppm")
    print("")


def main():
    """Main function."""
    argparser = get_argparser()
    args = argparser.parse_args()

    try:
        device = serial.Serial(args.devicename, timeout=1, write_timeout=1)
    except Exception as err:
        print("ERROR: Could not open device ", args.devicename)
        print("")
        print(err)
        print("")
        print("The script is aborting.")
        return

    setup_device_under_test(device, args.with_receiver)
    rtt = print_round_trip_time(device)

    stats = {
        "tx_requests": 0,
        "tx_complete": 0,
        "tx_dropped": 0,
        "tx_rejected": 0,
        "st_checked": 0,
        "st_no_error_count": 0,
        "st_buf_error_count": 0,
        "st_can_error_count": 0,
        "ts_verified": 0,
        "ts_error_sum": 0,
        "ts_error_max": 0,
        "ts_failure_count": 0,
        "ts_sentinel_count": 0,
        "clock_samples": 0,
        "clock_offset": 0,
        "clock_duration": 0,
        "clock_offset_upper_bound": 0,
        "clock_offset_lower_bound": 0,
        # Wall clock vs perf_counter reference. Refreshed before each stats
        # print so the snapshot is consistent with the rest of `stats`.
        "host_walltime_elapsed_us": 0,
        "host_perfcounter_elapsed_us": 0,
    }

    # Reference points for the time.time() vs perf_counter comparison.
    host_walltime_start_us = int(round(time.time() * 1_000_000))
    host_perfcounter_start_us = int(round(time.perf_counter() * 1_000_000))

    # Timestamp tracking. List entries are (seq, perf_counter_us) tuples; seq
    # is also embedded in the sent frame and round-tripped via the device's Z
    # reply, which is what lets the receive side detect dropped commands and
    # resync the pairing.
    host_tx_time_us_list = []
    host_tx_time_us_initial = -1
    host_tx_time_us_prev = -1
    tx_seq_counter = 0
    device_ts = -1
    device_ts_initial = -1
    device_ts_prev = -1

    pending_rx = b""

    tick_start = int(round(time.time() * 1000))
    tick_tx = tick_start
    tick_stats = tick_start + STATS_INTERVAL_MS
    tick_end = tick_start + 3600 * 1000 * args.duration     # Hours to ms
    tick_end += 2 * STATS_INTERVAL_MS   # Add extra time to print the last stats

    while True:
        # Read and process incoming message.
        chunk = device.read_all()
        if chunk:
            pending_rx += chunk
            while True:
                while pending_rx.startswith(b"\a"):
                    pending_rx = pending_rx[1:]
                    stats["tx_rejected"] += 1   # Maybe NACK for F but NACK for frame is more likely.

                delimiter_index = pending_rx.find(b"\r")
                if delimiter_index == -1:
                    break

                msg = pending_rx[:delimiter_index + 1]
                pending_rx = pending_rx[delimiter_index + 1:]

                if msg.startswith(b"F"):
                    stats["st_checked"] += 1
                    if len(msg) >= 3:
                        flags = int(msg[1:3].decode(), 16)
                        if flags & 0b00001011:
                            #print("WARNING: Buffer error detected in status check message:", msg.strip())
                            stats["st_buf_error_count"] += 1
                        elif flags & 0b10110100:
                            #print("WARNING: CAN bus error detected in status check message:", msg.strip())
                            stats["st_can_error_count"] += 1
                        else:
                            stats["st_no_error_count"] += 1
                    else:
                        print("WARNING: Malformed status check message (too short):", msg.strip())

                if msg.startswith(b"Z"):
                    stats["tx_complete"] += 1

                    # Resync against the device-echoed seq: drop pending list
                    # entries whose seq is older than the reply we just got.
                    # Those frames were lost between the host write and the
                    # firmware (e.g. CDC Rx ring overrun under sustained
                    # pressure). Without this, every subsequent comparison
                    # would be permanently shifted by one slot.
                    rx_seq = extract_seq_from_tx_event(msg)
                    if rx_seq >= 0:
                        drops_here = 0
                        while host_tx_time_us_list and host_tx_time_us_list[0][0] < rx_seq:
                            host_tx_time_us_list.pop(0)
                            drops_here += 1
                        if drops_here:
                            stats["tx_dropped"] += drops_here
                            # The per-pair diff baseline pointed to a frame
                            # that no longer round-tripped, so the next diff
                            # would span the drop gap and be meaningless.
                            # Reset prev so the next matched Z starts a fresh
                            # diff chain. The clock-drift baseline (*_initial)
                            # is intentionally NOT reset: drift is measured
                            # against the very first matched frame and that
                            # reference stays valid even when intermediate
                            # frames drop.
                            host_tx_time_us_prev = -1
                            device_ts_prev = -1
                        if not host_tx_time_us_list or host_tx_time_us_list[0][0] != rx_seq:
                            # The matching host write is gone (or never
                            # happened). Skip this Z silently rather than
                            # pairing it with the wrong host time.
                            continue

                    device_ts = extract_timestamp_from_tx_event(msg)
                    if device_ts < 0:
                        print("The script is aborting.")
                        return

                    # The sentinel is the firmware's last-resort defence and is expected
                    # NOT to occur in normal operation. If it appears, treat it as a test
                    # failure (counted in both ts_failure_count and ts_sentinel_count).
                    # The numeric comparison itself is skipped because device_ts is invalid.
                    if device_ts == SENTINEL_US:
                        stats["ts_sentinel_count"] += 1
                        stats["ts_failure_count"] += 1
                        print(f"WARNING: device reported timestamp sentinel for message {msg.strip()}")
                        if host_tx_time_us_list:
                            host_tx_time_us_prev = host_tx_time_us_list.pop(0)[1]
                        device_ts_prev = device_ts
                        continue

                    # Perform timestamp verification if we have previous values
                    if host_tx_time_us_prev >= 0 and device_ts_prev >= 0 and device_ts_prev != SENTINEL_US and host_tx_time_us_list:
                        # Compare with the last timestamp
                        host_diff_us = host_tx_time_us_list[0][1] - host_tx_time_us_prev
                        device_diff_us = calc_timestamp_diff(device_ts, device_ts_prev)
                        error_us = abs(host_diff_us - device_diff_us)

                        stats["ts_verified"] += 1
                        stats["ts_error_sum"] += error_us
                        stats["ts_error_max"] = max(stats["ts_error_max"], error_us)

                        if error_us > TIMESTAMP_DIFF_THRESHOLD_US:
                            print(f"WARNING: host/device timestamp diff mismatch for message {msg.strip()}:")
                            print(f"  host_diff={host_diff_us}us, device_diff={device_diff_us}us, error={error_us}us")
                            stats["ts_failure_count"] += 1

                        # Compare with the initial timestamp
                        host_interval_us = host_tx_time_us_list[0][1] - host_tx_time_us_initial
                        device_interval_us = calc_timestamp_diff(device_ts, device_ts_initial)
                        drift_us = device_interval_us - host_interval_us
                        while drift_us < -3600_000_000 // 2:
                            drift_us += 3600_000_000
                        # Supposed initial RTT is 0 and current RTT is 2 * ave. RTT (or reverse) as the worst case.
                        # Then include safety margin as the RTT can sometimes be much higher than the average (like x10).
                        drift_upper_bound_us = abs(drift_us) + RTT_SAFETY_MARGIN * 2 * rtt
                        drift_lower_bound_us = abs(drift_us) - RTT_SAFETY_MARGIN * 2 * rtt
                        if drift_lower_bound_us < 0:
                            drift_lower_bound_us = 0

                        stats["clock_samples"] += 1
                        stats["clock_offset"] = drift_us
                        stats["clock_duration"] = host_interval_us
                        stats["clock_offset_upper_bound"] = drift_upper_bound_us
                        stats["clock_offset_lower_bound"] = drift_lower_bound_us

                    # Store initial timestamp on the very first valid frame.
                    # Once set, the initial pair is intentionally preserved
                    # across drop resyncs and sentinel events so the long-term
                    # clock drift measurement keeps a stable reference.
                    elif host_tx_time_us_list:
                        if host_tx_time_us_initial < 0:
                            host_tx_time_us_initial = host_tx_time_us_list[0][1]
                            device_ts_initial = device_ts

                    else:
                        print("ERROR: Something went wrong.")
                        print("The script is aborting.")
                        return

                    host_tx_time_us_prev = host_tx_time_us_list.pop(0)[1]
                    device_ts_prev = device_ts

        ms = int(round(time.time() * 1000))
        if ms >= tick_tx:
            rnd = random.randint(1, 1000)
            if rnd <= 500:
                # Short delay (0-150 ms) covers idle that crosses up to 2 TIM3
                # 16-bit wraps (~65.5 ms each); verifies the sentinel does not
                # fire across wrap boundaries.
                tick_tx = ms + random.randint(0, 150)
            elif rnd <= 999:
                # No delay maximises sample count for the sentinel-never-fires
                # assertion and exercises the buffer under sustained pressure.
                tick_tx = ms + 0
            else:
                # Long delay (0-6600 ms) covers idle far beyond the design
                # window so that the sentinel-never-fires assertion holds even
                # after prolonged inactivity. Upper bound is the host/device
                # drift budget: 65.5 ms / 2 / 0.5% ~= 6.6 s.
                tick_tx = ms + random.randint(0, 6600)

            # Record (seq, host TX time) so the Z reply can be matched on seq.
            host_tx_time_us_list.append(
                (tx_seq_counter, int(round(time.perf_counter() * 1000 * 1000)))
            )

            device.write(make_data_to_write(tx_seq_counter))    # Tx a frame
            tx_seq_counter += 1
            stats["tx_requests"] += 1
            device.write(b"F\r")        # Status check

        if ms >= tick_stats:
            tick_stats = ms + STATS_INTERVAL_MS

            # Refresh the wall-clock / perf_counter reference pair before
            # printing so print_clock_accuracy() can compute the NTP-aware
            # reference drift consistently with the rest of `stats`.
            stats["host_walltime_elapsed_us"] = (
                int(round(time.time() * 1_000_000)) - host_walltime_start_us
            )
            stats["host_perfcounter_elapsed_us"] = (
                int(round(time.perf_counter() * 1_000_000)) - host_perfcounter_start_us
            )

            print("")
            print(f"--- Stats at {(ms - tick_start) / 3600 / 1000:.3f} hours ---")
            print("")
            print(f"sent frames: {stats["tx_complete"]} / {stats["tx_requests"]} (-{stats["tx_rejected"]})")
            print(f"  resync-detected drops: {stats["tx_dropped"]}")
            print("")
            print_status_check(stats)
            print_timestamp_verification(stats)
            print_clock_accuracy(stats)

        if ms >= tick_end:
            break

    cleanup_device_under_test(device)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        # TODO close USB port cleanly
        pass
