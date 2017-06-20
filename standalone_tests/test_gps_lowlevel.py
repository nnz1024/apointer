#!/usr/bin/env python2

import socket
import json

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(("127.0.0.1", 2947))
vers = json.loads(s.recv(1024))
print vers
s.send('?WATCH={"enable":true}')
while True:
	rec_raw = s.recv(1024)
	if ("\n" in rec_raw):
		rec_raw = rec_raw.split("\n", 1)
	print "!!!"
	print rec_raw
	print "!!!"
	rec = json.loads(rec_raw[0])
	if (('class' in rec) and ((rec['class'] == 'WATCH') or (rec['class'] == 'DEVICES'))):
		break
s.send("?POLL;")
pol = json.loads(s.recv(1024))
s.close()
print pol
if (('fixes' in pol) and (len(pol['fixes']) > 0) and 
		('lat' in pol['fixes'][0]) and ('lon' in pol['fixes'][0])):
	print "lat = {0:8.5f}, lon = {1:8.5f}\n".format(pol['fixes'][0]['lat'],
			pol['fixes'][0]['lon'])
