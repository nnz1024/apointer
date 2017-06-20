#!/usr/bin/env python2

import socket
import time
import json

addr = ('127.0.0.1', 12345)

coords = [{'lat':60.75, 'lon':30.048471, 'alt':200},
	{'lat':60.750759, 'lon':30.0, 'alt':200},
	{'lat':60.8, 'lon':30.0, 'alt':4000},
	{'lat':60.9, 'lon':30.1, 'alt':3500},
	{'lat':60.968, 'lon':30.305, 'alt':0}]


sk = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
for it in coords:
	msg = json.dumps(it) + '\n'
	sk.sendto(msg, addr)
	time.sleep(1)
sk.close()
