#!/usr/bin/env python3
import tty
import shutil
from os import path
from sys import stderr, stdout, stdin, version_info
import sys
import unicodedata
import argparse as ap
import pyperclip
import textwrap
import setproctitle

def getargs():
	par = ap.ArgumentParser(description = 'View a text file one line at a time.', epilog = 'Keys:\nJ/Down:  Scroll down a line\nK/Up:  Scroll up a  line\nH/Left:  Scroll left one screen\nL/Right:  Scroll right one screen\nGG:  Go to the beginning of the file\nShift-G:  Go to the end of the file\nA number: Affects the next command as follows:\n  J/Down:  Scroll down by N lines\n  K/Up:  Scroll up by N lines\n  G:  Go to line N\nP:  Show a progress bar, with percentage. Press any key to dismiss\nN:  Toggle line numbers\nShift-S:  Save a bookmark for the present location. The next time oneline is launched wiht the same file, reading will start at this line. The bookmark is stored in a file called .filename.txt.bookmark (if the file being read is filename.txt)\nW: Toggle line wrap. If line wrap is on, then scrolling up/down will actually scroll left/right if there is text off-screen in the given direction on the current line\nB:  Go back to the line before the last "long" jump. Long jumps are GG, Shift-G, any movement command preceeded by a number, and B (so B undoes itself and only keeps one jump worth of "history")\nShift-P:  Append the current system clipboard contents to the existing text. Only works if input was from a pipe or the clipboard (i.e. not a text file). Requires the pyperclip module.\nCtrl-P:  Replace the current text with text from the system clipboard\nQ:  Quit', formatter_class=ap.RawDescriptionHelpFormatter)
	par.add_argument('Input', nargs = '?', help = 'The text file to read. If not given (and -p is also not specified), or if "-" is given, then the text to display will be read from stdin')
	par.add_argument('-w', '--wrap', action = 'store_true', help = 'Turn on line wrap by default. If line wrap is on then scrolling up/down will actually scroll left/right if there is more text offscreen on the current line in that direction', dest = 'w')
	par.add_argument('-p', '--paste', action = 'store_true', help = 'Read text from the clipboard. No input file should be specified in this case.', dest = 'p')
	return par.parse_args()

save = False
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

def get_pasted_lines(newlines=False):
	pasted_lines = None
	w = shutil.get_terminal_size((80, 20)).columns	# w is the total screen width
	if not newlines:
		clearln(w)
		nl = ''
	else:
		nl = '\n'
	if save:
		stdout.write('Cannot paste when reading from a file' + nl)
	else:
		try:
			pasted = pyperclip.paste()
			if(pasted == ''):
				stdout.write('No text on clipboard' + nl)
			else:
				pasted_lines = []
				for pasted_line in pasted.split('\n'):
					pasted_lines += textwrap.wrap(pasted_line, width=min(80,w))
			if not newlines:
				stdout.write('Pasted')
		except FileNotFoundError as e:
			stdout.write('Pyperclip requires %s to be in the PATH'%e.filename + nl)
	return pasted_lines
def main():
	if version_info.major < 3:
		stderr.write('Oneline requires python 3\n')
		exit(1)
	setproctitle.setproctitle('oneline')
	args = getargs()
	try:
		if args.p:
			w = shutil.get_terminal_size((80, 20)).columns	# w is the total screen width
			lines = get_pasted_lines(newlines = True)
			if lines is None:
				exit(1)
			save = False
		else:
			if args.Input is None or args.Input == '-':
				f = sys.stdin
				save = False
			else:
				f = open(args.Input, 'r', encoding = 'utf-8', errors='surrogateescape')
				save = True
			unproc_lines = f.readlines()
			try:
				lines = [line.expandtabs() for line in unproc_lines]
			except UnicodeDecodeError:
				lines = unproc_lines
			f.close()
	except IOError as e:
		stderr.write('%s: %s\n'%(e.filename, e.strerror))
		exit(1)

	old_settings = tty.tcgetattr(sys.stdin.fileno())
	try:
		if sys.stdin.closed:
			try:
				sys.stdin = open('/dev/tty', 'r')
			except IOError as e:
				stdout.write('Error opening /dev/tty: %s. Reading from standard input may not work on this system.'%e.strerror)
				exit(1)
		tty.setcbreak(sys.stdin, tty.TCSANOW)
		line_n = 0
		prev_n = -1
		if save:
			#savename = '.%s.bookmark'%args.Input
			savename = path.join(path.dirname(args.Input),f'.{path.basename(args.Input)}.bookmark')
			try:
				bkmkfile = open(savename, 'r')
				line_n = min(int(bkmkfile.read()), len(lines)-1)
			except Exception:
				pass
		showline = False
		hpos = 0
		c = ''
		wrap = args.w
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
			c = sys.stdin.read(1)	# c is the character representing the key the user pressed
			if c == esc:		# Escape sequence - what we get when the user presses an arrow key. To ensure consistent behavior, we respond to this by changing c to an equivalent key (hjkl) and falling through to the subsequent if-else chain 
				c = sys.stdin.read(1)
				if c == '[':
					c = sys.stdin.read(1)
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
				if hpos == 1: hpos = 0
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
				sys.stdin.read(1)
			elif c == 'n':
				showline = not showline
			elif c == 'g':
				prev_n = line_n
				line_n = 0
			elif c == 'G':
				prev_n = line_n
				line_n = len(lines)-1
			elif c == 'S':
				clearln(w)
				if not save:
					stdout.write('Cannot save position when reading from stdin')
				else:
					try:
						with open(savename, 'w') as bkmkfile:
							bkmkfile.write(str(line_n))
							stdout.write('Saved')
					except IOError as e:
						stdout.write('%s: %s'%(savename, e.strerror))
				stdout.flush()
				sys.stdin.read(1)
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
				sys.stdin.read(1)
			elif c == 'P' or c == '\x10':
				pasted_lines = get_pasted_lines()
				if pasted_lines:
					if c == 'P':
						lines += pasted_lines
					else:
						lines = pasted_lines
						line_n = 0
				stdout.flush()
				sys.stdin.read(1)
			elif c == 'w':
				clearln(w)
				wrap = not wrap
				stdout.write('Wrap '+('on' if wrap else 'off'))
				stdout.flush()
				sys.stdin.read(1)
			elif c == 'q':
				clearln(w)
				break
			elif c == 'b' and prev_n >= 0:
				goto = prev_n
				prev_n = line_n
				line_n = goto
			elif c.isdigit():
				prev_n = line_n
				goto = int(c)
				while True:
					clearln(w)
					stdout.write(str(goto))
					stdout.flush()
					c = sys.stdin.read(1)
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
		tty.tcsetattr(sys.stdin.fileno(), tty.TCSADRAIN, old_settings)

if __name__ == '__main__':
	main()
