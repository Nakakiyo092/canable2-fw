"""
A helper class for testing the SLCAN device under test.

License:
    MIT License.
    See the accompanying LICENSE file for full terms.
"""

import sys
import time
import serial


class DeviceUnderTest:
    """A helper class for testing the SLCAN device under test."""
    print_on: bool
    ser: serial.Serial
    slcan_ver: bytes
    debug_build: bool
    fd_support: bool

    def __init__(self):
        """Initialize the class."""
        # initialize
        self.print_on = False


    def open(self, port=None):
        """Open the connection to the device.

        Args:
            port: optional OS-specific port name override
                  (e.g., "COM8" on Windows, "/dev/ttyACM1" on Linux).
                  If None, uses the OS-default port (COM9 / /dev/ttyACM0).
        """
        # connect to serial
        if port is None:
            if sys.platform == "win32":
                port = "COM9"
            elif sys.platform.startswith("linux"):
                port = "/dev/ttyACM0"
            else:
                port = "XXX"    # TODO: put default device name in the macOS
        self.ser = serial.Serial(port, timeout=1, write_timeout=1)


    def setup(self):
        """Setup the device for testing."""
        # Clear false characters in the buffer. See the link for details.
        # https://github.com/Nakakiyo092/usb2canfdv1/discussions/36
        self.send(b"\a\r\r")
        self.receive()

        # Close the CAN channel just in case
        self.send(b"C\r")
        self.receive()

        # Check the SLCAN version
        self.send(b"V\r")
        slcan_ver = self.receive()
        if slcan_ver[:4] == b"VL2K":
            # CANable2.0 "Nakakiyo092/canable2-fw"
            self.fd_support = True
        elif slcan_ver[:4] == b"VW1K":
            # WeAct Studio "Nakakiyo092/usb2canfdv1"
            self.fd_support = True
        else:
            self.fd_support = False
            print("WARNING: Unsupported SLCAN version ", slcan_ver.decode())

        self.debug_build = bool(b"DEBUG" in slcan_ver)

        # Reset to default settings. Setup is best-effort: a firmware
        # variant may not implement every command (e.g. some CANable2.0
        # builds reject W/M/m), so an unexpected response is logged as a
        # warning rather than aborting the test. The downstream test is
        # then responsible for tolerating any leftover non-default state.
        for cmd in (b"S4\r", b"Y2\r", b"Z0\r", b"W0\r",
                    b"M00000000\r", b"mFFFFFFFF\r"):
            self.send(cmd)
            resp = self.receive()
            if resp != b"\r":
                print(f"WARNING: Setup: {cmd!r} returned {resp!r}")


    def close(self):
        """Close the connection to the device."""
        # close serial
        self.ser.close()


    def print_data(self, direction: str, data: bytes):
        """Print the data in a human-readable format.
        param direction: 'T' for transmit, 'R' for receive
        """
        datar = data
        datar = datar.replace(b"\r", b"[CR]")
        datar = datar.replace(b"\a", b"[BELL]")
        if direction in ('t', 'T'):
            print("")
            print("<<< ", datar.decode())
        else:
            print("")
            print(">>> ", datar.decode())


    def send(self, tx_data: bytes):
        """Send data to the device."""
        self.ser.write(tx_data)

        if self.print_on:
            self.print_data("T", tx_data)


    def receive(self) -> bytes:
        """Receive data from the device."""
        rx_data = b""
        cycle = 0.02    # sec - should be more than RRT to the device and cdc stream gap including VM USB jitter
        timeout = 1     # sec
        for _ in range(0, int(timeout / cycle)):
            time.sleep(cycle)
            tmp = self.ser.read_all()
            rx_data = rx_data + tmp
            if len(tmp) == 0 and len(rx_data) != 0:
                break

        if self.print_on:
            self.print_data("R", rx_data)

        return rx_data
