#!/usr/bin/python
import argparse
parser = argparse.ArgumentParser(
        description='A daemon to analyze PGN-file games in a watch folder.')
parser.add_argument('-i', metavar='<WORKDIR>', 
        help='Input working directory.')
parser.add_argument('-t', metavar='<T_MS>', default=5000, 
        help='Engine time per move in ms (default: 5000).')
parser.add_argument('-v', action='store_true', 
        help='Verbose output.')
parser.add_argument('-r', metavar='<INTERVAL>', default=30, 
        help='Worker interval in seconds.')
args = parser.parse_args()

from bptbx.b_logging import setup_logging
setup_logging(args.v)

from chesster.core.daemon import ChessterDaemon
if args.i == None:
    print 'No working directory set.'
    parser.print_help()
    exit()
daemon = ChessterDaemon(args.r)
daemon.configure_daemon(args.i, args.t)
daemon.start()
