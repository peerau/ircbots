#!/usr/bin/env python
"""
searchbot: Queries bikcmp's search api for results.
Copyright 2011 Jordan Songer <http://libirc.so>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import re, asyncore
from ConfigParser import ConfigParser
from sys import argv, exit
from ircasync import *
import simplejson as json
from urllib2 import urlopen
import lxml.html

config = ConfigParser()
try:
	config.readfp(open(argv[1]))
except:
	try:
		config.readfp(open('searchbot.ini'))
	except:
		print "Syntax:"
		print "  %s [config]" % argv[0]
		print ""
		print "If no configuration file is specified or there was an error, it will default to `searchbot.ini'."
		print "If there was a failure reading the configuration, it will display this message."
		exit(1)

# read config
SERVER = config.get('searchbot', 'server')
try: PORT = config.getint('searchbot', 'port')
except: PORT = DEFAULT_PORT
NICK = config.get('searchbot', 'nick')
CHANNEL = config.get('searchbot', 'channel')

VERSION = "searchbotv1"

try: NICKSERV_PASS = config.get('searchbot', 'nickserv_pass')
except: NICKSERV_PASS = None

try: API_USER = config.get('searchbot', 'api_user')
except: API_USER = 'invalid'
try: API_PASS = config.get('searchbot', 'api_pass')
except: API_PASS = 'invalid'


# NO TRAILING SLASH
API_URL = 'http://api.search.fossnet.info:12123/api/bot/%s/%s/dosearch' % (API_USER, API_PASS)

def strip_tags(value):
	"Return the given HTML with all tags stripped."
	return re.sub(r'<[^>]*?>', '', value)

# main code
def handle_welcome(event, match):
	global NICKSERV_PASS
	# Compliance with most network's rules to set this mode on connect.
	event.connection.usermode("+B")
	if NICKSERV_PASS != None:
		event.connection.todo(['NickServ', 'identify', NICKSERV_PASS])

def handle_cmd(event, match):
	global API_URL
	msg = event.text
	if msg.startswith("!") and len(msg) >= 4:
		query = msg.split(" ")
		if query[0] == "!s":
			try:
				if unicode.isnumeric(unicode(query[1])):
					resnum = int(query[1]) - 1
					searchstring = msg.split("!s "+str(query[1])+" ")[1]
				else:
					resnum = 0
					searchstring = msg.split("!s ")[1]
			
			except IndexError:
				resnum = 0
				searchstring = msg.split("!s ")[1]
			
			searchstring = searchstring.replace(' ', '%20')
			search = "%s/%s" % (API_URL, searchstring)
			try: handle = urlopen(search)
			except:
				event.reply("bikcmp fucked something up")
				return
			
			handled = handle.read()
			if handled.split(" ")[0] == "NORESULTS":
				event.reply("nope.avi")
				return
			
			data = json.loads(handled)
			if data["amount_of_results"] == 1:
				rcount = "1 Result"
			else:
				rcount = "%s Results" % data["amount_of_results"]
			
			try: 
				title = lxml.html.parse(str(data["results"][resnum][0]))
				titletext = title.find(".//title").text
			except IOError:
				titletext = "Connection Error"
			resnumhuman = resnum + 1
			try: event.reply(rcount+": #"+str(resnumhuman)+": "+titletext+" "+str(data["results"][resnum][0])+" Score: "+str(data["results"][resnum][1])+" Took "+str(data["time"])+" seconds")
			except IndexError:
				event.reply("nope.avi")

irc = IRC(nick=NICK, start_channels=[CHANNEL], version=VERSION)
irc.bind(handle_welcome, RPL_WELCOME)
irc.bind(handle_cmd, PRIVMSG)
irc.make_conn(SERVER, PORT)
asyncore.loop()

