#!/usr/bin/env python2
# Class for reading signal level from Ubiquiti Rocket M5 via SNMP (Net-SNMP).
# Note that specific OID may depend on device model and firmware version.

import netsnmp
import time
import utils

def snmpsignet(comm='public', host='192.168.1.26', oid='1.3.6.1.4.1.14988.1.1.1.1.1.4.5', \
		waitpre=0, waitbtw=0.1, nprobes=3, timeout=1, retries=0):

	sigval = [None] * nprobes
	var = netsnmp.Varbind('.' + oid)

	time.sleep(waitpre)
	for it in range(0, nprobes):
		try:
			res = netsnmp.snmpget(var, Version = 1, DestHost = host, 
					Community = comm, Timeout=int(timeout*1000000),
					Retries = retries)
			sigval[it] = int(var.val)
		except:
			sigval[it] = None
		time.sleep(waitbtw)
	return (utils.median(sigval))
