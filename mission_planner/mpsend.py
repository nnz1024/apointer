# -*- coding: cp1251 -*-

import sys
#sys.path.append(r"c:\Python27\Lib\site-packages")
sys.path.append(r"c:\\Python27\\Lib\\")
import socket
import json

addr = ("192.168.1.29", 12345)
debug = 0

sk = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
print "Transmitting data..."
try:
	while True:
                msg = {'lat':float(cs.lat), \
                       'lon':float(cs.lng), \
                       'alt':float(cs.alt)}
                if (debug > 0):
                        print msg
                msgj = json.dumps(msg) + "\n"
                sk.sendto(msgj, addr)
                # If we don't have json module... it's ok
                #msgp = "{{\"lat\": {0:0.5f}, \"lon\": {1:0.5f}, \"alt\": {2:0.5f}}}\n".\
                #       format(float(cs.lat), float(cs.lng), float(cs.alt))
                #if (debug > 0):
                #        print msgp
                #sk.send(msgp)
                Script.Sleep(500)
finally:
        sk.close()
        print "Done!"
