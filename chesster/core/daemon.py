import logging
from multiprocessing import cpu_count
from os import path, listdir
from threading import Lock, Thread
from time import sleep

from chesster.core.uci_frontend import ChessterUciFrontend


class ChessterDaemon:
    
    workdir = None
    interval = 30
    time_to_think = 5000
    stopped = False
    lock = Lock()
    daemon_locked = False
    
    def __init__(self, workdir, time_to_think, interval):
        self.workdir = path.abspath(workdir)
        self.interval = interval
        self.time_to_think = time_to_think

    def start(self):
        while not self.stopped:
            thr = Thread(target=self._run_process)
            thr.start()
            sleep(self.interval)
                    
    def stop(self):
        pass
    
    def _run_process(self):
        if self.daemon_locked:
            logging.debug('ChessterDaemon already processing')
            return
        self._lock_daemon()
        logging.debug('========== ChessterDaemon started processing')
        already_processed = []
        log_filepath = path.join(self.workdir, '.chesster_server')
        if path.exists(log_filepath):
            ofile = open (log_filepath)
            for line in ofile:
                already_processed.append(line.strip())
            ofile.close()
        
        chesster_server = ChessterUciFrontend()
        options = { 
           'setoption name Hash value 32',
           'setoption name Threads value {}'.format(cpu_count()),
           'setoption name Skill Level value 20',
        }
        chesster_server.init_engine(options)
        for name in listdir(self.workdir):
            file_path = path.join(self.workdir, name)
            if path.isdir(file_path) or not file_path.endswith('.pgn'):
                continue
            if self._analyzed_before(file_path, already_processed):
                logging.info('Processed before: {} '.format(name))
                continue
            chesster_server.analyse_games(file_path, self.workdir, self.time_to_think, 
                                   False, False)
            already_processed.append(file_path)
        chesster_server.shutdown()

        ofile = open (log_filepath, 'w')
        for item in already_processed:
            ofile.write(item + '\n')
        ofile.close()
        
        logging.debug('========== ChessterDaemon finished processing')
        
        self._unlock_daemon()

    def _lock_daemon(self):
        self.lock.acquire()
        self.daemon_locked = True
        self.lock.release()
    
    def _unlock_daemon(self):
        self.lock.acquire()
        self.daemon_locked = False
        self.lock.release()
    
    def _analyzed_before(self, pgn_file, already_processed):
        if pgn_file in already_processed:
            return True
        ofile = open (pgn_file, 'r')
        for line in ofile:
            if 'ChessterAnalysisTs' in line:                
                ofile.close()
                return True
        ofile.close()
        return False
