#!/usr/bin/env python3
import tty
import shutil
from sys import stderr, stdout, stdin, argv
import unicodedata

try:
	import pyperclip
	import textwrap
	paste = True
except ImportError:
	paste = False

try:
	import procname
	procname.setprocname('oneline')
except ImportError:
	pass

esc = '\x1b'	# The escape character
csi = esc + '['	# Control Sequence Introducer, used for terminal control sequences
def sgr(n):	# Return a string that when printed will send a Select Graphic Rendition command to the terminal. n should be an integer indicating the display mode to select
	return(csi + str(n) + 'm')
def with_sgr(n, string):	# Return a string containing the given string with graphic rendition code n, and a code that resets the terminal after
	return(sgr(n)+string+sgr(0))
def clearln(n):
	stdout.write('\r' + ' ' * n + '\r')
def write_more_indicator_right():	# Print the inverted '>', used to indicate there is more text on the current line to the right of the screen
	stdout.write(with_sgr(7, '>'))
def write_more_indicator_left():	# Print the inverted '<', used to indicate there is more text on the current line to the left of the screen
	stdout.write(with_sgr(7, '<'))

try:
	if len(argv) < 2 or argv[1] == '-':
		fname = 'stdin'
		f = stdin
		save = False
	else:
		fname = argv[1]
		f = open(fname, 'r', encoding = 'utf-8', errors='surrogateescape')
		save = True
	unproc_lines = f.readlines()
	try:
		lines = [line.expandtabs() for line in unproc_lines]
	except UnicodeDecodeError:
		lines = unproc_lines
	f.close()
except IOError as e:
	stderr.write('%s: %s\n'%(fname, e.strerror))
	exit(1)

try:
	if stdin.closed:
		try:
			stdin = open('/dev/tty', 'r')
		except IOError as e:
			stdout.write('Error opening /dev/tty: %s. Reading from standard input may not work on this system.'%e.strerror)
			exit(1)
	old_settings = tty.tcgetattr(stdin.fileno())
	tty.setcbreak(stdin, tty.TCSANOW)
	line_n = 0
	if save:
		savename = '.%s.bookmark'%argv[1]
		try:
			bkmkfile = open(savename, 'r')
			line_n = min(int(bkmkfile.read()), len(lines)-1)
		except Exception:
			pass
	showline = False
	hpos = 0
	c = ''
	wrap = True
	while True:
		line = lines[line_n].rstrip()
		w = shutil.get_terminal_size((80, 20)).columns	# w is the total screen width
		clearln(w)
		lnstr = '%i: '%(line_n+1)	# lnstr is the string representing the current line number
		rem_w = w-len(lnstr) if showline else w		# rem_w is the remaining screen width after the line number, if enabled, has been printed
		if hpos+rem_w < len(line):	# True if the current line runs off the edge of the screen, in which case we need to print the inverse-styled '>' to indicate there's more text on this line (modeled after less)
			rem_w -= 1;
			indicate_more_right = True
		else:
			indicate_more_right = False
		if hpos > 0:
			rem_w -= 1;
			indicate_more_left = True
		else:
			indicate_more_left = False
		to_end = min(rem_w, len(line))
		if c != 'c':	# If the last command was anything but 'c' (clear display), then print the current line
			if showline:
				stdout.buffer.write(lnstr.encode('utf8', errors = 'surrogateescape'))
			if indicate_more_left:
				write_more_indicator_left()
				stdout.flush()
			try:
				stdout.buffer.write((line[hpos:hpos+to_end]).encode('utf8', errors = 'surrogateescape'))
			except TypeError:
				stdout.write("index: %s, rem_w: %s, to_end: %s"%(hpos, rem_w, to_end))
			if indicate_more_right:
				write_more_indicator_right()
			stdout.flush()
		c = stdin.read(1)	# c is the character representing the key the user pressed
		if c == esc:		# Escape sequence - what we get when the user presses an arrow key. To ensure consistent behavior, we respond to this by changing c to an equivalent key (hjkl) and falling through to the subsequent if-else chain 
			c = stdin.read(1)
			if c == '[':
				c = stdin.read(1)
				if c == 'A':	# Up arrow
					c = 'k'
				elif c == 'B':	# Down arrow
					c = 'j'
				elif c == 'C':	# Right arrow
					c = 'l'
				elif c == 'D':	# Left arrow
					c = 'h'
		if c == 'h' or (wrap and c == 'k' and hpos > 0):
			hpos = max(hpos-rem_w, 0)
		elif c == '0':
			hpos = 0
		elif (c == 'l' or (wrap and c == 'j')) and hpos + rem_w < len(line):
			hpos = hpos+to_end
		elif (c == 'j'  or c == ' ' or c == '\r' or c == '\n') and line_n < len(lines)-1:
			line_n += 1
			hpos = 0
		elif c == 'k' and line_n > 0:
			line_n -= 1
			if wrap:
				hpos = int(int(len(lines[line_n].rstrip()))/int(rem_w))*int(rem_w)
			else:
				hpos = 0
		elif c == 'i':
			clearln(w)
			stdout.write('Line %s, length %s, disp width %s, chars to print %s, hpos %s'%(line_n, len(line), rem_w, to_end, hpos))
			stdout.flush()
			stdin.read(1)
		elif c == 'n':
			showline = not showline
		elif c == 'g':
			line_n = 0
		elif c == 'G':
			line_n = len(lines)-1
		elif c == 'S':
			clearln(w)
			if not save:
				stdout.write('Cannot save position when reading from stdin')
			else:
				try:
					bkmkfile = open(savename, 'w')
					bkmkfile.write(str(line_n))
					stdout.write('Saved')
				except IOError as e:
					stdout.write('%s: %s'%(savename, e.strerror))
				finally:
					bkmkfile.close()
			stdout.flush()
			stdin.read(1)
		elif c == 'p':
			clearln(w)
			if len(lines)<=1:
				pct = 1
			else:
				pct = line_n / (len(lines)-1)
			pct_str = str(round(pct*100,2))+'%'
			w_left = w-len(pct_str)
			if(w >= len(pct_str)):
				if(w_left > 0):
					pct_complete = int(pct * w_left)
					pct_left = w_left-pct_complete
					stdout.write('*'*pct_complete)
					stdout.write('-'*pct_left)
				stdout.write(pct_str)
			stdout.flush()
			stdin.read(1)
		elif c == 'P' or c == '\x10':
			clearln(w)
			if not paste:
				stdout.write('Pasting requires the pyperclip module')
			elif save:
				stdout.write('Cannot paste when reading from a file')
			else:
				pasted = pyperclip.paste()
				if(pasted == ''):
					stdout.write('No text on clipboard')
				else:
					pasted_lines = []
					for pasted_line in pasted.split('\n'):
						pasted_lines += textwrap.wrap(pasted_line, width=min(80,w))
					if c == 'P':
						lines += pasted_lines
					else:
						lines = pasted_lines
						line_n = 0
					stdout.write('Pasted')
			stdout.flush()
			stdin.read(1)
		elif c == 'w':
			clearln(w)
			wrap = not wrap
			stdout.write('Wrap '+('on' if wrap else 'off'))
			stdout.flush()
			stdin.read(1)
		elif c == 'q':
			clearln(w)
			break
		elif c.isdigit():
			goto = int(c)
			while True:
				clearln(w)
				stdout.write(str(goto))
				stdout.flush()
				c = stdin.read(1)
				if c.isdigit():
					goto = goto*10+int(c)
				elif c == 'g' or c == 'G':
					line_n = max(min(goto-1, len(lines)-1), 0)
					break
				elif c == 'j' or c == ' ':
					line_n = min(line_n+goto, len(lines)-1)
					break
				elif c == 'k':
					line_n = max(line_n-goto, 0)
					break
				elif c == '\x7f':
					goto = int(goto/10)
				else:
					break
			
finally:
	tty.tcsetattr(stdin.fileno(), tty.TCSADRAIN, old_settings)
