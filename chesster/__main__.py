from os import path, listdir
from re import search, sub


for filename in listdir(path.dirname(path.realpath(__file__))):
    if search('^chesster_.*py$', filename):
        print 'chesster.{}'.format(sub('\\.py$', '', filename))
