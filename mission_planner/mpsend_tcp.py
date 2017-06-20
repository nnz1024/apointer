# -*- coding: cp1251 -*-

import sys
#sys.path.append(r"c:\Python27\Lib\site-packages")
sys.path.append(r"c:\\Python27\\Lib\\")
import socket
import json

addr = ("192.168.1.29", 12345)
debug = 0

# Test connection
sk = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
print "Connectivity test..."
sk.connect(addr)
print "Ok"
sk.close()

print "Waiting for GPS..."
while (cs.lat == 0):
        Script.Sleep(1000)
print "Got GPS!"

# Now we got GPS, let's establish the main connection
sk = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sk.connect(addr)
print "Transmitting data..."
try:
        while (cs.lat != 0):
                msg = {'lat':float(cs.lat), \
                       'lon':float(cs.lng), \
                       'alt':float(cs.alt)}
                if (debug > 0):
                        print msg
                msgj = json.dumps(msg) + "\n"
                sk.send(msgj)
                #msgp = "{{\"lat\": {0:0.5f}, \"lon\": {1:0.5f}, \"alt\": {2:0.5f}}}\n".\
                #       format(float(cs.lat), float(cs.lng), float(cs.alt))
                #if (debug > 0):
                #        print msgp
                #sk.send(msgp)
                Script.Sleep(1000)
finally:
        sk.close()
        print "Done!"
