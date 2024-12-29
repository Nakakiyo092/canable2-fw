#!/bin/sh

# Set permission for USB port
sudo chmod 666 /dev/ttyACM0

# Run all test cases
echo "Run slcan test cases"
python3 test_slcan.py
echo "Run loopback test cases"
python3 test_loopback.py
echo "Run error test cases"
python3 test_error.py
