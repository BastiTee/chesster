import logging
from os import makedirs, listdir, rename
from os import path
import re
from shutil import copy
from time import time
from Chessnut import Game
from dateutil.parser import parse
from tabulate import tabulate
from bptbx.b_cmdline import get_command_process
from bptbx.b_iotools import remove_silent
from bptbx import b_legacy
from chesster.core.position import Position
from chesster.core.tagset import get_pgn_tag_string, ChessterTagSet, \
    append_chesster_tagset_ordered


class ChessterAnalyzer:

    script_path = path.dirname(path.realpath(__file__))
    """Path to this Python script"""
    server = None
    """Currently active Chesster server instance"""
    game_tags = {}
    """Maps the game id to the key/values of the game's tag information"""
    temporary_files = []
    """A list of all files created during analysis expect single game files"""
    playbook_name = '_full-playbook.pgn'
    """Name of output playbook file"""

    def __init__(self, server):
        self.server = server

    def analyze(self, pgn_in_file, pgn_out_folder, engine_movetime,
                create_playbook, delete_source, pattern_file=None):

        pattern_file = self._load_pattern_file(pattern_file)

        keep_temp_files = False  # dev

        pgn_in_file, pgn_out_folder = self._verify_io_settings(
            pgn_in_file, pgn_out_folder)

        analysis_input_files = []
        analysis_output_files = []

        # list current files
        curr_files = listdir(pgn_out_folder)

        # split PGN into single files
        logging.info('-- splitting input file..')
        cmd = ('{0} {1} -#1'
               .format(self.server.pgn_extract_path, pgn_in_file))
        p = get_command_process(cmd, pgn_out_folder, stdin=None, stdout=None)
        p.wait()

        # get new files
        new_files = list(filter(lambda x: x not in curr_files,
                                listdir(pgn_out_folder)))
        self.temporary_files += new_files

        # rename input files
        for name in new_files:
            old_name = path.join(pgn_out_folder, name)
            if path.isdir(old_name):
                continue
            pattern = re.compile('[0-9]+\\.pgn')
            if not pattern.match(name):
                continue
            basename = path.basename(name)
            basename = re.sub('\\.pgn$', '', basename)
            new_name = path.join(
                pgn_out_folder, basename.zfill(5) + '_01_split.pgn')
            remove_silent(new_name)
            rename(old_name, new_name)
            analysis_input_files.append(new_name)

        logging.info('-- analyzing games..')

        # analyze games
        analysis_input_files.sort()
        for analysis_input_file in analysis_input_files:
            file_out = self._do_game_analysis(
                analysis_input_file, pgn_out_folder, engine_movetime,
                pattern_file)
            analysis_output_files.append(file_out)

        if create_playbook:
            self._create_playbook(analysis_output_files, pgn_out_folder)

        logging.info('-- removing temporary files..')

        # cleanup
        if not keep_temp_files:
            for temporary_file in self.temporary_files:
                remove_silent(temporary_file)

        for analysis_output_file in analysis_output_files:
            game_id = path.basename(analysis_output_file).split('_')[0]
            to_name = path.join(pgn_out_folder,
                                self._get_filesafe_game_string(game_id))
            logging.info('{} <<< {}'
                         .format(to_name, analysis_output_file))
            remove_silent(to_name)
            rename(analysis_output_file, to_name)

        if delete_source:
            remove_silent(pgn_in_file)

        logging.info('-- done processing')

    def _verify_io_settings(self, pgn_in_file, pgn_out_folder):
        if pgn_in_file == None:
            raise IOError('pgn_in_file cannot be None.')
        if pgn_out_folder == None:
            raise IOError('pgn_out_folder cannot be None.')
        pgn_in_file = path.abspath(pgn_in_file)
        pgn_out_folder = path.abspath(pgn_out_folder)
        try:
            with open(pgn_in_file):
                pass
        except IOError:
            raise IOError(
                'pgn_in_file \'{}\' does not exist!'.format(pgn_in_file))
        if not path.exists(pgn_out_folder):
            makedirs(pgn_out_folder)
        return pgn_in_file, pgn_out_folder

    def _get_filesafe_game_string(self, game_id):
        tags = self.game_tags[game_id]
        filename = '{}_R{}_{}-{}_{}.pgn'.format(
            re.sub('\.', '', tags['date']),
            str(tags['round']).zfill(3),
            re.sub('[,\. ]', '', tags['white']),
            re.sub('[,\. ]', '', tags['black']),
            re.sub('1/2', '0.5', tags['result']),
        )
        return filename

    def _do_game_analysis(self, pgn_in_file, pgn_out_folder, engine_movetime,
                          pattern_file):

        self.temporary_files.append(pgn_in_file)
        game_id = path.basename(pgn_in_file)
        game_id = re.sub('_01_split\\.pgn$', '', game_id)

        chessgame, moves, result, _ = self._extract_chessgame(pgn_in_file)
        file_annotated_game, positions = self._annotate_game(
            chessgame, moves, game_id, pgn_out_folder, result, engine_movetime)
        self.temporary_files.append(file_annotated_game)
        file_fixed_tags, fixed_tags = self._extract_fixed_tags(
            pgn_in_file, pgn_out_folder, game_id, positions, pattern_file)
        self.temporary_files.append(file_fixed_tags)
        game_tags_for_id = self._extract_dict_from_tags(fixed_tags)
        self.game_tags[game_id] = game_tags_for_id
        file_merged = self._merge_tags_and_annotations(
            file_fixed_tags, file_annotated_game, pgn_out_folder, game_id)
        self.temporary_files.append(file_merged)
        file_fin = self._create_output_format(
            file_merged, pgn_out_folder, game_id)
        return file_fin

    def _pgn_tag_to_keyvalue(self, pgn_tag):
        tag_sub = re.sub('[\[\]]', '', pgn_tag)
        key = tag_sub.split(' ')[0].strip().lower()
        value = re.sub('\"', '', re.sub('^[^"]+\"', '', tag_sub)).strip()
        return key, value

    def _extract_dict_from_tags(self, tags):
        game_info = {}
        if not tags:
            return
        for tag in tags:
            key, value = self._pgn_tag_to_keyvalue(tag)
            game_info[key] = value
        return game_info

    def _create_playbook(self, pgn_files, pgn_out_folder):
        ofile = open(path.join(pgn_out_folder, self.playbook_name), 'w')
        pgn_files = b_legacy.b_sorted(
            pgn_files, cmp=self._compare_output_files)
        for pgn_file in pgn_files:
            ifile = open(pgn_file)
            for line in ifile:
                ofile.write(line.strip() + '\n')
            ifile.close()
            ofile.write('\n')
        ofile.close()

    def _compare_output_files(self, file1, file2):
        f1_game_id = path.basename(file1).split('_')[0]
        f2_game_id = path.basename(file2).split('_')[0]
        f1_date = self.game_tags[f1_game_id]['date']
        f2_date = self.game_tags[f2_game_id]['date']
        logging.debug('{} ({}) <<>> {} ({})'.format(f1_date, f1_game_id,
                                                    f2_date, f2_game_id))
        minv = min(f1_date, f2_date)
        if minv == f1_date:
            return 1
        elif minv == f2_date:
            return -1
        return 0

    def _create_output_format(self, file_merged, pgn_out_folder, game_id):
        file_fin = path.join(pgn_out_folder, game_id + '_05_fin.pgn')
        logging.info('-- creating output for game #{}'.format(game_id))
        cmd = ('{0} {1} -s --output {2}'
               .format(self.server.pgn_extract_path, path.join(pgn_out_folder, file_merged),
                       file_fin))
        p = get_command_process(cmd, stdout=None)
        p.wait()

        return file_fin

    def _merge_tags_and_annotations(self, file_fixed_tags, file_annotated_game, pgn_out_folder, game_id):
        ofile = open(path.join(pgn_out_folder,
                               game_id + '_04_merged.pgn'), 'w')
        # write  tags
        ifile = open(path.join(pgn_out_folder, file_fixed_tags))
        for line in ifile:
            ofile.write(line.strip() + '\n')
        ifile.close()
        # write annotations
        ifile = open(path.join(pgn_out_folder, file_annotated_game))
        for line in ifile:
            ofile.write(line.strip() + '\n')
        ifile.close()
        ofile.close()
        return ofile.name

    def _annotate_game(self, chessgame, moves, game_id, pgn_out_folder, result, engine_movetime):
        logging.info('-- analysing game #{0}'.format(game_id))

        use_engine = True  # debug
        # analyze game through engine
        positions = []
        move_idx = 0

        # go through fen history and collect engine calculation
        for fen in chessgame.fen_history:
            try:
                move = moves[move_idx]
            except IndexError:
                move = None
            logging.debug(
                '   -- analyze move \'{}\' on fen \'{}\''.format(move, fen))
            last_info = ''
            if use_engine:
                self.server.eval_uci('position fen {0}'.format(fen))
                output = self.server.eval_uci(
                    'go movetime {}'.format(engine_movetime))
                for out in output:
                    if out and 'info' in out and 'score' in out:
                        last_info = out
            position = Position(fen, move, last_info)
            positions.append(position)
            move_idx += 1

        # go reversed through positions and compare/annotate_position
        next_position = None
        for position in reversed(positions):
            position.annotate_position(next_position)
            next_position = position

        # DEBUG OUTPUT
        debug_headers = []
        debug_positions = []
        for position in positions:
            debug_string, debug_headers = position.get_debug_string()
            debug_positions.append(debug_string)
        logging.debug(tabulate(debug_positions,
                               debug_headers, tablefmt='psql'))

        game_annotation = []
        for position in positions:
            if not position.move_played:
                continue
            # append move and annotation
            game_annotation.append('{}{} '.format(
                position.move_played, position.annotation))
            if position.comment:
                game_annotation.append('{{ {0} }} '.format(position.comment))
            # on blunders append the full best line
            if position.annotation == '??':
                game_annotation.append('( {0} ) '.format(position.best_line))
            # on mistakes append the first three moves of the best line
            elif position.annotation == '?':
                bestline = b_legacy.b_filter(
                    None, position.best_line.split(' '))
                game_annotation.append(
                    '( {0} ) '.format(' '.join(bestline[0:3])))
        game_annotation.append(result)

        logging.info('-- game annotation for game #{}:\n{}'.format(game_id,
                                                                   ''.join(game_annotation)))

        ofile = open(path.join(pgn_out_folder,
                               game_id + '_02_annotated.pgn'), 'w')
        ofile.write(''.join(game_annotation) + '\n')
        ofile.close()
        return ofile.name, positions

    def _extract_fixed_tags(self, pgn_in_file, pgn_out_folder, game_id,
                            positions, pattern_file):

        # read existing tags
        cmd = ('{} {} -s -e{}'.format(
            self.server.pgn_extract_path, pgn_in_file,
            self.server.pgn_extract_eco))
        p = get_command_process(cmd, stdin=None)
        fixed_tags = []
        for line in p.stdout.readlines():
            # We need to decode the bytes from stdout when running on python 3
            if not b_legacy.get_python_major_version() <= 2:
                line = line.decode()
            line = line.strip()
            if line and line.startswith('[') and \
                    not line.startswith('[%') and 'Analyze This' not in line:
                fixed_tags.append(self._fix_tag(line, pattern_file))

        fixed_tags = self._append_chesster_specific_tags(fixed_tags, positions)
        fixed_tags = b_legacy.b_sorted(fixed_tags, cmp=self._compare_tags)

        logging.info('-- writing tags for game #{}'.format(game_id))
        ofile = open(path.join(pgn_out_folder,
                               game_id + '_03_tagfix.pgn'), 'w')
        for fixed_tag in fixed_tags:
            logging.debug('   {}'.format(fixed_tag))
            ofile.write(fixed_tag + '\n')
        ofile.close()
        return ofile.name, fixed_tags

    def _append_chesster_specific_tags(self, tags, positions):
        # analysis time
        timestamp = int(round(time() * 1000))
        tags.append(get_pgn_tag_string(ChessterTagSet.ANALYSIS_TS, timestamp))
        w_mis = b_mis = w_blun = b_blun = 0
        w_bestpos = -1000.0
        b_bestpos = 1000.0
        for position in positions:
            if position.white_move and position.annotation == '?':
                w_mis += 1
            elif not position.white_move and position.annotation == '?':
                b_mis += 1
            elif position.white_move and position.annotation == '??':
                w_blun += 1
            elif not position.white_move and position.annotation == '??':
                b_blun += 1
            w_bestpos = self._get_better_position(w_bestpos,
                                                  position.score_display, True, not position.white_move)
            b_bestpos = self._get_better_position(b_bestpos,
                                                  position.score_display, False, not position.white_move)
        tags.append(get_pgn_tag_string(
            ChessterTagSet.MISTAKES, '{}/{}'.format(w_mis, b_mis)))
        tags.append(get_pgn_tag_string(
            ChessterTagSet.BLUNDERS, '{}/{}'.format(w_blun, b_blun)))
        tags.append(get_pgn_tag_string(ChessterTagSet.BEST_POSITIONS,
                                       '{}/{}'.format(w_bestpos, b_bestpos)))
        return tags

    def _get_better_position(self, curr_bestpos, new_bestpos, calc_for_white, white_move=None):
        result = None
        if 'M0' == str(new_bestpos):  # corner-case: one player mated
            if calc_for_white == white_move:
                result = 'M0'
            else:
                result = str(curr_bestpos)
        else:
            cp1 = float(re.sub('M', '', curr_bestpos)) * \
                10000.0 if 'M' in str(curr_bestpos) else float(curr_bestpos)
            cp2 = float(re.sub('M', '', new_bestpos)) * \
                10000.0 if 'M' in str(new_bestpos) else float(new_bestpos)
            # on two mates flip comparison because mate in 1 is better than
            # mate in 2
            two_mates = True if ('M' in str(curr_bestpos)
                                 and 'M' in str(new_bestpos)) else False
            calc_for_white = not calc_for_white if two_mates else calc_for_white
            selection = max(cp1, cp2) if calc_for_white else min(cp1, cp2)
            result = curr_bestpos if cp1 == selection else new_bestpos
        logging.debug('[{}/{}move] CURR = {} NEW = {} >> {}'.format(
            'W' if calc_for_white else 'B', 'W' if white_move else 'B',
            curr_bestpos, new_bestpos, result))
        return str(result)

    def _compare_tags(self, tag1, tag2):
        tag1 = re.sub('[\[\]]', '', tag1).split(' ')[0]
        tag2 = re.sub('[\[\]]', '', tag2).split(' ')[0]
        tag1_rank = self._get_tag_rank(tag1)
        tag2_rank = self._get_tag_rank(tag2)
        compare_val = tag1_rank - tag2_rank
        return compare_val

    def _get_tag_rank(self, tag):
        tag = tag.lower()
        order = {
            'event': 0, 'site': 1, 'date': 2, 'round': 3, 'white': 4,
            'black': 5, 'result': 6, 'eco': 7, 'opening': 8,
            'variation': 9, 'timecontrol': 10, 'termination': 11,
            'whiteelo': 12, 'blackelo': 13, 'chessterts': 14}
        order = append_chesster_tagset_ordered(order)
        if not tag:
            return 99
        try:
            return order[tag]
        except KeyError:
            return 99

    def _load_file_or_none(self, filepath):
        if not filepath:
            return None
        try:
            return open(filepath)
        except IOError:
            return None

    def _load_pattern_file(self, pattern_file):
        logging.info('-- received ext patterns: {}'.format(pattern_file))
        # if external file provided and readable, return first...
        pattern_fh = self._load_file_or_none(pattern_file)
        if pattern_fh:
            logging.info('-- loading ext patterns from {}'
                         .format(pattern_file))
            return pattern_fh
        # try to load copy from internal default file...
        pattern_file = path.join(
            self.script_path, 'tag_replace_patterns.properties')
        pattern_fh = self._load_file_or_none(pattern_file)
        if pattern_fh:
            logging.info('-- loading from-def patterns from {}'
                         .format(pattern_file))
            return pattern_fh
        # copy from default and load default set
        copy(pattern_file + '.default', pattern_file)
        pattern_fh = self._load_file_or_none(pattern_file)
        if pattern_fh:
            logging.info('-- loading def patterns from {}'
                         .format(pattern_file))
            return pattern_fh
        return None

    def _fix_tag(self, tag, pattern_file):
        pattern_file.seek(0)
        for pattern_line in pattern_file:
            pattern_line = pattern_line.strip()
            search_replace = pattern_line.split('=')
            if len(search_replace) != 2:
                continue
            tag = re.sub(search_replace[0], search_replace[
                         1], tag, re.IGNORECASE)

        # Normalize date
        if '[Date' in tag:
            _, value = self._pgn_tag_to_keyvalue(tag)
            date_obj = parse(value)
            tag = '[Date "{}.{}.{}]"'.format(
                date_obj.year, str(date_obj.month).zfill(2),
                str(date_obj.day).zfill(2))
        return tag

    def _filter_move(self, move):
        if move is None or len(move) == 0:
            return False
        if '$' in move:
            return False
        return True

    def _extract_chessgame(self, pgn_in_file):
        # get game model
        chessgame = Game()
        cmd = ('{0} {1} -Wlalg --nomovenumbers --nocomments --nochecks -V --notags -s'
               .format(self.server.pgn_extract_path, pgn_in_file))
        p = get_command_process(cmd)
        stdout_content = p.stdout.readlines()
        # We need to decode the bytes from stdout when running on python 3
        if not b_legacy.get_python_major_version() <= 2:
            temp = []
            for stdout_line in stdout_content:
                temp.append(stdout_line.decode())
            stdout_content = temp
        stdout_content = ''.join(stdout_content)
        moves = re.sub('[\r\n]+', ' ', stdout_content)
        moves = b_legacy.b_filter(self._filter_move, moves.split(' '))
        result = moves[-1]
        del moves[-1]
        for i in range(0, len(moves)):
            chessgame.apply_move(moves[i])
        # extract existing comments
        comments = {}
        # TODO
        return chessgame, moves, result, comments
