import logging
from os import makedirs, listdir, rename, remove
from os import path
import re 
from shutil import copy
from time import time

from Chessnut import Game
from dateutil.parser import parse
from tabulate import tabulate

from chesster.core.externals import get_cmd_process
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
                create_playbook, delete_source):
        
        keep_temp_files=False # dev
        
        pgn_in_file, pgn_out_folder = self._verify_io_settings(pgn_in_file, pgn_out_folder)
                
        analysis_input_files = []
        analysis_output_files = []
        now = time()
        
        # split PGN into single files 
        logging.info('-- splitting input file..')
        cmd = ('{0} {1} -#1'
               .format(self.server.pgn_extract_path, pgn_in_file))
        p = get_cmd_process(cmd, pgn_out_folder, stdin=None, stdout=None)
        p.wait()
        
        # rename input files 
        for name in listdir(pgn_out_folder):
            old_name = path.join(pgn_out_folder, name)
            if path.isdir(old_name):
                continue
            pattern = re.compile('[0-9]+\\.pgn')
            if not pattern.match(name):
                continue
            modts = max(path.getmtime(old_name), path.getctime(old_name))
            modified = True if modts > now else False
            if not modified:  # only work with newly created files 
                continue 
            logging.debug('{} {} = {}'.format(modified, name, modts)) 
            basename = path.basename(name)
            basename = re.sub('\\.pgn$', '', basename)
            new_name = path.join(pgn_out_folder, basename.zfill(5) + '_01_split.pgn')
            self._remove_silent(new_name) 
            rename(old_name, new_name)
            analysis_input_files.append(new_name)
        
        # analyze games 
        analysis_input_files.sort()
        for analysis_input_file in analysis_input_files:
            file_out = self._do_game_analysis(analysis_input_file, pgn_out_folder, engine_movetime)
            analysis_output_files.append(file_out)
        
        if create_playbook:
            self._create_playbook(analysis_output_files, pgn_out_folder)
        
        # cleanup
        if not keep_temp_files:
            for temporary_file in self.temporary_files:
                self._remove_silent(temporary_file)
                
        for analysis_output_file in analysis_output_files:
            game_id = path.basename(analysis_output_file).split('_')[0]
            to_name = path.join(pgn_out_folder,
                                self._get_filesafe_game_string(game_id))
            logging.info('{} <<< {}'
                         .format(to_name, analysis_output_file))
            self._remove_silent(to_name)
            rename(analysis_output_file, to_name)

        if delete_source:
            self._remove_silent(pgn_in_file)

    def _verify_io_settings(self, pgn_in_file, pgn_out_folder):
        if pgn_in_file == None:
            raise IOError( 'pgn_in_file cannot be None.')
        if pgn_out_folder == None:
            raise IOError( 'pgn_out_folder cannot be None.')
        pgn_in_file = path.abspath(pgn_in_file)
        pgn_out_folder = path.abspath(pgn_out_folder)
        try:
            with open(pgn_in_file):
                pass
        except IOError:
            raise IOError( 'pgn_in_file \'{}\' does not exist!'.format(pgn_in_file))
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
   
    def _do_game_analysis(self, pgn_in_file, pgn_out_folder, engine_movetime):

        self.temporary_files.append(pgn_in_file)
        game_id = path.basename(pgn_in_file)
        game_id = re.sub('_01_split\\.pgn$', '', game_id)

        chessgame, moves, result, _ = self._extract_chessgame(pgn_in_file)
        file_annotated_game, positions = self._annotate_game(chessgame, moves, game_id, pgn_out_folder, result, engine_movetime)
        self.temporary_files.append(file_annotated_game)
        file_fixed_tags, fixed_tags = self._extract_fixed_tags(pgn_in_file, pgn_out_folder, game_id, positions)
        self.temporary_files.append(file_fixed_tags)
        game_tags_for_id = self._extract_dict_from_tags(fixed_tags)
        self.game_tags[game_id] = game_tags_for_id
        file_merged = self._merge_tags_and_annotations(file_fixed_tags, file_annotated_game, pgn_out_folder, game_id)
        self.temporary_files.append(file_merged)
        file_fin = self._create_output_format(file_merged, pgn_out_folder, game_id)
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
        ofile = open (path.join(pgn_out_folder, self.playbook_name), 'w')
        pgn_files = sorted(pgn_files, cmp=self._compare_output_files)
        for pgn_file in pgn_files:
            ifile = open (pgn_file)
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
        p = get_cmd_process(cmd, stdout=None)
        p.wait() 
        
        return file_fin

    def _merge_tags_and_annotations(self, file_fixed_tags, file_annotated_game, pgn_out_folder, game_id):
        ofile = open (path.join(pgn_out_folder, game_id + '_04_merged.pgn'), 'w')
        # write  tags
        ifile = open (path.join(pgn_out_folder, file_fixed_tags))
        for line in ifile:
            ofile.write(line.strip() + '\n')
        ifile.close()
        # write annotations
        ifile = open (path.join(pgn_out_folder, file_annotated_game))
        for line in ifile:
            ofile.write(line.strip() + '\n')
        ifile.close()  
        ofile.close()
        return ofile.name

    def _annotate_game(self, chessgame, moves, game_id, pgn_out_folder, result, engine_movetime):
        logging.info('-- analysing game #{0}'.format(game_id))

        use_engine = True # debug
        # analyze game through engine 
        positions = []
        move_idx = 0
        
        # go through fen history and collect engine calculation
        for fen in chessgame.fen_history:
            try:
                move = moves[move_idx]
            except IndexError:
                move = None
            logging.debug('   -- analyze move \'{}\' on fen \'{}\''.format(move, fen))
            last_info = ''
            if use_engine:
                self.server.eval_uci('position fen {0}'.format(fen))
                output = self.server.eval_uci('go movetime {}'.format(engine_movetime))
                for out in output:  
                    if out and 'info' in out and 'score' in out:
                        last_info = out
            position = Position(fen, move, last_info)
            positions.append(position)
            move_idx += 1
        
        # go reversed through positions and compare/annotate 
        next_position = None
        for position in reversed(positions):
            position.annotate(next_position)
            next_position = position
        
        debug_headers = []
        debug_positions = []
        for position in positions:
            data, debug_headers = position.get_info_string()
            debug_positions.append(data)
        logging.debug(tabulate(debug_positions, debug_headers, tablefmt='psql'))
 
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
                bestline = filter(None, position.best_line.split(' '))
                game_annotation.append('( {0} ) '.format(' '.join(bestline[0:3])))
        game_annotation.append(result)
        
        logging.info('-- game annotation for game #{}:\n{}'.format(game_id,
                                                ''.join(game_annotation)))
        
        ofile = open (path.join(pgn_out_folder, game_id + '_02_annotated.pgn'), 'w')
        ofile.write(''.join(game_annotation) + '\n')
        ofile.close()
        return ofile.name, positions

    def _extract_fixed_tags(self, pgn_in_file, pgn_out_folder, game_id, positions):
                
        # read existing tags 
        cmd = ('{} {} -s -e{}'.format(self.server.pgn_extract_path,
                pgn_in_file, self.server.pgn_extract_eco))
        p = get_cmd_process(cmd, stdin=None)
        fixed_tags = []
        for line in p.stdout.readlines():
            line = line.strip()
            if line and line.startswith('[') and \
            not line.startswith('[%') and not 'Analyze This' in line:
                fixed_tags.append(self._fix_tag(line))
                
        fixed_tags = self._append_chesster_specific_tags(fixed_tags, positions)
        fixed_tags = sorted(fixed_tags, cmp=self._compare_tags)

        logging.info('-- writing tags for game #{}'.format(game_id))  
        ofile = open (path.join(pgn_out_folder, game_id + '_03_tagfix.pgn'), 'w')
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
        tags.append(get_pgn_tag_string(ChessterTagSet.MISTAKES, '{}/{}'.format(w_mis, b_mis)))
        tags.append(get_pgn_tag_string(ChessterTagSet.BLUNDERS, '{}/{}'.format(w_blun, b_blun)))
        tags.append(get_pgn_tag_string(ChessterTagSet.BEST_POSITIONS, '{}/{}'.format(w_bestpos, b_bestpos)))
        return tags

    def _get_better_position (self, curr_bestpos, new_bestpos, calc_for_white, white_move=None):
        result = None
        if 'M0' == str(new_bestpos):  # corner-case: one player mated   
            if calc_for_white == white_move:
                result = 'M0'
            else:
                result = str(curr_bestpos)
        else:
            cp1 = float(re.sub('M', '', curr_bestpos)) * 10000.0 if 'M' in str(curr_bestpos) else float(curr_bestpos)
            cp2 = float(re.sub('M', '', new_bestpos)) * 10000.0  if 'M' in str(new_bestpos) else float(new_bestpos)
            # on two mates flip comparison because mate in 1 is better than mate in 2
            two_mates = True if ('M' in str(curr_bestpos) and 'M' in str(new_bestpos)) else False
            calc_for_white = not calc_for_white if two_mates else calc_for_white
            selection = max (cp1, cp2) if calc_for_white else min(cp1, cp2)
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
                'whiteelo': 12, 'blackelo': 13, 'chessterts': 14 }
        order = append_chesster_tagset_ordered(order)
        if not tag:
            return 99
        try:
            return order[tag] 
        except KeyError:
            return 99
        
    def _fix_tag(self, tag):
        
        # apply search replace patterns from file
        pattern_file = None
        pattern_file_path = path.join(self.script_path, 
                                      'tag_replace_patterns.properties')
        try:
            pattern_file = open(pattern_file_path)
        except IOError:
            copy(pattern_file_path + '.default', pattern_file_path)
            pattern_file = open(pattern_file_path)
        for pattern_line in pattern_file:
            pattern_line = pattern_line.strip()
            search_replace = pattern_line.split('=')
            if len(search_replace) != 2:
                continue
            print search_replace
            re.sub(search_replace[0], search_replace[1], tag, re.IGNORECASE)
        
        # Normalize date 
        if '[Date' in tag:
            _, value = self._pgn_tag_to_keyvalue(tag)
            date_obj = parse(value)
            tag = '[Date "{}.{}.{}]"'.format(date_obj.year, 
                    str(date_obj.month).zfill(2), str(date_obj.day).zfill(2))
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
        p = get_cmd_process(cmd)
        moves = re.sub('[\r\n]+', ' ', ''.join(p.stdout.readlines()))
        moves = filter(self._filter_move, moves.split(' '))
        result = moves[-1]
        del moves[-1]    
        for i in range(0, len(moves)):
            chessgame.apply_move(moves[i])
        # extract existing comments 
        comments= {}
        # TODO 
        return chessgame, moves, result, comments
    
    def _remove_silent(self, path):
        try:
            remove(path)
        except OSError:
            pass  # catch if file does not exist

# TESTING PURPOSES
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    analyzer = ChessterAnalyzer(None)
    assert analyzer._get_better_position(-1.0, 1.0, True) == '1.0'
    assert analyzer._get_better_position(1.0, -1.0, True) == '1.0'
    assert analyzer._get_better_position(-1.0, 1.0, False) == '-1.0'
    assert analyzer._get_better_position(1.0, -1.0, False) == '-1.0'
    assert analyzer._get_better_position(1.0, 1.0, True) == '1.0'
    assert analyzer._get_better_position(1.0, 1.0, False) == '1.0'
    assert analyzer._get_better_position(0.0, 0.0, True) == '0.0'
    assert analyzer._get_better_position(0.0, 0.0, False) == '0.0'
    assert analyzer._get_better_position(0.0, 'M1', True) == 'M1'
    assert analyzer._get_better_position('M1', 0.0, True) == 'M1'
    assert analyzer._get_better_position(0.0, 'M-1', True) == '0.0'
    assert analyzer._get_better_position(0.0, 'M1', False) == '0.0'
    assert analyzer._get_better_position(0.0, 'M-1', False) == 'M-1'
    assert analyzer._get_better_position('M1', 'M3', True) == 'M1'
    assert analyzer._get_better_position('M1', 'M3', False) == 'M3'
    assert analyzer._get_better_position('M1', 'M0', True, True) == 'M0'
    assert analyzer._get_better_position('M-1', 'M0', False, True) == 'M-1'
    assert analyzer._get_better_position('M1', 'M0', True, False) == 'M1'
    assert analyzer._get_better_position('M-1', 'M0', False, False) == 'M0'
    assert analyzer._get_better_position(0.05, 'M0', True, True) == 'M0'
    assert analyzer._get_better_position(0.05, 'M0', True, False) == '0.05'
    assert analyzer._get_better_position(0.05, 'M0', False, True) == '0.05'
    assert analyzer._get_better_position(0.05, 'M0', False, False) == 'M0'
    
    
