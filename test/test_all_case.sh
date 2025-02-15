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
echo ""
echo ""
echo "Setup before reset"
python3 test/test_reset_before.py
echo ""
echo ""
echo "Reset the device then press enter..."
read input
sudo chmod 666 /dev/ttyACM0
echo ""
echo ""
echo "Run test after reset"
python3 test/test_reset_after.py
echo ""
echo ""
echo "Fix CAN bus at dominant level then press enter..."
read input
echo ""
echo ""
echo "Run dominant test cases"
python3 test/test_dominant.py
echo ""
echo ""
echo "Short CAN high and low then press enter..."
read input
echo ""
echo ""
echo "Run short test cases"
python3 test/test_short.py
echo ""
echo ""
echo "Make ready to check LED then press enter..."
read input
echo ""
echo ""
echo "Run led test cases"
python3 test/test_led.py

# Restore default setup
echo ""
echo ""
echo "Restore default setup"
python3 test/tool_default_setup.py
echo ""
echo ""
echo "Complete"

