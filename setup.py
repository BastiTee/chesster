#!/usr/bin/env python

from distutils.core import setup

setup(
	name='chesster',
    version='0.2.0',
    description='''Chesster - Personal chess buddy.''',
	long_description='''Chesster - Personal chess buddy.''',
    author='Basti Tee',
    author_email='basti.tee@gmx.de',
    url='https://github.com/BastiTee/chesster',
    packages=['chesster'],
	package_data={'chesster': [
		'**/*.py',
		'**/*.default',
		'pgnextract/*',
		'stockfish/*',
	]},
)
