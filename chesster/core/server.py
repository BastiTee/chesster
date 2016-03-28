import logging 
from re import sub

from bottle import request, abort, response, route, run

from chesster.core.uci_frontend import ChessterUciFrontend


class ChessterServer:
    
    uci_frontend = ChessterUciFrontend()
    
    def __init__(self, host, port):
        logging.info('Obtained new server instance.')
        self.uci_frontend.init_engine()
        route('/')(self.bottle_get)
        route('/uci')(self.bottle_get_eval_uci)
        route('/bestmove')(self.bottle_get_bestmove)
        route('/evalpos')(self.bottle_get_eval_position)
        logging.info('Routed default webservice endpoints.')
        run(host=host, port=port)
    
    def bottle_get(self):
        return self._bottle_generate_response({ 'chesster in online'},
                                              request, response)
    
    def bottle_get_eval_uci(self):
        uci_string = request.query.com
        if uci_string is None or uci_string == '':
            abort(400, text='Obligatory parameter \'com\' missing.')
        output = self.uci_frontend.eval_uci(uci_string)
        return self._bottle_generate_response(output, request, response)
    
    def bottle_get_bestmove(self):
        fen_string = request.query.fen
        ttm = request.query.ttm
        if not fen_string:
            abort(400, text='Obligatory parameter \'fen\' missing.')
        best_move = self.uci_frontend.bestmove(fen_string, ttm)
        return self._bottle_generate_response(best_move,
                                       request, response)

    def bottle_get_eval_position(self):
        fen_string = request.query.fen
        ttm = request.query.ttm
        if not fen_string:
            abort(400, text='Obligatory parameter \'fen\' missing.')
        evaluation = self.uci_frontend.eval_position(fen_string, ttm)
        return self._bottle_generate_response(evaluation,
                                       request, response)
    
    def _bottle_generate_response(self, output, request, response):
        response.add_header('Content-Type', 'text/html; charset=utf-8')
        content = '<html><style>* {{font-family:Consolas;}}</style><body>{0}</body></html>'.format(
                                                '<br/>'.join(output))
        content = sub('\n', '<br/>', content)
        return content
