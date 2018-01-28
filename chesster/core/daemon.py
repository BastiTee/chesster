import logging
from multiprocessing import cpu_count
from os import path, listdir
from chesster.core.uci_frontend import ChessterUciFrontend
from chesster.core.analyzer import ChessterAnalyzer
from bptbx.b_iotools import read_file_to_list, write_list_to_file
from bptbx.b_daemon import Daemon


class ChessterDaemon(Daemon):

    workdir = None
    log_filepath = None
    time_to_think = 5000
    options = {
        'setoption name Hash value 32',
        'setoption name Threads value {}'.format(cpu_count()),
        'setoption name Skill Level value 20',
    }

    def configure_daemon(self, workdir, time_to_think, pattern_file):
        self.workdir = path.abspath(workdir)
        self.log_filepath = path.join(workdir, '.chesster_server')
        self.time_to_think = time_to_think
        self.pattern_file = pattern_file

    def _run_daemon_process(self):
        logging.info('========== ChessterDaemon started processing')
        chesster_server = ChessterUciFrontend()
        chesster_server.init_engine(self.options)
        for name in listdir(self.workdir):
            already_processed = read_file_to_list(self.log_filepath, True)
            file_path = path.join(self.workdir, name)
            if path.isdir(file_path) or not file_path.endswith('.pgn'):
                continue
            if file_path in already_processed:
                logging.info(
                    'File \'{}\' processed before according to log list.'
                    .format(file_path))
                continue
            content = read_file_to_list(file_path)
            tag_found = False
            for line in content:
                if 'ChessterAnalysisTs' in line:
                    logging.info(
                        'File \'{}\' processed before according to tags.'
                        .format(file_path))
                    tag_found = True
            if tag_found:
                continue
            chesster_analyzer = ChessterAnalyzer(chesster_server)
            chesster_analyzer.analyze(
                file_path, self.workdir, self.time_to_think, False, False,
                self.pattern_file)
            already_processed.append(file_path)
            write_list_to_file(already_processed, self.log_filepath)

        chesster_server.shutdown()
        logging.info('========== ChessterDaemon finished processing')
