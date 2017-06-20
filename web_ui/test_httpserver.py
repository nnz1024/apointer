#!/usr/bin/env python2

import signal
import sys
import threading
import time
import json
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer

print "Ok, let's begin."
debug = 0

#class GlobalState:
#	az = 0
#	el = 0
#	sig = 0
#	#def __init__(self):
#	#	pass


class HttpProcessor(BaseHTTPRequestHandler):
	def do_GET(self):
		self.send_response(200)
		self.send_header('Content-Type', 'text/json')
		self.end_headers()
		#self.wfile.write('{{"az":{0:0.2f},"el":{1:0.2f},"sig":{2:0.1f}}}'.\
		#		format(gs.az, gs.el, gs.sig))
		self.wfile.write(json.dumps(gs))
	def log_message(self, frmt, *args):
		if (debug > 0):
			BaseHTTPRequestHandler.log_message(self, frmt, *args)

class ServeHTTP(threading.Thread):
	def __init__(self, port):
		threading.Thread.__init__(self)
		#self.stop_cycle = threading.Event()
		self.serv = HTTPServer(("127.0.0.1", port), HttpProcessor)
		print "Serving requests on port {0:0d}/tcp.".format(port)
	def run(self):
		self.serv.serve_forever()
		print "Server stopped."
		#while (not self.stop_cycle.is_set()):
		#	self.serv.handle_request()

#gs = GlobalState()
gs = {'az':0, 'el':0, 'sig':0}
http_thr = ServeHTTP(8000)
http_thr.serv.gs = gs

def get_interrupt(sig, frame):
	print "\nStopping the web server..."
	#http_thr.stop_cycle.set()
	http_thr.serv.shutdown()
	print "Waiting for the server thread..."
	http_thr.join()
	print "Done."
	sys.exit(0)

signal.signal(signal.SIGINT, get_interrupt)

http_thr.start()
it = 0
while True:
	it = (it + 1) % 90
	gs['az'] = it*4
	gs['el'] = 90 - it
	gs['sig'] = -it
	time.sleep(0.5)
