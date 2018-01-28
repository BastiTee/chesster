#!/usr/bin/python
import argparse
from os import path
from bptbx.b_logging import setup_logging
from multiprocessing import cpu_count
from chesster.core.uci_frontend import ChessterUciFrontend
from chesster.core.analyzer import ChessterAnalyzer

parser = argparse.ArgumentParser(
    description='Analyze and annotate games provided by a PGN file.')
parser.add_argument('-i', metavar='<INPUT-FILE>',
                    help='Input PGN file.')
parser.add_argument('-o', metavar='<OUTPUT-DIR>',
                    help='PGN output folder.')
parser.add_argument('-t', metavar='<T_MS>', default=5000,
                    help='Engine time per move in ms (default: 5000).')
parser.add_argument('-r', metavar='<PATTERN_FILE>', default=None,
                    help='Engine time per move in ms (default: 5000).')
parser.add_argument('-p', action='store_true',
                    help='Generate playbook with all games.')
parser.add_argument('-d', action='store_true', help='Delete source file.')
parser.add_argument('-v', action='store_true',
                    help='Verbose output.')
args = parser.parse_args()
if not args.i:
    print('No input file set.')
    parser.print_help()
    exit()
if not args.o:
    args.o = path.dirname(args.i)

setup_logging(args.v)

chesster_server = ChessterUciFrontend()
try:
    options = {
        'setoption name Hash value 32',
        'setoption name Threads value {}'.format(cpu_count()),
        'setoption name Skill Level value 20',
    }
    chesster_server.init_engine(options)
    chesster_analyser = ChessterAnalyzer(chesster_server)
    chesster_analyser.analyze(args.i, args.o, args.t, args.p, args.d, args.r)
except KeyboardInterrupt:
    print('Aborted.')
finally:
    chesster_server.shutdown()
