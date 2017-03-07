#!/usr/bin/python
import argparse
import logging
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
logging.info('Go to http://{}:{}/?com=uci to see if the server is up!'
             .format(args.d, args.p))
chesster_server = ChessterServer(args.d, args.p)
