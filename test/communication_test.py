#!/usr/bin/env python3

import re
import sys
import unittest

from device_under_test import DeviceUnderTest


# Characterization test for end-to-end two-device communication across
# the full S x Y bit-rate grid and across data-phase sample points.
# Categorised with the other *_test.py benchmarks (cdc_speed_test.py,
# long_time_test.py) rather than the test_*.py unittest CI suite: it
# requires special hardware setup and takes a few minutes to run, so it
# is intended to be invoked manually rather than picked up by
# `python -m unittest discover`.
#
# Hardware setup:
# - DUT: default port (COM9 on Windows, /dev/ttyACM0 on Linux)
# - AUX: second device (COM8 on Windows, /dev/ttyACM1 on Linux)
# - Both devices wired together on a single CAN bus (CAN-H to CAN-H,
#   CAN-L to CAN-L, with proper termination).
#
# Built on unittest so individual combos appear as subTests, but invoke
# the file directly:
#     python -m unittest communication_test
# (or run the module directly via `python communication_test.py`).
class CommunicationTestCase(unittest.TestCase):
    """End-to-end two-device communication characterization.

    Provides three methods with distinct roles:

    - test_bidirectional_within_safe_ratio is a hard pass/fail gate
      over (S, Y) combos whose data:nominal ratio is at or below
      MAX_SAFE_RATIO. Use it to confirm the hardware operates
      correctly in the chosen safe envelope.

    - test_full_grid_report iterates the full 10x10 (S, Y) grid and
      prints a table classifying each combo by the CAN node state
      inferred from the F flags. It NEVER fails — the table is the
      artefact, useful for visualising the operating envelope of a
      given hardware/firmware combination (e.g. crystal-precision
      vs ceramic-resonator devices show very different boundaries).

    - test_sp_grid_report iterates (data bit rate x data SP) with a
      fixed nominal bit rate and prints a table in the same way. It
      NEVER fails either; it visualises which data-phase sample points
      the hardware can communicate at.
    """

    FRAMES_PER_SIDE = 50
    # Frame mix per side: 15 classic + 15 FD-noBRS + 20 FD-BRS
    NUM_CLASSIC = 15
    NUM_FD_NO_BRS = 15
    NUM_FD_BRS = 20

    # Nominal / data bit rates per doc/2.-Command-List.md.
    # Y3 is documented as N/A; Y6-9 and S9 do not exist.
    S_KBPS = {0: 10, 1: 20, 2: 50, 3: 100, 4: 125, 5: 250, 6: 500, 7: 800, 8: 1000}
    Y_KBPS = {0: 500, 1: 1000, 2: 2000, 4: 4000, 5: 5000}

    # Test-local pass/fail threshold for the data:nominal ratio.
    # NOT a quotation from the CAN-FD spec — the spec defines no hard
    # ratio cap, and published evaluations span a wide range (Hartwich
    # CiA 2013 uses 1:4 in its realistic example; Mutter CiA 2013
    # evaluates configurations up to ~1:20). 16 here is a deliberate
    # test boundary chosen for this project; combos beyond it are
    # observed (not enforced) by test_full_grid_report.
    MAX_SAFE_RATIO = 16

    # Grid for test_sp_grid_report. The nominal bit rate is fixed and
    # not above the lowest data bit rate. SP below 20 % cannot be
    # represented within the y field ranges.
    SP_NOMINAL_S = 8                        # 1 Mbps
    SP_DATA_KBPS = (1000, 2000, 4000, 5000, 8000, 10000, 16000, 20000)
    SP_PERCENT = range(20, 100, 5)          # 20 .. 95 %

    # Data bit timing field ranges accepted by the y command.
    MAX_DATA_PRESCALER = 32
    MAX_DATA_TSEG1 = 32
    MAX_DATA_TSEG2 = 16

    dut: DeviceUnderTest
    aux: DeviceUnderTest

    def setUp(self):
        self.dut = DeviceUnderTest()
        self.aux = DeviceUnderTest()
        self.dut.open()                              # default port
        self.aux.open(port=self._get_aux_port())     # OS-specific AUX port
        self.dut.setup()
        self.aux.setup()


    def tearDown(self):
        self.dut.close()
        self.aux.close()


    @staticmethod
    def _get_aux_port():
        """Return the hardcoded AUX port for the current OS."""
        if sys.platform == "win32":
            return "COM8"
        if sys.platform.startswith("linux"):
            return "/dev/ttyACM1"
        return "XXX"    # TODO: put default AUX device name in the macOS


    def test_bidirectional_within_safe_ratio(self):
        """CI gate: iterate (S, Y) combos where Y_kbps / S_kbps is at
        or below MAX_SAFE_RATIO, and require bus errors and frame loss
        to NOT occur.

        MAX_SAFE_RATIO is a test-local engineering threshold (see the
        class constant docstring), not a quotation from the CAN-FD
        spec. Combos beyond it are out of scope for this gate; the
        full S x Y space is covered by test_full_grid_report.
        """
        for s, s_kbps in self.S_KBPS.items():
            for y, y_kbps in self.Y_KBPS.items():
                if y_kbps < s_kbps:
                    continue        # BRS implies data >= nominal
                if y_kbps / s_kbps > self.MAX_SAFE_RATIO:
                    continue        # delegated to the diagnostic test
                with self.subTest(s=s, y=y):
                    self._run_one_combo(s, y)


    def test_full_grid_report(self):
        """Diagnostic: iterate the full S=0..9 x Y=0..9 grid and
        produce a result table on stdout. This test NEVER FAILS — it
        catches every per-combo exception so the table is always
        printed. Use it to visualise the operating envelope of the
        actual hardware; combos beyond 16x are expected to fail and
        their failure is the data point, not an error.
        """
        results = {}
        for s in range(0, 10):
            for y in range(0, 10):
                results[(s, y)] = self._try_one_combo(s, y)
        self._print_results_table(results)


    def test_sp_grid_report(self):
        """Diagnostic: iterate every (data bit rate, data SP) cell with
        the nominal bit rate fixed to SP_NOMINAL_S, and produce a result
        table on stdout. This test NEVER FAILS.

        Each device uses the smallest prescaler that represents the SP
        exactly with its own CAN clock (read with the I command), so
        devices with different clocks can be paired. Cells that either
        device cannot represent are skipped. Cells whose setup the
        device rejects are reported as 'other', since the bit timing is
        computed within the accepted ranges.
        """
        dut_clock_mhz = self._read_clock_mhz(self.dut)
        aux_clock_mhz = self._read_clock_mhz(self.aux)
        results = {}
        for kbps in self.SP_DATA_KBPS:
            for sp in self.SP_PERCENT:
                dut_cfg = self._find_data_bit_timing(dut_clock_mhz, kbps, sp)
                aux_cfg = self._find_data_bit_timing(aux_clock_mhz, kbps, sp)
                if dut_cfg is None or aux_cfg is None:
                    results[(kbps, sp)] = 'skip'
                else:
                    results[(kbps, sp)] = self._classify(
                        self._run_one_sp_cell, kbps, sp, dut_cfg, aux_cfg)
        self._print_sp_results_table(results, dut_clock_mhz, aux_clock_mhz)


    def _try_one_combo(self, s, y):
        """Run one (S, Y) combo and classify the outcome (see _classify)."""
        return self._classify(self._run_one_combo, s, y)


    def _classify(self, run, *args):
        """Run one combo/cell and classify by the CAN node state
        inferred from the F flags reported by either device. Frame loss
        is NOT a separate outcome here — under continuous bus errors
        the frames sit in the firmware's tx queue while auto-retransmit
        keeps retrying, so any 'missing frame' on the wire is a
        symptom of the node-state transition, not the root cause.

        Returns one of:
            'pass'     all checks succeeded (F=00 both sides)
            'skip'     S/Y rejected with [BELL] by either device
            'busErr'   bus errors flagged (BEI) but still error-active
            'passive'  node reached error-passive (EPI set)
            'busOff'   node reached bus-off (BO set)
            'other'    unexpected/anomalous failure (e.g. a frame
                       mismatch with F=00 — rare measurement noise)
        """
        try:
            run(*args)
            return 'pass'
        except unittest.SkipTest:
            return 'skip'
        except AssertionError as e:
            f_hex = re.findall(r"F=b'F([0-9A-Fa-f]{2})", str(e))
            if not f_hex:
                return 'other'
            combined = 0
            for v in f_hex:
                combined |= int(v, 16)
            if combined & 0x10:        # BO  (bus-off)
                return 'busOff'
            if combined & 0x20:        # EPI (error-passive)
                return 'passive'
            if combined & 0x80:        # BEI (bus error, still active)
                return 'busErr'
            return 'other'


    def _print_results_table(self, results):
        """Render the (S, Y) result grid to stdout. Pass is rendered
        as '.' so the failing combos (E/P/O) pop out of the table."""
        symbol = {
            'pass':    '  . ',
            'skip':    '  - ',
            'busErr':  '  E ',
            'passive': '  P ',
            'busOff':  '  O ',
            'other':   '  ? ',
        }
        tally = {}
        for v in results.values():
            tally[v] = tally.get(v, 0) + 1

        print()
        print("=" * 64)
        print("test_full_grid_report  (S = nominal index, Y = data index)")
        print("Legend: .=pass  E=bus_error  P=passive  O=bus-off  -=skip  ?=other")
        print()
        header = "     " + "".join(f" Y{y} " for y in range(10))
        print(header)
        for s in range(10):
            row = f" S{s} "
            for y in range(10):
                row += symbol.get(results.get((s, y), 'other'), ' ? ')
            print(row)
        print()
        summary = "  ".join(f"{k}={tally.get(k, 0)}"
                            for k in ('pass', 'busErr', 'passive', 'busOff', 'skip', 'other'))
        print(f"summary:  {summary}")
        print("=" * 64)


    def _print_sp_results_table(self, results, dut_clock_mhz, aux_clock_mhz):
        """Render the (data SP, data bit rate) result grid to stdout."""
        symbol = {
            'pass':    '   . ',
            'skip':    '   - ',
            'busErr':  '   E ',
            'passive': '   P ',
            'busOff':  '   O ',
            'other':   '   ? ',
        }
        tally = {}
        for v in results.values():
            tally[v] = tally.get(v, 0) + 1

        print()
        print("=" * 64)
        print(f"test_sp_grid_report  (nominal S{self.SP_NOMINAL_S}, rows = data SP, columns = data bit rate)")
        print(f"CAN clock: DUT {dut_clock_mhz} MHz, AUX {aux_clock_mhz} MHz")
        print("Legend: .=pass  E=bus_error  P=passive  O=bus-off  -=not representable  ?=other")
        print()
        header = "      " + "".join(f"{kbps // 1000:>4}M" for kbps in self.SP_DATA_KBPS)
        print(header)
        for sp in self.SP_PERCENT:
            row = f" {sp:>3}% "
            for kbps in self.SP_DATA_KBPS:
                row += symbol.get(results.get((kbps, sp), 'other'), '   ? ')
            print(row)
        print()
        summary = "  ".join(f"{k}={tally.get(k, 0)}"
                            for k in ('pass', 'busErr', 'passive', 'busOff', 'skip', 'other'))
        print(f"summary:  {summary}")
        print("=" * 64)


    def _run_one_combo(self, s, y):
        """Run one (S, Y) combo: setup, then exchange frames.

        Setup is wrapped in skipTest so unsupported bitrates are skipped
        with a clear message rather than failing the subTest.
        """
        # Set S and Y on both devices; [BELL] -> skip this combo.
        self._set_bitrate_or_skip(self.dut, "DUT", b"S", s)
        self._set_bitrate_or_skip(self.aux, "AUX", b"S", s)
        self._set_bitrate_or_skip(self.dut, "DUT", b"Y", y)
        self._set_bitrate_or_skip(self.aux, "AUX", b"Y", y)

        self._exchange_frames(f"S{s}Y{y}")


    def _run_one_sp_cell(self, kbps, sp, dut_cfg, aux_cfg):
        """Run one (data bit rate, data SP) cell: setup with S and a
        custom y per device, then exchange frames."""
        label = f"{kbps // 1000}M@{sp}%"
        dut_y = "y" + "".join(f"{v:02X}" for v in dut_cfg)
        aux_y = "y" + "".join(f"{v:02X}" for v in aux_cfg)

        for dev, name, y_cmd in [(self.dut, "DUT", dut_y), (self.aux, "AUX", aux_y)]:
            for cmd in (f"S{self.SP_NOMINAL_S}", y_cmd):
                dev.send(cmd.encode() + b"\r")
                r = dev.receive()
                self.assertEqual(r, b"\r",
                                 f"{label}: {name} unexpected response to {cmd!r}: {r!r}")

        self._exchange_frames(f"{label} (DUT {dut_y}, AUX {aux_y})")


    def _exchange_frames(self, label):
        """Open both devices, send 50 frames each, verify, close.

        The send/verify block is wrapped in try/finally so the CAN
        channel on both devices is always closed, even when an
        assertion fails — otherwise a leftover open channel would cause
        the very next combo's bitrate commands to be rejected with
        [BELL].
        """
        # 1. Build frame lists.
        # DUT uses even IDs (0x000, 0x002, ..., 0x062);
        # AUX uses odd IDs  (0x001, 0x003, ..., 0x063).
        dut_frames = self._build_frames(start_id=0)
        aux_frames = self._build_frames(start_id=1)

        try:
            # 2. Open both devices in normal mode.
            for dev, name in [(self.dut, "DUT"), (self.aux, "AUX")]:
                dev.send(b"O\r")
                self.assertEqual(dev.receive(), b"\r",
                                 f"{label}: {name} failed to open in normal mode")

            # 3. Send all 50 frames from each side (interleaved push).
            for i in range(self.FRAMES_PER_SIDE):
                self.dut.send(dut_frames[i])
                self.aux.send(aux_frames[i])

            # 4. Drain both sides until the bus is quiet.
            dut_rx = self._drain_until_quiet(self.dut)
            aux_rx = self._drain_until_quiet(self.aux)

            # 5. Read F on both BEFORE asserting frame contents, so we
            # always record the bus-error state even when frame loss
            # would otherwise short-circuit the check at step 6.
            self.dut.send(b"F\r")
            dut_f = self.dut.receive()
            self.aux.send(b"F\r")
            aux_f = self.aux.receive()

            # 6. Collect both observations (frame loss and bus errors)
            # then fail with a single combined message.
            problems = []
            try:
                self._assert_received(dut_rx, aux_frames, "DUT", label)
            except AssertionError as e:
                problems.append(f"DUT rx: {e}")
            try:
                self._assert_received(aux_rx, dut_frames, "AUX", label)
            except AssertionError as e:
                problems.append(f"AUX rx: {e}")
            if dut_f != b"F00\r":
                problems.append(f"DUT F={dut_f!r}")
            if aux_f != b"F00\r":
                problems.append(f"AUX F={aux_f!r}")
            if problems:
                self.fail(f"{label}: " + " | ".join(problems))
        finally:
            # 7. Always close both channels. We drain the response but
            # do not assert on it; the goal is to leave both devices
            # in the closed state so the next combo can re-configure
            # the bit rates. C\r is idempotent on an already-closed
            # channel.
            for dev in (self.dut, self.aux):
                dev.send(b"C\r")
                dev.receive()


    def _set_bitrate_or_skip(self, dev, dev_name, cmd_letter, n):
        """Try a bitrate command; skip this subTest if [BELL] is returned.

        Both S and Y must be tried separately on both devices, because
        either S or Y may individually be unsupported.
        """
        cmd = cmd_letter + str(n).encode() + b"\r"
        dev.send(cmd)
        r = dev.receive()
        if r == b"\a":
            self.skipTest(f"{cmd_letter.decode()}{n} not accepted by {dev_name}")
        self.assertEqual(r, b"\r",
                         f"{dev_name}: unexpected response to {cmd!r}: {r!r}")


    def _read_clock_mhz(self, dev):
        """Return the CAN clock in MHz from the I command (Ixyzz, zz in hex)."""
        dev.send(b"I\r")
        r = dev.receive()
        match = re.fullmatch(rb"I[0-9A-F]{2}([0-9A-F]{2})\r", r)
        self.assertIsNotNone(match, f"Unexpected I reply: {r!r}")
        return int(match.group(1), 16)


    def _find_data_bit_timing(self, clock_mhz, kbps, sp):
        """Return (prescaler, tseg1, tseg2, sjw) that gives the data bit
        rate and SP exactly with the smallest prescaler, or None.

        SP = (1 + tseg1) / (1 + tseg1 + tseg2). SJW is set to the
        largest allowed value, min(tseg1, tseg2).
        """
        for prescaler in range(1, self.MAX_DATA_PRESCALER + 1):
            if (clock_mhz * 1000) % (kbps * prescaler):
                continue
            tq = clock_mhz * 1000 // (kbps * prescaler)
            if (tq * sp) % 100:
                continue
            tseg1 = tq * sp // 100 - 1
            tseg2 = tq - 1 - tseg1
            if 1 <= tseg1 <= self.MAX_DATA_TSEG1 and 1 <= tseg2 <= self.MAX_DATA_TSEG2:
                return (prescaler, tseg1, tseg2, min(tseg1, tseg2))
        return None


    def _drain_until_quiet(self, dev):
        """Call dev.receive() repeatedly until it returns empty.

        The DUT's receive() returns as soon as it sees a single 20 ms
        gap, which at low bitrates can happen mid-burst. By calling
        again until one full receive() comes back empty, we make sure
        the bus has actually quieted down before we verify.
        """
        rx_data = b""
        while True:
            chunk = dev.receive()
            if not chunk:
                break
            rx_data += chunk
        return rx_data


    def _build_frames(self, start_id):
        """Build 50 frames with IDs start_id, start_id+2, ..., start_id+98.

        Mix: 15 t (classic) + 15 d (FD no BRS) + 20 b (FD BRS).
        Payload is 2 bytes holding the CAN ID value (for traceability).
        """
        frames = []
        for i in range(self.FRAMES_PER_SIDE):
            can_id = start_id + i * 2   # 0..98 step 2 or 1..99 step 2
            if i < self.NUM_CLASSIC:
                ftype = b"t"
            elif i < self.NUM_CLASSIC + self.NUM_FD_NO_BRS:
                ftype = b"d"
            else:
                ftype = b"b"
            frames.append(
                ftype
                + format(can_id, "03X").encode()
                + b"2"                                  # DLC = 2 bytes
                + format(can_id, "04X").encode()        # data = ID value (2 bytes hex)
                + b"\r"
            )
        return frames


    def _assert_received(self, rx_data, expected_frames, recipient, label):
        """Verify rx_data contains all expected_frames in order, after
        stripping the recipient's own z[CR] acks.

        Frame payloads are hex digits only, so [CR] only appears as a
        frame delimiter — splitting on [CR] is safe.
        """
        stripped = rx_data.replace(b"z\r", b"")
        received_msgs = [m for m in stripped.split(b"\r") if m]
        expected_msgs = [f.rstrip(b"\r") for f in expected_frames]
        self.assertEqual(received_msgs, expected_msgs,
                         f"{label}: {recipient} received frames mismatch")


if __name__ == "__main__":
    unittest.main()
