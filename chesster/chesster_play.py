#!/usr/bin/python
import argparse
parser = argparse.ArgumentParser(
        description='A command-line chess UI to play against Stockfish.')
parser.add_argument('-b', action='store_true',
        help='Play as black.')
parser.add_argument('-v', action='store_true',
        help='Verbose output.')
parser.add_argument('-l', metavar='<LEVEL>', default=1,
        help='Engine level (1-20).')
args = parser.parse_args()

from bptbx.b_logging import setup_logging
from bptbx import b_legacy
setup_logging(args.v)

from Chessnut import Game
from Chessnut.game import InvalidMove
from chesster.core.position import Position
from chesster.core.uci_frontend import ChessterUciFrontend

uci_frontend = ChessterUciFrontend()
chessgame = Game()
options = {
           'setoption name Skill Level value {}'.format(args.l),
           'setoption name Hash value 32',
           'setoption name Threads value 2'
        }
uci_frontend.init_engine(options)
print (Position(chessgame.get_fen()).fen_to_string_board())

while True:
    if not args.b: # if user plays black, skip first user move
        # get move from user
        while True:
            print ('-- Your move: ')
            try:
                raw = b_legacy.b_raw_input().strip()
            except KeyboardInterrupt:
                print ('Goodbye!')
                exit(0)
            if raw is None or raw == '':
                print ('Invalid input! Please try again.')
            try:
                chessgame.apply_move(raw)
                print (Position(chessgame.get_fen()).fen_to_string_board())
                break
            except InvalidMove as e:
                print ('{0}'.format(e.message))

    args.b = False

    # get move from engine
    print ('-- Waiting for engine move')
    engine_move = uci_frontend.bestmove(chessgame.get_fen(), 2500).pop()
    print ('-- Engine played {0}'.format(engine_move))
    chessgame.apply_move(engine_move)
    print (Position(str(chessgame)).fen_to_string_board())
