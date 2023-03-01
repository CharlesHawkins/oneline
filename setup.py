from setuptools import setup
with open('README.md') as readme:
	ldesc = readme.read()
setup(name='Oneline',
	  description='Read a text file, one line at a time',
	  long_description=ldesc,
	  version="1.0",
	  url='https://github.com/CharlesHawkins/oneline',
	  entry_points={'console_scripts':['oneline=oneline:main']},
	  install_requires=['setproctitle','pyperclip'],
	  py_modules=['oneline'])
