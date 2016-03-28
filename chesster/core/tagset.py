def enum(*sequential, **named):
	"""Definition for an enumeration like data structure."""
	
	enums = dict(zip(sequential, range(len(sequential))), **named)
	return type('Enum', (), enums)

ChessterTagSet = enum ('ANALYSIS_TS', 'MISTAKES', 'BLUNDERS',
					'BEST_POSITIONS',)
"""An enumeration that contains all known Chesster PGN-tags.""" 

def _get_label_for_tagnumber(tag):
	"""Private helper method to get pgn tag for enum entries."""
	return {
        0: 'ChessterAnalysisTs',
        1: 'ChessterMistakes',
        2: 'ChessterBlunders',
        3: 'ChessterBestPositions',
    }.get(tag, None)

def get_pgn_tag_string(tag, value):
	"""Returns the PGN-formatted tag entry for the given tag and
	tag value combination."""
	
	label = _get_label_for_tagnumber(tag)
	return  '[{} "{}"]'.format(label, value)

def append_chesster_tagset_ordered(order_dict):
	"""Appends all chesster-tags to a given dictionary mapping 
	tags to tagset ordering."""
	
	start_idx = max(order_dict.itervalues()) + 1
	for key, value in ChessterTagSet.__dict__.iteritems():
		if not key.startswith('__'):
			idx = int (value) + start_idx 
			order_dict[_get_label_for_tagnumber(value).lower()] = idx
	return order_dict
