#!/usr/bin/python
import argparse
import logging
from multiprocessing import cpu_count
from os import path
from chesster.core.uci_frontend import ChessterUciFrontend    

parser = argparse.ArgumentParser(description='Analyze PGN games')
parser.add_argument('-i', metavar='<INPUT-FILE>', help='Input PGN file.')
parser.add_argument('-o', metavar='<OUTPUT-DIR>', help='PGN output folder.')
parser.add_argument('-t', metavar='<T_MS>', help='Engine time per move in ms'
                    + ' (default: 5000).')
parser.add_argument('-p', action='store_true', help='Generate playbook with all games.')
parser.add_argument('-d', action='store_true', help='Delete source file.')
parser.add_argument('-v', action='store_true', help='Verbose output.')
args = parser.parse_args()

if args.i == None:
    print 'No input file set.'
    parser.print_help()
    exit()
    
if args.o == None:
    args.o = path.dirname(args.i)

if args.t == None:
    args.t = 5000

if args.v:
    logging.basicConfig(level=logging.DEBUG, format='[%(levelname)s]\t%(message)s')
else:
    logging.basicConfig(level=logging.INFO, format='[%(levelname)s]\t%(message)s')

logging.info('\nin_file=\t{}\nout_dir=\t{}\nen_time=\t{}\nverbose=\t{}'.format(
        args.i, args.o, args.t, args.v))

chesster_server = ChessterUciFrontend()
try:                   
    options = { 
               'setoption name Hash value 32',
               'setoption name Threads value {}'.format(cpu_count()),
               'setoption name Skill Level value 20',
            }
    chesster_server.init_engine(options)
    chesster_server.analyse_games(args.i, args.o, args.t, args.p, args.d)
except KeyboardInterrupt:
    print 'Aborted.'
finally:
    chesster_server.shutdown()
