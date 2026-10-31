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

Broker_Address = '192.168.168.112' # insert your own broker here
Mqtt_Prefix = 'iot/pv/voltwerk'
Topics = {
    'current':'iot/pv/voltwerk/ac_current_A',
    'voltage':'iot/pv/voltwerk/ac_voltage_V',
    'power':'iot/pv/voltwerk/ac_active_power_kW',
    'freq':'iot/pv/voltwerk/grid_frequency_Hz',
    'status':'iot/pv/voltwerk/service',
    }
Subscriptions = {}

requests = [can.Message(arbitration_id=0x0f89c181, dlc=1, data=[0x20]),
            can.Message(arbitration_id=0x0f8a0181, dlc=1, data=[0x20]),
            can.Message(arbitration_id=0x0f8a4181, dlc=1, data=[0x20]),
            can.Message(arbitration_id=0x0f890181, dlc=1, data=[0x20])]

request_count = 0

def on_disconnect(client, userdata, flags, reasonCode, properties=None):
  # paho >= 2.0 (CallbackAPIVersion.VERSION2) passes disconnect flags as 3rd argument.
  # Reconnecting is done by the loop_start() thread itself.
  logging.info("MQTT disconnected")
  if reasonCode != 0:
    logging.error(f"Unexpected MQTT disconnect rc={reasonCode}. Will auto-reconnect")
    print('Unexpected MQTT disconnect. Will auto-reconnect')


def on_connect(client, userdata, flags, reasonCode, properties=None):
  if reasonCode == 0:
    logging.info("Connected to MQTT Broker " + Broker_Address)
    for topic in Subscriptions.values():
      print("subcribe to " + topic)
      client.subscribe(topic)
    client.publish(Topics['status'], 'online', qos=1, retain=True)
  else:
    logging.error("Failed to connect, return code %d\n", reasonCode)
    sys.exit(3)


def on_message(client, userdata, msg):
  try:
    pass #we don't expect messages yet

  except Exception as e:
    logging.warning("Message parsing error " + str(e))
    print(e)


client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, 'Voltwerk2Mqtt')
client.on_disconnect = on_disconnect
client.on_connect = on_connect
client.on_message = on_message

def go_offline(*args):
  client.publish(Topics['status'], 'offline', qos=1, retain=True)
  client.disconnect()
  logging.info("Disconnect")
  sys.exit(0)


try:
  for sig in (SIGABRT, SIGINT, SIGTERM):
    signal(sig, go_offline)

  logging.basicConfig(format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    level=logging.INFO,
                    handlers=[
                        RotatingFileHandler("/opt/voltwerk2mqtt/log", maxBytes=100000, backupCount=2),
                        logging.StreamHandler()
                    ])

  client.will_set(Topics['status'], 'offline', qos=1, retain=True)  # must be set before connect
  client.connect(Broker_Address)  # connect to broker

  client.loop_start()


  logging.info("Start Voltwerk2MQTT service")

  with can.interface.Bus(channel='can0', interface="socketcan", bitrate=125000) as bus:
    while True:
      sleep(0.25)

      bus.send(requests[request_count])
      request_count = (request_count + 1) % len(requests)

      multiplier = 1
      topic = ''
      for msg in bus:
        if msg.arbitration_id == 0x0f0a4083:
          multiplier = 4
          topic = 'power'
        elif msg.arbitration_id == 0x0f0a0083:
          multiplier = 16
          topic = 'current'
        elif msg.arbitration_id == 0x0f09c083:
          multiplier = 256
          topic = 'voltage'
        elif msg.arbitration_id == 0x0f090083:
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
  client.publish(Topics['status'], 'offline', qos=1, retain=True)
  sys.exit(1)



