from os import path, listdir
from re import search, sub


script_path = path.dirname(path.realpath(__file__))
"""Path to this python script"""

for filename in listdir(script_path):
    if search('^chesster_.*py$', filename):
        print 'chesster.{}'.format(sub('\\.py$', '', filename))
