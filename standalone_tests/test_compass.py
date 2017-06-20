#!/usr/bin/env python2

import smbus
import time
import signal
import sys
#import numpy as np
import math

ADDR_ACC = 0x19
ADDR_MAG = 0x1e

CTRL_REG1_A = 0x20
CTRL_REG4_A = 0x23

MR_REG_M = 0x02
CRA_REG_M = 0x00
CRB_REG_M = 0x01

OUT_X_L_A = 0x28
OUT_X_H_A = 0x29
OUT_Y_L_A = 0x2A
OUT_Y_H_A = 0x2B
OUT_Z_L_A = 0x2C
OUT_Z_H_A = 0x2D

OUT_X_H_M = 0x03
OUT_X_L_M = 0x04
OUT_Z_H_M = 0x05
OUT_Z_L_M = 0x06
OUT_Y_H_M = 0x07
OUT_Y_L_M = 0x08

TEMP_OUT_H_M = 0x31
TEMP_OUT_L_M = 0x32

def proc_sign2w(x):
	if (x >= 32768):
		x ^= 65535
		x += 1
		x *= -1
	return x

def proc_data1(h, l):
	return proc_sign2w(((h << 8) | l)) >> 4

def proc_data2(h, l):
	return proc_sign2w((h << 8) | l)

def get_acc():
	xh = bus.read_byte_data(ADDR_ACC, OUT_X_H_A)
	xl = bus.read_byte_data(ADDR_ACC, OUT_X_L_A)
	yh = bus.read_byte_data(ADDR_ACC, OUT_Y_H_A)
	yl = bus.read_byte_data(ADDR_ACC, OUT_Y_L_A)
	zh = bus.read_byte_data(ADDR_ACC, OUT_Z_H_A)
	zl = bus.read_byte_data(ADDR_ACC, OUT_Z_L_A)
	res = [proc_data1(xh, xl), proc_data1(yh, yl), proc_data1(zh, zl)]
	global maxacc, minacc
	maxacc = map(max, res, maxacc)
	minacc = map(min, res, minacc)
	return res

def get_mag():
	xh = bus.read_byte_data(ADDR_MAG, OUT_X_H_M)
	xl = bus.read_byte_data(ADDR_MAG, OUT_X_L_M)
	yh = bus.read_byte_data(ADDR_MAG, OUT_Y_H_M)
	yl = bus.read_byte_data(ADDR_MAG, OUT_Y_L_M)
	zh = bus.read_byte_data(ADDR_MAG, OUT_Z_H_M)
	zl = bus.read_byte_data(ADDR_MAG, OUT_Z_L_M)
	res = [proc_data2(xh, xl), proc_data2(yh, yl), proc_data2(zh, zl)]
	global maxmag, minmag
	maxmag = map(max, res, maxmag)
	minmag = map(min, res, minmag)
	return res

def get_temp():
	th = bus.read_byte_data(ADDR_MAG, TEMP_OUT_H_M)
	tl = bus.read_byte_data(ADDR_MAG, TEMP_OUT_L_M)
	return (float(proc_data1(th, tl))/8 + 16)

def print_err(*args):
	sys.stderr.write(' '.join(map(str,args)) + '\n')

def normalize(v):
	norm = math.sqrt(sum(map(lambda x: x**2, v)))
	#norm_ = np.linalg.norm(v)
	#print_err("TEST: ", norm - norm_)
	if (norm == 0): 
		return v
	res = map(lambda x: x/norm, v)
	#print_err("TEST: ", res - v/norm_)
	return res

def cross(a, b):
	return [a[1]*b[2] - a[2]*b[1], a[2]*b[0] - a[0]*b[2], a[0]*b[1] - a[1]*b[0]]

def dot(a, b):
	return sum(map(lambda x, y: x*y, a, b))

def mynormalize(v, vmin, vmax):
	f = lambda x, xmin, xmax: 2*(float(x) - xmin)/(xmax - xmin) - 1
	return map(f, v, vmin, vmax)

def recv_intr(rec_signal, frame):
	signal.signal(signal.SIGINT, signal.SIG_IGN)
	global maxacc, minacc, maxmag, minmag
	print_err("Get interrupt! Calibration data:")
	print_err("MIN ACC: ", minacc, " MIN MAG: ", minmag)
	print_err("MAX ACC: ", maxacc, " MAX MAG: ", maxmag)
	df = open('calib_data.txt', 'a')
	df.seek(0, 2)
	df.write("{0:5d} {1:5d} {2:5d} {3:5d} {4:5d} {5:5d} {6:5d} {7:5d} {8:5d} {9:5d} {10:5d} {11:5d}\n"
			.format(minmag[0], minmag[1], minmag[2], maxmag[0], maxmag[1], maxmag[2],
			minacc[0], minacc[1], minacc[2], maxacc[0], maxacc[1], maxacc[2]))
	df.close()
	nacc = normalize(get_acc())
	nmag = mynormalize(get_mag(), minmag, maxmag)
	east = normalize(cross(nmag, nacc))
	north = cross(nacc, east)
	axis = [1, 0, 0]
	#print_err("TEST: ", cross(nmag, nacc) - np.cross(nmag, nacc))
	#print_err("TEST: ", north - np.cross(nacc, east))
	#print_err("TEST: ", dot(east, axis) - np.dot(east, axis))
	#print_err("TEST: ", dot(north, axis) - np.dot(north, axis))
	heading = round(math.atan2(dot(east, axis), dot(north, axis)) * 180 / math.pi);
	if (heading < 0):
		heading += 360
	print_err("Normalized ACC: ", nacc, " Normalized MAG: ", nmag, " heading ", heading)
	sys.exit(0)

bus = smbus.SMBus(1)

bus.write_byte_data(ADDR_ACC, CTRL_REG1_A, 0b00100111)
bus.write_byte_data(ADDR_ACC, CTRL_REG4_A, 0b00001000) # !BLE!

bus.write_byte_data(ADDR_MAG, MR_REG_M,  0b00000000)
bus.write_byte_data(ADDR_MAG, CRA_REG_M, 0b10010000)
bus.write_byte_data(ADDR_MAG, CRB_REG_M, 0b01100000)

signal.signal(signal.SIGINT, recv_intr)

maxacc = [0, 0, 0]
minacc = maxacc
maxmag = maxacc
minmag = maxacc

print_err("Ready.")

while True:
	print "ACCEL: ", get_acc(), " MAGN: ", get_mag(), " TEMP: ", get_temp()
	time.sleep(0.05)
