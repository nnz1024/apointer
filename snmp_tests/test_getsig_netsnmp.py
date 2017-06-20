#!/usr/bin/env python2

import netsnmp
import time
import utils
import ConfigParser
import myconf

debug = 0

# Old-style config parsing (don't use myconf methods and defaults)
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

sigval = [None] * nprobes
var = netsnmp.Varbind('.' + oid)
#sess = netsnmp.Session(Version = 1, DestHost=host,
#	Community=comm, Timeout=int(timeout*1000000), Retries=retries)

print "Ready"

while True:
	time.sleep(waitpre)
	for it in range(0, nprobes):
		try:
			res = netsnmp.snmpget(var, Version = 1, DestHost = host, 
					Community = comm, Timeout=int(timeout*1000000),
					Retries = retries)
			#res = sess.walk(var)
			sigval[it] = int(var.val)
			if (debug > 0):
				print "RESULT: ", sigval[it] 
		except:
			if (debug > 0):
				utils.print_err("ERROR: SNMP")
			sigval[it] = None
		time.sleep(waitbtw)
	#break
	utils.cls()
	print "SIGNAL: ", utils.median(sigval)
