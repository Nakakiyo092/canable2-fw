# CANable 2.0 Firmware

This repository contains sources for the slcan CANable 2.0 firmware. This firmware implements non-standard slcan commands to support CANFD messaging alongside a LAWICEL-style command set.

## Supported Commands

- `O` - Open channel in normal mode
- `L` - Open channel in silent mode
- `C` - Close channel
- `S0` - Set nominal bitrate to 10k
- `S1` - Set nominal bitrate to 20k
- `S2` - Set nominal bitrate to 50k
- `S3` - Set nominal bitrate to 100k
- `S4` - Set nominal bitrate to 125k (default)
- `S5` - Set nominal bitrate to 250k
- `S6` - Set nominal bitrate to 500k
- `S7` - Set nominal bitrate to 800k
- `S8` - Set nominal bitrate to 1M
- `sDDXXYYZZ` - Set nominal bitrate and bittiming
- `Y0` - Set data bitrate to 500k
- `Y1` - Set data bitrate to 1M
- `Y2` - Set data bitrate to 2M (default)
- `Y4` - Set data bitrate to 4M
- `Y5` - Set data bitrate to 5M
- `Y8` - Set data bitrate to 8M (If supported by the CAN tranceiver)
- `yDDXXYYZZ` - Set data bitrate and bittiming
- `rIIIL` - Transmit remote frame (Standard ID) [ID, length]
- `RIIIIIIIIL` - Transmit remote frame (Extended ID) [ID, length]
- `tIIILDD...` - Transmit data frame (Standard ID) [ID, length, data]
- `TIIIIIIIILDD...` - Transmit data frame (Extended ID) [ID, length, data]
- `dIIILDD...` - Transmit CAN FD standard ID (no BRS) [ID, length, data]
- `DIIIIIIIILDD...` - Transmit CAN FD extended ID (no BRS) [ID, length, data]
- `bIIILDD...` - Transmit CAN FD BRS standard ID [ID, length, data]
- `BIIIIIIIILDD...` - Transmit CAN FD extended ID [ID, length, data]

- `V` and `v` - Returns firmware version and remote path as a string
- `N` - Returns and sets serial number 
- `I` and `i` - Returns CAN controller information
- `Z` and `z` - Configure reporting mechanism including time stamp and Tx event
- `M` and `m` - Configure CAN acceptance filter
- `F` and `f` - Returns status flags and detailed status
- `Q` - Turn on or off auto-startup feature

Note: CANFD message lengths are as follows (expressed in hexadecimal):

- `0-8`: Same as standard CAN
- `9`: Length = 12
- `A`: Length = 16
- `B`: Length = 20
- `C`: Length = 24
- `D`: Length = 32
- `E`: Length = 48
- `F`: Length = 64

Note: Channel configuration commands must be sent before opening the channel. The channel must be opened before transmitting frames.

## Building

Firmware builds with GCC. Specifically, you will need gcc-arm-none-eabi, which
is packaged for Windows, OS X, and Linux on
[Launchpad](https://launchpad.net/gcc-arm-embedded/+download). Download for your
system and add the `bin` folder to your PATH.

Your Linux distribution may also have a prebuilt package for `arm-none-eabi-gcc`, check your distro's repositories to see if a build exists. Simply compile by running `make`.

## Flashing with the Bootloader

Plug in your CANable2 while pressing down the BOOT button. The blue LED should be dimly illuminated. Next, type `make flash` and your CANable will be updated to the latest firwmare. Unplug/replug the device after moving the boot jumper back, and your CANable will be up and running.

## License

See LICENSE.md
