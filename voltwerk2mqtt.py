#!/usr/bin/env python3
'''
start CAN bus with
ip link set can0 up type can bitrate 125000
'''

import can
import sys, os
import logging
from time import sleep
import paho.mqtt.client as mqtt

Broker_Address = '192.168.168.112'
Mqtt_Prefix = 'iot/pv/voltwerk'
Topics = { 
    'current':'iot/pv/voltwerk/ac_current_A',
    'voltage':'iot/pv/voltwerk/ac_voltage_V',
    'power':'iot/pv/voltwerk/ac_active_power_W',
    'freq':'iot/pv/voltwerk/grid_frequency_Hz',
    }
Subscriptions = {}


bus = can.interface.Bus()

requests = [can.Message(arbitration_id=0x0f89c101, dlc=1, data=[0x20]),
            can.Message(arbitration_id=0x0f8a0101, dlc=1, data=[0x20]),
            can.Message(arbitration_id=0x0f8a4101, dlc=1, data=[0x20]),
            can.Message(arbitration_id=0x0f890101, dlc=1, data=[0x20])]

request_count = 0

def on_disconnect(client, userdata, rc):
  print("mqtt disconnected")
  if rc != 0:
    print('Unexpected MQTT disconnect. Will auto-reconnect')
  try:
    client.connect(Broker_Address)
    is_connected = True
  except Exception as e:
    logging.error("Failed to Reconnect to " + Broker_Address + " " + str(e))
    print("Failed to Reconnect to " + Broker_Address + " " + str(e))
    is_connected = False


def on_connect(client, userdata, flags, rc):
  if rc == 0:
    logging.info("Connected to MQTT Broker " + Broker_Address)
    is_connected = True
    for topic in Subscriptions.values():
      print("subcribe to " + topic)
      client.subscribe(topic)
  else:
    logging.error("Failed to connect, return code %d\n", rc)


def on_message(client, userdata, msg):
  try:
    pass #we don't expect messages yet

  except Exception as e:
    logging.warning("Message parsing error " + str(e))
    print(e)


client = mqtt.Client('Voltwerk2Mqtt') 
client.on_disconnect = on_disconnect
client.on_connect = on_connect
client.on_message = on_message
client.connect(Broker_Address)  # connect to broker

client.loop_start()

logging.basicConfig(format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    level=logging.INFO,
                    handlers=[
                        logging.FileHandler(
                            "%s/current.log" % (os.path.dirname(os.path.realpath(__file__)))),
                        logging.StreamHandler()
                    ])

logging.info("Start Voltwerk2MQTT service")

with can.Bus() as bus:
  while True:

    bus.send(requests[request_count])
    request_count = (request_count + 1) % len(requests)

    for msg in bus:
      if msg.arbitration_id == 0x0f0a4082:
        multiplier = 4
        topic = 'power'
      elif msg.arbitration_id == 0x0f0a0082:
        multiplier = 16
        topic = 'current'
      elif msg.arbitration_id == 0x0f09c082:
        multiplier = 256
        topic = 'voltage'
      elif msg.arbitration_id == 0x0f090082:
        multiplier = 64
        topic = 'freq'

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

      client.publish(Topics[topic],f'{data:.3f}')
      sleep(0.25)
      break



