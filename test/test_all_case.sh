#!/bin/sh

# Set permission for USB port
sudo chmod 666 /dev/ttyACM0

# Run all test cases
python3 test_slcan.py
python3 test_loopback.py
python3 test_error.py
