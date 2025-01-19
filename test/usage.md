# Usage of test scripts

1. Connect PC and CANable
2. CANable should not be connected to another CAN device
4. Search device and get the device name of CANable
5. Update test scripts with the device name
6. Run test scripts


## Reference command for linux

### Search device command
`ls /dev/tty*`

### Set authority command
`sudo chmod 666 /dev/ttyACM0`

### Communicate with device
`screen /dev/ttyACM0`

