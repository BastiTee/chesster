## Chesster
> A Stockfish/UCI & pgn-extract frontend for Python.

[![GitHub release](https://img.shields.io/github/release/BastiTee/chesster.svg)](https://github.com/BastiTee/chesster/releases/latest)
![Python 2 support](https://img.shields.io/badge/python2-stable-green.svg)
![Python 3 support](https://img.shields.io/badge/python3-stable-green.svg)

This module contains
* a Python-frontend for any UCI-compatible chess engine (e.g. [Stockfish](https://stockfishchess.org/)) with Stockfish being included.
* a Python-frontend for [pgn-extract](https://www.cs.kent.ac.uk/people/staff/djb/pgn-extract/).
* a console client to play against Stockfish.
* a command-line tool to analyse and annotate chess games in PGN format.
* a simple standalone-server to send UCI commands over the web to a chesster instance.

## Installation

If you have downloaded a release or the master branch you can run

    python setup.py install

With `pip` and `git` installed, you can also download and install chesster directly

    pip install git+git://github.com/BastiTee/chesster.git#egg=chesster

This will give you a bleeding-edge master version. For a specific release run

    pip install git+git://github.com/BastiTee/chesster.git@0.2.0#egg=chesster

Afterwards you can run chesster using one of the four supported commands:

    python -m chesster.chesster_analyze
    python -m chesster.chesster_analyze_daemon
    python -m chesster.chesster_play
    python -m chesster.chesster_server

## Tools

### chesster_analyze

```
usage: chesster_analyze.py [-h] [-i <INPUT-FILE>] [-o <OUTPUT-DIR>]
                           [-t <T_MS>] [-p] [-d] [-v]

Analyze and annotate one or more games provided by a PGN file.

optional arguments:
  -h, --help       show this help message and exit
  -i <INPUT-FILE>  Input PGN file.
  -o <OUTPUT-DIR>  PGN output folder.
  -t <T_MS>        Engine time per move in ms (default: 5000).
  -p               Generate playbook with all games.
  -d               Delete source file.
  -v               Verbose output.
```

Input file example:

```
[Event "Friendly game"]
[Site "ChessTime"]
[Date "2014.09.16"]
[Round "?"]
[White "Player, White"]
[Black "Player, Black"]
[Result "1-0"]

1. e4 c5 2. Nf3 e6 3. c4 Nc6 4. Be2 d5 5. d3 d4 6. O-O Bd6
7. Bd2 Nf6 8. a3 O-O 9. b4 cxb4 10. axb4 e5 11. b5 Ne7
12. c5 Bc7 13. b6 axb6 14. Rxa8 bxc5 15. Qc2 Qd6 16. Na3
Bd7 17. Nc4 Qc6 18. Qa2 Rxa8 19. Qxa8+ Nc8 20. Ra1 Ne8
21. Nfxe5 Nb6 22. Nxb6 Qd6 23. Nbxd7 f6 24. Qxe8+ 1-0
```

Output file example:

```
[Event "Friendly game"]
[Site "ChessTime"]
[Date "2014.09.16]"]
[Round "1"]
[White "Player, White"]
[Black "Player, Black"]
[Result "1-0"]
[ECO "B40"]
[Opening "Sicilian defence"]
[ChessterAnalysisTs "1459242617805"]
[ChessterMistakes "2/3"]
[ChessterBlunders "1/7"]
[ChessterBestPositions "M1/-0.58"]

1. e4 c5 2. Nf3 e6 3. c4 Nc6 4. Be2 d5 5. d3 d4 6. O-O Bd6 7. Bd2 Nf6 8. a3
O-O 9. b4 cxb4 10. axb4 e5 $4 { Blunder -0.58/0.67 } (10... Bxb4 11. Bxb4
Nxb4 12. Na3 Nc6 13. e5 Nd7 14. Nb5 Qb6 15. Qb1 Qc5 16. Qb2 Ndxe5 17. Nxe5
Qxe5 18. Bf3 Bd7 19. Rfe1 Qc5 20. Bxc6 Bxc6 21. Nxd4 Rfd8 22. Nxc6 Qxc6)
11. b5 $2 { Mistake 0.67/0.11 } (11. c5 Bc7 12. b5) 11... Ne7 12. c5 Bc7
13. b6 axb6 $4 { Blunder 0.38/3.36 } (13... Bb8 14. bxa7 Bc7 15. Na3 Rxa7
16. Nc4 Rxa1 17. Qxa1 Nc6 18. Rb1 Qe7 19. Qa3 h6 20. Nd6 b6 21. Nb5 bxc5
22. Nxc7 Qxc7 23. Qxc5 Bd7 24. Rb5 Rc8) 14. Rxa8 bxc5 15. Qc2 Qd6 16. Na3
Bd7 $2 { Mistake 3.73/4.46 } (16... Qc6 17. Qa4 Nd7) 17. Nc4 Qc6 $4 {
Blunder 4.71/7.11 } (17... Qe6 18. Rxf8+) 18. Qa2 $4 { Blunder 7.11/4.03 }
(18. Rxf8+) 18... Rxa8 $4 { Blunder 4.03/5.78 } (18... Ng6 19. Rxf8+) 19.
Qxa8+ Nc8 $4 { Blunder 6.07/7.34 } (19... Bc8 20. Nfxe5 Qb5 21. f4 b6 22.
Ra1 Qe8 23. Qa7 Qd8 24. Rb1 Nd7 25. Nxd7 Nc6 26. Qa8 Bxd7 27. Qxd8+ Nxd8
28. Nxb6 Bc6 29. Nd5 Bxd5 30. exd5 g6 31. Rc1 Bd6 32. g3) 20. Ra1 $2 {
Mistake 7.34/6.48 } (20. Nfxe5) 20... Ne8 $4 { Blunder 6.48/7.9 } (20...
Be6 21. Ra7) 21. Nfxe5 Nb6 $2 { Mistake 8.25/8.79 } (21... Bxe5 22. Nxe5
Qc7) 22. Nxb6 Qd6 $4 { Blunder 10.35/28.41 } (22... Bxe5 23. Nxd7 Qxd7 24.
Ra7 h5 25. Rxb7 Qc6 26. Bd1 Kh7 27. Ba4 Nc7 28. Bxc6 Nxa8 29. Rxf7 c4 30.
Bxa8 c3 31. Bc1 Bf6 32. f4 Bh4 33. g3 Bf6 34. e5 Kg6) 23. Nbxd7 f6 $2 {
Mate set up } (23... Bb8 24. Qxb7) 24. Qxe8+ 1-0
```

### chesster_analyze_daemon

```
usage: chesster_analyze_daemon.py [-h] [-i <WORKDIR>] [-t <T_MS>] [-v]
                                  [-r <INTERVAL>]

A daemon to analyze PGN-file games in a watch folder.

optional arguments:
  -h, --help     show this help message and exit
  -i <WORKDIR>   Input working directory.
  -t <T_MS>      Engine time per move in ms (default: 5000).
  -v             Verbose output.
  -r <INTERVAL>  Worker interval in seconds.
```

### chesster_play

```
usage: chesster_play.py [-h] [-b] [-v] [-l <LEVEL>]

A command-line chess UI to play against Stockfish.

optional arguments:
  -h, --help  show this help message and exit
  -b          Play as black.
  -v          Verbose output.
  -l <LEVEL>  Engine level (1-20).
```

Screenshot:

```
    a b c d e f g h
  /-----------------\
8 | r n b q k b n r |8
7 | p p p p p p p p |7
6 | _ _ _ _ _ _ _ _ |6
5 | _ _ _ _ _ _ _ _ |5
4 | _ _ _ _ _ _ _ _ |4
3 | _ _ _ _ _ _ _ _ |3
2 | P P P P P P P P |2
1 | R N B Q K B N R |1
  \-----------------/
    a b c d e f g h


-- Your move:  e2e4

    a b c d e f g h
  /-----------------\
8 | r n b q k b n r |8
7 | p p p p p p p p |7
6 | _ _ _ _ _ _ _ _ |6
5 | _ _ _ _ _ _ _ _ |5
4 | _ _ _ _ P _ _ _ |4
3 | _ _ _ _ _ _ _ _ |3
2 | P P P P _ P P P |2
1 | R N B Q K B N R |1
  \-----------------/
    a b c d e f g h


-- Waiting for engine move
-- Engine played e7e6

    a b c d e f g h
  /-----------------\
8 | r n b q k b n r |8
7 | p p p p _ p p p |7
6 | _ _ _ _ p _ _ _ |6
5 | _ _ _ _ _ _ _ _ |5
4 | _ _ _ _ P _ _ _ |4
3 | _ _ _ _ _ _ _ _ |3
2 | P P P P _ P P P |2
1 | R N B Q K B N R |1
  \-----------------/
    a b c d e f g h

...
```

### chesster_server

```
usage: chesster_server.py [-h] [-d <HOSTNAME>] [-p <PORT>] [-v]

A server-frontend to send UCI commands over the web.

optional arguments:
  -h, --help     show this help message and exit
  -d <HOSTNAME>  Hostname (default: localhost).
  -p <PORT>      Port (default: 8000).
  -v             Verbose output.
```
