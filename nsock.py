#!/usr/bin/env python2
# Working with datagram and stream sockets where messages separated by newline
# characters. Mostly for stream, but, ironically, stream support was abandoned.

import socket
import utils
import errno

class NSockUDP:
	def __init__(self, addr, port, fragsize=4096):
		self.sk = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		# Workaroung for "EBUSY" (don't need for UDP?)
		self.sk.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		self.sk.bind((addr, port))

		self.buf = ''
		self.debug = 2
		self.fragsize = fragsize
	
	def readline(self):
		eol = self.buf.find('\n')
		while (eol == -1):
			try:
				frag, addr = self.sk.recvfrom(self.fragsize)
			except socket.error, e:
				if (e.errno == errno.EINTR):
					# Got a signal while waiting data& Don't worry!
					continue
				else:
					raise
			if (not frag):
				continue
			self.buf += frag
			if (self.debug > 1):
				utils.print_tm("Get frag <{0:s}> from {1:s}:{2:0d} (buf = <{3:s}>).".\
					format(frag.rstrip(), addr[0], addr[1], self.buf.rstrip()))
			elif (self.debug > 0):
				utils.print_tm("Get new data from {0:s}:{1:0d}.".\
					format(addr[0], addr[1]))
			eol = self.buf.find('\n')
		eol += 1
		res = self.buf[:eol]
		self.buf = self.buf[eol:]
		return res

	def finish(self):
		self.sk.close()

""" !!!NOT TESTED!!! """
class NSockTCP:
	def __init__(self, addr, port):
		self.sk = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		# Workaroung for "EBUSY"
		self.sk.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		self.sk.bind((addr, port))
		sk.listen(1)

		self.buf = ''
		self.debug = 2
		self.conn = None

	def accept_conn(self):
		self.conn, self.addr = self.sk.accept()
		if (self.debug > 0):
			print "Get client connection from {0:s}:{1:0d}".\
					format(self.addr[0], self.addr[1])

	def close_conn(self):
		try:
			self.conn.close()
		except:
			pass
		self.conn = None

	def readline(self):
		if (not self.conn):
			#utils.print_err("WARNING! Attempt to read from TCP socket without connection.")
			return None
		self.eol = buf.find('\n')
		while (eol == -1):
			frag, addr = self.conn.recv(4096)
			if (not frag):
				# Now eol == -1
				break
			self.buf += frag
			if (self.debug > 1):
				print "Get frag <{0:s}> from {1:s}:{2:0d} (buf = <{3:s}>).".\
					format(frag.rstrip(), addr[0], addr[1], self.buf.rstrip())
			elif (self.debug > 0):
				print "Get new data from {0:s}:{1:0d}.".format(addr[0], addr[1])
			eol = self.buf.find('\n')
		if (eol == -1): # Connection closed
			self.close_conn()
			return None
		eol += 1
		res = self.buf[:eol]
		self.buf = self.buf[eol:]
		return res

	def finish(self):
		if (self.conn):
			self.close_conn()
		self.sk.close()
