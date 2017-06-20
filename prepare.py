#!/usr/bin/env python2
# Script to calibrate the installation (mainly the compass). It determines
# own GPS coordinates and magnetic north, and writes it to config.

# While one thread rotates the antenna and trying to calibrate compass,
# another one trying to get GPS coordinates.

import time
import signal
import sys
import threading
import altimu
import utils
import radant
import gps
import os
#import ConfigParser
import myconf

# Here in comments there is an implementation of old-style config parsing 
# (which don't use myconf methods and defaults), with config locking which
# prevents concurrent access.
# In actual implementation (via myconf) writing to config are done once 
# at finish, so we don't need a locking.

#conflock = threading.Lock()

# Old-style config implementation requires explicit call of ConfigParser...
#conf = ConfigParser.ConfigParser()
#conf.optionxform = str
#conf.read(myconf.confn)

# ... and explicit setting of defaults.
#dev = "/dev/ttyUSB0"
#rad_timeout = 10
#mainaz = 180
#mainel = 0
#if ('Radant' in conf.sections()):
#	if (conf.has_option('Radant', 'Dev')):
#		dev = conf.get('Radant', 'Dev')
#	if (conf.has_option('Radant', 'Timeout')):
#		rad_timeout = conf.getfloat('Radant', 'Timeout')
#	if (conf.has_option('Radant', 'MainAZ')):
#		mainaz = conf.getfloat('Radant', 'MainAZ')
#	if (conf.has_option('Radant', 'MainEL')):
#		mainel = conf.getfloat('Radant', 'MainEL')


debug = 2
conf = myconf.MyConf()

print("Ready.")

class SensWorking(threading.Thread):
	def __init__(self, conf, debug):
		threading.Thread.__init__(self)
		self.event = threading.Event()
		self.debug = debug - 1
		self.conf = conf
	def run(self):
		sens = altimu.Sensor()
		sens.debug = self.debug
		while (not self.event.is_set()):
			acc = sens.acc()
			mag = sens.mag()
			temp2 = sens.temp2()
			press = sens.press()
			temp = sens.temp()
			if (self.debug > 1):
				print "ACCEL: ", acc, " MAGN: ", mag, " TEMP2: ", temp2, \
					"PRESS: ", press, "TEMP: ", temp
			time.sleep(self.conf['WaitCal'])
		sens.chkcal()
		sens.writecal()
		cnt = 0
		head = 0
		time.sleep(self.conf['WaitPre'])
		while (cnt < self.conf['NProbes']):
			chead = sens.heading2d()
			head += chead
			cnt += 1
			if (self.debug > 0):
				print "2D heading is {0:6.2f} deg (point {1:0d} of {2:0d}).".\
					format(chead, cnt, self.conf['NProbes'])
			time.sleep(self.conf['WaitBtw'])
		#conf = ConfigParser.ConfigParser()
		#conflock.acquire()
		#if (self.debug > 1):
		#	print "Acquiring the lock..."
		#try:
		#	conf.read(confn)
		#	if (not ('Heading' in conf.sections())):
		#		conf.add_section('Heading')
		#	conf.set('Heading', 'Head', head)
		#	conffd = open(confn, 'w')
		#	conf.write(conffd)
		#	conffd.close()
		#finally:
		#	conflock.release()
		head /= float(cnt)
		self.conf['Head'] = round(head, 2)
		if (self.debug > 0):
			print "After all, heading = {0:6.2f} deg (by {1:0d} points).".\
				format(head, cnt)


class GPSWorking(threading.Thread):
	def __init__(self, conf, debug):
		threading.Thread.__init__(self)
		self.debug = debug
		self.conf = conf
	def run(self):
		cnt = 0
		lat = 0
		lon = 0
		#alt = 0
		maxcnt = self.conf['NProbes']
		time.sleep(self.conf['WaitPre'])
		gs = gps.gps(mode=(gps.WATCH_ENABLE|gps.WATCH_NEWSTYLE))
		try:
			gs.sock.settimeout(self.conf['Timeout'])
			starttime = time.time()
			# We need to pass the first iteration without pause
			waitstarttime = starttime - self.conf['WaitBtw']
			while (cnt < maxcnt):
				if ((time.time() - starttime) > self.conf['WaitMax']):
					#gs.close()
					#return None
					# Leaving lat, lon and cnt as is
					break
				if (self.debug > 1):
					print "Waiting for GPS... ({0:1d} of {1:1d})".\
						format(cnt, maxcnt)
				try:
					rep = gs.next()
				except:
					print "WARNING! GPS timeout on {0:0d} iteration.".\
						format(cnt + 1)
					# Just testing
					#rep = {'class':'TPV', 'lat':0, 'lon':0, 'alt':0}
					continue
				if (self.debug > 1):
					print "gpsd response: ", rep
				if ((time.time() - waitstarttime) < self.conf['WaitBtw']):
					if (self.debug > 1):
						print "We are waiting. Ignoring this response."
					continue
				if ((rep['class'] == 'TPV') and ('lat' in rep) \
						and ('lon' in rep)): # and ('alt' in rep))
					clat = float(rep['lat'])
					lat += clat
					clon = float(rep['lon'])
					lon += clon
					#calt = float(rep['alt'])
					#alt += calt
					cnt += 1
					if (self.debug > 0):
						print "GPS data: lat = {0:8.5f}, lon = {1:8.5f}".\
							format(clat, clon)
					#time.sleep(self.conf['WaitBtw'])
					waitstarttime = time.time()
		finally:
			gs.close()
		if (lat == 0):
			# No connection to satellites (timeout) :(
			# We are in screened area?!
			utils.print_err("ERROR! No GPS signal found.")
			return None
		lat /= float(cnt)
		lon /= float(cnt)
		#alt /= float(cnt)
		#conf = ConfigParser.ConfigParser()
		#if (self.debug > 1):
		#	print "Acquiring the lock..."
		#conflock.acquire()
		#try:
		#	conf.read(confn)
		#	if (not ('GPS' in conf.sections())):
		#		conf.add_section('GPS')
		#	conf.set('GPS', 'Lat', lat)
		#	conf.set('GPS', 'Lon', lon)
		#	#conf.set('GPS', 'Alt', alt)
		#	conffd = open(confn, 'w')
		#	conf.write(conffd)
		#	conffd.close()
		#finally:
		#	conflock.release()
		self.conf['Lat'] = round(lat, 6)
		self.conf['Lon'] = round(lon, 6)
		if (self.debug > 0):
			print "After all, lat = {0:8.5f}, lon = {1:8.5f} (by {2:0d} points).".\
				format(lat, lon, cnt)

sens_thr = SensWorking(conf.val['Heading'], debug)
gps_thr = GPSWorking(conf.val['GPS'], debug)

rconf = conf.val['Radant'] # Only short-hand
rad = radant.Radant(rconf['Dev'], rconf['Timeout'], rconf['Emulate'])
rad.debug = 0

N = conf.val['Heading']['NCycles']

sens_thr.start()
gps_thr.start()

print "Prepare to calibration: goto {0:0.0f}, {1:0.0f}".\
	format(rconf['MainAZ'], rconf['MainEL'])
print rad.gotopos(rconf['MainAZ'], rconf['MainEL'])
for it in range(1, N + 1):
	print "Begin calibration ({0:0d} of {1:0d}): goto 2,0".\
		format(it, N)
	print rad.gotopos(2, 0)
	print "Continue calibration ({0:0d} of {1:0d}): goto 359, 0".\
		format(it, N)
	print rad.gotopos(359, 0)
print "Finish calibration: goto {0:0.0f}, {1:0.0f}".\
	format(rconf['MainAZ'], rconf['MainEL'])
print rad.gotopos(rconf['MainAZ'], rconf['MainEL'])

rad.finish()

#time.sleep(1) # Moved to SensWorking.run()
sens_thr.event.set()

sens_thr.join()
gps_thr.join()

conf.dump()

# Don't need after gs.sock.settimeout()?
#if (gps_thr.isAlive()):
#	# Fucking GPS!
#	print "ERROR: GPS timeout. We need to kill ourselves"
#	os.kill(os.getpid(), signal.SIGKILL)	
