import unittest
import logging
import cook
import util
import chess
from model import Puzzle
from tagger import logger, read
from chess.engine import SimpleEngine, Mate, Cp, Score, PovScore
from chess import Move, Color, Board, Square, parse_square
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

    def test_fork(self):
        self.assertTrue(cook.fork(make("0PQep", "6q1/p6p/6p1/4k3/1P2N3/2B2P2/4K1P1/8 b - - 3 43", "e5d5 e4f6 d5c4 f6g8")))
        self.assertFalse(cook.fork(make("0O5RW", "rnb1k2r/p1B2ppp/4p3/1Bb5/8/4P3/PP1K1PPP/nN4NR b kq - 0 12", "b8d7 b5c6 c8a6 c6a8 c5b4 b1c3")))
        self.assertTrue(cook.fork(make("1NxIN", "r3k2r/p2q1ppp/4pn2/1Qp5/8/4P3/PP1N1PPP/R3K2R w KQkq - 2 16", "b5c5 d7d2 e1d2 f6e4 d2e2 e4c5")))
        self.assertFalse(cook.fork(make("6ppA2", "8/p7/1p6/2p5/P6P/2P2Nk1/1r4P1/4R1K1 w - - 1 39", "f3d2 b2d2 h4h5 d2g2")))

    def test_trapped(self):
        self.assertTrue(cook.trapped_piece(make("nPqjh", "r4rk1/pp1nppbp/3p1n2/q4p2/8/N1P1PP2/PP1BB1PP/2RQ1RK1 b - - 0 13", "b7b6 e2b5 a7a6 c3c4 a5a3 b2a3")))
        self.assertFalse(cook.trapped_piece(make("pjqyb", "r1b1k3/1pp4R/3p4/p2P4/2P5/8/PP2pKPP/8 b - - 1 34", "c8f5 h7h8 e8e7 h8a8 e2e1q f2e1")))
        self.assertTrue(cook.trapped_piece(make("pqkqG", "rnb1k2r/ppppqppp/8/2b4n/4P1N1/2N5/PPPP1PPP/R1BQKB1R w KQkq - 3 6", "f2f3 e7h4 g2g3 h5g3 h2g3 h4h1")))
        self.assertFalse(cook.trapped_piece(make("23J63", "2r2rk1/3bbpp1/p2p1n1p/1p1Pp3/4P3/5QNP/PPq2PPN/R1B1R1K1 w - - 6 19", "e1e2 c2d1 h2f1 c8c1 a1c1 d1c1")))
        self.assertFalse(cook.trapped_piece(make("2NQ68", "3qr1k1/p5pp/1p3n2/3p2P1/2rQ4/5B1P/PBb2P2/2R2RK1 w - - 1 21", "f3d5 d8d5 d4d5 f6d5")))

    def test_discovered_attack(self):
        self.assertFalse(cook.discovered_attack(make("0e7Q3", "5rk1/2pqnrpp/p3p1b1/N3P3/1PRPPp2/P4Q2/3B1RPP/6K1 w - - 3 30", "d2f4 f7f4 f3f4 f8f4")))
        self.assertFalse(cook.discovered_attack(make("0ZSP0", "5rk1/3R4/p1p3pp/1p2b3/2P1n2q/4Q2P/PP3PP1/4R1K1 w - - 4 27", "e3e4 h4f2 g1h1 f2f1 e1f1 f8f1")))
        self.assertTrue(cook.discovered_attack(make("01Y7w", "r2q1rk1/pppb1pbp/2n1pnp1/1BPpB3/3P4/4PN2/PP3PPP/RN1QK2R w KQ - 3 9", "e1g1 c6e5 d4e5 d7b5")))
        self.assertTrue(cook.discovered_attack(make("07jQK", "r4rk1/p1p1qppp/3b4/4n3/Q7/2NP4/PP3PPP/R1B2RK1 w - - 0 16", "f1e1 e5f3 g2f3 e7e1")))
        self.assertTrue(cook.discovered_attack(make("0VlKP", "5r2/6k1/8/p1p1p1p1/Pp1p2P1/1P1PnN1P/2P1KR2/8 w - - 3 38", "f3e5 f8e8 e5c6 e3g4 e2f1 g4f2")))
        self.assertFalse(cook.discovered_attack(make("m3h3k", "2r3k1/1r2pp1p/bqNp2p1/3P4/1p2P3/4bN2/1P4PP/2RQR2K w - - 0 24", "c6e7 b7e7 c1c8 a6c8")))

    def test_deflection(self):
        self.assertTrue(cook.deflection(make("25Qpt", "r1bqkbnr/pp3p1p/6p1/2pBp3/4P3/2P1B3/PP3PPP/RN1QK2R b KQkq - 0 9", "g8f6 d5f7 e8f7 d1d8")))
        self.assertFalse(cook.deflection(make("0EgUL", "rnb1k2r/pppp2p1/4p2p/5p2/1q1Pn2P/2NQPN2/PPP2PP1/R3KB1R w KQkq - 1 9", "a2a3 b4b2 a1b1 b2c3 d3c3 e4c3")))
        self.assertFalse(cook.deflection(make("08vBP", "8/1R4p1/p5rp/4bN2/5kP1/2P4K/PP6/8 b - - 0 40", "g6g4 b7b4 f4f5 b4g4")))
        self.assertFalse(cook.deflection(make("0ZSP0", "5rk1/3R4/p1p3pp/1p2b3/2P1n2q/4Q2P/PP3PP1/4R1K1 w - - 4 27", "e3e4 h4f2 g1h1 f2f1 e1f1 f8f1")))
        self.assertFalse(cook.deflection(make("3J2Nl", "r2q2k1/pp4bp/3pnppn/3N4/4Pp1B/7P/PPPQ2P1/R4RK1 w - - 0 19", "d5f4 e6f4 f1f4 g6g5 d2d5 g8h8 f4f2 g5h4")))
        self.assertFalse(cook.deflection(make("3051j", "r2k2r1/1b2nQb1/1p2p2p/p3Pp2/2P4q/P6P/NP2R1PN/2R4K b - - 0 26", "h4d4 a2c3 g8f8 f7g7 f8g8 g7h6")))
        self.assertFalse(cook.deflection(make("0VlKP", "5r2/6k1/8/p1p1p1p1/Pp1p2P1/1P1PnN1P/2P1KR2/8 w - - 3 38", "f3e5 f8e8 e5c6 e3g4 e2f1 g4f2")))

    def test_skewer(self):
        self.assertTrue(cook.skewer(make("29HGS", "3r4/6p1/5r1p/7k/3N1P2/3K2P1/3R4/3R4 w - - 1 50", "d2e2 d8d4 d3d4 f6d6 d4e5 d6d1")))

    def test_interference(self):
        self.assertFalse(cook.interference(make("2t6Xz", "6k1/1b1q1pbp/4pnp1/2Pp4/rp1P1P2/3BPRNP/4Q1P1/4B1K1 b - - 1 26", "f6e4 d3b5 b7c6 b5a4")))
        self.assertTrue(cook.interference(make("QssMO", "r5k1/ppp2r2/3p3p/3Pp3/1P2N1bb/R5N1/1P3P1K/6R1 b - - 5 25", "g4f3 g3f5 g8h7 a3f3")))

    def test_pin(self):
        # pins the queen from attacking the g2 pawn
        self.assertTrue(cook.pin(make("P2D4h", "2k5/p7/bpq1p3/8/2PP2P1/1K2P1p1/4Q1P1/8 b - - 4 36", "a6c4 e2c4 c6c4 b3c4")))
        self.assertTrue(cook.pin(make("aJPsJ", "r2q1r1k/pp3pp1/2p2n1p/3PB2b/3P4/1B5P/P1PQ1PP1/R3R1K1 b - - 0 18", "f6d5 d2h6 h8g8 h6g7")))

    def test_hanging_piece(self):
        self.assertTrue(cook.hanging_piece(make("069il", "r2qr1k1/1p3ppp/p1p2nb1/8/4P3/1P5P/PBQN1PP1/R3R1K1 w - - 1 17", "c2c4 d8d2 b2f6 g7f6")))

    def test_advanced_pawn(self):
        self.assertFalse(cook.advanced_pawn(make("C3gv2", "4r3/R1p2k2/3p1pp1/2r2p1p/1pN2Pn1/1P2PKP1/2P3P1/4R3 b - - 3 39", "d6d5 c4d6 f7e7 d6e8")))

class TestUtil(unittest.TestCase):

    def test_trapped(self):
        self.assertFalse(util.is_trapped(
            chess.Board("q3k3/7p/8/4N2q/3PP3/4B3/8/4K2R b - - 0 1"), parse_square("h5")
        ))
        self.assertTrue(util.is_trapped(
            chess.Board("q3k3/7p/8/4N2q/3PP3/4B3/7R/4K2R b - - 0 1"), parse_square("h5")
        ))
        self.assertFalse(util.is_trapped(
            chess.Board("q3k3/7p/8/4N2b/3PP3/4B3/7R/4K2R b - - 0 1"), parse_square("h5")
        ))
        self.assertFalse(util.is_trapped(
            chess.Board("4k3/7p/8/4N2q/3PP2p/4B3/8/4K3 b - - 0 1"), parse_square("h5")
        ))
        self.assertTrue(util.is_trapped(
            chess.Board("8/3P4/8/4N2b/7p/6N1/8/4K3 b - - 0 1"), parse_square("h5")
        ))

    # def test_takers(self):
    #     # https://lichess.org/editor/1r1bk2b/1R4n1/4N3/8/3Q1P1q/8/8/1K6_w_-_-_0_1
    #     board = chess.Board("1r1bk2b/1R4n1/4N3/8/3Q1P1q/8/8/1K6 w - - 0 1")
    #     def check(dest: Square, origs: List[Square]):
    #         square = parse_square(dest)
    #         takers = [(board.piece_at(s), s) for s in [parse_square(s) for s in origs]]
    #         self.assertCountEqual(util.takers(board, square), takers)
    #     check("c2", ["b1"])
    #     check("b8", ["b7"])
    #     check("d8", ["d4", "e6"])
    #     check("g7", ["d4", "e6"])
    #     check("h8", [])
    #     check("h4", [])

if __name__ == '__main__':
    unittest.main()
