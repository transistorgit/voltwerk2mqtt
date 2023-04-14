# voltwerk2mqtt

pick up power generation data from voltwerk/conergy string inverters and publish to mqtt

This is written for my single phase VS5 (same as Conergy IPG 5S)
Will work also for 3 and 5kW inverters and may be extended to tri phase string inverters with CAN (e.g. VS15).

You must tweak the MQTT Broker IP and maybe also the Topics to your needs.
This is no real protocol implementation, just caputure replay from a monitoring display. So your Inverter may use other addresses and won't answer my requests. Then you have to play around a bit to find the right request messages...


## Install 

copy all files to /opt/voltwerk2mqtt

then copy service file to lib folder and activate service
```
cp voltwerk2mqtt.service /lib/systemd/system/
systemctl enable voltwerk2mqtt
systemctl start voltwerk2mqtt
```


