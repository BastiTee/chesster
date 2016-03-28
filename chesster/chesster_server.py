#!/usr/bin/python
import argparse
import logging 

from chesster.core.server import ChessterServer


parser = argparse.ArgumentParser(description='Setup a chesster_server server')
parser.add_argument('-d', metavar='<HOSTNAME>', help='Hostname (default: localhost).')
parser.add_argument('-p', metavar='<PORT>', help='Port (default: 8000).')
parser.add_argument('-v', action='store_true', help='Verbose output.')
args = parser.parse_args()

if args.d == None:
    args.d = 'localhost'
if args.p == None:
    args.p = 8000
if args.v:
    logging.basicConfig(level=logging.DEBUG, format='[%(levelname)s]\t%(message)s')
else:
    logging.basicConfig(level=logging.INFO, format='[%(levelname)s]\t%(message)s')

chesster_server = ChessterServer(args.d, args.p)

