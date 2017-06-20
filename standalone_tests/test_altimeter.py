#!/usr/bin/env python2

import smbus
import sys
import time

def proc_sign2w(x):
	if x >= 32768:
		x ^= 65535
		x += 1
		x *=-1
	return x

def proc_sign3w(x):
	if x >= 8388608:	# 2**23
		x ^= 16777215	# 2**24 -1
		x += 1
		x *=-1
	return x

bus = smbus.SMBus(1)
if (bus.read_byte_data(0x5d,0x0F) != 0xbb):
	print "This isn't an LPS331AP altimeter!"
	sys.exit(1)

# Init: 12.5 kHz (see table 18 on page 21)
bus.write_byte_data(0x5d, 0x20, 0b11100000)

while True:
	pxl = bus.read_byte_data(0x5d, 0x28)
	pl = bus.read_byte_data(0x5d, 0x29)
	ph = bus.read_byte_data(0x5d, 0x2a)
	ptotal = ((ph << 16) | (pl << 8) | pxl)
	p = float(proc_sign3w(ptotal)) / 4096
	tl = bus.read_byte_data(0x5d, 0x2b)
	th = bus.read_byte_data(0x5d, 0x2c)
	ttotal = ((th << 8) | tl)
	t = 42.5 + (float(proc_sign2w(ttotal)) / 480)
	print 'Pressure now is ', p, 'mbars, temperature is ', t, 'C'
	time.sleep(1)
