#!/usr/bin/env python3
'''
start CAN bus with
ip link set can0 up type can bitrate 125000
'''

import can
import sys, os
import logging
from logging.handlers import RotatingFileHandler
from time import sleep
import paho.mqtt.client as mqtt
from signal import *

Broker_Address = '192.168.168.112'
Mqtt_Prefix = 'iot/pv/voltwerk'
Topics = { 
    'current':'iot/pv/voltwerk/ac_current_A',
    'voltage':'iot/pv/voltwerk/ac_voltage_V',
    'power':'iot/pv/voltwerk/ac_active_power_kW',
    'freq':'iot/pv/voltwerk/grid_frequency_Hz',
    'status':'iot/pv/voltwerk/service',
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
  except Exception as e:
    logging.error("Failed to Reconnect to " + Broker_Address + " " + str(e))
    print("Failed to Reconnect to " + Broker_Address + " " + str(e))


def on_connect(client, userdata, flags, rc):
  if rc == 0:
    logging.info("Connected to MQTT Broker " + Broker_Address)
    for topic in Subscriptions.values():
      print("subcribe to " + topic)
      client.subscribe(topic)
    client.publish(Topics['status'], 'online')
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

def go_offline(*args):
  client.publish(Topics['status'], 'offline')
  client.disconnect()
  logging.info("Disconnect")
  sys.exit(0)


try:
  for sig in (SIGABRT, SIGINT, SIGTERM):
    signal(sig, go_offline)

  client.connect(Broker_Address)  # connect to broker
  client.will_set(Topics['status'], 'offline', qos=1, retain=True)

  client.loop_start()

  logging.basicConfig(format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    level=logging.INFO,
                    handlers=[
                        RotatingFileHandler("/opt/voltwerk2mqtt/log", maxBytes=100000, backupCount=2),
                        logging.StreamHandler()
                    ])

  logging.info("Start Voltwerk2MQTT service")

  with can.Bus() as bus:
    while True:
      sleep(0.25)

      bus.send(requests[request_count])
      request_count = (request_count + 1) % len(requests)

      multiplier = 1
      topic = ''
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

        if len(topic)==0 or len(msg.data)<2:
          break

        data = bytearray(msg.data)
        # to little endian
        data[0], data[1] = data[1], data[0]

        dataBin = data[0]<<8 | data[1]

        if dataBin&0x8000>0:
          dataBin = ((~dataBin) & 0x7fff) + 1
          data = -(dataBin/0x2000) * multiplier
        else:
          dataBin = dataBin & 0x7fff
          data = (dataBin/0x2000) * multiplier

        client.publish(Topics[topic],f'{data}')
        break
except Exception as e:
  logging.error("Error: ", exc_info=e)
finally:
  client.publish(Topics['status'], 'offline')
  sys.exit(1)



