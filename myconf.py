#!/usr/bin/env python2
# Own config parser based on ConfigParser. Defines default values.

import ConfigParser
import utils
import time

confn = "main.ini"
#confn = "test.ini"
#caln = "calib_data.txt"
#ttyn = "/dev/ttyUSB0"
#mainpos = (180, 0)
#addr = ('192.168.1.29', 12345)
#az_step = 0.5
#el_step = 0.5

# Earth radius in km
#eR = 6367.45*1000 # Mean equator/polar
eR = 6371.0*1000 # FAI sphere
eR2 = eR**2

# Yes, this is subject to configuration too (debug-time only)
def small_wait():
	time.sleep(0.01)

class MyConf:
	defaults = {'Heading': 
			{'Head': 180, '_Head': 'f',
			'Decline': 10.67, '_Decline': 'f',
			'StaticError': 13, '_StaticError': 'f',
			'WaitPre': 1, '_WaitPre': 'f',
			'WaitBtw': 1, '_WaitBtw': 'f',
			'WaitCal': 0.5, '_WaitCal': 'f',
			'NProbes': 3, '_NProbes': 'd',
			'NCycles': 2, '_NCycles': 'd'},
		'Radant': 
			{'Dev': '/dev/ttyUSB0',
			'Timeout': 10, '_Timeout': 'f',
			'MainAZ': 180, '_MainAZ': 'f',
			'MainEL': 0, '_MainEL': 'f',
			'DiscAZ': 0.5, '_DiscAZ': 'f',
			'DiscEL': 0.5, '_DiscEL': 'f',
			'ELBase': 0, '_ELBase': 'f',
			'Emulate': True, '_Emulate': 'b'},
		'GPS':
			{'Lat': 60.750759, '_Lat': 'f',
			'Lon': 30.048471, '_Lon': 'f',
			'Alt': 1, '_Alt': 'f',
			'WaitPre': 30, '_WaitPre': 'f',
			'WaitBtw': 15, '_WaitBtw': 'f',
			'NProbes': 5, '_NProbes': 'd',
			'Timeout': 10, '_Timeout': 'f',
			'WaitMax': 120, '_WaitMax': 'f'},
		'SNMP':
			{'Comm': 'public',
			'Host': '192.168.1.20',
			'OID': '1.3.6.1.4.1.14988.1.1.1.1.1.4.5',
			'WaitPre': 0, '_WaitPre': 'f',
			'WaitBtw': 0.1, '_WaitBtw': 'f',
			'NProbes': 3, '_NProbes': 'd',
			'Timeout': 1, '_Timeout': 'f',
			'Retries': 0, '_Retries': 'd'},
		'Net':
			{'Addr': '10.129.0.140',
			'Port': 12345, '_Port': 'd'},
		'Search':
			{'NPoints': 4, '_NPoints': 'd',
			'AZRad': 3, '_AZRad': 3,
			'ELRad': 3, '_ELRad': 3,
			'Delta': 3, '_Delta': 3,
			'Thres': -30, '_Thres': -30,
			'AZStep': 1, '_AZStep': 1,
			'ELStep': 1, '_ELStep': 1,
			'PhiStep': 30, '_PhiStep': 30,},
		'Log':
			{'File': 'main.log',
			'Period': 5, '_Period': 'f'},
		'HTTP':
			{'Addr': '127.0.0.1',
			'Port': 8000, '_Port': 'd'},
	}
	def __init__(self, configfn=confn):
		self.name = configfn
		self.conf = ConfigParser.ConfigParser()
		self.conf.optionxform = str
		self.val = self.defaults
		self.update()
	def update(self):
		self.conf.read(self.name)
		for it in self.conf.sections():
			if (not (it in self.val)):
				self.val[it] = {}
			for jt in self.conf.options(it):
				try:
					ujt = '_'+jt;
					if (ujt in self.val[it]): # Type of value
						if (self.val[it][ujt] == 'd'): # Integer
							tmp = self.conf.getint(it, jt)
						elif (self.val[it][ujt] == 'f'): # Float
							tmp = self.conf.getfloat(it, jt)
						elif (self.val[it][ujt] == 'b'): # Boolean
							tmp = self.conf.getboolean(it, jt)
						else: # Unkown type casts to string
							tmp = self.conf.get(it, jt)
					else: # Default type is string
						tmp = self.conf.get(it, jt)
					self.val[it][jt] = tmp
				except:
					utils.print_err(('ERROR while reading parameter {0:s} in section {1:s} (file {2:s})').\
							format(jt, it, self.name))
		self.val['Heading']['TrueHead'] = self.val['Heading']['Head'] + self.val['Heading']['Decline'] + \
				self.val['Heading']['StaticError']
		self.val['Radant']['AZBase'] = self.val['Radant']['MainAZ'] - self.val['Heading']['TrueHead']
		print "Config file {0:s} (re)loaded".format(self.name)
	def print_runtime(self):
		print "Mag heading is {0:0.2f} deg, decline is {1:0.2f} deg, static error is {2:0.2f} deg.".\
			format(self.val['Heading']['Head'], self.val['Heading']['Decline'], self.val['Heading']['StaticError'])
		print "True heading is {0:0.2f} deg, base pos is {1:0.2f} deg, azimuth calibirated on {2:0.2f} deg.".\
			format(self.val['Heading']['TrueHead'], self.val['Radant']['MainAZ'], self.val['Radant']['AZBase'])
		if (self.val['Radant']['ELBase']):
			print "Elevation calibrated at {0:0.2f} deg.".format(self.val['Radant']['ELBase'])
		print "Our latitude is {0:0.5f} deg, longtitude is {1:0.5f} deg, altitude is {2:0.2f} m.".\
			format(self.val['GPS']['Lat'], self.val['GPS']['Lon'], self.val['GPS']['Alt'])
		print "Getting signal level from {0:s} (OID {1:s}, N = {2:0d}).".\
			format(self.val['SNMP']['Host'], self.val['SNMP']['OID'], self.val['SNMP']['NProbes'])
	def dump(self):
		for it in self.val.keys():
			if (not self.conf.has_section(it)):
				self.conf.add_section(it)
			for jt in self.val[it].keys():
				if ((len(jt) < 1) or (jt[0] == "_")):
					continue
				self.conf.set(it, jt, self.val[it][jt])
		conffd = open(self.name, 'w')
		self.conf.write(conffd)
		conffd.close()
		print "Config file {0:s} modified".format(self.name)

# Ok, let's test it
#conf = MyConf()
#print(conf.val)
#conf.val['Heading']['Head'] = round(conf.val['Heading']['Head'])
#conf.dump()
