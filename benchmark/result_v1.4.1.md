# Benchmark for ver.1.4.1

Commit ID: 66e41d51638688f5135a360aca8a2f49a984cb0d

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
Python 3.13.14
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

ping: [341, 374, 294, 300, 280] us

tx speed:    201.47 kB/s          1611.78 kbits/s
rx speed:    601.97 kB/s          4815.75 kbits/s
message loss:  4078  /  1007360

device status: 
detail:

tx speed:    197.91 kB/s          1583.28 kbits/s
rx speed:    589.83 kB/s          4718.64 kbits/s
message loss:  6502  /  989552

device status: 
detail:

> python ./test/cdc_speed_test.py COM9 --tx --chunk-size 16 --iteration 2 --duration 10
usb port name: COM9

serial number: NEC02
slcan version: VL2K5
detail:
    v: hardware="CANable2.0", software="v1.4.0-dirty", url="github.com/Nakakiyo092/canable2-fw.git"

can port status: closed

ping: [379, 259, 187, 169, 174] us

tx speed:    568.01 kB/s          4544.08 kbits/s
rx speed:      4.09 kB/s            32.69 kbits/s
message loss:  0  /  40864

device status: 
detail:

tx speed:    573.57 kB/s          4588.56 kbits/s
rx speed:      4.13 kB/s            33.01 kbits/s
message loss:  0  /  41264

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
 S1   .   .   E   -   P   P   -   -   P   - 
 S2   .   .   .   -   E   E   -   -   P   - 
 S3   .   .   .   -   .   .   -   -   E   - 
 S4   .   .   .   -   .   .   -   -   E   - 
 S5   .   .   .   -   .   .   -   -   .   - 
 S6   .   .   .   -   .   .   -   -   .   - 
 S7   .   .   .   -   .   .   -   -   .   - 
 S8   .   .   .   -   .   .   -   -   .   - 
 S9   .   .   P   -   P   P   -   -   P   - 

summary:  pass=42  busErr=5  passive=13  busOff=0  skip=40  other=0
================================================================
.WARNING: Setup: b'W0\r' returned b'\x07'
WARNING: Setup: b'W0\r' returned b'\x07'

================================================================
test_sp_grid_report  (nominal S8, rows = data SP, columns = data bit rate)
CAN clock: DUT 160 MHz, AUX 160 MHz
Legend: .=pass  E=bus_error  P=passive  O=bus-off  -=not representable  ?=other

         1M   2M   4M   5M   8M  10M  16M  20M
  20%    .    .    .    -    P    -    P    - 
  25%    .    .    .    .    P    P    -    P 
  30%    .    .    .    -    P    -    P    - 
  35%    .    .    .    -    .    -    -    - 
  40%    .    .    .    -    .    -    P    - 
  45%    P    .    .    -    .    -    -    - 
  50%    P    .    .    .    .    .    P    P 
  55%    P    .    .    -    .    -    -    - 
  60%    .    .    .    -    .    -    P    - 
  65%    .    .    .    -    .    -    -    - 
  70%    .    .    .    -    .    -    .    - 
  75%    .    .    .    .    .    .    -    P 
  80%    .    .    .    -    .    -    .    - 
  85%    .    .    .    -    .    -    -    - 
  90%    .    .    .    -    .    -    .    - 
  95%    .    .    .    -    .    -    -    - 

summary:  pass=66  busErr=0  passive=15  busOff=0  skip=47  other=0
================================================================
.
----------------------------------------------------------------------
Ran 3 tests in 438.384s

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

  t+    10s  sent=   20061  recv=   20056  loss=    5  corrupt=  0  ~ 2000.4 fps
  t+    20s  sent=   40020  recv=   40016  loss=    4  corrupt=  0  ~ 2000.2 fps
  t+    30s  sent=   60083  recv=   60078  loss=    5  corrupt=  0  ~ 2000.1 fps
  t+    40s  sent=   80028  recv=   80024  loss=    4  corrupt=  0  ~ 2000.0 fps
  t+    50s  sent=  100013  recv=  100008  loss=    5  corrupt=  0  ~ 2000.0 fps

======================================================================
 stress_test summary  (elapsed 60.0 s, target 2000.0 fps)
======================================================================
  Pings sent (DUT->AUX):           120000
  Pings observed at AUX:           120000
  Echos sent (AUX->DUT):           120000
  Echos observed at DUT:           120000
  Echos with corrupted payload:    0
  Unexpected frames at DUT:        0
  Unexpected frames at AUX:        0
  Rejected commands ([BELL]):      DUT=0  AUX=0
  End-to-end loss:                 0 (0.00 %)
  Actual achieved rate:            1999.9 fps

  DUT final F: F00
  AUX final F: F00
======================================================================
> python ./test/can_stress_test.py --rate 4000
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

  t+    10s  sent=   32598  recv=   32549  loss=   49  corrupt=  0  ~ 3256.9 fps
  t+    20s  sent=   64834  recv=   64784  loss=   50  corrupt=  0  ~ 3237.5 fps
  t+    30s  sent=   97560  recv=   97534  loss=   26  corrupt=  0  ~ 3251.1 fps
  t+    40s  sent=  130399  recv=  130366  loss=   33  corrupt=  0  ~ 3256.1 fps
  t+    50s  sent=  163233  recv=  163187  loss=   46  corrupt=  0  ~ 3262.2 fps

======================================================================
 stress_test summary  (elapsed 60.0 s, target 4000.0 fps)
======================================================================
  Pings sent (DUT->AUX):           196032
  Pings observed at AUX:           196032
  Echos sent (AUX->DUT):           196032
  Echos observed at DUT:           196032
  Echos with corrupted payload:    0
  Unexpected frames at DUT:        0
  Unexpected frames at AUX:        0
  Rejected commands ([BELL]):      DUT=0  AUX=0
  End-to-end loss:                 0 (0.00 %)
  Actual achieved rate:            3265.7 fps

  DUT final F: F00
  AUX final F: F00
======================================================================
> 
```

## Long Time Test

```powershell
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
