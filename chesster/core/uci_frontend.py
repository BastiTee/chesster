import logging
from os import path
from threading import Thread, Lock
from time import sleep
from bptbx.b_cmdline import get_command_process, get_platform
from chesster.core.position import Position


class ChessterUciFrontend:
    """Core UCI frontend"""
    
    script_path = path.dirname(path.realpath(__file__))
    """Path to this Python script"""
    engine_proc = None
    """Subprocess for the underlying engine"""    
    engine_path = None
    """Path to engine binary"""
    pgn_extract_path = None
    """Path to pgn extract binary"""   
    pgn_extract_eco = None
    """Path to pgn extract opening book"""
    output = []
    """A shared container for the engine's output"""
    no_response_coms = ['position', 'setoption', 'ucinewgame', 'quit' ]
    """Uci commands that don't require evaluating the response"""
    lock = Lock()
    """Re-entrance lock for core engine operations"""
    signal = False
    """Signal that engine is finished operating"""
    
    def __init__(self):
        parent_dir = path.dirname(self.script_path)
        platform_type = get_platform()
        logging.debug('Platform type is {}'.format(platform_type))
        if 'windows' in platform_type or 'cygwin' in platform_type:
            self.engine_path = path.join(parent_dir, 
                                    'stockfish/stockfish-7-x64-win.exe')
            self.pgn_extract_path = path.join(parent_dir, 
                                    'pgnextract/pgn-extract-17-21-win.exe')
        elif 'linux' in get_platform():
            # assumed to be preinstalled 
            self.engine_path = 'stockfish'
            self.pgn_extract_path = path.join(parent_dir, 
                                    'pgnextract/pgn-extract-17-21-pi')
        self.pgn_extract_eco = path.join(parent_dir, 'pgnextract/eco.pgn')
        self.engine_proc = get_command_process(self.engine_path)
        engine_thread = Thread(target=self._handle_engine_output)
        engine_thread.start()
    
    def init_engine(self, options={}):
        self.eval_uci('uci')
        for option in options:
            self.eval_uci(option)
        self.eval_uci('isready')    
        
    def eval_uci(self, uci_string):
        if uci_string is None:
            return 'Nothing to do.'
        uci_string = uci_string.strip()
        uci_com = uci_string.split(' ')[0]
        if any(uci_com in s for s in self.no_response_coms):
            self._eval_uci_async(uci_string)
            return { 'Ok.' }
        else:
            return self._eval_uci_sync(uci_string)
    
    def eval_position(self, fen_string, ttm):
        output = []
        fen_string = fen_string.strip()
        output.append(fen_string)
        position = Position(fen_string)
        output.append(position.fen_to_string_board())
        self._eval_uci_async('setoption name Hash value 32')
        self._eval_uci_async('setoption name Threads value 2')
        self._eval_uci_async('setoption name Skill Level value 20')
        self._eval_uci_async('setoption name MultiPV value 3')
        self._eval_uci_async('position fen {0}'.format(fen_string))
        uciout = self._eval_uci_sync('go movetime {0}'.format(ttm))
        output.append(self._get_last_entry_for_pattern(uciout, 'multipv 1'))
        output.append(self._get_last_entry_for_pattern(uciout, 'multipv 2'))
        output.append(self._get_last_entry_for_pattern(uciout, 'multipv 3'))
        return output
    
    def bestmove(self, fen_string, ttm):
        fen_string = fen_string.strip()
        self._eval_uci_async('position fen {0}'.format(fen_string))
        output = self._eval_uci_sync('go movetime {0}'.format(ttm))
        for line in output:
            if 'bestmove' in line:
                return { line.split(' ')[1] }
        
    def shutdown(self):
        self.engine_proc.kill()
    
    def _eval_uci_sync(self, command):
        self.lock.acquire()
        try:
#             logging.debug('[ENGINE] [IN] {0}'.format(command))
            self.engine_proc.stdin.write(command + '\n')
            self.engine_proc.stdin.flush()
            while self.signal == False:
                sleep(0.1)
            uci_engine_output = self.output
            self.output = []
            self.signal = False
            return uci_engine_output
        finally:
            self.lock.release()
    
    def _eval_uci_async(self, command):
        self.lock.acquire()
        try:
#             logging.debug('[ENGINE] [IN] {0}'.format(command))
            self.engine_proc.stdin.write(command + '\n')
            self.engine_proc.stdin.flush()
        finally:
            self.lock.release()
    
    def _get_last_entry_for_pattern(self, entries, pattern):
        last_entry = None
        for entry in entries:
            if pattern in entry:
                last_entry = entry
        return last_entry
        
    def _handle_engine_output(self):
        while True and self.engine_proc.poll() is None:
            line = self.engine_proc.stdout.readline().strip()
            self.output.append(line)
#             if line:
#                 logging.debug('[ENGINE] [OU] {0}'.format(line))
            if 'uciok' in line or 'bestmove' in line or 'readyok' in line:
                self.signal = True
