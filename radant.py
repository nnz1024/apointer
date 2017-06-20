#!/usr/bin/env python2
# Class for working with Radant AzEl Antenna Rotator (i.e. AZ3000V)
# via AZV-1 serial controller (vendor site: http://www.povorotka.ru/)

# Protocol description:
# http://www.povorotka.ru/data/documents/Radant_Port_Exchange.txt
# Note that real baudrate for our AZV-1 was 115200 (rather than 9600).

# This class must also support AZV-3 protocol described in
# http://povorotka.ru/data/documents/Radant_Port_Exchange_V3.txt
# including setting angle speeds, but it was not tested.

# These guys used \r as line (and message) terminator, so it has been decided to
# re-implement readline method with eol parameter and timeout support.

import serial
import utils
import time
import re

class Radant:
	fakepos = [180, 0]
	# Limits from http://povorotka.ru/data/documents/Radant_Port_Exchange_V3.txt
	speedlim = [0.3, 9.9]
	def __init__(self, fname='/dev/ttyUSB0', timeout=10, 
			emulate=False, baudrate=115200):
		self.debug = 2
		self.emulate = emulate
		if (self.emulate):
			self.port = None
			utils.print_err('Radant: WARNING! Radant now works in emulation mode.')
			return
		self.port = serial.Serial(port=fname, baudrate=baudrate, timeout=timeout)
		#self.ack = re.compile('ACK')
		#self.err = re.compile('ERR')
		self.okpos = re.compile('OK(\d+\.\d+) ([-+]?\d+.\d+)')

	def __del__(self):
		self.finish()

	def finish(self):
		if (self.emulate):
			return
		self.port.close()
		
	def myreadline(self, size=None, eol="\r"):
		""" Read a line which is terminated with end-of-line (eol) 
		character ('\r' by default) or until timeout """
		leneol = len(eol)
		line = bytearray()
		while True:
			c = self.port.read(1)
			if c:
				line += c
				if (self.debug > 1):
					print "Readline: line = '" + bytes(line) + "'"
				if (line[-leneol:] == eol):
					if (self.debug > 1):
						print "Readline: EOL occured";
					break
				if ((size is not None) and (len(line) >= size)):
					if (self.debug > 0):
						utils.print_err("Readline: Length exceeds max!")
					break
			else:
				if (self.debug > 0):
					utils.print_err("Readline: Timeout!")
				break
		return bytes(line)

	def getpos(self):
		""" Read and decode current position (after position request or 
		end of movement) """
		if (self.emulate):
			return self.fakepos
		ans = self.myreadline(size=255, eol="\r")
		#strs = re.findall('OK(\d+\.\d+) ([-+]?\d+.\d+)', ans)
		strs = self.okpos.findall(ans)
		if (self.debug > 1):
			print "Radant: answer found: ", strs
		if ((len(strs) < 1) or (len(strs[-1]) < 2)):
			return None
		# Return the last found pair of numbers
		return [float(strs[-1][0]), float(strs[-1][1])]

	def reqpos(self):
		""" Request current position """
		if (self.emulate):
			return self.fakepos
		self.port.write("Y\r")
		return self.getpos()

	def setpos(self, az=0, el=0):
		""" Send new position """
		if (self.emulate):
			return True
		while (az < 0):
			az += 360
		while (az > 360):
			az -= 360
		cmd = "Q{:.2f} {:.2f}\r".format(az, el)
		if (self.debug > 0):
			print(cmd)
		self.port.write(cmd)
		return True

	def ackwait(self):
		""" Waiting for ACK. Controller often works strangely on this 
		operation (i.e. sends unprintable characters or does not send 
		line terminator, so simple myreadline() is not robust enough """
		if (self.emulate):
			return True
		ans = ''
		while (1):
			time.sleep(0.01)
			c = self.port.read(1)
			if c:
				ans = ans + c
			else:
				return None
			if (self.debug > 1):
				print "Radant: ans = '" + ans + "'"
			#if (self.ack.search(ans)):
			if ('ACK' in ans):
				return True
			#if (self.err.search(ans)):
			if ('ERR' in ans):
				if (self.debug > 0):
					utils.print_err("Radant: Some error occured")
				return False

	def gotopos_nowait(self, az=180, el=0):
		""" Set new position and wait for ACK, but don't wait for end
		of movement """
		if (self.emulate):
			return True
		self.setpos(az, el)
		return self.ackwait()

	def gotopos(self, az=180, el=0):
		""" Set new position and wait for end of movement """
		if (self.emulate):
			return self.fakepos
		res = self.gotopos_nowait(az, el)
		if (not res):
			return res
		while True:
			time.sleep(0.1)
			pos = self.getpos()
			if (pos):
				return pos

	def stop(self):
		""" Stop movement """
		if (self.emulate):
			return True
		self.port.write("S\r")
		return True

	def setspeed(self, azs=5, els=5):
		""" Send angle speeds. AZV-3 only. !!!NOT TESTED!!! """
		if (self.emulate):
			return True
		if (not (speedlim[0] <= azs <= speedlim[1])):
			utils.print_err("Azimutail angle speed is out of limits");
			return False
		if (not (speedlim[0] <= els <= speedlim[1])):
			utils.print_err("Elevation angle speed is out of limits");
			return False
		cmd = "X{:.1f} {:.1f}\r".format(azs, els)
		if (self.debug > 0):
			print(cmd)
		self.port.write(cmd)
		return self.ackwait()
