import logging
from os import devnull
from os import path
from os.path import dirname
from platform import system
from subprocess import Popen, PIPE


script_path = path.dirname(dirname(path.realpath(__file__)))
"""Path to this Python script"""
    
def get_stockfish_path():
    if 'windows' in _get_platform():
        return path.join(script_path, 'stockfish/stockfish-7-x64-win.exe')
    elif 'linux' in _get_platform():
        # assumed to be preinstalled 
        return 'stockfish'
    return None
        
def get_pgn_extract_path():
    if 'windows' in _get_platform():
        return path.join(script_path, 'pgnextract/pgn-extract-17-21-win.exe')
    elif 'linux' in _get_platform():
        return path.join(script_path, 'pgnextract/pgn-extract-17-21-pi')
    return None

def get_pgn_extract_opening_book():
    return path.join(script_path, 'pgnextract/eco.pgn')
  
def get_cmd_process(command, cwd=None, stdin=PIPE, stdout=PIPE):            
    logging.debug('Invoking: {}'.format(command))
    shell = False
    if _get_platform() == 'linux':
        shell = True
    with open(devnull, 'w') as fp:
        if not stdin:
            stdin = fp
        if not stdout:
            stdout = fp
        return Popen(command, stdin=stdin, stdout=stdout, stderr=stdout,
                     cwd=cwd, shell=shell)

def _get_platform():
    platform = str(system()).lower()
    return platform    
