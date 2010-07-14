import irclib, re
from datetime import datetime, timedelta
from ConfigParser import ConfigParser
from sys import argv, exit

host, port = "localhost", 6667
nick = "regexbot"
channel = "#streetgeek"

config = ConfigParser()
try:
	config.readfp(open(argv[1]))
except:
	try:
		config.readfp(open('regexbot.ini'))
	except:
		print "Syntax:"
		print "  %s [config]" % argv[0]
		print ""
		print "If no configuration file is specified or there was an error, it will default to `regexbot.ini'."
		print "If there was a failure reading the configuration, it will display this message."
		exit(1)

# read config
SERVER = config.get('regexbot', 'server')
PORT = config.getint('regexbot', 'port')
NICK = config.get('regexbot', 'nick')
CHANNEL = config.get('regexbot', 'channel')
FLOOD_COOLDOWN = timedelta(seconds=config.getint('regexbot', 'flood_cooldown'))
MAX_MESSAGES = config.getint('regexbot', 'max_messages')

message_buffer = []
last_message = datetime.now()
flooders = []
ignore_list = []

if config.has_section('ignore'):
	for k,v in config.items('ignore'):
		try:
			ignore_list.append(re.compile(v, re.I))
		except Exception, ex:
			print "Error compiling regular expression in ignore list (%s):" % k
			print "  %s" % v
			print ex
			exit(1)

def handle_pubmsg(connection, event):
	global message_buffer, MAX_MESSAGES, last_message, flooders
	nick = event.source().partition("!")[0]
	msg = event.arguments()[0]
	
	if msg.startswith('s/'):
		for item in ignore_list:
			if item.search(event.source()) != None:
				# ignore list item hit
				print "Ignoring message from %s because of: %s" % (event.source(), item.pattern)
				return
		
		# handle regex
		parts = msg.split('/')
		
		# now flood protect!
		now = datetime.now()
		delta = now - last_message
		last_message = now
		
		if delta < FLOOD_COOLDOWN:
			# 5 seconds between requests
			# any more are ignored
			print "Flood protection hit, %s of %s seconds were waited" % (delta.seconds, FLOOD_COOLDOWN.seconds)
		
		if len(message_buffer) == 0:
			connection.privmsg(event.target(), '%s: message buffer is empty' % nick)
			return
		
		if len(parts) == 3:
			connection.privmsg(event.target(), '%s: invalid regular expression, you forgot the trailing slash, dummy' % nick)
			return
		
		if len(parts) != 4:
			# not a valid regex
			connection.privmsg(event.target(), '%s: invalid regular expression, not the right amount of slashes' % nick)
			return
		
		# find messages matching the string
		if len(parts[1]) == 0:
			connection.privmsg(event.target(), '%s: original string is empty' % nick)
			return
			
		ignore_case = 'i' in parts[3]
		
		e = None
		try:
			if ignore_case:
				e = re.compile(parts[1], re.I)
			else:
				e = re.compile(parts[1])
		except Exception, ex:
			connection.privmsg(event.target(), '%s: failure compiling regular expression: %s' % (nick, ex))
			return
		
		# now we have a valid regular expression matcher!
		
		for x in range(len(message_buffer)-1, -1, -1):
			if e.search(message_buffer[x][1]) != None:
				# match found!
				
				new_message = []
				# replace the message in the buffer
				try:
					new_message = [message_buffer[x][0],	e.sub(parts[2], message_buffer[x][1]).replace('\n','').replace('\r','')[:200]]
					del message_buffer[x]
					message_buffer.append(new_message)
				except Exception, ex:
					connection.privmsg(event.target(), '%s: failure replacing: %s' % (nick, ex))
					return
				
				# now print the new text
				print new_message
				connection.privmsg(event.target(), ('<%s> %s' % (new_message[0], new_message[1]))[:200])
				return
		
		# no match found
		connection.privmsg(event.target(), '%s: no match found' % nick)		 
	else:
		# add to buffer
		message_buffer.append([nick, msg[:200]])
		
	# trim the buffer
	message_buffer = message_buffer[-MAX_MESSAGES:]

def join_channels(connection, event):
	connection.join(CHANNEL)
	connection.send_raw("MODE %s +B" % NICK) # Compliance with most network's rules to set this mode on connect.

irc = irclib.IRC()
irc.add_global_handler('pubmsg', handle_pubmsg)
irc.add_global_handler('welcome', join_channels)
server = irc.server()
server.connect(SERVER, PORT, NICK)
irc.process_forever()
