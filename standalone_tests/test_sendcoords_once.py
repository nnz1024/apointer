#!/usr/bin/env python2

import socket
import json

addr = ('127.0.0.1', 12345)

# Lat = 60.750759, Lon = 30.048471, Alt = 150
#coords = {'lat':60.75, 'lon':30.048471, 'alt':200}
#coords = {'lat':60.750759, 'lon':30.0, 'alt':200}
coords = {'lat':60.8, 'lon':30.0, 'alt':4000}
#coords2 = {'lat':60.9, 'lon':30.1, 'alt':3500}

msg = json.dumps(coords) + '\n'
#msg2 = json.dumps(coords2) + '\n'

#sk = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sk = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#sk.connect(addr)
sk.sendto(msg, addr)
#sk.send(msg2)
#sk.send(msg)
sk.close()
