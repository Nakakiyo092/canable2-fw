# Benchmark for ver.1.4.0

Commit ID: ae8b9fefac4c326021873675d8a8d5caa4ff4e1b

## Environment

USB Hub Usage: No

```powershell
PS C:\Users\kiyomaro> function prompt { "> " }
> (Get-CimInstance Win32_Processor).Name
13th Gen Intel(R) Core(TM) i7-13620H
> (Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory / 1GB
15.6787643432617
> (Get-CimInstance Win32_OperatingSystem).Caption
Microsoft Windows 11 Home
> (Get-CimInstance Win32_OperatingSystem).Version
10.0.26200
> $PSVersionTable.PSVersion.ToString()
7.6.6
> python --version
Python 3.10.11
> pip freeze
pyserial==3.5
> 
```

## CDC Speed Test

```powershell
> python ./test/cdc_speed_test.py COM9 --rx --chunk-size 16 --iteration 2 --duration 10
usb port name: COM9

serial number: NEC02
slcan version: VL2K5
detail:
    v: hardware="CANable2.0", software="v1.4.0-dirty", url="github.com/Nakakiyo092/canable2-fw.git"

can port status: closed

ping: [490, 276, 162, 361, 355] us

tx speed:    178.01 kB/s          1424.05 kbits/s
rx speed:    533.56 kB/s          4268.50 kbits/s
message loss:  762  /  890032

device status:
detail:

tx speed:    181.61 kB/s          1452.85 kbits/s
rx speed:    540.27 kB/s          4322.18 kbits/s
message loss:  7578  /  908032

device status:
detail:

> python ./test/cdc_speed_test.py COM9 --tx --chunk-size 16 --iteration 2 --duration 10
usb port name: COM9

serial number: NEC02
slcan version: VL2K5
detail:
    v: hardware="CANable2.0", software="v1.4.0-dirty", url="github.com/Nakakiyo092/canable2-fw.git"

can port status: closed

ping: [254, 211, 229, 203, 215] us

tx speed:    556.22 kB/s          4449.78 kbits/s
rx speed:      4.00 kB/s            32.01 kbits/s
message loss:  0  /  40016

device status:
detail:

tx speed:    548.88 kB/s          4391.07 kbits/s
rx speed:      3.95 kB/s            31.59 kbits/s
message loss:  0  /  39488

device status:
detail:

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
 S0   .   P   P   -   P   P   -   -   P   -
 S1   .   .   P   -   P   P   -   -   P   -
 S2   .   .   .   -   E   P   -   -   P   -
 S3   .   .   .   -   .   .   -   -   P   -
 S4   .   .   .   -   .   .   -   -   E   -
 S5   .   .   .   -   .   .   -   -   .   -
 S6   .   .   .   -   .   .   -   -   .   -
 S7   .   .   .   -   .   .   -   -   .   -
 S8   .   .   .   -   .   .   -   -   .   -
 S9   .   .   P   -   P   P   -   -   P   -

summary:  pass=42  busErr=2  passive=16  busOff=0  skip=40  other=0
================================================================
.
----------------------------------------------------------------------
Ran 2 tests in 353.356s

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
   slcan version: VL2K5
   serial number: NEC02
 AUX (COM8):
   slcan version: VL2K5
   serial number: NEC01
=========================================================
Starting: frame_type=b, S8/Y5, payload=64 bytes, rate=2000.0 fps, duration=60 s, ping_id=0x100, echo_id=0x101
Press Ctrl-C to stop early.

  t+    10s  sent=    5137  recv=    5117  loss=   20  corrupt=  0  ~  511.3 fps
  t+    20s  sent=   10241  recv=   10227  loss=   14  corrupt=  0  ~  510.8 fps
  t+    30s  sent=   15353  recv=   15337  loss=   16  corrupt=  0  ~  510.7 fps
  t+    40s  sent=   20433  recv=   20411  loss=   22  corrupt=  0  ~  510.6 fps
  t+    50s  sent=   25537  recv=   25515  loss=   22  corrupt=  0  ~  510.3 fps

======================================================================
 stress_test summary  (elapsed 60.0 s, target 2000.0 fps)
======================================================================
  Pings sent (DUT->AUX):           30617
  Pings observed at AUX:           30617
  Echos sent (AUX->DUT):           30617
  Echos observed at DUT:           30617
  Echos with corrupted payload:    0
  Unexpected frames at DUT:        0
  Unexpected frames at AUX:        0
  Rejected commands ([BELL]):      DUT=0  AUX=0
  End-to-end loss:                 0 (0.00 %)
  Actual achieved rate:            509.9 fps

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
   slcan version: VL2K5
   serial number: NEC02
 AUX (COM8):
   slcan version: VL2K5
   serial number: NEC01
=========================================================
Starting: frame_type=b, S8/Y5, payload=64 bytes, rate=3000.0 fps, duration=60 s, ping_id=0x100, echo_id=0x101
Press Ctrl-C to stop early.

  t+    10s  sent=    5103  recv=    5083  loss=   20  corrupt=  0  ~  510.3 fps
  t+    20s  sent=   10217  recv=   10201  loss=   16  corrupt=  0  ~  510.5 fps
  t+    30s  sent=   15305  recv=   15283  loss=   22  corrupt=  0  ~  509.6 fps
  t+    40s  sent=   20377  recv=   20369  loss=    8  corrupt=  0  ~  509.4 fps
  t+    50s  sent=   25473  recv=   25461  loss=   12  corrupt=  0  ~  509.0 fps

======================================================================
 stress_test summary  (elapsed 60.0 s, target 3000.0 fps)
======================================================================
  Pings sent (DUT->AUX):           30545
  Pings observed at AUX:           30545
  Echos sent (AUX->DUT):           30545
  Echos observed at DUT:           30545
  Echos with corrupted payload:    0
  Unexpected frames at DUT:        0
  Unexpected frames at AUX:        0
  Rejected commands ([BELL]):      DUT=0  AUX=0
  End-to-end loss:                 0 (0.00 %)
  Actual achieved rate:            508.8 fps

  DUT final F: F00
  AUX final F: F00
======================================================================
>
```

```powershell
> python ./test/can_stress_test.py --rate 3000 --max-batch 60
WARNING: Setup: b'W0\r' returned b'\x07'
WARNING: Setup: b'W0\r' returned b'\x07'

=========================================================
 stress_test target devices
=========================================================
 DUT (COM9):
   slcan version: VL2K5
   serial number: NEC02
 AUX (COM8):
   slcan version: VL2K5
   serial number: NEC01
=========================================================
Starting: frame_type=b, S8/Y5, payload=64 bytes, rate=3000.0 fps, duration=60 s, ping_id=0x100, echo_id=0x101
Press Ctrl-C to stop early.

  t+    10s  sent=   30088  recv=   30032  loss=   56  corrupt=  0  ~ 2994.7 fps
  t+    20s  sent=   59944  recv=   59852  loss=   92  corrupt=  0  ~ 2992.4 fps
  t+    30s  sent=   89960  recv=   89899  loss=   61  corrupt=  0  ~ 2994.0 fps
  t+    40s  sent=  119797  recv=  119734  loss=   63  corrupt=  0  ~ 2993.7 fps
  t+    50s  sent=  149716  recv=  149633  loss=   83  corrupt=  0  ~ 2994.3 fps

======================================================================
 stress_test summary  (elapsed 60.0 s, target 3000.0 fps)
======================================================================
  Pings sent (DUT->AUX):           179710
  Pings observed at AUX:           179710
  Echos sent (AUX->DUT):           179710
  Echos observed at DUT:           179710
  Echos with corrupted payload:    0
  Unexpected frames at DUT:        0
  Unexpected frames at AUX:        0
  Rejected commands ([BELL]):      DUT=0  AUX=0
  End-to-end loss:                 0 (0.00 %)
  Actual achieved rate:            2993.6 fps

  DUT final F: F00
  AUX final F: F00
======================================================================
> python ./test/can_stress_test.py --rate 4000 --max-batch 60
WARNING: Setup: b'W0\r' returned b'\x07'
WARNING: Setup: b'W0\r' returned b'\x07'

=========================================================
 stress_test target devices
=========================================================
 DUT (COM9):
   slcan version: VL2K5
   serial number: NEC02
 AUX (COM8):
   slcan version: VL2K5
   serial number: NEC01
=========================================================
Starting: frame_type=b, S8/Y5, payload=64 bytes, rate=4000.0 fps, duration=60 s, ping_id=0x100, echo_id=0x101
Press Ctrl-C to stop early.

  t+    10s  sent=   34138  recv=   33102  loss= 1036  corrupt=  0  ~ 3403.2 fps
  t+    20s  sent=   67908  recv=   66345  loss= 1563  corrupt=  0  ~ 3390.1 fps
  t+    30s  sent=  101386  recv=   99594  loss= 1792  corrupt=  0  ~ 3379.5 fps
  t+    40s  sent=  135047  recv=  133074  loss= 1973  corrupt=  0  ~ 3376.2 fps
  t+    50s  sent=  168706  recv=  166697  loss= 2009  corrupt=  0  ~ 3372.0 fps

======================================================================
 stress_test summary  (elapsed 60.1 s, target 4000.0 fps)
======================================================================
  Pings sent (DUT->AUX):           202429
  Pings observed at AUX:           200735
  Echos sent (AUX->DUT):           200735
  Echos observed at DUT:           200577
  Echos with corrupted payload:    0
  Unexpected frames at DUT:        0
  Unexpected frames at AUX:        0
  Rejected commands ([BELL]):      DUT=0  AUX=0
  End-to-end loss:                 1852 (0.91 %)
  Actual achieved rate:            3369.4 fps

  DUT final F: F01
  AUX final F: F01
======================================================================
>
```

## Long Time Test

```powershell
> python --version
Python 3.13.14
> python ./test/long_time_test.py COM9 --duration 3
usb port name: COM9

serial number: NEC02
slcan version: VL2K5
detail:
    v: hardware="CANable2.0", software="v1.4.0-dirty", url="github.com/Nakakiyo092/canable2-fw.git"

can port status: open/loopback (1M/5Mbps)

ping: [503, 230, 333, 215, 340, 195, 336, 197, 753, 738] us


--- Stats at 0.017 hours ---

sent frames: 1288 / 1288 (-0)
  resync-detected drops: 0

status check: 1288 samples
  no error: 1288
  buffer error: 0
  can bus error: 0

timestamp comparison (host - device): 1287 samples
  ave abs error: 90.9 us
  max abs error: 9185 us
  failures: 0
    of which >32767 us: 0
    of which sentinel: 0

clock accuracy: 59 sec
  clock offset: 93.8 ms
  drift upper bound: 1642.2 ppm
  drift lower bound: 1488.4 ppm
  (reference, time.time() based):
    host perf_counter vs wall clock: -0.2 ppm
    device drift vs wall clock:      +1563.0 ppm


... snip ...


--- Stats at 3.033 hours ---

sent frames: 268034 / 268034 (-0)
  resync-detected drops: 0

status check: 268034 samples
  no error: 268034
  buffer error: 0
  can bus error: 0

timestamp comparison (host - device): 268033 samples
  ave abs error: 92.4 us
  max abs error: 14555 us
  failures: 0
    of which >32767 us: 0
    of which sentinel: 0

clock accuracy: 10918 sec
  clock offset: 19626.2 ms
  drift upper bound: 1797.9 ppm
  drift lower bound: 1797.1 ppm
  (reference, time.time() based):
    host perf_counter vs wall clock: -132.1 ppm
    device drift vs wall clock:      +1929.4 ppm

> 
```
