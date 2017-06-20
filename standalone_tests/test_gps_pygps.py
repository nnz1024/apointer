#!/usr/bin/env python2

import gps

gs = gps.gps(mode=(gps.WATCH_ENABLE|gps.WATCH_NEWSTYLE))
while True:
	rep = gs.next()
	print rep
#	if ((rep['class'] == 'TPV') and
#			('fixes' in rep) and
#			(len(pol['fixes']) > 0) and
#			('lat' in rep['fixes'][0]) and 
#			('lon' in rep['fixes'][0])):
	if ((rep['class'] == 'TPV') and
			('lat' in rep) and 
			('lon' in rep)):
		print "lat = {0:8.5f}, lon = {1:8.5f}\n".\
				format(rep['lat'], \
				rep['lon'])
		break
gs.close()
