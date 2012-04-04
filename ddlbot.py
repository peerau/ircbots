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
except: VERSION = 'riebot; https://github.com/peerau/ircbots/; %s'
try: VERSION = VERSION % Popen(["git","branch","-v","--contains"], stdout=PIPE).communicate()[0].strip()
except: VERSION = VERSION % 'unknown'

try: NICKSERV_PASS = config.get('ddlbot', 'nickserv_pass')
except: NICKSERV_PASS = None
try: SECRET = config.get('ddlbot', 'secret')
except: SECRET = '1234567890'

def secure_download (prefix, url):
    t = '%08x' % (time.time())
    return "/%s/%s" % (hashlib.md5(SECRET + url + t).hexdigest(), t + url)

irc = IRC(nick=NICK, start_channels=[CHANNEL], version=VERSION)
irc.bind(handle_msg, PRIVMSG)
irc.bind(handle_welcome, RPL_WELCOME)
irc.bind(handle_ctcp, CTCP_REQUEST)

irc.make_conn(SERVER, PORT)
asyncore.loop()

