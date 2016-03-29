#!/usr/bin/python
import argparse
import logging

from chesster.core.daemon import ChessterDaemon


parser = argparse.ArgumentParser(description='A daemon to analyze PGN-file games in a watch folder.')
parser.add_argument('-i', metavar='<WORKDIR>', help='Input working directory.')
parser.add_argument('-t', metavar='<T_MS>', help='Engine time per move in ms'
                    + ' (default: 5000).')
parser.add_argument('-v', action='store_true', help='Verbose output.')
parser.add_argument('-r', metavar='<INTERVAL>',
                    help='Worker interval in seconds.')
args = parser.parse_args()

if args.i == None:
    print 'No working directory set.'
    parser.print_help()
    exit()
if args.t == None:
    args.t = 5000
if args.r == None:
    args.r = 30
if args.v:
    logging.basicConfig(level=logging.DEBUG, format='[%(levelname)s]\t%(message)s')
else:
    logging.basicConfig(level=logging.INFO, format='[%(levelname)s]\t%(message)s')

daemon = ChessterDaemon(args.i, args.t, args.r)
daemon.start()
