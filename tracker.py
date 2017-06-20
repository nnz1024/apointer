#!/usr/bin/env python2
# Main app which tracks target via GPS telemetry data from Mission Planner 
# (see mission_planner/mpsend.py) and controls antenna position via Radant
# AZV-1. Also maintains a log, serves HTML5 UI and perhaps do some other things.

import time
import signal
import sys
import threading
import utils
import radant
import socket
import math
import json
import ubntsig
#import ConfigParser
import myconf
import nsock
import urlparse
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer

class GlobalState:
	def __init__(self):
		self.az = 0
		self.el = 0
		self.az_fix = 0
		self.el_fix = 0
		self.sig = -128
		self.lat = 0
		self.lon = 0
		self.alt = 0
		self.dist = 0
		self.debug = 2

class RadantGuide(threading.Thread):
	def __init__(self, gs, conf):
		threading.Thread.__init__(self)
		self.stop_cycle = threading.Event()
		self.renew_pos = threading.Event()
		self.gs = gs
		self.debug = gs.debug - 1
		self.paused = False
		self.finished = False
		try:
			self.rad = radant.Radant(conf['Dev'], conf['Timeout'], conf['Emulate'])
		except:
			utils.print_err("ERROR! Cannot open device {0:s}. Radant will be disabled.")
			self.finished = True
		else:
			self.rad.debug = self.debug - 1
			print "Control port {0:s} opened.".format(conf['Dev'])
	def gotopos(self, az, el):
		if (self.finished):
			return None
		res = self.rad.gotopos(az, el)
		if (res):
			gs.az_fix = res[0]
			gs.el_fix = res[1]
		return res
	def pause(self, paused=True):
		self.paused = paused
	def finish(self):
		if (self.finished):
			return None
		self.rad.finish()
		print "Control port closed."
		self.finished = True
	def run(self):
		while (not (self.stop_cycle.is_set() or self.finished)):
			if (self.renew_pos.is_set() and (not (self.paused))):
				if (self.debug > 0):
					print "New position: AZ = {0:8.5f}, EL = {1:8.5f}".\
						format(self.gs.az_fix, self.gs.el_fix)
				self.rad.stop()
				self.rad.gotopos_nowait(self.gs.az_fix, self.gs.el_fix)
				self.renew_pos.clear()
			#time.sleep(0.01)
			myconf.small_wait()
		self.finish()

class SigTracker(threading.Thread):
	def __init__(self, gs, conf):
		threading.Thread.__init__(self)
		self.stop_cycle = threading.Event()
		self.gs = gs
		self.debug = gs.debug - 1
		#print "Getting signal level from {0:s} (OID {1:s}, N = {2:0d}).".\
		#		format(conf['Host'], conf['OID'], conf['NProbes'])
		self.conf = conf
		self.paused = False
	def pause(self, paused=True):
		self.paused = paused
	def getsig(self):
		return ubntsig.snmpsignet(comm=self.conf['Comm'], \
				host=self.conf['Host'], oid=self.conf['OID'], \
				waitpre=self.conf['WaitPre']/2, waitbtw=self.conf['WaitBtw'], \
				nprobes=self.conf['NProbes'], timeout=self.conf['Timeout'], \
				retries=self.conf['Retries'])
	def run(self):
		while (not self.stop_cycle.is_set()):
			if (self.paused):
				myconf.small_wait()
				continue
			sig = self.getsig()
			if (sig is None):
				sig = -128
			gs.sig = sig
			if (self.debug > 1):
				print "Signal level is {0:3.1f} dBm".format(sig)

class Logger(threading.Thread):
	def __init__(self, gs, conf):
		threading.Thread.__init__(self)
		self.stop_cycle = threading.Event()
		self.gs = gs
		self.paused = False
		self.finished = False
		self.period = conf['Period']
		try:
			self.file = open(conf['File'], 'a')
			print "Logging into {0:s} with period {1:0.1f} sec.".\
					format(conf['File'], conf['Period'])
		except:
			utils.print_err('ERROR! Cannot open log file {0:s} for writing. '.format(conf['File']) + \
					'Logging will be disabled.')
			self.finished = True
	def pause(self, paused=True):
		self.paused = paused
	def log(self):
		if (self.finished):
			return None
		self.file.write("{0:5f},{1:0.3f},{2:0.3f},{3:0.3f},{4:0.2f},{5:0.2f},{6:0.4f},{7:0.1f}\r\n".\
			format(time.time(), self.gs.lon, self.gs.lat, self.gs.alt, self.gs.az, self.gs.el, \
			self.gs.dist, self.gs.sig))
		self.file.flush()
	def finish(self):
		if (self.finished):
			return None
		self.file.close()
		print "Log file closed."
		self.finished = True
	def run(self):
		while (not (self.stop_cycle.is_set() or self.finished)):
			if (self.paused):
				myconf.small_wait()
				continue
			# Waiting before writing, to partially eliminate 000-strings (starting) from log.
			# Wait with many control points, for fast react on stopping
			begin_wait = time.time()
			while ((not self.stop_cycle.is_set()) and ((time.time() - begin_wait) < self.period)):
				#time.sleep(0.01)
				myconf.small_wait()
			self.log()
		self.finish()

class HttpProcessor(BaseHTTPRequestHandler):
	def __init__(self, gs, conf, *args):
		self.gs = gs
		self.conf = conf
		self.debug = gs.debug
		BaseHTTPRequestHandler.__init__(self, *args)
	def do_GET(self):
		self.send_response(200)
		self.send_header('Content-Type', 'text/json')
		self.end_headers()
		parsed = urlparse.urlparse(self.path)
		if (parsed.path == '/tracker/state'):
			self.wfile.write(json.dumps(self.gs.__dict__))
		elif (parsed.path == '/tracker/config'):
			self.wfile.write(json.dumps(self.conf.val))
		elif (parsed.path == '/tracker/update'):
			self.conf.update()
			self.conf.print_runtime()
			self.wfile.write(json.dumps(self.conf.val))
		else:
			self.wfile.write(json.dumps({'ErrorUnknownPath': self.path}))
	def log_message(self, frmt, *args):
		if (self.debug > 0):
			BaseHTTPRequestHandler.log_message(self, frmt, *args)

class ServeHTTP(threading.Thread):
	def __init__(self, gs, conf):
		threading.Thread.__init__(self)
		http_processor = lambda *args: HttpProcessor(gs, conf, *args)
		self.serv = HTTPServer((conf.val['HTTP']['Addr'], conf.val['HTTP']['Port']), \
				http_processor)
		print "Serving requests on  {0:s}:{1:0d}/TCP".format(conf.val['HTTP']['Addr'], \
				conf.val['HTTP']['Port'])
		self.gs = gs
	def finish(self):
		self.serv.shutdown()
	def run(self):
		self.serv.serve_forever()
		print "HTTP server stopped."

def calculate_angles(gs, conf, resp):
	if ((not ('lat' in resp)) or \
			(not ('lon' in resp)) or \
			(not ('alt' in resp))):
		utils.print_err("WARNING! Response doesn't contain needed data.")
		return {}
	tg_lat = resp['lat']
	tg_lon = resp['lon']
	tg_alt = resp['alt']
	if ((tg_lat == 0) and (tg_lon == 0) and (tg_alt == 0)):
		utils.print_err('WARNING! Telemetry failure.')
		return {}
	if (gs.debug > 0):
		print "TARGET lat = {0:8.5f}, lon = {1:8.5f}, alt = {2:8.5f}".\
			format(tg_lat, tg_lon, tg_alt)
	lat1 = conf.val['GPS']['Lat']*utils.deg2rad
	lon1 = conf.val['GPS']['Lon']*utils.deg2rad
	lat2 = tg_lat*utils.deg2rad
	lon2 = tg_lon*utils.deg2rad
	#dalt = tg_alt - conf.val['GPS']['Alt']
	alt1 = myconf.eR + conf.val['GPS']['Alt']
	alt2 = myconf.eR + tg_alt
	dist_r = 2 * math.asin(math.sqrt(((math.sin((lat1 - lat2)/2))**2) + \
		(math.cos(lat1) * math.cos(lat2) * (math.sin((lon1 - lon2)/2))**2))) 
	dist_2d = dist_r * myconf.eR
	#dist_3d = math.sqrt(dalt**2 + dist_2d**2) 
	#alt_ofs = (math.sqrt(dist_2d**2 + myconf.eR2) - myconf.eR)
	dist_3d = math.sqrt(alt1**2 + alt2**2 - 2*alt1*alt2*math.cos(dist_r))
	if (gs.debug > 0):
		print "TARGET dist = {0:8.3f} ({1:8.3f}) km.".format(dist_3d/1000, dist_2d/1000) + \
			" Signal level is {0:3.1f} dBm.".format(gs.sig)
	az = -(math.atan2(math.sin(lon1 - lon2) * math.cos(lat2), \
		(math.cos(lat1) * math.sin(lat2)) - \
		(math.sin(lat1) * math.cos(lat2) * math.cos(lon1-lon2))))*utils.rad2deg
	#err2 = math.fmod(az2-az, 2*math.pi)
	#el = math.atan2(dalt - alt_ofs, dist_2d)*utils.rad2deg
	#el = math.acos((alt1**2 + dist_3d**2 - alt2**2)/(2*alt1*dist_3d))*utils.rad2deg - 90
	el = math.asin(-(alt1**2 + dist_3d**2 - alt2**2)/(2*alt1*dist_3d))*utils.rad2deg
	az_fix = conf.val['Radant']['AZBase'] + az
	el_fix = conf.val['Radant']['ELBase'] + el
	if (az_fix < 0):
		az_fix += 360
	if (gs.debug > 0):
		print "TARGET az = {0:6.2f} ({1:6.2f}), el = {2:6.2f} ({3:6.2f}).".\
			format(az, az_fix, el, el_fix)
	gs.lat = tg_lat
	gs.lon = tg_lon
	gs.alt = tg_alt
	gs.dist = dist_3d
	if (((math.fabs(az_fix - gs.az) < conf.val['Radant']['DiscAZ']) and \
			(math.fabs(el_fix - gs.el) < conf.val['Radant']['DiscEL']))):
		if (gs.debug > 1):
			print "Position changes are too small, do nothing!"
		return {}
	return {'az': az, 'az_fix': az_fix, 'el': el, 'el_fix': el_fix}

def calculate_angles_oldstyle(gs, conf, resp):
	if ((not ('lat' in resp)) or \
			(not ('lon' in resp)) or \
			(not ('alt' in resp))):
		utils.print_err("WARNING! Response doesn't contain needed data.")
		return {}
	tg_lat = resp['lat']
	tg_lon = resp['lon']
	tg_alt = resp['alt']
	if ((tg_lat == 0) and (tg_lon == 0) and (tg_alt == 0)):
		utils.print_err('WARNING! Telemetry failure.')
		return {}
	if (gs.debug > 0):
		print "TARGET lat = {0:8.5f}, lon = {1:8.5f}, alt = {2:8.5f}".\
			format(tg_lat, tg_lon, tg_alt)
	lat_dist_km = 110.574*(tg_lat - conf.val['GPS']['Lat'])
	lon_dist_km = (tg_lon - conf.val['GPS']['Lon']) * 111.320 * \
			math.cos(conf.val['GPS']['Lat']*utils.deg2rad)
	dist_km = math.sqrt(lat_dist_km**2 + lon_dist_km**2)
	dist_m = dist_km*1000
	alt_ofs = (math.sqrt(dist_m**2 + myconf.eR2) - myconf.eR)
	if (gs.debug > 0):
		print "Lat dist = {0:8.3f} km, Lon dist = {1:8.3f} km, Total dist = {2:8.3f} km.".\
				format(lat_dist_km, lon_dist_km, dist_km) + \
				" Altitude fix is {0:8.3f} m.".format(alt_ofs) + \
				" Signal level is {0:3.1f} dBm.".format(gs.sig)
	##az = 90 - math.atan2(lat_dist_km, lon_dist_km)*utils.rad2deg
	az = math.atan2(lon_dist_km, lat_dist_km)*utils.rad2deg
	#el = math.atan2((tg_alt - conf.val['GPS']['Alt']), dist_m)*utils.rad2deg
	el = math.atan2((tg_alt - conf.val['GPS']['Alt'] - alt_ofs), dist_m)*utils.rad2deg
	az_fix = conf.val['Radant']['AZBase'] + az
	el_fix = conf.val['Radant']['ELBase'] + el
	if (az_fix < 0):
		az_fix += 360
	if (gs.debug > 0):
		print "TARGET az = {0:6.2f} ({1:6.2f}), el = {2:6.2f} ({3:6.2f}).".\
			format(az, az_fix, el, el_fix)
	gs.lat = tg_lat
	gs.lon = tg_lon
	gs.alt = tg_alt
	gs.dist = dist_m
	if (((math.fabs(az_fix - gs.az) < conf.val['Radant']['DiscAZ']) and \
			(math.fabs(el_fix - gs.el) < conf.val['Radant']['DiscEL']))):
		if (gs.debug > 1):
			print "Position changes are too small, do nothing!"
		return {}
	return {'az': az, 'az_fix': az_fix, 'el': el, 'el_fix': el_fix}

conf = myconf.MyConf()
conf.print_runtime()

nsock = nsock.NSockUDP(conf.val['Net']['Addr'], conf.val['Net']['Port'])

print "Now listen on {0:s}:{1:0d}/UDP".format(conf.val['Net']['Addr'], conf.val['Net']['Port'])


gs = GlobalState()
gs.az_fix = conf.val['Radant']['MainAZ']
gs.az = conf.val['Radant']['AZBase']
gs.el_fix = conf.val['Radant']['MainEL'] 
gs.el = conf.val['Radant']['ELBase']

rad_thr = RadantGuide(gs, conf.val['Radant'])
rad_thr.start()

sig_thr = SigTracker(gs, conf.val['SNMP'])
sig_thr.start()

log_thr = Logger(gs, conf.val['Log'])
log_thr.start()

# Full conf because we must have public access to it
http_thr = ServeHTTP(gs, conf)
http_thr.start()

def get_usr1(sig, frame):
	""" We can update only run-time parameters, such as Radant.AZBase,
	but not an init ones, such as Radant.Dev, Net.Addr, Log.Name etc"""
	conf.update()
	conf.print_runtime()

# Not HUP, beasuse we are not a daemon (see signal(7))
signal.signal(signal.SIGUSR1, get_usr1)

def get_interrupt(sig, frame):
	print "\nFinishing..."
	sig_thr.stop_cycle.set()
	rad_thr.stop_cycle.set()
	log_thr.stop_cycle.set()
	http_thr.finish()
	nsock.finish()
	print "Socket closed."
	sig_thr.join()
	rad_thr.join()
	log_thr.join()
	sys.exit(0)

signal.signal(signal.SIGINT, get_interrupt)

#time.sleep(0.05)
myconf.small_wait()
print "Ready."

try:
	while True: # Main loop
		resp_raw = nsock.readline()
		try:
			resp = json.loads(resp_raw)
		except:
			utils.print_err("ERROR! Can't parse json: ", resp_raw)
			continue
		angles = calculate_angles(gs, conf, resp)
		if (angles):
			if (not rad_thr.renew_pos.is_set()):
				# Commit position changes
				gs.az_fix = angles['az_fix']
				gs.el_fix = angles['el_fix']
				gs.az = angles['az']
				gs.el = angles['el']
				rad_thr.renew_pos.set()
			elif (gs.debug > 1):
				print "Radant now already working, do nothing!"
finally:
	nsock.finish()
