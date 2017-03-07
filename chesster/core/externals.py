import logging
from os import path
from bptbx.b_cmdline import get_platform, check_for_command


def _get_basedir():
    return path.dirname(path.dirname(path.realpath(__file__)))


def get_stockfish_path():
    sys_platform = get_platform()
    if 'windows' in sys_platform:
        return path.join(_get_basedir(), 'stockfish', 'stockfish-7-x64-win.exe')
    elif 'linux' in sys_platform:
        is_available = check_for_command('stockfish', ['uci'])
        if not is_available:
            logging.error('Engine not present. ' +
                          'You need to install stockfish first!')
            exit(1)
        return 'stockfish'
    else:
        logging.error('Unsupported platform. Please code it first :)')
        exit(1)


def get_pgn_extract_path():

    sys_platform = get_platform()
    if 'windows' in sys_platform:
        return path.join(_get_basedir(),
                         'pgnextract', 'pgn-extract-17-21-win.exe')
    elif 'linux' in sys_platform:
        is_available = check_for_command('pgn-extract', ['--version'])
        if not is_available:
            logging.error('pgn-extract not present. ' +
                          'You need to install pgn-extract first!')
            exit(1)
        return 'pgn-extract'
    return None


def get_pgn_extract_opening_book():
    return path.join(_get_basedir(), 'pgnextract', 'eco.pgn')
