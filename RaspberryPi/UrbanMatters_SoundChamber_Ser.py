#/user/bin/python

from OSC import OSCServer, OSCClient, OSCMessage
import spidev
import threading
#import thread
import sys
import os
import atexit
import time
from serial import Serial
from time import sleep
from dotstar import Adafruit_DotStar
# from serial import Serial
import re
import RPi.GPIO as GPIO
 
GPIO.setmode(GPIO.BCM)
DEBUG = 1

import pygame

import socket
import fcntl
import struct

DEBUG = 1

OSCAddress = "/0"

spi = spidev.SpiDev()
spi.open(0, 0)

# ip address finder
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
ifname = 'eth0'
localIP = socket.inet_ntoa(fcntl.ioctl(
        s.fileno(),
        0x8915,  # SIOCGIFADDR
        struct.pack('256s', ifname[:15])
    )[20:24])

clientAddress = '192.168.0.190', 9999
serverAddress = localIP, 9998

ser = Serial('/dev/ttyUSB0', 57600)

columnServer = OSCServer( serverAddress ) 
columnServer.timeout = 0
run = True

columnClient = OSCClient()
columnClient.connect(clientAddress)

# Audio player
pygame.mixer.init()
uniqueSound = pygame.mixer.Sound("testSound.wav")
uniqueSound.set_volume(0)
uniqueSound.play(-1)

pygame.mixer.music.load("testSound.wav")
pygame.mixer.music.set_volume(0)
pygame.mixer.music.play(-1)


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
globalRed = 0
globalGreen = 0
globalBlue = 0

# SPI Pins.  - Change as needed
SPICLK = 11
SPIMISO = 9
SPIMOSI = 10
SPICS = 8

# PWM Pins.  Change as needed
REDPIN = 6
GREENPIN = 13
BLUEPIN = 5

# Frequencey of PWM
HERTZ = 800
 
# set up the SPI interface pins
GPIO.setup(SPIMOSI, GPIO.OUT)
GPIO.setup(SPIMISO, GPIO.IN)
GPIO.setup(SPICLK, GPIO.OUT)
GPIO.setup(SPICS, GPIO.OUT)
GPIO.setup(REDPIN, GPIO.OUT)
GPIO.setup(GREENPIN, GPIO.OUT)
GPIO.setup(BLUEPIN, GPIO.OUT)

redPWM = GPIO.PWM(REDPIN, HERTZ)
bluePWM = GPIO.PWM(BLUEPIN,HERTZ)
greenPWM = GPIO.PWM(GREENPIN, HERTZ)

#redPWM.start(0)
#bluePWM.start(0)
#greenPWM.start(0)

# proximity sensor connected to adc #0
prox_adc = 0;


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
		#displayColumn() 
class ProximityCommsThread (threading.Thread):
	def __init__(self, threadID, name):
		threading.Thread.__init__(self)
		self.threadID = threadID
		self.name = name
	def run(self):
		print "Starting " + self.name
		proximityComms()

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
		global globalRed 
		global globalGreen 
		global globalBlue
		time.sleep(0.001)
		if prevColor != color:	
			redPWM.ChangeDutyCycle(globalRed)
			greenPWM.ChangeDutyCycle(globalGreen)
			bluePWM.ChangeDutyCycle(globalBlue)
			# print str(globalRed) + ", " + str(globalGreen) + ", " + str(globalBlue)
			# print str(color)
			# for pixel in range(totalPixels):
			# 	strip.setPixelColor(pixel, color)	#Assign Color to pixel
			# strip.show()

			prevColor = color

def setColorValue(red, green, blue):
	global color
	global globalRed 
	global globalGreen 
	global globalBlue
	globalRed = (red/256.0 * 100.0)
	color = red
	color <<= 8
	globalGreen = (green/256.0 * 100.0)
	color += green
	color <<= 8
	globalBlue = (blue/256.0 * 100.0)
	color += blue


def led_callback(path, tags, args, source):
	user = ''.join(path.split("/"))
	print ("We received", user,args[0],args[1],args[2]) 
	if checkValues(args[0], args[1], args[2]):
		ser.write(str(args[0])+','+str(args[1])+','+str(args[2]))
		ser.write('\n')
		print("wrote to serial")
		#setColorValue(args[0], args[1], args[2])

def checkValues(arg1, arg2, arg3):
	if isinstance(arg1, (int, long)) and isinstance(arg2, (int, long)) and isinstance(arg3, (int, long)):
		if arg1 >= 0 and arg1 <=255 and arg2 >= 0 and arg2 <=255 and arg3 >= 0 and arg3 <=255:
			return True
		else:
			print(arg1 + " " + arg2 + " " + arg3)
			return False
	else:
		print(arg1 + " " + arg2 + " " + arg3)
		return False		

def quit_callback(path, tags, args, source):
	# don't do this at home (or it'll quit blender)
	global run
	run = False

# read SPI data from MCP3008 chip, 8 possible adc's (0 thru 7)
def readadc(adcnum, clockpin, mosipin, misopin, cspin):
        if ((adcnum > 7) or (adcnum < 0)):
                return -1
        GPIO.output(cspin, True)
 
        GPIO.output(clockpin, False)  # start clock low
        GPIO.output(cspin, False)     # bring CS low
 
        commandout = adcnum
        commandout |= 0x18  # start bit + single-ended bit
        commandout <<= 3    # we only need to send 5 bits here
        for i in range(5):
                if (commandout & 0x80):
                        GPIO.output(mosipin, True)
                else:
                        GPIO.output(mosipin, False)
                commandout <<= 1
                GPIO.output(clockpin, True)
                GPIO.output(clockpin, False)
 
        adcout = 0
        # read in one empty bit, one null bit and 10 ADC bits
        for i in range(12):
                GPIO.output(clockpin, True)
                GPIO.output(clockpin, False)
                adcout <<= 1
                if (GPIO.input(misopin)):
                        adcout |= 0x1
 
        GPIO.output(cspin, True)
        
        adcout >>= 1       # first bit is 'null' so drop it
        return adcout

def volume_callback(path, tags, args, source):
	user = ''.join(path.split("/"))
#	print("We received", user, args[0])
	uniqueSound.set_volume(args[0])
	#pygame.mixer.music.set_volume(args[0])

def soundfile_callback(path, tags, args, source):
	user = ''.join(path.split("/"))
	print("We received", user, args[0])
	global uniqueSound
	uniqueSound.stop()
	uniqueSound = pygame.mixer.Sound(args[0])
	uniqueSound.set_volume(0)
	uniqueSound.play(-1)
	
def setTargetIP_callback(path, tags, args, source):
	user = ''.join(path.split("/"))
	print("We received", user, args[0])
	columnClient.close()
	clientAddress = args[0], 9999
	columnClient.connect(clientAddress)

columnServer.addMsgHandler( "/led", led_callback )
columnServer.addMsgHandler( "/quit", quit_callback )
columnServer.addMsgHandler( "/volume", volume_callback )
columnServer.addMsgHandler( "/soundfile", soundfile_callback )
columnServer.addMsgHandler( "/sendTo", setTargetIP_callback )

def eventListener():
	#clear time_out flag
	columnServer.timed_out = False
	# handle all pending requests then return
	while not columnServer.timed_out:
		time.sleep(0.01)
		columnServer.handle_request()

def godListener():
	while run:
		eventListener()
	columnServer.close()



def proximityComms():
	while run:
		proximity = ser.readline()
		print(proximity)
		time.sleep(0.01)
		#proximity = readadc(prox_adc, SPICLK, SPIMOSI, SPIMISO, SPICS)
		proxMsg = OSCMessage()
		proxMsg.setAddress(OSCAddress)
		proxMsg.append(proximity)
		try:
			columnClient.send(proxMsg)
		except:
			print("client unavailable")
			pass

try:
	listenerThread = ColumnOSCThread(1, "ColumnListenerThread")
	displayThread = ColumnDisplayThread(2, "LEDDisplayThread")
	proximityThread = ProximityCommsThread(3, "SerialCommsThread")
	listenerThread.daemon = True
	displayThread.daemon = True
	proximityThread.daemon = True
	listenerThread.start()
	displayThread.start()
	proximityThread.start()
	while True:
		time.sleep(0.1)
except KeyboardInterrupt:
	redPWM.stop()
	bluePWM.stop()
	greenPWM.stop()
	GPIO.cleanup();
	print("Keyboard interrupt")
except Exception, e:
	print str(e)
