# voltwerk2mqtt

pick up power generation data from a voltwerk/suntechnics/conergy string inverter and publish to mqtt

This is written for my single phase VS5 (same as Conergy IPG 5S)
Will work also for 3 and 5kW inverters and may be extended to tri phase string inverters with CAN (e.g. VS15).

You must tweak the MQTT Broker IP to your needs.
This is no full protocol implementation, as no documentation is available. I just scraped caputured data from a monitoring display and reengineered the telegrams. So your Inverter may use other addresses and won't answer my requests. Then you have to play around a bit to find the right request messages...


## Install 

I used a linux SBC to host this script as a service. Any raspi, beagle bone, orange pi will work. You need a socket CAN supported CAN interface, of course.

copy all files to /opt/voltwerk2mqtt

then copy service file to lib folder and activate service
```
cp voltwerk2mqtt.service /lib/systemd/system/
systemctl enable voltwerk2mqtt
systemctl start voltwerk2mqtt
```


