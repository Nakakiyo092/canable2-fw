# Usage of test scripts

1. Connect PC and the device
2. The device should not be connected to another CAN device
4. Search the device and get the device name (ex. COMX or ttyACMX)
5. Update test scripts with the device name
6. Run the test script from the root directory

Windows
```
.\test\test_all_case.bat
```
Linux
```
./test/test_all_case.sh
```


## Reference command for linux

### Search device command
```
ls /dev/tty*
```

### Set authority command
```
sudo chmod 666 /dev/ttyACM0
```

### Communicate with device
```
screen /dev/ttyACM0
```

