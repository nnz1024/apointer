#!/usr/bin/env python2
# Tracking target by signal level, without GPS data.
# JUST PROTOTYPE, NOT FINISHED!

import ubntsig
import utils
import time
import math
import sys
import signal
import radant
import ConfigParser
import myconf

debug = 1

class Logger:
	def __init__(self, logfname):
		self.notwork = 0
		try:
			self.file = open(logfname, 'a')
			print "Logging into {0:s}.".format(logfname)
		except:
			self.notwork = 1
	def log(self, az, el, sig):
		if (not self.notwork):
			self.file.write("{0:5f},,,,{1:0.2f},{2:0.2f},,{3:0.1f}\r\n".\
				format(time.time(), az, el, sig))
			#self.file.flush()
	def finish(self):
		self.file.close()
		print "Log file closed."

conf = ConfigParser.ConfigParser()
conf.read(myconf.confn)

comm = 'public'
host = '192.168.1.26'
oid = '1.3.6.1.4.1.14988.1.1.1.1.1.4.5'
waitpre = 0
waitbtw = 0.1
nprobes = 3
timeout = 1
retries = 0

if ('SNMP' in conf.sections()):
	if (conf.has_option('SNMP', 'Comm')):
		comm = conf.get('SNMP', 'Comm')
	if (conf.has_option('SNMP', 'Host')):
		host = conf.get('SNMP', 'Host')
	if (conf.has_option('SNMP', 'OID')):
		oid = conf.get('SNMP', 'OID')
	if (conf.has_option('SNMP', 'WaitPre')):
		pass
		#waitpre = conf.getfloat('SNMP', 'WaitPre')
	if (conf.has_option('SNMP', 'WaitBtw')):
		pass
		#waitbtw = conf.getfloat('SNMP', 'WaitBtw')
	if (conf.has_option('SNMP', 'NProbes')):
		nprobes = conf.getint('SNMP', 'NProbes')
	if (conf.has_option('SNMP', 'Timeout')):
		timeout = conf.getfloat('SNMP', 'Timeout')
	if (conf.has_option('SNMP', 'Retries')):
		retries = conf.getint('SNMP', 'Retries')

npoints = 4
azrad = 3
elrad = 3
delta = 8
thres = -70
azstep = 1
elstep = 1
phistep = math.pi/6

if ('Search' in conf.sections()):
	if (conf.has_option('Search', 'npoints')):
		npoints = conf.getint('Search', 'npoints')
	if (conf.has_option('Search', 'azrad')):
		azrad = conf.getfloat('Search', 'azrad')
	if (conf.has_option('Search', 'elrad')):
		elrad = conf.getfloat('Search', 'elrad')
	if (conf.has_option('Search', 'delta')):
		delta = conf.getfloat('Search', 'delta')
	if (conf.has_option('Search', 'thres')):
		thres = conf.getfloat('Search', 'thres')
	if (conf.has_option('Search', 'azstep')):
		azstep = conf.getfloat('Search', 'azstep')
	if (conf.has_option('Search', 'elstep')):
		elstep = conf.getfloat('Search', 'elstep')
	if (conf.has_option('Search', 'phistep')):
		phistep = conf.getfloat('Search', 'phistep')
		phistep = math.pi*phistep/180

phic = 2*math.pi/npoints

ev = "/dev/ttyUSB0"
rad_timeout = 10
mainaz = 180
mainel = 0
if ('Radant' in conf.sections()):
	if (conf.has_option('Radant', 'Dev')):
		dev = conf.get('Radant', 'Dev')
	if (conf.has_option('Radant', 'Timeout')):
		rad_timeout = conf.getfloat('Radant', 'Timeout')
	if (conf.has_option('Radant', 'MainAZ')):
		mainaz = conf.getfloat('Radant', 'MainAZ')
	if (conf.has_option('Radant', 'MainEL')):
		mainel = conf.getfloat('Radant', 'MainEL')

logfname = 'main.log'
if ('Log' in conf.sections()):
	if (conf.has_option('Log', 'File')):
		logfname = conf.get('Log', 'File')

rad = True
#rad = radant.Radant(dev, rad_timeout)
#rad.debug = debug - 1
print "Control port {0:s} opened.".format(dev)

pos = [mainaz, mainel]
#pos = rad.reqpos()
pos = [280, 0]
if (pos):
	az = float(pos[0])
	el = float(pos[1])
	print "Current position is: AZ = {0:8.5f}, EL = {1:8.5f}".\
			format(az, el)
else:
	utils.print_err("ERROR: Radant hangs")
	sys.exit(1)

snmpsigf = lambda: ubntsig.snmpsignet(comm=comm, host=host, oid=oid, waitpre=waitpre, \
		waitbtw=waitbtw, nprobes=nprobes, timeout=timeout, \
		retries=retries)
sig = snmpsigf()
if (sig):
	print "Cirrent signal is {0:0.1f} dBm".format(snmpsigf())
else:
	print "WARNING: Start in dead zone"

logger = Logger(logfname)
logger.log(az, el, sig)

def finish(rad, excode):
	print "\nFinishing..."
	logger.finish()
	#rad.finish()
	print "Control port closed"
	sys.exit(excode)

def get_interrupt(sig, frame):
	finish(rad, 0)

signal.signal(signal.SIGINT, get_interrupt)

def rebase(rad, az, el):
	res = True
	if (debug > 0):
		print "Go to position: AZ = {0:5.3f}, EL = {1:5.3f}".\
				format(az, el)
	#res = rad.gotopos(az, el)
	if (res is None):
		# Timeout
		utils.print_err("ERROR: Radant hangs")
		finish(rad, 1)
	return res

def tgt_fun(rad, snmpsigf, az, el, logger):
	if (not rebase(rad, az, el)):
		return None
	sig = snmpsigf()
	logger.log(az, el, sig)
	return sig

def tgt_fun_emulate(rad, snmpsigf, az, el, logger):

	if ((el < 0) or (el > 90) or (az < 2) or (az > 358)):
		if (debug > 0):
			print "Prohibited position: AZ = {0:5.3f}, EL = {1:5.3f}".\
					format(az, el)
		return None

	x0 = 0.4
	y0 = -0.7
	sx = 1
	sy = 1
	sr = 0.2
	sres = 50

	theta = az*math.pi/180
	rho = (1 - el/90)*math.pi/2
	x = rho*math.cos(theta)
	y = rho*math.sin(theta)
	x1 = (x - x0)/sx
	y1 = (y - y0)/sy
	theta1 = math.atan2(y1, x1)
	rho1 = math.sqrt(x1**2 + y1**2)
	
	res = sres*(utils.sinc(rho1/sr) - 1)

	if (debug > 0):
		print "Pointing to AZ = {0:5.3f}, EL = {1:5.3f}, SIG = {2:5.3f}".\
				format(az, el, res)
	
	logger.log(az, el, res)

	return res

need_research = False

while True:
	oldsig = sig
	#sig = snmpsigf()
	sig = tgt_fun_emulate(rad, snmpsigf, az, el, logger)
	if ((sig < thres) or ((oldsig - sig) > delta) or need_research):
		if (debug > 0):
			print "Begin cycle search"
		need_research = False
		azs = [None] * npoints
		els = [None] * npoints
		sigs = [None] * npoints
		for it in range(0, npoints):
			phi = phic*it
			azs[it] = az + azrad*math.cos(phi)
			els[it] = el + elrad*math.sin(phi)
			sigs[it] = tgt_fun_emulate(rad, snmpsigf, \
					azs[it], els[it], logger) 
		maxsig = max(sigs)
		idx = sigs.index(maxsig)
		if (sig > maxsig):
			print "Found local max AZ = {0:5.3f}, EL = {1:5.3f}, SIG = {2:5.3f}".\
					format(az, el, sig)
			if (not rebase(rad, az, el)):
				utils.print_err("ERROR: Max in prohibited postion AZ = {0:5.3f}" +\
						", EL = {0:5.3f}, SIG = {2:5.3f}".format(az, el, \
						sig))
				finish(rad, 2)
		elif (len(set(sigs)) <= 1):
			print "WARNING: Stuck in dead zone"
		else:
			az = azs[idx]
			el = els[idx]
			if (not rebase(rad, az, el)):
				utils.print_err("ERROR: Max in prohibited postion AZ = {0:5.3f}" +\
						", EL = {0:5.3f}, SIG = {2:5.3f}".format(az, el, \
						sigs[idx]))
				finish(rad, 1)
			need_research = True
			continue
		if (sig > thres):
			continue
		az0 = az
		el0 = el
		cnt = 0
		need_research = True
		print "Trying helix search. azstep = {0:5.3f}, elstep = {1:5.3f}, phistep = {2:5.3f}".\
				format(azstep, elstep, phistep*180/math.pi)
		while (sig < thres):
			cnt += 1
			az_r = azstep*cnt
			el_r = elstep*cnt
			phi = phistep*cnt
			if (debug > 0):
				print "Next step: az_r = {0:5.3f}, el_r = {1:5.3f}, phi = {2:5.3f}".\
						format(az_r, el_r, phi*180/math.pi)
			az = az0 + az_r*math.cos(phi)
			el = el0 + el_r*math.sin(phi)
			if (el >= 90):
				print "WARNING: We reached top point. Stop and go home!"
				az = az0
				el = el0
				rebase(rad, az, el)
				finish(rad, 3)
			sig = tgt_fun_emulate(rad, snmpsigf, az, el, logger)
	time.sleep(1)
