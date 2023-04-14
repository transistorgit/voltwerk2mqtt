#!/usr/bin/env python3
import can
import sys
from time import sleep

bus = can.interface.Bus()

requests = [can.Message(arbitration_id=0x0f89c101, dlc=1, data=[0x20]),
            can.Message(arbitration_id=0x0f8a0101, dlc=1, data=[0x20]),
            can.Message(arbitration_id=0x0f8a4101, dlc=1, data=[0x20]),
            can.Message(arbitration_id=0x0f890101, dlc=1, data=[0x20])]

request_count = 0

with can.Bus() as bus:
  while True:

    bus.send(requests[request_count])
    request_count = (request_count + 1) % len(requests)

    for msg in bus:
      #print(f'Header: {msg.arbitration_id:0x} DLC: {msg.dlc} Data: {bytes(msg.data).hex()}')

      # answer for get power reg 41: 0x7e0451 > 0.561523kW
      if msg.arbitration_id == 0x0f0a4082:
        #print("Power received")

        multiplier = 4      
        data = bytearray(msg.data)

        # to little endian
        data[0], data[1] = data[1], data[0]

        dataBin = data[0]<<8 | data[1]

        if dataBin&0x8000>0:    
            dataBin=((~dataBin)&0x7fff)+1
            data=-(dataBin/0x2000)*multiplier 
        else:
            dataBin = dataBin & 0x7fff
            data = (dataBin/0x2000)*multiplier

        print(f'AC Power {data:2.2f}kW')

      # answer for get currents reg 40: 0xa7 - 0x04 - 0x52 > 2.32617A 
      if msg.arbitration_id == 0x0f0a0082:
        #print("Current received")

        multiplier = 16      
        data = bytearray(msg.data)

        # to little endian
        data[0], data[1] = data[1], data[0]

        dataBin = data[0]<<8 | data[1]

        if dataBin&0x8000>0:    
            dataBin=((~dataBin)&0x7fff)+1
            data=-(dataBin/0x2000)*multiplier 
        else:
            dataBin = dataBin & 0x7fff
            data = (dataBin/0x2000)*multiplier

        print(f'AC Current {data:2.1f}A')

      # answer for get voltage reg 39: 0xbf - 0x1d - 0x54 > 237.969V 
      if msg.arbitration_id == 0x0f09c082:
        #print("Voltage received")

        multiplier = 256      
        data = bytearray(msg.data)

        # to little endian
        data[0], data[1] = data[1], data[0]

        dataBin = data[0]<<8 | data[1]

        if dataBin&0x8000>0:    
            dataBin=((~dataBin)&0x7fff)+1
            data=-(dataBin/0x2000)*multiplier 
        else:
            dataBin = dataBin & 0x7fff
            data = (dataBin/0x2000)*multiplier

        print(f'AC Voltage {data:3.0f}V')


      # answer for get freq reg 36: 
      if msg.arbitration_id == 0x0f090082:
        #print("Frequency received")

        multiplier = 64      
        data = bytearray(msg.data)

        # to little endian
        data[0], data[1] = data[1], data[0]

        dataBin = data[0]<<8 | data[1]

        if dataBin&0x8000>0:    
            dataBin=((~dataBin)&0x7fff)+1
            data=-(dataBin/0x2000)*multiplier 
        else:
            dataBin = dataBin & 0x7fff
            data = (dataBin/0x2000)*multiplier

        print(f'AC Frequency {data:2.2f}Hz')
      
      sleep(1)
      break

sys.exit(1)


