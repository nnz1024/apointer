#!/usr/bin/env python2
# Class for working with Pololu AltIMU-10 module which includes LPS331AP digital
# barometer, L3GD20 3-axis gyroscope, and LSM303DLHC 3-axis 
# accelerometer/magnetometer via I2C/SMBus.
# (vendor site: https://www.pololu.com/)

# Used by prepare.py to determine magnetic heading.
# Using accelerometer to calibrate elevation was planned, but never implemented
# (however accelerometer support presents in this module and even tested).
# The same applies also to using barometer to determine altitude.
# Support for L3GD20 3-axis gyroscope WAS NOT IMPLEMENTED AT ALL.

import smbus
import math
import utils

class Sensor:
	# Bus addrs
	ADDR_ACC = 0x19
	ADDR_MAG = 0x1e
	ADDR_ALT = 0x5d
	# Acc ctrl regs
	CTRL_REG1_A = 0x20
	CTRL_REG4_A = 0x23
	# Mag ctrl regs
	MR_REG_M = 0x02
	CRA_REG_M = 0x00
	CRB_REG_M = 0x01
	# Acc out regs
	OUT_X_L_A = 0x28
	OUT_X_H_A = 0x29
	OUT_Y_L_A = 0x2A
	OUT_Y_H_A = 0x2B
	OUT_Z_L_A = 0x2C
	OUT_Z_H_A = 0x2D
	# Mag out regs
	OUT_X_H_M = 0x03
	OUT_X_L_M = 0x04
	OUT_Z_H_M = 0x05
	OUT_Z_L_M = 0x06
	OUT_Y_H_M = 0x07
	OUT_Y_L_M = 0x08
	# Temp out regs
	TEMP_OUT_H_M = 0x31
	TEMP_OUT_L_M = 0x32
	# Altimeter
	ALT_IDENT = 0xbb
	WHO_AM_I_ALT = 0x0f
	CTRL_REG1_ALT = 0x20
	OUT_P_XL_ALT = 0x28
	OUT_P_L_ALT = 0x29
	OUT_P_H_ALT = 0x2a
	OUT_T_L_ALT = 0x2b
	OUT_T_H_ALT = 0x2c
	# Calib data fname
	cfname = 'calib_data.txt'
	# Base axis
	axis = [1, 0, 0]
	debug = 1
	# Methods
	def __init__(self, port=1):
		self.bus = smbus.SMBus(port)
		# Init LSM303DLHC accelerometer
		self.bus.write_byte_data(self.ADDR_ACC, self.CTRL_REG1_A, 0b00100111)
		self.bus.write_byte_data(self.ADDR_ACC, self.CTRL_REG4_A, 0b00001000) # !BLE!
		# Init LSM303DLHC magnetometer
		self.bus.write_byte_data(self.ADDR_MAG, self.MR_REG_M,  0b00000000)
		self.bus.write_byte_data(self.ADDR_MAG, self.CRA_REG_M, 0b10010000)
		self.bus.write_byte_data(self.ADDR_MAG, self.CRB_REG_M, 0b01100000)
		# Init LPS331AP altimeter (barometer)
		if (self.bus.read_byte_data(self.ADDR_ALT, self.WHO_AM_I_ALT) != self.ALT_IDENT):
			utils.print_err("This isn't an LPS331AP altimeter!")
		else:
			self.bus.write_byte_data(self.ADDR_ALT, self.CTRL_REG1_ALT, 0b11100000)
		# Init internal vals
		self.maxacc  = self.minacc  = self.minmag  = self.maxmag  = [0, 0, 0]
		self.cmaxacc = self.cminacc = self.cminmag = self.cmaxmag = [0, 0, 0]
		self.calinit = 0

	def acc(self):
		""" Get accelerometer data from LSM303DLHC """
		xh = self.bus.read_byte_data(self.ADDR_ACC, self.OUT_X_H_A)
		xl = self.bus.read_byte_data(self.ADDR_ACC, self.OUT_X_L_A)
		yh = self.bus.read_byte_data(self.ADDR_ACC, self.OUT_Y_H_A)
		yl = self.bus.read_byte_data(self.ADDR_ACC, self.OUT_Y_L_A)
		zh = self.bus.read_byte_data(self.ADDR_ACC, self.OUT_Z_H_A)
		zl = self.bus.read_byte_data(self.ADDR_ACC, self.OUT_Z_L_A)
		res = [utils.data1(xh, xl), utils.data1(yh, yl), utils.data1(zh, zl)]
		self.cmaxacc = map(max, res, self.cmaxacc)
		self.cminacc = map(min, res, self.cminacc)
		return res

	def mag(self):
		""" Get magnetometer data from LSM303DLHC """
		xh = self.bus.read_byte_data(self.ADDR_MAG, self.OUT_X_H_M)
		xl = self.bus.read_byte_data(self.ADDR_MAG, self.OUT_X_L_M)
		yh = self.bus.read_byte_data(self.ADDR_MAG, self.OUT_Y_H_M)
		yl = self.bus.read_byte_data(self.ADDR_MAG, self.OUT_Y_L_M)
		zh = self.bus.read_byte_data(self.ADDR_MAG, self.OUT_Z_H_M)
		zl = self.bus.read_byte_data(self.ADDR_MAG, self.OUT_Z_L_M)
		res = [utils.data2(xh, xl), utils.data2(yh, yl), utils.data2(zh, zl)]
		self.cmaxmag = map(max, res, self.cmaxmag)
		self.cminmag = map(min, res, self.cminmag)
		return res

	def temp2(self):
		""" Get temperature from LSM303DLHC (very rough) """
		th = self.bus.read_byte_data(self.ADDR_MAG, self.TEMP_OUT_H_M)
		tl = self.bus.read_byte_data(self.ADDR_MAG, self.TEMP_OUT_L_M)
		return (float(utils.data1(th, tl))/8 + 16)
	
	def press(self):
		""" Get atmospheric pressure from LPS331AP """
		pxl = self.bus.read_byte_data(self.ADDR_ALT, self.OUT_P_XL_ALT)
		pl = self.bus.read_byte_data(self.ADDR_ALT, self.OUT_P_L_ALT)
		ph = self.bus.read_byte_data(self.ADDR_ALT, self.OUT_P_H_ALT)
		return float(utils.data3(ph, pl, pxl))/4096

	def temp(self):
		""" Get temperature from LPS331AP """
		tl = self.bus.read_byte_data(self.ADDR_ALT, self.OUT_T_L_ALT)
		th = self.bus.read_byte_data(self.ADDR_ALT, self.OUT_T_H_ALT)
		return (42.5 + (float(utils.data2(th, tl)) / 480))

	def heading(self):
		""" Determine magnetic heading (3D) """
		self.chkcal()
		nacc = utils.normalize(self.acc())
		nmag = utils.mynormalize(self.mag(), self.minmag, self.maxmag)
		east = utils.normalize(utils.cross(nmag, nacc))
		north = utils.cross(nacc, east)
		head = math.atan2(utils.dot(east, self.axis), utils.dot(north, self.axis)) * 180 / math.pi
		if (head < 0):
			head += 360
		if (self.debug > 0):
			print "Calibration data:"
			print "MIN ACC: ", self.minacc, " MIN MAG: ", self.minmag
			print "MAX ACC: ", self.maxacc, " MAX MAG: ", self.maxmag
			print "Normalized ACC: ", nacc, \
				" Normalized MAG: ", nmag, \
				"\nHeading: ", head
		return head
	
	def heading2d(self, zindex=3):
		""" Determine magnetic heading (2D) """
		self.chkcal()
		nacc = utils.normalize(self.acc())
		minmag = self.minmag
		minmag[zindex-1] = -65536
		maxmag = self.maxmag
		maxmag[zindex-1] = 65535
		nmag = utils.mynormalize(self.mag(), minmag, maxmag)
		east = utils.normalize(utils.cross(nmag, nacc))
		north = utils.cross(nacc, east)
		head = math.atan2(utils.dot(east, self.axis), utils.dot(north, self.axis)) * 180 / math.pi
		if (head < 0):
			head += 360
		if (self.debug > 0):
			print "Calibration data:"
			print "MIN ACC: ", self.minacc, " MIN MAG: ", minmag
			print "MAX ACC: ", self.maxacc, " MAX MAG: ", maxmag
			print "Normalized ACC: ", nacc, \
				" Normalized MAG: ", nmag, \
				"\nHeading: ", head
		return head

	def chkcal(self):
		if (self.calinit == 0):
			self.minmag = self.cminmag;
			self.maxmag = self.cmaxmag;
			self.minacc = self.cminacc;
			self.maxacc = self.cmaxacc;
			return True
		return False

	def writecal(self):
		df = open(self.cfname, 'a')
		#cdata = [self.minmag[0], self.minmag[1], self.minmag[2], self.maxmag[0], self.maxmag[1], self.maxmag[2],
		#	self.minacc[0], self.minacc[1], self.minacc[2], self.maxacc[0], self.maxacc[1], self.maxacc[2]];
		cdata = self.minmag[0:2] + self.maxmag[0:2] + self.minacc[0:2] + self.maxacc[0:2];
		df.write(" ".join(["{:+5d}".format(cdata[it]) for it in range(len(cdata))]))
		df.close()
		return True

	def readcal(self):
		df = open(self.cfname, 'r')
		for line in df:
			pass
		cdata = map(int, line.split(string.whitespace))
		self.minmag = cdata[0:2]
		self.maxmag = cdata[3:5]
		self.minacc = cdata[6:8]
		self.maxacc = cdata[9:11]
		self.calinit = 1

