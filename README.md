# Oneline
Oneline is a program that displays text files the terminal in the manner of less, but only one line at a time, for distraction-free reading. It supports reading text files or text from the clipboard, and for text files supports saving your place.
You can install it by cd'ing to the project directory and running:

	sudo python setup.py install

You can then invoke oneline on a file with:

	oneline Book.txt
	
The first line will be displayed. To move up and down lines you can use the arrows or k and j (as in vim or less). Space and enter also move down a line. If the line is longer than the terminal width, an inverted > will be displayed at the end of the window; you can scroll horizontally with the arrows or h and l. If wrap is turned on, scrolling down will instead scroll right until there is no more to see on that line, and vice-versa for scrolling up. Wrap can be toggled with w.
Quit with q.
Other features include:
* You can read from a pipe rather than a text file (cat file.txt | tr 'a' 'o' | oneline.py)
* Save your progress with shift-s. This will create a file called (if your text file is Book.txt) .Book.txt.bookmark containing the number of the line you are on. The next time you invoke Oneline on the same file, the bookmark file will be found and you will be taken to that line.
* You can paste text from the clipboard to read with shift-p (add to the end of the current text) or ctrl-p (replace the current text).
* Toggle display of the current line number with n.
* Get a visual progress bar, with what percentage of the way through the file you are, with p. Press any key to dismiss
* Temporarily hide the displayed line with c.
* To jump multiple lines forward or backward, enter the number of lines and then press the appropriate movement key.
* To jump to a particular line, enter the line number and press g.
* To jump to the beginning of the file, press g. To jump to the end, press shift-g.
* Press b to go back after a long jump of any kind. When you jump using g, shift-g, b, or use up, down, j, k, or g with a number of lines or line number, your position from before the jump is saved and can be returned to with b (even if you moved around after the jump using up/down). The b command undoes itself, but only keeps one step of "undo history" so pressing it multiple times will flip between the lines before and after the initial long jump. Note that if you swap between two positions with b but move around at each place with up/down, the two positions will be kept updated with your movements. So if you're on line 20 and type 100g, then j a couple times to get to line 102, then b to go back to 20, then b again, you'll be taken once again to line 102.

The following command-line options are available:
* -w activates line wrap on startup (see above for what that does). It can still be toggled with the W key
* -p starts with text from the system clipboard rather than a file or pipe.
