import re

class Position:
    
    fen_string = None
    engine_info = None    
    white_move = None
    score_original = None
    score_display = 0.0
    move_number = None
    best_line = None
    move_played = None
    score_change = None
    annotation = ''
    comment = ''
    
    def __init__(self, fen_string, move_played=None, engine_info=None):
        self.fen_string = str(fen_string)
        if move_played is not None:
            self.move_played = str(move_played)
        if engine_info is not None:
            self.engine_info = str(engine_info)
        self._extract_information()
    
    def annotate_position(self, next_position):
        # get score change due to move 
        if (next_position == None or 
             next_position.score_display == None):
            self.score_change = '-'
        else:
            self.score_change = self._get_score_change(
                self.score_display, next_position.score_display) 
        if self.score_change == None or self.score_change == '-':
            return
        if self.score_change == 'CM':
            self.annotation = '?'
            self.comment = 'Mate set up'
        elif self.score_change == 'MM':
            self.annotation = '?'
            self.comment = 'Missed mate'
        elif 'M' in str(self.score_change):
            return
        elif ((self.score_change >= 1.0 and not self.white_move) or 
            (self.score_change <= -1.0 and self.white_move)):
            self.annotation = '??'
            self.comment = 'Blunder {}/{}'.format(self.score_display,
                                                    next_position.score_display)
        elif ((self.score_change >= 0.5 and not self.white_move) or 
            (self.score_change <= -0.5 and self.white_move)):
            self.annotation = '?'
            self.comment = 'Mistake {}/{}'.format(self.score_display,
                                                    next_position.score_display)
            
    def fen_to_string_board(self):
        unicode_board = []
        unicode_board.append('\n')
        unicode_board.append('    a b c d e f g h\n')
        unicode_board.append('  /-----------------\\\n')
        row_count = 8
        positions = self.fen_string.split(' ')[0]
        for row in positions.split('/'):
            unicode_board.append('{0} |'.format(row_count),)
            for col in row:
                try: 
                    col_int = int(col)
                    for _ in range(col_int):
                        unicode_board.append(' _',)
                except ValueError:
                    unicode_board.append(' ' + col)
            unicode_board.append(' |{0}\n'.format(row_count))
            row_count -= 1
        unicode_board.append('  \-----------------/\n')
        unicode_board.append('    a b c d e f g h\n')
        unicode_board.append('\n')
        return ''.join(unicode_board)

    def get_debug_string(self):
        player = 'White'
        if not self.white_move:
            player = 'Black'
        if not self.best_line:
            self.best_line = ''
        headers = [ 'm#', 'player', 'move', 'eval', 'diff', 'anno', 
                   'comm', 'best_line_short' ]
        pos_data = [ self.move_number, player, self.move_played, 
                    self.score_display, self.score_change, self.annotation, 
                    self.comment, self.best_line[:10] ]
        return pos_data, headers

    def _extract_information(self):
        if not self.engine_info:
            return
        # extract moving player
        if self.fen_string.split(' ')[1] == 'w':
            self.white_move = True
        else:
            self.white_move = False
        # extract move number
        try:
            self.move_number = self.fen_string.split(' ')[5]
        except IndexError:
            pass
        if self.engine_info is None:
            return
        # get position score 
        self.score_original = self._get_engine_info_or_none(
                'score[ ]+(cp|mate)[ ]+-?\d+[ ]?(lowerbound|upperbound)?')
        self._convert_original_score()
        # get best line 
        self.best_line = self._get_engine_info_or_none(
                                            ' pv([ ]+[abcdefgh12345678]+)+')
        
    def _get_score_change(self, this_score, next_score):
        if 'M' in str(this_score) or 'M' in str(next_score):
            if not 'M' in str(this_score) and 'M' in str(next_score):
                return 'CM'
            if 'M' in str(this_score) and not 'M' in str(next_score):
                return 'MM'
            return '{0}M'.format(int(re.sub('M', '', 
                    str(next_score))) - int(re.sub('M', '', str(this_score))))  
        return next_score - this_score 
    
    def _convert_original_score(self):
        score_type = self.score_original.split(' ')[0].strip()
        score_num = float(self.score_original.split(' ')[1].strip())
        if score_type == 'mate':
            if not self.white_move:
                score_num = -1.0 * score_num
            score_num = int(score_num)
            self.score_display = 'M{0}'.format(int(score_num))
        else:
            if not self.white_move and int(score_num) != 0: 
                score_num = -1.0 * score_num
            self.score_display = score_num / 100.0        

    def _get_engine_info_or_none(self, pattern):
        match_ob = re.search(pattern, self.engine_info, re.IGNORECASE)
        if not match_ob:
            return None
        info = match_ob.group()
        info = re.sub('^[ ]*[^\s]+ ', '', info)  # remove the info key 
        return info
