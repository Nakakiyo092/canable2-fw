# Benchmark for ver.1.3.1

Commit ID: 

## Environment

USB Hub Usage: No

```powershell
PS C:\Users\kiyomaro> function prompt { "> " }
> (Get-CimInstance Win32_Processor).Name
AMD Ryzen 9 9950X 16-Core Processor            
> (Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory / 1GB
31.1132659912109
> (Get-CimInstance Win32_OperatingSystem).Caption
Microsoft Windows 11 Home
> (Get-CimInstance Win32_OperatingSystem).Version
10.0.26200
> $PSVersionTable.PSVersion.ToString()
7.6.1
> python --version
Python 3.14.5
> pip freeze
pyserial==3.5
... snip ...
> 
```

## CDC Speed Test

```powershell
> python ./test/cdc_speed_test.py COM9 --rx --chunk-size 16 --iteration 2 --duration 10
usb port name: COM9

serial number: NEC01
slcan version: VL2K4
detail:
    v: hardware="CANable2.0", software="v1.3.1-dirty", url="github.com/Nakakiyo092/canable2-fw.git"

can port status: closed

ping: [789, 972, 983, 123, 209] us

tx speed:    239.94 kB/s          1919.49 kbits/s
rx speed:    548.27 kB/s          4386.14 kbits/s
message loss:  285900  /  1199680

device status: 
detail:

tx speed:    241.16 kB/s          1929.27 kbits/s
rx speed:    549.31 kB/s          4394.45 kbits/s
message loss:  290282  /  1205792

device status: 
detail:

> python ./test/cdc_speed_test.py COM9 --tx --chunk-size 16 --iteration 2 --duration 10
usb port name: COM9

serial number: NEC01
slcan version: VL2K4
detail:
    v: hardware="CANable2.0", software="v1.3.1-dirty", url="github.com/Nakakiyo092/canable2-fw.git"

can port status: closed

ping: [411, 369, 117, 184, 306] us

tx speed:    208.39 kB/s          1667.11 kbits/s
rx speed:      1.50 kB/s            11.99 kbits/s
message loss:  0  /  14992

device status: 
detail:

tx speed:    207.72 kB/s          1661.77 kbits/s
rx speed:      1.49 kB/s            11.96 kbits/s
message loss:  0  /  14944

device status: 
detail:

> 
```

## Long Time Test

```powershell
> python ./test/long_time_test.py COM9 --duration 3
usb port name: COM9

serial number: NEC01
slcan version: VL2K4
detail:
    v: hardware="CANable2.0", software="v1.3.1-dirty", url="github.com/Nakakiyo092/canable2-fw.git"

can port status: open/loopback (1M/5Mbps)

ping: [801, 455, 102, 119, 119, 124, 113, 121, 119, 178] us


--- Stats at 0.017 hours ---

sent frames: 1505 / 1505 (-0)
  resync-detected drops: 0

status check: 1505 samples
  no error: 1505
  buffer error: 0
  can bus error: 0

timestamp comparison (host - device): 1504 samples
  ave abs error: 182.1 us
  max abs error: 6493 us
  failures: 0
    of which >32767 us: 0
    of which sentinel: 0

clock accuracy: 59 sec
  clock offset: 133.4 ms
  drift upper bound: 2272.6 ppm
  drift lower bound: 2182.4 ppm
  (reference, time.time() based):
    host perf_counter vs wall clock: -0.1 ppm
    device drift vs wall clock:      +2223.3 ppm


... snip ...


--- Stats at 3.033 hours ---

sent frames: 268977 / 268977 (-0)
  resync-detected drops: 0

status check: 268977 samples
  no error: 268977
  buffer error: 0
  can bus error: 0

timestamp comparison (host - device): 268976 samples
  ave abs error: 203.3 us
  max abs error: 15197 us
  failures: 0
    of which >32767 us: 0
    of which sentinel: 0

clock accuracy: 10919 sec
  clock offset: 23815.3 ms
  drift upper bound: 2181.1 ppm
  drift lower bound: 2180.7 ppm
  (reference, time.time() based):
    host perf_counter vs wall clock: -0.0 ppm
    device drift vs wall clock:      +2180.9 ppm

> 
```

## CAN Communication Test

```powershell
> python ./test/communication_test.py
WARNING: Setup: b'W0\r' returned b'\x07'
WARNING: Setup: b'W0\r' returned b'\x07'
.WARNING: Setup: b'W0\r' returned b'\x07'
WARNING: Setup: b'W0\r' returned b'\x07'

================================================================
test_full_grid_report  (S = nominal index, Y = data index)
Legend: .=pass  E=bus_error  P=passive  O=bus-off  -=skip  ?=other

      Y0  Y1  Y2  Y3  Y4  Y5  Y6  Y7  Y8  Y9 
 S0   .   E   P   -   P   P   -   -   P   - 
 S1   .   .   P   -   P   P   -   -   P   - 
 S2   .   .   .   -   E   E   -   -   P   - 
 S3   .   .   .   -   .   .   -   -   E   - 
 S4   .   .   .   -   .   .   -   -   E   - 
 S5   .   .   .   -   .   .   -   -   .   - 
 S6   .   .   .   -   .   .   -   -   .   - 
 S7   .   .   .   -   .   .   -   -   .   - 
 S8   .   .   .   -   .   .   -   -   .   - 
 S9   -   -   -   -   -   -   -   -   -   - 

summary:  pass=40  busErr=5  passive=9  busOff=0  skip=46  other=0
================================================================
.
----------------------------------------------------------------------
Ran 2 tests in 215.528s

OK
> 
```

## CAN Stress Test

```powershell
> python ./test/can_stress_test.py --rate 2000
WARNING: Setup: b'W0\r' returned b'\x07'
WARNING: Setup: b'W0\r' returned b'\x07'

=========================================================
 stress_test target devices
=========================================================
 DUT (COM9):
   slcan version: VL2K4
   serial number: NEC01
 AUX (COM8):
   slcan version: VL2K4
   serial number: NEC02
=========================================================
Starting: frame_type=b, S8/Y5, payload=64 bytes, rate=2000.0 fps, duration=60 s, ping_id=0x100, echo_id=0x101
Press Ctrl-C to stop early.

  t+    10s  sent=   20055  recv=   20049  loss=    6  corrupt=  0  ~ 2000.1 fps
  t+    20s  sent=   40005  recv=   39999  loss=    6  corrupt=  0  ~ 2000.0 fps
  t+    30s  sent=   60061  recv=   60056  loss=    5  corrupt=  0  ~ 1999.9 fps
  t+    40s  sent=   80015  recv=   80009  loss=    6  corrupt=  0  ~ 1999.9 fps
  t+    50s  sent=  100080  recv=  100073  loss=    7  corrupt=  0  ~ 1999.9 fps

======================================================================
 stress_test summary  (elapsed 60.0 s, target 2000.0 fps)
======================================================================
  Pings sent (DUT->AUX):           120024
  Pings observed at AUX:           120024
  Echos sent (AUX->DUT):           120024
  Echos observed at DUT:           120024
  Echos with corrupted payload:    0
  Unexpected frames at DUT:        0
  Unexpected frames at AUX:        0
  Rejected commands ([BELL]):      DUT=0  AUX=0
  End-to-end loss:                 0 (0.00 %)
  Actual achieved rate:            1999.8 fps

  DUT final F: F00
  AUX final F: F00
======================================================================
> python ./test/can_stress_test.py --rate 3000
WARNING: Setup: b'W0\r' returned b'\x07'
WARNING: Setup: b'W0\r' returned b'\x07'

=========================================================
 stress_test target devices
=========================================================
 DUT (COM9):
   slcan version: VL2K4
   serial number: NEC01
 AUX (COM8):
   slcan version: VL2K4
   serial number: NEC02
=========================================================
Starting: frame_type=b, S8/Y5, payload=64 bytes, rate=3000.0 fps, duration=60 s, ping_id=0x100, echo_id=0x101
Press Ctrl-C to stop early.

  t+    10s  sent=   24919  recv=   21236  loss= 3683  corrupt=  0  ~ 2486.6 fps
  t+    20s  sent=   48169  recv=   37791  loss=10378  corrupt=  0  ~ 2403.3 fps
  t+    30s  sent=   70094  recv=   50978  loss=19116  corrupt=  0  ~ 2335.5 fps
  t+    40s  sent=   94170  recv=   69310  loss=24860  corrupt=  0  ~ 2351.8 fps
  t+    50s  sent=  115646  recv=   80270  loss=35376  corrupt=  0  ~ 2312.3 fps

======================================================================
 stress_test summary  (elapsed 60.0 s, target 3000.0 fps)
======================================================================
  Pings sent (DUT->AUX):           138844
  Pings observed at AUX:           96506
  Echos sent (AUX->DUT):           96506
  Echos observed at DUT:           96506
  Echos with corrupted payload:    0
  Unexpected frames at DUT:        0
  Unexpected frames at AUX:        0
  Rejected commands ([BELL]):      DUT=0  AUX=0
  End-to-end loss:                 42338 (30.49 %)
  Actual achieved rate:            2312.6 fps

  DUT final F: F00
  AUX final F: F01
======================================================================
> 
```
