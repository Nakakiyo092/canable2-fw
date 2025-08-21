# CANable 2.0 Firmware

This repository contains sources for the slcan CANable 2.0 firmware. This firmware implements non-standard slcan commands to support CANFD messaging alongside a LAWICEL-style command set.

## Frequently Used Commands

- `O` - Opens channel
- `C` - Closes channel
- `sddxxyyzz` - Sets nominal bitrate and bittiming
- `yddxxyyzz` - Sets data bitrate and bittiming
- `tiiildd...` - Transmits a classical base data frame
- `Tiiiiiiiildd...` - Transmits a classical extended data frame
- `diiildd...` - Transmits a FD base data frame without bit rate switch
- `Diiiiiiiildd...` - Transmits a FD extended data frame without bit rate switch
- `biiildd...` - Transmits a FD base data frame with bit rate switch
- `Biiiiiiiildd...` - Transmits a FD extended data frame with bit rate switch
- `V` and `v` - Returns firmware version and remote path as a string
- `Z` and `z` - Configures reporting mechanism including time stamp and Tx event
- `M` and `m` - Configures CAN acceptance filter
- `F` and `f` - Returns status flags and detailed status

Please find more information in the `doc` directory or the [wiki](https://github.com/Nakakiyo092/canable2-fw/wiki).

## Building

Firmware builds with GCC. Specifically, you will need gcc-arm-none-eabi, which
is packaged for Windows, OS X, and Linux on
[Launchpad](https://launchpad.net/gcc-arm-embedded/+download). Download for your
system and add the `bin` folder to your PATH.

Your Linux distribution may also have a prebuilt package for `arm-none-eabi-gcc` or `gcc-arm-none-eabi`, check your distro's repositories to see if a build exists. Simply compile by running `make`.

## Flashing with the Bootloader

Plug in your CANable2 while boot pins are shorted with jumper. Neither the blue nor the green LED should be illuminated. Next, type `make flash` and your CANable will be updated to the latest firwmare. Unplug/replug the device after moving the boot jumper back, and your CANable2 will be up and running.

## License

See LICENSE.md
