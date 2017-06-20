#!/usr/bin/env python2
# Some handy utils.

import math
import sys
import time

deg2rad = math.pi/180
rad2deg = 180/math.pi

def sign2w(x):
	""" Decode signed 2-byte integer from unsigned int """
	if x >= 32768:
		x ^= 65535
		x += 1
		x *=-1
	return x

def sign3w(x):
	""" Decode signed 3-byte integer from unsigned int """
	if x >= 8388608:        # 2**23
		x ^= 16777215   # 2**24 -1
		x += 1
		x *=-1
	return x

def data1(h, l):
	""" Decode 12-bit signed value from two bytes """
	return sign2w(((h << 8) | l)) >> 4

def data2(h, l):
	""" Decode 16-bit signed value from two bytes """
	return sign2w((h << 8) | l)

def data3(h, l, xl):
	""" Decode 24-bit signed value from three bytes """
	return sign3w((h << 16) | (l << 8) | xl)

def normalize(v):
	""" Normalize vector by it Euclidean norm """
	norm = math.sqrt(sum(map(lambda x: x**2, v)))
	if (norm == 0):
		return v
	return map(lambda x: x/norm, v)

def mynormalize(v, vmin, vmax):
	""" Normalization of accelerometer and magnetometer data """
	f = lambda x, xmin, xmax: 2*(float(x) - xmin)/(xmax - xmin) - 1
	return map(f, v, vmin, vmax)

def dot(a, b):
	""" Scalar product of real-valued vectors """
	return sum(map(lambda x, y: x*y, a, b))

def cross(a, b):
	""" Vector product of real-valued vectors """
	return [a[1]*b[2] - a[2]*b[1], a[2]*b[0] - a[0]*b[2], a[0]*b[1] - a[1]*b[0]]

def realroot3(x):
	""" Real 3-rd degree root of a real number """
	return math.copysign(abs(x)**(1/3.0), x)

def sinc(x):
	""" Incomplete sine """
	if (x == 0):
		return 1
	else:
		pix = math.pi*x
		return (math.sin(pix)/pix)

def median(lst):
	""" Median value of the list """
	lst = sorted([x for x in lst if x is not None])
	if (len(lst) < 1):
		return None
	if ((len(lst) % 2) == 1):
		return lst[((len(lst)+1)/2)-1]
	else:
		return float(sum(lst[(len(lst)/2)-1:(len(lst)/2)+1]))/2.0

def cls():
	""" Clear terminal """
	sys.stderr.write("\x1b[2J\x1b[H")

def print_err(*args):
	""" Write message(s) to stderr """
	sys.stderr.write(' '.join(map(str, args)) + '\n')

def print_tm(*args):
	""" Write message(s) to stdout with timestamp """
	print("[ {0:16.5f} ]".format(time.time()) + ' '.join(map(str, args)))
