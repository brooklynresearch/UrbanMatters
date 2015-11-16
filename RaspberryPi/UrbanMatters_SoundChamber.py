#/user/bin/python

from OSC import OSCServer, OSCClient, OSCMessage
import threading
#import thread
import sys
import atexit
import time
from time import sleep
from dotstar import Adafruit_DotStar
from serial import Serial
import re

import socket
import fcntl
import struct

DEBUG = 1

OSCAddress = "/0"

# ip address finder
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
ifname = 'eth0'
localIP = socket.inet_ntoa(fcntl.ioctl(
        s.fileno(),
        0x8915,  # SIOCGIFADDR
        struct.pack('256s', ifname[:15])
    )[20:24])

clientAddress = '192.168.0.168', 9999
serverAddress = localIP, 9998

ser = Serial('/dev/ttyUSB0', 9600)

columnServer = OSCServer( serverAddress ) 
columnServer.timeout = 0
run = True

columnClient = OSCClient()
columnClient.connect(clientAddress)

totalPixels = 150		# Number of LEDs in Locker
pixel = 0

# Control Pins for the Raspberry Pi to the Dot Star strip
datapin   = 23
clockpin  = 24
# strip	  = Adafruit_DotStar(totalPixels, datapin, clockpin)
strip	  = Adafruit_DotStar(totalPixels, 100000)

strip.begin()		 # Initialize pins for output
strip.setBrightness(254) # Limit brightness to ~1/4 duty cycle

color = 0		 # Global Color Value
prevColor = 0


class ColumnOSCThread (threading.Thread):
	def __init__(self, threadID, name):
		threading.Thread.__init__(self)
		self.threadID = threadID
		self.name = name
	def run(self):
		print "Starting " + self.name
		godListener() 

class ColumnDisplayThread (threading.Thread):
	def __init__(self, threadID, name):
		threading.Thread.__init__(self)
		self.threadID = threadID
		self.name = name
	def run(self):
		print "Starting " + self.name
		displayColumn() 
class SerialCommsThread (threading.Thread):
	def __init__(self, threadID, name):
		threading.Thread.__init__(self)
		self.threadID = threadID
		self.name = name
	def run(self):
		print "Starting " + self.name
		serialComms()

# this method of reporting timeouts only works by convention
# that before calling handle_request() field .timed_out is 
# set to False
def handle_timeout(self):
	self.timed_out = True

# funny python's way to add a method to an instance of a class
import types
columnServer.handle_timeout = types.MethodType(handle_timeout, columnServer)

def clearStrip():
	for pixel in range(totalPixels):
		strip.setPixelColor(pixel, 0x000000)
	strip.show()

def displayColumn():
	while True:
		global color
		global prevColor
		time.sleep(0.001)
		if prevColor != color:	
			#print str(color)
			for pixel in range(totalPixels):
				strip.setPixelColor(pixel, color)	#Assign Color to pixel
			strip.show()
			prevColor = color

def setColorValue(red, green, blue):
	global color
	color = red
	color <<= 8
	color += green
	color <<= 8
	color += blue


def led_callback(path, tags, args, source):
	# which user will be determined by path:
	# we just throw away all slashes and join together what's left
	user = ''.join(path.split("/"))
	# tags will contain 'fff'
	# args is a OSCMessage with data
	# source is where the message came from (in case you need to reply)
	#print ("We received", user,args[0],args[1],args[2], args[3]) 
	#confirmMsg = OSCMessage()
	#confirmMsg.setAddress(" /ledConfirmed ")
	#confirmMsg.append(args[0])
	#confirmMsg.append(args[1])
	#confirmMsg.append(args[2])
	#confirmMsg.append(args[3])
	#lockerClient.send(confirmMsg)
	setColorValue(args[0], args[1], args[2])
	

def quit_callback(path, tags, args, source):
	# don't do this at home (or it'll quit blender)
	global run
	run = False

columnServer.addMsgHandler( "/led", led_callback )
columnServer.addMsgHandler( "/quit", quit_callback )

def eventListener():
	#clear time_out flag
	columnServer.timed_out = False
	# handle all pending requests then return
	while not columnServer.timed_out:
		columnServer.handle_request()

def godListener():
	while run:
		eventListener()
	columnServer.close()



def serialComms():
	while run:
		proximity = ser.readline()
		proxMsg = OSCMessage()
		proxMsg.setAddress(OSCAddress)
		proxMsg.append(proximity)
		columnClient.send(proxMsg)


try:
	listenerThread = ColumnOSCThread(1, "ColumnListenerThread")
	displayThread = ColumnDisplayThread(2, "LEDDisplayThread")
	serialThread = SerialCommsThread(3, "SerialCommsThread")
	listenerThread.start()
	displayThread.start()
	serialThread.start()
except Exception, e:
	print str(e)

#while True:
#	testStrip()
