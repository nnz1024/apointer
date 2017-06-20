#!/usr/bin/env python2

import time
import signal
import sys
import altimu
import utils

sens = altimu.Sensor()

def recv_intr(rec_signal, frame):
	#signal.signal(signal.SIGINT, signal.SIG_IGN)
	utils.print_err("Get interrupt! Calibration data:")
	sens.chkcal()
	utils.print_err("MIN ACC: ", sens.minacc, " MIN MAG: ", sens.minmag)
	utils.print_err("MAX ACC: ", sens.maxacc, " MAX MAG: ", sens.maxmag)
	utils.print_err("Normalized ACC: ", utils.normalize(sens.acc()), 
		" Normalized MAG: ", utils.mynormalize(sens.mag(), sens.minmag, sens.maxmag), 
		" Heading: ", sens.heading())
	sys.exit(0)

signal.signal(signal.SIGINT, recv_intr)

utils.print_err("Ready.")

while True:
	print "ACCEL: ", sens.acc(), " MAGN: ", sens.mag(), " TEMP2: ", sens.temp2(), \
		"PRESS: ", sens.press(), "TEMP: ", sens.temp()
	time.sleep(0.1)
