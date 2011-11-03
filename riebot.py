import re, asyncore
from datetime import datetime, timedelta
from ConfigParser import ConfigParser
from sys import argv, exit
from ircasync import *
from subprocess import Popen, PIPE

config = ConfigParser()
try:
	config.readfp(open(argv[1]))
except:
	try:
		config.readfp(open('riebot.ini'))
	except:
		print "Syntax:"
		print "  %s [config]" % argv[0]
		print ""
		print "If no configuration file is specified or there was an error, it will default to `regexbot.ini'."
		print "If there was a failure reading the configuration, it will display this message."
		exit(1)

# read config
SERVER = config.get('riebot', 'server')
try: PORT = config.getint('riebot', 'port')
except: PORT = DEFAULT_PORT
NICK = config.get('riebot', 'nick')
CHANNEL = config.get('riebot', 'channel')
VERSION = 'riebot ver0.1b; http://github.com/peer/ircbots/'

try: TEXT_TIME = timedelta(minutes=config.getint('riebot', 'text_timeout'))
except: TEXT_TIME = timedelta(minutes=60)
try: FROM_HOST = config.getint('riebot', 'from_host')
except: FROM_HOST = '@defocus/regular/crazycatlady'
try: NICKSERV_PASS = config.get('riebot', 'nickserv_pass')
except: NICKSERV_PASS = None
try: BAN_HOST = config.get('riebot', 'ban_host')
except: BAN_HOST = '*!*@unaffiliated/sabian'

message_buffer = []
last_message = datetime.now()
flooders = []
BAN_ACTIVE = False

# main code

def handle_msg(event, match):
	global last_message, flooders, CHANNEL, TEXT_TIME, FROM_HOST, BAN_HOST, BAN_ACTIVE
	msg = event.text
	
	if event.channel.lower() == CHANNEL.lower():
		if FROM_HOST in event.origin:
			delta = event.when - last_message
			if delta < TEXT_TIME:
				last_message = event.when
				print "RESET COUNTER" % (delta.seconds, TEXT_TIME.seconds)
				return
			if BAN_ACTIVE:
				event.connection.todo(['MODE', CHANNEL, '-j', BAN_HOST])
				BAN_ACTIVE = False
		else:
			if (delta > TEXT_TIME) and not BAN_ACTIVE:
				BAN_ACTIVE = True
				event.connection.todo(['MODE', CHANNEL, '+j', BAN_HOST])
				

def handle_welcome(event, match):
	global NICKSERV_PASS
	# Compliance with most network's rules to set this mode on connect.
	event.connection.usermode("+B")
	if NICKSERV_PASS != None:
		event.connection.todo(['NickServ', 'identify', NICKSERV_PASS])

irc = IRC(nick=NICK, start_channels=[CHANNEL], version=VERSION)
irc.bind(handle_msg, PRIVMSG)
irc.bind(handle_welcome, RPL_WELCOME)
irc.bind(handle_ctcp, CTCP_REQUEST)

irc.make_conn(SERVER, PORT)
asyncore.loop()

