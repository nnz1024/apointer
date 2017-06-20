#!/usr/bin/env python2

import serial
#import io
import time
import re
import random
import math

def myreadline(port, size=None, eol="\r"):
	"""read a line which is terminated with end-of-line (eol) character
	('\n' by default) or until timeout."""
	leneol = len(eol)
	line = bytearray()
	while True:
		c = port.read(1)
		if c:
			line += c
			print "line = '" + bytes(line) + "'"
			if line[-leneol:] == eol:
				#print "Eol occured!"
				break
			if size is not None and len(line) >= size:
				#print "Length exceeds max!"
				break
		else:
			#print "Timeout!"
			break
	return bytes(line)

def getpos(port):
	ans = myreadline(port, size=255, eol="\r")
	strs = re.findall('OK(\d+\.\d+) ([-+]?\d+.\d+)', ans)
	print strs
	if ((len(strs) < 1) or (len(strs[-1]) < 2)):
		return None
	return [float(strs[-1][0]), float(strs[-1][1])] 

def reqpos(port):
	port.write("Y\r")
	return getpos(port)

def setpos(port, x=0, y=0):
	#cmd = 'Q' + str(x) + " " + str(y) + "\r"
	while (x < 0):
		x += 360
	while (x > 360):
		x -= 360
	#cmd = 'Q' + "{:.2f}".format(x) + " " + "{:.2f}".format(y) + "\r"
	cmd = "Q{:.2f} {:.2f}\r".format(x, y)
	print(cmd)
	port.write(cmd)

def ackwait(port):
	ack = re.compile('ACK')
	err = re.compile('ERR')
	ans = ''
	while (1):
		time.sleep(0.01)
		c = port.read(1)
		if c:
			ans = ans + port.read(1)
		else:
			return None
		print "ans = '" + ans + "'"
		if (ack.search(ans)):
			return 0
		if (err.search(ans)):
			return -1

def gotopos(port, x=0, y=0):
	setpos(port, x, y)
	if (ackwait(port) < 0):
		return None
	while (1):
		time.sleep(0.01)
		pos = getpos(port)
		if (pos):
			return pos

port = serial.Serial('/dev/ttyUSB0', 115200, timeout=10)
#print port
#port.write('Y\r')
#msg = port.readline(255)
#sio = io.TextIOWrapper(io.BufferedRWPair(port, port, 1), encoding='KOI8-R')
#sio.write(unicode("Y\r"))
#sio.flush()
#msg = sio.readline()
#port.write("Y\r")
#port.write("Q10 10\r")
#msg = myreadline(port, size=255, eol="\r")
#print 'MSG: <' + msg + ">\n"
#setpos(port, 0.1, -0.1)
n = 8
x0 = 180
y0 = 40
r = 30
for it in range(1, n+1):
	print 'Begin iter ' + str(it) + ': get pos'
	print reqpos(port)
	#print 'Go to 0, 0'
	#print gotopos(port, 0, 0)
	#print 'Check are we in 0, 0'
	#print reqpos(port)
	#x = random.randrange(-2300, 33500, 1)/100.0
	#y = random.randrange(-2300, 11100, 1)/100.0
	#print 'Go to some random point: x = ' + str(x) + ', y = ' + str(y)
	#print gotopos(port, x, y)
	phi = (2*math.pi*(it - 1))/n
	x = x0 + r*math.cos(phi)
	y = y0 + r*math.sin(phi)
	print 'Go to some circle point: x = ' + str(x) + ', y = ' + str(y) + ', phi = ' + str(phi)
	print gotopos(port, x, y)
	print 'Check are we in some point'
	print reqpos(port)

print gotopos(port, 180, 0)

port.close()
