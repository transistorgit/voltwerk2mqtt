# voltwerk2mqtt

pick up power generation data from voltwerk/conergy string inverters and publish to mqtt

This is written for my single phase VS5 (same as Conergy IPG 5S)

Will work also for 3 and 4kW inverters and may be extended to tri phase string inverters with CAN (e.g. VS15).

You must tweak the MQTT Broker IP to your needs.
This is no real protocol implementation, just fumbled out from capturing monitoring display traffic. So your Inverter may use another can ID and won't answer my requests. Then you have to play around a bit to find the right request messages. Same if you have more than 1 inverter on the bus.


## Install 

I use this on a small linux box. Orange Pi Zero in my case, but any beagle bone, raspberry etc will do.

As can interface I used a peak can usb dongle that I had laying around. Any other OS supported device will do. For peak, activate driver with 
```
sudo modprobe peak_usb
echo peak_usb >>/etc/modules
```

copy all files to /opt/voltwerk2mqtt/

then copy the service file to lib folder and activate service like so:
```
cp voltwerk2mqtt.service /lib/systemd/system/
systemctl enable voltwerk2mqtt
systemctl start voltwerk2mqtt
```
finally check the logfile ./log for errors and your mqtt broker for incomming data.

Remember, the inverter will answer only when it has enough daylight ;-)

