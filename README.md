# voltwerk2mqtt

pick up power generation data from a voltwerk/suntechnics/conergy string inverter and publish to mqtt

This is written for my single phase VS5 (same as Conergy IPG 5S)

Will work also for 3 and 4kW inverters and may be extended to tri phase string inverters with CAN (e.g. VS15).

You must tweak the MQTT Broker IP to your needs.
This is no real protocol implementation, just fumbled out from capturing monitoring display traffic. So your Inverter may use another can ID and won't answer my requests. Then you have to play around a bit to find the right request messages. Same if you have more than 1 inverter on the bus.


## Install 

I used a linux SBC to host this script as a service. Any raspi, beagle bone, orange pi will work. You need a socket CAN supported hardware CAN interface, of course.

### Prerequisites
```
sudo apt install python3-can
```

### script install
copy all files from this repo to a new folder /opt/voltwerk2mqtt

then copy the service file to lib folder and activate service like so:
```
cp voltwerk2mqtt.service /lib/systemd/system/
systemctl enable voltwerk2mqtt
systemctl start voltwerk2mqtt
```
finally check the logfile ./log for errors and your mqtt broker for incomming data.

Remember, the inverter will answer only when it has enough daylight ;-)

