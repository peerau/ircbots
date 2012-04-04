import time, hashlib, re, asyncore
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
		config.readfp(open('ddlbot.ini'))
	except:
		print "Syntax:"
		print "  %s [config]" % argv[0]
		print ""
		print "If no configuration file is specified or there was an error, it will default to `ddlbot.ini'."
		print "If there was a failure reading the configuration, it will display this message."
		exit(1)

# read config
SERVER = config.get('ddlbot', 'server')
try: PORT = config.getint('ddlbot', 'port')
except: PORT = DEFAULT_PORT
NICK = config.get('ddlbot', 'nick')
CHANNEL = config.get('ddlbot', 'channel')
VERSION = 'ddlbot; https://github.com/peerau/ircbots/; %s'
try: VERSION = VERSION % Popen(["git","branch","-v","--contains"], stdout=PIPE).communicate()[0].strip()
except: VERSION = VERSION % 'unknown'

try: NICKSERV_PASS = config.get('ddlbot', 'nickserv_pass')
except: NICKSERV_PASS = None
try: SECRET = config.get('ddlbot', 'secret')
except: SECRET = '1234567890'

def secure_download (prefix, url):
	t = '%08x' % (time.time())
	return "/%s/%s" % (hashlib.md5(SECRET + url + t).hexdigest(), t + url)

def handle_msg(event, match):
	global message_buffer, MAX_MESSAGES, last_message, flooders, CHANNEL
	msg = event.text

	if event.channel.lower() != CHANNEL.lower():
		# ignore messages not from our channel
		return

	if (msg.startswith(':') or msg.startswith(NICK)):
		event.reply("%s: Yes hello there!" % event.nick)
		return

def handle_notice(event, match):
	pass

def handle_welcome(event, match):
	global NICKSERV_PASS
	# Compliance with most network's rules to set this mode on connect.
	event.connection.usermode("+B")
	if NICKSERV_PASS != None:
		event.connection.todo(['NickServ', 'identify', NICKSERV_PASS])

irc = IRC(nick=NICK, start_channels=[CHANNEL], version=VERSION)
irc.bind(handle_msg, PRIVMSG)
irc.bind(handle_notice, NOTICE)
irc.bind(handle_welcome, RPL_WELCOME)

irc.make_conn(SERVER, PORT)
asyncore.loop()

