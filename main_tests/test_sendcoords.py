#!/usr/bin/env python2

import socket
import utils
import math
import json
import time

addr = ('127.0.0.1', 12345)

N = 8 
p0 = {'lat':60.75052, 'lon':30.050325, 'alt': 1}
r_step = 0.01
phi_step = 2*math.pi/N
alt_step = -50

lat2lon = 110.574/111.32/math.cos(p0['lat']*utils.deg2rad)
r = 0
phi = math.pi/2
alt = 1000

sk = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
for it in range(0, N+1):
	coords = {'lat': (p0['lat'] + r*math.sin(phi)),
		'lon': (p0['lon'] + r*lat2lon*math.cos(phi)),
		'alt': alt}
	#print "phi = ", (90 - phi/math.pi*180)
	print "phi = ", (90 - math.atan2(coords['lat'] - p0['lat'], \
		coords['lon'] - p0['lon'])*utils.rad2deg)
	print coords
	msg = json.dumps(coords) + '\n'
	sk.sendto(msg, addr)
	r += r_step
	phi += phi_step
	alt += alt_step
	time.sleep(2)
sk.close()
