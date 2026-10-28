# voltwerk2mqtt

pick up power generation data from a voltwerk/suntechnics/conergy string inverter and publish to mqtt

This is written for my single phase VS5 (same as Conergy IPG 5S)

Will work also for 3 and 4kW inverters and may be extended to tri phase string inverters with CAN (e.g. VS15).

You must tweak the MQTT Broker IP to your needs.
This is no real protocol implementation, just fumbled out from capturing monitoring display traffic. So your Inverter may use another can ID and won't answer my requests. Then you have to play around a bit to find the right request messages. Same if you have more than 1 inverter on the bus.

The CAN IDs contain the inverter address. If your inverter does not answer, find its address with `canscan.py` (see below) and adapt the IDs in `voltwerk2mqtt.py`. The protocol, as far as it is known, is described at the end of this file.


## Install 

I used a linux SBC to host this script as a service. Any raspi, beagle bone, orange pi will work. You need a socket CAN supported CAN interface, of course.

copy all files to /opt/voltwerk2mqtt

then copy the service file to lib folder and activate service like so:
```
cp voltwerk2mqtt.service /lib/systemd/system/
systemctl enable voltwerk2mqtt
systemctl start voltwerk2mqtt
```
finally check the logfile ./log for errors and your mqtt broker for incomming data.

Remember, the inverter will answer only when it has enough daylight ;-)

## Find the inverter address: canscan.py

My inverter originally had address 2. After a second monitoring display was connected to the bus, it answered only on address 3; most likely the display re-addressed it. `canscan.py` finds the address by sending a read request to every address and waiting for the answer.

Run it in daylight, and stop the service first, because both use the bus:
```
sudo systemctl stop voltwerk2mqtt
python3 /opt/voltwerk2mqtt/canscan.py
sudo systemctl start voltwerk2mqtt
```

What it does:
1. **Listen** passively for 10 s and print every frame, decoded by the ID layout below. Other devices on the bus show up here.
2. **Scan**: read register 39 (AC voltage) from destination address 0..127 with own source address 1, waiting 0.3 s for each answer (about 40 s in total). It stops at the first valid answer. Frames that are not the expected answer are printed too.
3. **Confirm**: read all four registers from the address found and print the request and response IDs to put into `voltwerk2mqtt.py`.

Before and after the scan it prints state and error counters of `can0` (e.g. `ERROR-ACTIVE (tx errors 0, rx errors 0, bitrate 125000)`). Rising error counters point to a wiring, termination or bitrate problem rather than a wrong address. The script refuses to run while `voltwerk2mqtt` is active (override with `--force`).

Options:

| Option | Default | Meaning |
|---|---|---|
| `--listen S` | `10` | seconds of passive listening first, `0` skips it |
| `--dst LIST` | `0-127` | destination (inverter) addresses to try, e.g. `3` or `1-10,20` |
| `--src LIST` | `1` | own source addresses to try; `--src 0-127` tries all combinations (128 × 128 requests, about 80 min) |
| `--reg N` | `39` | register to read |
| `--timeout S` | `0.3` | seconds to wait for each answer |
| `--all` | off | do not stop at the first hit |
| `--channel`, `--interface` | `can0`, `socketcan` | CAN interface (python-can) |
| `--force` | off | run even if voltwerk2mqtt is active |

Exit code: 0 if the inverter answered, 1 if not.

## CAN protocol

Reverse engineered from the traffic between inverter and monitoring display. It is not complete; only the four registers below are known.

- 125 kbit/s, 29 bit extended IDs
- polling: the master (display or this script) sends a request, the inverter answers within about 3 ms
- the inverter is silent when it is dark

### CAN ID

| Bits | Width | Meaning |
|---|---|---|
| 28..24 | 5 | always `0x0F` |
| 23 | 1 | `1` = request, `0` = response |
| 22..14 | 9 | register |
| 13..7 | 7 | destination address |
| 6..0 | 7 | source address |

```
id = 0x0F << 24 | request << 23 | register << 14 | destination << 7 | source
```

Addresses: the master is 1 (the original display, and this script, which imitates it); the inverter was 2 and is 3 now. In a response, destination and source are swapped. The register field may be narrower than 9 bits; only values up to 41 have been seen.

### Registers

IDs for the current setup (master 1, inverter 3):

| Register | Value | Request ID | Response ID | Byte 2 | Factor 4ⁿ | Resolution |
|---|---|---|---|---|---|---|
| 36 (0x24) | grid frequency, Hz | `0x0F890181` | `0x0F090083` | `0x53` | 64 | 0.0078 Hz |
| 39 (0x27) | AC voltage, V | `0x0F89C181` | `0x0F09C083` | `0x54` | 256 | 0.031 V |
| 40 (0x28) | AC current, A | `0x0F8A0181` | `0x0F0A0083` | `0x52` | 16 | 0.002 A |
| 41 (0x29) | AC active power, kW | `0x0F8A4181` | `0x0F0A4083` | `0x51` | 4 | 0.49 W |

With the old inverter address 2 the IDs end in `…0101` (request) and `…0082` (response) instead of `…0181` and `…0083`.

### Request frame

| Byte | Value | Meaning |
|---|---|---|
| 0 | `0x20` | read (the only command known) |

DLC 1.

### Response frame

| Byte | Meaning |
|---|---|
| 0 | value, low byte |
| 1 | value, high byte |
| 2 | `0x5n`: low nibble `n` is the scale exponent, high nibble always `5` (meaning unknown) |

DLC 3. Bytes 0 and 1 form a signed 16 bit integer (little endian, two's complement):
```
value = int16(byte1 << 8 | byte0) / 8192 * 4**n
```
`voltwerk2mqtt.py` uses a fixed factor per register instead of byte 2; the factors are the same (4, 16, 64, 256). Reading byte 2 as the scale exponent is an interpretation based on these four registers only.

Examples captured on 2026-10-28:

| Response ID | Data | Raw | Value |
|---|---|---|---|
| `0x0F09C083` | `C7 1D 54` | 0x1DC7 = 7623 | 7623 / 8192 × 256 = 238.2 V |
| `0x0F0A0083` | `29 00 52` | 0x0029 = 41 | 41 / 8192 × 16 = 0.080 A |
| `0x0F0A4083` | `18 00 51` | 0x0018 = 24 | 24 / 8192 × 4 = 0.012 kW |
| `0x0F090083` | `00 19 53` | 0x1900 = 6400 | 6400 / 8192 × 64 = 50.00 Hz |
