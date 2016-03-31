#!/usr/bin/python
import argparse
parser = argparse.ArgumentParser(
        description='A server-frontend to send UCI commands over the web.')
parser.add_argument('-d', metavar='<HOSTNAME>', default='localhost',
        help='Hostname (default: localhost).')
parser.add_argument('-p', metavar='<PORT>', default=8000,
        help='Port (default: 8000).')
parser.add_argument('-v', action='store_true', 
        help='Verbose output.')
args = parser.parse_args()

from bptbx.b_logging import setup_logging
setup_logging(args.v)

from chesster.core.server import ChessterServer
chesster_server = ChessterServer(args.d, args.p)
