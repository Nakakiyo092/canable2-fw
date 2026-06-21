#!/usr/bin/env python3
"""Long-running bidirectional stress test with frame-content verification.

The DUT sends ping frames at a configurable rate; the AUX device echoes each
ping back to the DUT with the CAN ID incremented by one and every payload byte
incremented by one. Pings are filled with consecutive bytes
(data[i] == data[i-1] + 1 mod 256), an invariant that is preserved by the +1
echo transform — so a single rule covers both directions and catches any
single-byte corruption that may occur in flight.

By varying --rate the operator can probe the operating envelope: at moderate
rates the test serves as a long-running endurance check, and at higher rates
the same harness reveals where loss and bus errors begin to appear.

Design inspired by canfdtest.c from the Linux can-utils suite
(https://github.com/linux-can/can-utils), which uses the same ping/echo plus
consecutive-byte invariant idea. This file is an independent Python
implementation built on the SLCAN/pyserial harness used elsewhere in this
repository; no source from canfdtest.c is incorporated.

Usage example:
    python stress_test.py --rate 200 --duration 600
    python stress_test.py --dut COM9 --aux COM8 --rate 50 --duration 0
"""

import argparse
import signal
import sys
import threading
import time

from device_under_test import DeviceUnderTest


DEFAULT_PING_ID = 0x100
DEFAULT_ECHO_ID = 0x101
DEFAULT_FRAME_TYPE = "b"         # b = FD with BRS, d = FD no BRS, t = classic
DEFAULT_PAYLOAD_LEN = 64         # FD max
DEFAULT_S_INDEX = 8              # nominal bit rate (S command index)
DEFAULT_Y_INDEX = 5              # data bit rate (Y command index, FD only)
DEFAULT_RATE_FPS = 100.0
DEFAULT_DURATION_S = 60
DEFAULT_STATUS_INTERVAL_S = 10.0

# CAN-FD DLC encoding for payload lengths above 8 bytes.
FD_DLC_TO_LEN = {
    0x0: 0, 0x1: 1, 0x2: 2, 0x3: 3, 0x4: 4,
    0x5: 5, 0x6: 6, 0x7: 7, 0x8: 8,
    0x9: 12, 0xA: 16, 0xB: 20, 0xC: 24,
    0xD: 32, 0xE: 48, 0xF: 64,
}
FD_LEN_TO_DLC = {v: k for k, v in FD_DLC_TO_LEN.items()}


def _default_dut_port():
    if sys.platform == "win32":
        return "COM9"
    if sys.platform.startswith("linux"):
        return "/dev/ttyACM0"
    return "XXX"


def _default_aux_port():
    if sys.platform == "win32":
        return "COM8"
    if sys.platform.startswith("linux"):
        return "/dev/ttyACM1"
    return "XXX"


class LineBuffer:
    """Streaming line splitter for SLCAN response bytes.

    Each \\r delimits a line. [BELL] (0x07) signals a rejected command and is
    counted separately. Non-empty lines are yielded; empty lines (the bare \\r
    ack returned by commands like S, Y, O, C) are dropped.
    """

    def __init__(self):
        self._buf = b""
        self.bell_count = 0

    def feed(self, chunk):
        self.bell_count += chunk.count(b"\a")
        self._buf += chunk.replace(b"\a", b"")
        while b"\r" in self._buf:
            line, _, self._buf = self._buf.partition(b"\r")
            if line:
                yield line


class Stats:
    """Cumulative counters updated as the test progresses."""

    def __init__(self):
        self.pings_sent = 0
        self.pings_seen_at_aux = 0
        self.echos_sent = 0
        self.echos_seen_at_dut = 0
        self.echos_corrupted = 0
        self.unexpected_at_dut = 0
        self.unexpected_at_aux = 0
        self.dut_bells = 0
        self.aux_bells = 0


def build_send_cmd(frame_type, can_id, data):
    """Build the SLCAN send command for the chosen frame type."""
    if frame_type == "t":
        dlc = len(data)         # classic: DLC == byte count, 0..8
    else:
        dlc = FD_LEN_TO_DLC[len(data)]
    return f"{frame_type}{can_id:03X}{dlc:X}{data.hex().upper()}\r".encode("ascii")


def parse_rx(line, frame_type):
    """Parse a received frame line of the configured type. Returns
    (can_id, data) or None if the line is not a well-formed frame
    report of that type."""
    prefix = frame_type.encode("ascii")
    if not line.startswith(prefix) or len(line) < 5:
        return None
    try:
        can_id = int(line[1:4], 16)
        dlc = int(line[4:5], 16)
        if frame_type == "t":
            length = dlc if dlc <= 8 else None
        else:
            length = FD_DLC_TO_LEN.get(dlc)
        if length is None or 5 + 2 * length != len(line):
            return None
        data = bytes.fromhex(line[5:].decode("ascii"))
        return (can_id, data)
    except (ValueError, UnicodeDecodeError):
        return None


def build_ping_payload(seq, payload_len):
    """Build a payload whose data[0] rotates with the send counter and
    whose bytes are consecutive (data[i] == data[i-1] + 1 mod 256). The
    +1 echo transform preserves the invariant, so the same check applies
    to both directions."""
    c = seq & 0xFF
    return bytes((c + i) & 0xFF for i in range(payload_len))


def build_echo_cmd_for_ping(line, stats, ping_id, echo_id, frame_type):
    """Inspect a possibly-ping line on AUX. If it matches the ping ID,
    update stats and return the echo command bytes (id+1, every byte +1).
    Otherwise return None (and tally as unexpected when applicable)."""
    parsed = parse_rx(line, frame_type)
    if parsed is None:
        return None
    can_id, data = parsed
    if can_id != ping_id:
        stats.unexpected_at_aux += 1
        return None
    stats.pings_seen_at_aux += 1
    echo_data = bytes((b + 1) & 0xFF for b in data)
    stats.echos_sent += 1
    return build_send_cmd(frame_type, echo_id, echo_data)


def on_dut_received(line, stats, echo_id, frame_type):
    """One complete line on the DUT rx stream. If it is an echo, verify
    the consecutive-byte invariant."""
    parsed = parse_rx(line, frame_type)
    if parsed is None:
        return
    can_id, data = parsed
    if can_id != echo_id:
        stats.unexpected_at_dut += 1
        return
    stats.echos_seen_at_dut += 1
    for i in range(1, len(data)):
        if data[i] != ((data[i - 1] + 1) & 0xFF):
            stats.echos_corrupted += 1
            return


def _dut_send_thread(args, dut, stats, stop_event):
    """Paced ping sender. Builds batches of pings whose scheduled emit
    time has passed and writes each batch to DUT in one pyserial call.
    Runs concurrent with _dut_recv_thread so the USB OUT and IN endpoints
    can be active at the same time."""
    period = 1.0 / args.rate
    max_batch = args.max_batch
    next_ping = time.monotonic()

    while not stop_event.is_set():
        now = time.monotonic()
        ping_batch = []
        while now >= next_ping and len(ping_batch) < max_batch:
            payload = build_ping_payload(stats.pings_sent, args.payload_size)
            ping_batch.append(
                build_send_cmd(args.frame_type, args.ping_id, payload)
            )
            stats.pings_sent += 1
            next_ping += period
        if next_ping < now:
            next_ping = now + period
        if ping_batch:
            dut.ser.write(b"".join(ping_batch))
        # No sleep — let the GIL hand back to the other threads naturally.


def _dut_recv_thread(args, dut, dut_lines, stats, stop_event):
    """Drain DUT rx and verify every echo against the consecutive-byte
    invariant. Concurrent with _dut_send_thread on the same port; pyserial
    is safe for one reader + one writer on the same port."""
    while not stop_event.is_set():
        chunk = dut.ser.read_all()
        if not chunk:
            continue
        for line in dut_lines.feed(chunk):
            on_dut_received(line, stats, args.echo_id, args.frame_type)


def _aux_thread(args, aux, aux_lines, stats, stop_event):
    """Manage AUX end-to-end: drain pings, build echos in a batch,
    flush them in one write. Lives on its own port so it runs fully
    independently of the DUT pair above."""
    while not stop_event.is_set():
        chunk = aux.ser.read_all()
        if not chunk:
            continue
        echo_batch = []
        for line in aux_lines.feed(chunk):
            cmd = build_echo_cmd_for_ping(
                line, stats, args.ping_id, args.echo_id, args.frame_type
            )
            if cmd:
                echo_batch.append(cmd)
        if echo_batch:
            aux.ser.write(b"".join(echo_batch))


def run_loop(args, dut, aux, stop_flag):
    """Drive the test from three worker threads:

      - DUT send thread: paced ping output, batched per write.
      - DUT recv thread: drains DUT, runs echo verification.
      - AUX thread: drains AUX, builds and writes echos in batches.

    Threading lets the USB CDC OUT and IN endpoints stay simultaneously
    busy on each port (the host driver runs the two directions in
    parallel) instead of serialising every write/read in one loop, which
    was the bottleneck behind the ~900 fps ceiling of the previous
    single-threaded design.

    The main thread owns pacing of the status print and the test
    duration / Ctrl-C condition; it never touches either serial port
    while the workers are alive.
    """
    stats = Stats()
    dut_lines = LineBuffer()
    aux_lines = LineBuffer()
    stop_event = threading.Event()

    threads = [
        threading.Thread(target=_dut_send_thread,
                         args=(args, dut, stats, stop_event),
                         daemon=True, name="dut-send"),
        threading.Thread(target=_dut_recv_thread,
                         args=(args, dut, dut_lines, stats, stop_event),
                         daemon=True, name="dut-recv"),
        threading.Thread(target=_aux_thread,
                         args=(args, aux, aux_lines, stats, stop_event),
                         daemon=True, name="aux"),
    ]
    for t in threads:
        t.start()

    start = time.monotonic()
    end = start + args.duration if args.duration > 0 else float("inf")
    next_status = start + args.status_interval

    try:
        while not stop_flag[0]:
            now = time.monotonic()
            if now >= end:
                break
            if now >= next_status:
                _print_status(stats, now - start)
                next_status += args.status_interval
            time.sleep(0.05)    # main thread can sleep — workers are hot
    finally:
        stop_event.set()
        for t in threads:
            t.join(timeout=2.0)

    elapsed = time.monotonic() - start

    # One last sweep on both rx streams to catch the inflight tail. Done
    # synchronously here because the worker threads are gone.
    final_drain_until = time.monotonic() + 0.5
    while time.monotonic() < final_drain_until:
        chunk = dut.ser.read_all()
        if chunk:
            for line in dut_lines.feed(chunk):
                on_dut_received(line, stats, args.echo_id, args.frame_type)
        chunk = aux.ser.read_all()
        if chunk:
            for line in aux_lines.feed(chunk):
                cmd = build_echo_cmd_for_ping(
                    line, stats, args.ping_id, args.echo_id, args.frame_type
                )
                if cmd:
                    aux.ser.write(cmd)
        time.sleep(0.01)

    stats.dut_bells = dut_lines.bell_count
    stats.aux_bells = aux_lines.bell_count

    return stats, elapsed


def _print_status(stats, elapsed):
    rate = stats.pings_sent / max(elapsed, 0.001)
    loss = stats.pings_sent - stats.echos_seen_at_dut
    print(f"  t+{elapsed:6.0f}s  sent={stats.pings_sent:>8}  "
          f"recv={stats.echos_seen_at_dut:>8}  "
          f"loss={loss:>5}  corrupt={stats.echos_corrupted:>3}  "
          f"~{rate:7.1f} fps", flush=True)


def print_banner(dut, dut_port, aux, aux_port):
    """One-shot identification of both devices before the run starts.
    Mirrors the banner pattern used by communication_test.py."""
    print()
    print("=" * 57)
    print(" stress_test target devices")
    print("=" * 57)
    for label, dev, port in [("DUT", dut, dut_port), ("AUX", aux, aux_port)]:
        dev.send(b"V\r")
        v = dev.receive().rstrip(b"\r").decode("ascii", errors="replace")
        dev.send(b"N\r")
        n = dev.receive().rstrip(b"\r").decode("ascii", errors="replace")
        print(f" {label} ({port}):")
        print(f"   slcan version: {v}")
        print(f"   serial number: {n}")
    print("=" * 57)
    sys.stdout.flush()


def print_summary(stats, elapsed, dut_f, aux_f, args):
    actual_rate = stats.pings_sent / max(elapsed, 0.001)
    loss = stats.pings_sent - stats.echos_seen_at_dut
    pct = 100.0 * loss / stats.pings_sent if stats.pings_sent else 0.0

    print()
    print("=" * 70)
    print(f" stress_test summary  (elapsed {elapsed:.1f} s, target {args.rate} fps)")
    print("=" * 70)
    print(f"  Pings sent (DUT->AUX):           {stats.pings_sent}")
    print(f"  Pings observed at AUX:           {stats.pings_seen_at_aux}")
    print(f"  Echos sent (AUX->DUT):           {stats.echos_sent}")
    print(f"  Echos observed at DUT:           {stats.echos_seen_at_dut}")
    print(f"  Echos with corrupted payload:    {stats.echos_corrupted}")
    print(f"  Unexpected frames at DUT:        {stats.unexpected_at_dut}")
    print(f"  Unexpected frames at AUX:        {stats.unexpected_at_aux}")
    print(f"  Rejected commands ([BELL]):      DUT={stats.dut_bells}  AUX={stats.aux_bells}")
    print(f"  End-to-end loss:                 {loss} ({pct:.2f} %)")
    print(f"  Actual achieved rate:            {actual_rate:.1f} fps")
    print()
    print(f"  DUT final F: {dut_f}")
    print(f"  AUX final F: {aux_f}")
    print("=" * 70)


def get_argparser():
    parser = argparse.ArgumentParser(
        description="Long-running bidirectional CAN ping/echo stress test "
                    "with frame-content verification. Requires two SLCAN "
                    "devices wired together on the same CAN bus."
    )
    parser.add_argument("--dut", metavar="PORT",
                        help=f"DUT serial port (default: {_default_dut_port()})")
    parser.add_argument("--aux", metavar="PORT",
                        help=f"AUX serial port (default: {_default_aux_port()})")
    parser.add_argument("-r", "--rate", type=float, default=DEFAULT_RATE_FPS,
                        help=f"target ping rate in fps (default: {DEFAULT_RATE_FPS})")
    parser.add_argument("-d", "--duration", type=int, default=DEFAULT_DURATION_S,
                        help=f"test duration in seconds; 0 = run until Ctrl-C "
                             f"(default: {DEFAULT_DURATION_S})")
    parser.add_argument("-s", "--status-interval", type=float,
                        default=DEFAULT_STATUS_INTERVAL_S,
                        help=f"status print interval in seconds "
                             f"(default: {DEFAULT_STATUS_INTERVAL_S})")
    parser.add_argument("--ping-id", type=lambda v: int(v, 0),
                        default=DEFAULT_PING_ID,
                        help=f"CAN ID for ping frames (default: 0x{DEFAULT_PING_ID:X})")
    parser.add_argument("--echo-id", type=lambda v: int(v, 0),
                        default=DEFAULT_ECHO_ID,
                        help=f"CAN ID for echo frames (default: 0x{DEFAULT_ECHO_ID:X})")
    parser.add_argument("--payload-size", type=int, default=DEFAULT_PAYLOAD_LEN,
                        help=f"frame payload size in bytes (classic: 0..8, "
                             f"FD: 0..8/12/16/20/24/32/48/64; "
                             f"default: {DEFAULT_PAYLOAD_LEN})")
    parser.add_argument("--frame-type", choices=("t", "d", "b"),
                        default=DEFAULT_FRAME_TYPE,
                        help=f"frame type: t=classic CAN, d=FD no BRS, "
                             f"b=FD with BRS (default: {DEFAULT_FRAME_TYPE})")
    parser.add_argument("--s-index", type=int, default=DEFAULT_S_INDEX,
                        help=f"S command index for nominal bit rate "
                             f"(default: {DEFAULT_S_INDEX})")
    parser.add_argument("--y-index", type=int, default=DEFAULT_Y_INDEX,
                        help=f"Y command index for data bit rate, ignored when "
                             f"--frame-type=t (default: {DEFAULT_Y_INDEX})")
    parser.add_argument("--max-batch", type=int, default=8,
                        help="max pings packed into one pyserial write "
                             "(default: 8). Higher values raise the achievable "
                             "ceiling but risk overrunning the firmware's CDC "
                             "Rx buffer.")
    return parser


def main():
    args = get_argparser().parse_args()

    if args.rate <= 0:
        print("--rate must be positive.", file=sys.stderr)
        return 1
    if args.frame_type == "t":
        if not 0 <= args.payload_size <= 8:
            print("Classic CAN: --payload-size must be 0..8.", file=sys.stderr)
            return 1
    else:
        if args.payload_size not in FD_LEN_TO_DLC:
            print(f"FD: --payload-size must be one of "
                  f"{sorted(FD_LEN_TO_DLC.keys())}.", file=sys.stderr)
            return 1

    dut_port = args.dut or _default_dut_port()
    aux_port = args.aux or _default_aux_port()

    dut = DeviceUnderTest()
    aux = DeviceUnderTest()
    dut.open(port=dut_port)
    aux.open(port=aux_port)
    dut.setup()
    aux.setup()

    print_banner(dut, dut_port, aux, aux_port)

    # Override the bit rates set by DeviceUnderTest.setup() (which always
    # picks the device default S4/Y2). Doing it after setup() so the
    # firmware is in a known state first.
    s_cmd = f"S{args.s_index}\r".encode("ascii")
    y_cmd = f"Y{args.y_index}\r".encode("ascii")
    for label, dev in (("DUT", dut), ("AUX", aux)):
        dev.send(s_cmd)
        if dev.receive() != b"\r":
            print(f"{label} rejected S{args.s_index}; aborting.",
                  file=sys.stderr)
            return 1
        if args.frame_type != "t":
            dev.send(y_cmd)
            if dev.receive() != b"\r":
                print(f"{label} rejected Y{args.y_index}; aborting.",
                      file=sys.stderr)
                return 1

    # Open the CAN channel on both devices (normal mode).
    for label, dev in (("DUT", dut), ("AUX", aux)):
        dev.send(b"O\r")
        if dev.receive() != b"\r":
            print(f"{label} failed to open the CAN channel; aborting.",
                  file=sys.stderr)
            return 1

    # Graceful Ctrl-C / SIGTERM handling.
    stop_flag = [False]
    def _stop_handler(*_):
        stop_flag[0] = True
    signal.signal(signal.SIGINT, _stop_handler)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, _stop_handler)

    print(f"Starting: frame_type={args.frame_type}, "
          f"S{args.s_index}"
          f"{('/Y' + str(args.y_index)) if args.frame_type != 't' else ''}, "
          f"payload={args.payload_size} bytes, "
          f"rate={args.rate} fps, duration={args.duration} s, "
          f"ping_id=0x{args.ping_id:X}, echo_id=0x{args.echo_id:X}")
    print("Press Ctrl-C to stop early.")
    print()

    stats, elapsed = run_loop(args, dut, aux, stop_flag)

    # Final F snapshot on each side.
    dut.send(b"F\r")
    dut_f = dut.receive().rstrip(b"\r").decode("ascii", errors="replace")
    aux.send(b"F\r")
    aux_f = aux.receive().rstrip(b"\r").decode("ascii", errors="replace")

    for dev in (dut, aux):
        dev.send(b"C\r")
        dev.receive()

    print_summary(stats, elapsed, dut_f, aux_f, args)

    dut.close()
    aux.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
