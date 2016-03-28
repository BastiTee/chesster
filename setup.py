#!/usr/bin/env python

from distutils.core import setup

setup(
	name='chesster',
    version='0.1.0',
    description='''Chesster - Personal chess trainer.''',
	long_description='''Chesster - Personal chess trainer.''',
    author='Basti Tee',
    author_email='basti.tee@gmx.de',
    url='https://github.com/BastiTee/chesster',
    packages=['chesster'],
	package_data={'chesster': ['**/*.*']},
) 
