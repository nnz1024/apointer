#!/usr/bin/env python2

from pysnmp.entity.rfc3413.oneliner import cmdgen
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
		waitpre = conf.getfloat('SNMP', 'WaitPre')
	if (conf.has_option('SNMP', 'WaitBtw')):
		waitbtw = conf.getfloat('SNMP', 'WaitBtw')
	if (conf.has_option('SNMP', 'NProbes')):
		nprobes = conf.getint('SNMP', 'NProbes')
	if (conf.has_option('SNMP', 'Timeout')):
		timeout = conf.getfloat('SNMP', 'Timeout')
	if (conf.has_option('SNMP', 'Retries')):
		retries = conf.getint('SNMP', 'Retries')

cmdGen = cmdgen.CommandGenerator()

sigval = [None] * nprobes

print "Ready"

while True:
	time.sleep(waitpre)
	for it in range(0, nprobes):
		errorIndication, errorStatus, errorIndex, varBinds = cmdGen.getCmd(\
				cmdgen.CommunityData(comm, mpModel=0),
				cmdgen.UdpTransportTarget((host, 161), 
					timeout=timeout, retries=retries),
				oid)
		if (errorIndication):
			utils.print_err("ERROR: SNMP: ", errorIndication)
			sigval[it] = None
		else:
			if (errorStatus):
				utils.print_err("ERROR: SNMP: {0:s} at {1:s}".format(\
						errorStatus.prettyPrint(),
						errorIndex and varBinds[int(errorIndex)-1] or '?'))
				sigval[it] = None
			else:
				sigval[it] = int(varBinds[0][1])
			if (debug > 0):
				print "RESULT:", sigval[it] 
		time.sleep(waitbtw)
	#break
	utils.cls()
	print "SIGNAL: ", utils.median(sigval)
