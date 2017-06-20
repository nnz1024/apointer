#!/usr/bin/env python2

import radant
import random
import math

rad = radant.Radant('/dev/ttyUSB0', 10)
n = 8
x0 = 180
y0 = 30
r = 10
for it in range(1, n+1):
	print 'Begin iter ' + str(it) + ': get pos'
	print rad.reqpos()
	#x = random.randrange(-2300, 33500, 1)/100.0
	#y = random.randrange(-2300, 11100, 1)/100.0
	#print 'Go to some random point: x = ' + str(x) + ', y = ' + str(y)
	phi = (2*math.pi*(it - 1))/n
	x = x0 + r*math.cos(phi)
	y = y0 + r*math.sin(phi)
	print 'Go to some circle point: x = ' + str(x) + ', y = ' + str(y) + ', phi = ' + str(phi)
	print rad.gotopos(x, y)
	print 'Check are we in some point'
	print rad.reqpos()

print rad.gotopos(180, 0)

rad.finish()
