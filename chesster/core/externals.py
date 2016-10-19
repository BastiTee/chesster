import logging
from os import path
from b_cmdline import get_platform

def get_stockfish_path():
    if 'windows' in get_platform():
        return path.join(script_path, 'stockfish/stockfish-7-x64-win.exe')
    elif 'linux' in get_platform():
        # assumed to be preinstalled
        return 'stockfish'
    return None

def get_pgn_extract_path():
    if 'windows' in get_platform():
        return path.join(script_path, 'pgnextract/pgn-extract-17-21-win.exe')
    elif 'linux' in get_platform():
        return path.join(script_path, 'pgnextract/pgn-extract-17-21-pi')
    return None

def get_pgn_extract_opening_book():
    return path.join(script_path, 'pgnextract/eco.pgn')
