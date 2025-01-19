#!/bin/sh

# Set permission for USB port
sudo chmod 666 /dev/ttyACM0

# Run all test cases
echo ""
echo ""
echo "Run slcan test cases"
python3 test/test_slcan.py
echo ""
echo ""
echo "Run loopback test cases"
python3 test/test_loopback.py
echo ""
echo ""
echo "Run error test cases"
python3 test/test_error.py
