#!/usr/bin/python
import argparse
from bptbx.b_logging import setup_logging
from chesster.core.daemon import ChessterDaemon

parser = argparse.ArgumentParser(
    description='A daemon to analyze PGN-file games in a watch folder.')
parser.add_argument('-i', metavar='<WORKDIR>',
                    help='Input working directory.')
parser.add_argument('-t', metavar='<T_MS>', default=5000,
                    help='Engine time per move in ms (default: 5000).')
parser.add_argument('-v', action='store_true',
                    help='Verbose output.')
parser.add_argument('-c', metavar='<INTERVAL>', default=30,
                    help='Worker interval in seconds (0 = single run).')
parser.add_argument('-r', metavar='<PATTERN_FILE>', default=None,
                    help='Engine time per move in ms (default: 5000).')
args = parser.parse_args()

setup_logging(args.v)

if not args.i:
    print('No working directory set.')
    parser.print_help()
    exit()

daemon = ChessterDaemon(args.c)
daemon.configure_daemon(args.i, args.t, args.r)
daemon.start()
