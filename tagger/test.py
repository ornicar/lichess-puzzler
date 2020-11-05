import unittest
import logging
import cook
from model import Puzzle
from tagger import logger, read
from chess.engine import SimpleEngine, Mate, Cp, Score, PovScore
from chess import Move, Color, Board, WHITE, BLACK
from chess.pgn import Game, GameNode
from typing import List, Optional, Tuple, Literal, Union

def make(id: str, fen: str, moves: str) -> Puzzle:
    return read({ "_id": id, "fen": fen, "moves": moves.split() })

class TestTagger(unittest.TestCase):

    logger.setLevel(logging.DEBUG)

    def test_attraction(self):
        self.assertFalse(cook.attraction(make("yUM8F",
            "r1bq1rk1/ppp1bppp/2n2n2/4p1B1/4N1P1/3P1N1P/PPP2P2/R2QKB1R w KQ - 1 9",
            "d1d2 f6e4 d3e4 c6d4 e1c1 d4f3 d2d8 e7g5 d8g5 f3g5"
        )))

        self.assertFalse(cook.attraction(make("wFGMa",
            "4r1k1/1R3ppp/1N3n2/1bP5/1P6/3p3P/6P1/3R2K1 w - - 0 28",
            "b6d5 f6d5 b7b5 d5c3 d1d3 c3b5"
        )))

        self.assertTrue(cook.attraction(make("uf4XN",
            "r4rk1/pp3pp1/7p/b2Pn3/4N3/6RQ/P4PPP/q1B1R1K1 b - - 8 26",
            "a5e1 g3g7 g8g7 h3h6 g7g8 e4f6"
        )))

        self.assertTrue(cook.attraction(make("wRDRr", "2kr1b1r/1p1b2pp/p1P1p2n/2P3N1/P4q2/5N2/4BKPP/R2Q3R b - - 2 18", "d7c6 d1d8 c8d8 g5e6 d8c8 e6f4")))

    def test_sacrifice(self):
        self.assertTrue(cook.sacrifice(make("1NHUV", "r1b2rk1/pppp1ppp/2n5/3Q2B1/2B5/2P2N2/P1q3PP/4RK1R b - - 1 14", "d7d6 d5f7 f8f7 e1e8")))
        self.assertFalse(cook.sacrifice(make("1HDGN", "3qr1k1/R4pbp/2p3p1/1p1p4/1P3Q2/2P1P3/3B2P1/7K b - - 0 33", "d8b8 f4f7 g8h8 f7g7")))
        self.assertTrue(cook.sacrifice(make("1PljR", "1R1r2k1/5ppp/p7/3q1P2/2pr1B2/3n2PP/4Q3/5RK1 b - - 4 30", "d3f4 e2e8 d8e8 b8e8")))
        self.assertTrue(cook.sacrifice(make("7frsv", "4r1k1/pb3ppp/1p1b1n2/2pP4/4P1q1/2N5/PBQ2PPP/R4RK1 w - - 0 19", "c2e2 d6h2 g1h2 g4h4 h2g1 f6g4 e2g4 h4g4")))
        self.assertFalse(cook.sacrifice(make("2FSmI", "r2q1rk1/pp3p2/4pn1R/8/3Q4/5N2/PPP2PPb/R5K1 w - - 0 19", "g1h2 d8d4 f3d4 f6g4 h2g3 g4h6")))
        self.assertTrue(cook.sacrifice(make("6UjJO", "r1bqnrk1/pp1n2p1/3bp1N1/3p1p2/2pP1P2/2P1PN1R/PP4PP/R1BQ2K1 b - - 1 15", "f8f6 h3h8 g8f7 f3g5 f7g6 d1h5")))
        self.assertTrue(cook.sacrifice(make("uHVch", "4r3/1b4p1/p7/1p1Pp1kr/4Qp2/1B1R1RP1/PP3P1P/2q3K1 w - - 1 31", "g1g2 h5h2 g2h2 e8h8 e4h7 h8h7 h2g2 c1h1")))
        self.assertFalse(cook.sacrifice(make("51K8X", "r3r1k1/pp1n1pp1/2p3p1/3p4/3PnqPN/2P4P/PPQN1P2/4RRK1 w - - 2 18", "h4g2 f4d2 c2d2 e4d2 e1e8 a8e8")))
        # temporary exchange sac
        self.assertTrue(cook.sacrifice(make("2pqYA", "6k1/p6p/2r2bp1/1pp4r/5P2/3R2P1/P5BP/3R3K b - - 1 29", "c5c4 d3d8 f6d8 d1d8 g8f7 g2c6")))

    def test_defensive(self):
        self.assertFalse(cook.defensive_move(make("6MVFt", "8/2P5/3K4/8/4pk2/2r3p1/R7/8 b - - 0 50", "f4f3 a2a3 c3a3 c7c8q")))
        self.assertFalse(cook.defensive_move(make("5Winv", "6k1/2Q2pp1/p5rp/3P4/2pn3r/5P1q/P1N2RPP/4R1K1 w - - 0 32", "c2d4 h4d4 c7b8 g8h7")))

if __name__ == '__main__':
    unittest.main()
