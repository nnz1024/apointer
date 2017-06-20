# APointer — antenna pointing system for Unmanned Aerial Vehicles (UAVs)

This repository contatins the results of the work I did in 2015 and which was
never finished. However, there may be some interesting technical solutions 
which can be useful in developing of simular systems.

Some modules from this repository (e.g. altimu, radant, ubntsig) also may be 
useful by itself in a wide variety of tasks related to the use of corresponding
hardware.

## Hardware

To make it easier for you to understand the organization of the software part, 
it is need to tell a little about the hardware one. Main task of the system is
to keep a pointing of the ground directional antenna to the flying UAV. On the 
UAV, the compact omnidirectional antenna was used, which is not requires for
special pointing.

### Data link

Data channel (primarily for HD video, i.e. FPV) was established with using of
two Ubiquiti Rocket M5 802.11n routers. Getting the signal level from the 
ground station (for displaying and logging) with such hardwave requires some
hacks. Firstly, it is need to configure the UAV's router as AP, and the
ground one as a station, for simplicity to receiving signal level from the 
ground one (because station can has only one AP, while AP can have many
connected stations, which would complicate the parsing of SNMP data). Secondly, 
by default Ubiquiti's snmpd configured to update SNMP counters only with 16 
seconds period, so there is no real-time data. This can be bypassed by some 
crutches (see `./ubiquiti_hacks/`).

### Coordinates of the UAV

Coordinate data from UAV was received via Mission Planner program, which is
mostly used as a remote management system for UAV's flight controller (such as
APM or PIX). Flight controller on the board on UAV gets coordinate data from
GPS and altimeter, and sends it to the ground point where Mission Planner 
receives and decodes it. Special Python script (Mission Planner allows to use 
such a scripts) sends this data next to the main control computer (see 
`./mission_planner/`). If you find this scheme unuseful, you may alter it as you
need, as the coordinate sending protocol is very simple (see
`./mission_planner/README.md`). For example, you may send it from the special 
on-board controller with own GPS, altimeter and Ethernet devices.

### Control device

Main control computer was Raspberry Pi B+ with Pololu AltIMU-10 
magnetometer/barometer/altimeter board connected via I2C and u-blox LEA-6 GPS 
module connected via USB through pl2303 USB-UART converter. These sensors was 
used to determine coordinates and heading of ground antenna installation, so all
of these devices was mounted directly on the antenna and rotates with it (this 
was used in calibration of accelermoter and magnetometer, see `./prepare.py`).
Main software of this computer was Raspbian Wheezy with gpsd 3.6, nginx 1.2.1
and Python 2.7.3 (there was some problems with GPS support in Python 3, so it 
has been decided to use Python 2 for an entire project). Also, additional Python 
modules are required (corresponding Raspbian packages):

* serial (python-serial)
* smbus (python-smbus)
* gps (python-gps)
* netsnmp (python-pynetsnmp in Wheezy, python-netsnmp since Jessie)

System was tested on Raspbian Wheezy, and, some parts, on Debian Squeeze (my 
working machine on that moment, amd64) with the stock versions of packages. 
I do not remember this exactly, but in the case of problems with gpsd/libgps20 
3.6, try 3.9 (can be found in Wheezy-Backports) or higher. There are no other 
dragons, AFAIK.

### Antenna rotator

Antenna (Ubiquiti RocketDish 5G-34 in our case) was mounted on azimuth-elevation
rotational device Radant AZ3000V which was managed by controller Radant AZV-1.
This controller also was connected to the main control computer via pl2303
USB-UART converter, so, to distinct AZV-1 and LEA-6, it was need to add udev 
rules which permanently maps USB ports to `/dev/ttyUSB*` devices, e.g.
```
    KERNEL=="ttyUSB*", KERNELS=="1-8.1.5", NAME="ttyUSB0"
    KERNEL=="ttyUSB*", KERNELS=="1-8.1.6", NAME="ttyUSB1"
```
where `KERNELS` can be found out by performing
```
    udevadm info --name=/dev/ttyUSBx --attribute-walk
```
when your device connected to the given port, and other USB ports are 
disconnected.

### Practical use

It is worth noting that with Ubiquiti Rocket M5 wireless routers on both sides,
Ubiquiti RocketDish 5G-34 antenna on the ground point and a simple 
omnidirectional (~5 dBi) antenna on the UAV, it is possible to reach **200 km 
distance** with stable link. (It was the main point to assemble all the system.)
A few tips if you want to do some simular on really long distance (over a tens
of kilometers):

* It is recommended *not* to use both polarizations (i.e. MCS higher than 7)
with H-V polarized antennas (e.g. RocketDish) since the horizontal polarization
fades out faster than vertical one, which leads to channel disbalance and link
unstability. Also you may completely disable one of the device's channels
(see `./ubiquiti_hacks/README.md`).

* It is **strongly not recommended** to use MCS0, as there is some serious 
problems with implementation of this MCS on Ubiquiti devices. Depends of your
data rate and selected channel width, MCS1 or MCS2 may be optimal on long
links. Don't set MCS which maximum data rate is less or equal of your peak data
rate (plus 20-30% gap for protocol overhead), since it may leads to long-term 
link failures.

* Don't forget to enable AirMAX (Ubiquiti-specific TDMA mode), because of IEEE 
802.11 implementation in such devices has an ACK timeout limit which in turn 
limits the maximium distance of the link to 25 or 50 kilometers (for 40 or 20
MHz channel width correspondingly). With AirMAX with "Long Range PtP Link Mode"
enabled, we had no such problems.

* It is recommended to disable DFS, or do not use DFS band if your firmware 
doesn't allow you to disable it. With DFS, re-establishing link after its loss
may take significally more time (about ~40 seconds) than without it. 

* Limitation of scanning frequencies on the station to the frequency of AP 
channel also speeds up (re)establishing of a link.

* Of course, if you want to get a really long link, you need to set TX power on
both devices to maximum. Note that the hardware limit of TX power on Rocket M5
is 28 dBm, but there is also a software limit, which depends on selected 
country. See 
https://wireless.wiki.kernel.org/en/developers/regulatory/wireless-regdb
for further details.

Example configs for UAV's access point and ground station (in Ubiquiti config
backup format) are located in `./router_configs/` dir. Note that it was a test
configuration, so there was no security remedies was taken (e.g. WPA2, HTTPS UI,
non-default root user ("ubnt:ubnt"), non-default SNMP comminity ("public"), 
etc). And, if you have uploaded them on your devices, don't forget to check all
the settings noted above in this section.

## Software

Main software components are

* `altimu.py` — implementation of receiving sensor data from LSM303DLHC 3-axis 
accelerometer/magnetometer and LPS331AP altimeter (from AltIMU-10 module
connected via I2C). Using of accelerometer/magnetometer requires preliminary
calibration with rotating device on different angles and fixation of highest
received values (to normalize follow-up indications on them). In our system,
it was made using antenna rotating device (see `./prepare.py`). In fact, our
system uses only magnetometer to detemine heading of rotator's base position
relative to the magnetic north. Support for accelerometer and barometer was 
implemented and planned to use, but never used really. Support for L3GD20 
gyroscope (also presents on AltIMU-10) was not implemented at all.

* `radant.py` — working with Radant AZV-1 (and possibly AZV-3) antenna rotator
controller. Allows to point antenna to the given position (with and without 
waiting for the end of movement), stop movement, request current antenna 
position and set angle speeds (last one is only for AZV-3 and was not tested).

* `ubntsig.py` — simple Net-SNMP wrapping module for receiving signal level from
the ground wireless router (Ubiquiti Rocket M5) for displaying and logging. 
Please note that it requires some hacks to works normally (see "Data link" 
section). Also, SNMP OID for signal level may differs for different device 
models and firmware versions.

* `myconf.py` — class for working with config file (`./main.ini`), which
incapsulates reading and writing confguration and also sets the default values
for the parameters missing in this file.

* `nsock.py` — implements classes for working with listening stream and 
datagram sockets where messages are divided by newline charater (\n). It was 
handy specially for stream sockets, as a datagram ones allows to easy separate 
small messages. Used to receive coordinate data from Mission Planner.
Note that stream (i.e. TCP) support was abandoned later due to problems on
unstable links (needs to re-establish connection after link loss).

* `prepare.py` — script for calibrating the installation. Firstly, it rotates
antenna with magnetometer for multiple times to calibrate the magnetometer.
After that, it return antenna to base position and determines magnetic heading
of this position. Using magnetic declination and static error (angle between
antenna and magnetometer axes) values from config file, it determines true
heading of antenna base position. In parallel, it determines antenna
coordinates via GPS. After all, it writes results back to config.

* `sigtracker.py` — unfinished prototype of script which points antenna using
only signal level, without GPS coordinates. I do not know what can be the use 
of it, but nonetheless did not delete it.

* `tracker.py` — main program which continously performs several tasks (yes,
I know about GIL, but it was not disturb in our case):

    * Receiving the coordinates of UAV and calculating azimuth and elevation of
    the antenna to point it to UAV.
    * Sending these angles to the rotator controller.
    * Tracking the signal level (from the ground wireless router).
    * Maintaining the log which every line contains a UNIX timestamp, 
    coordinates of the UAV, calculated azimuth and elevation of the antenna, 
    calculated distance to the UAV and signal power in dBm in CSV format with 
    Windows-style newline termination (\r\n).
    * Serving the requests from web UI (see `./web_ui/`), viz. sending 
    configuration parameters, coordinates of the UAV, azimuth and elevation of
    the antenna, distance to the UAV and signal power in dBm for displaying in 
    the web UI. Note that this UI uses HTML5 and AJAX and requires some settings
    for web server (see `./web_ui/README.md`), but **does not require** any 
    additional server-side interpreters such as PHP.

## Current status

Work is abandoned since the August of 2015. Now there is a many of things in
code I don't like, but I can't heavy refactor it since it is impossible to
test it on real hardware. So the code provided "AS IS". (Sorry for tabs.)

## Legals

The customer did not fulfill his contract obligations, and the only owner of 
all rights to the code is me. So I decided to publish all the code under WTFPL 
in the hope that it will be useful to somebody.
