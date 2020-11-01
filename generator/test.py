import unittest
import logging
from model import Puzzle
from generator import logger
from server import Server
from chess.engine import SimpleEngine, Mate, Cp, Score, PovScore
from chess import Move, Color, Board, WHITE, BLACK
from chess.pgn import Game, GameNode
from typing import List, Optional, Tuple, Literal, Union

import generator

class TestGenerator(unittest.TestCase):

    engine = generator.make_engine("stockfish", 8)
    server = Server(logger, "", "", 0)
    # logger.setLevel(logging.DEBUG)

    def test_puzzle_1(self) -> None:
        # https://lichess.org/analysis/standard/3q1k2/p7/1p2Q2p/5P1K/1P4P1/P7/8/8_w_-_-_5_57#112
        self.get_puzzle("3q1k2/p7/1p2Q2p/5P1K/1P4P1/P7/8/8 w - - 5 57",
                Cp(-1000), "h5g6", Mate(2), "d8g5 g6h7 g5g7")

    def test_puzzle_2(self) -> None:
        # https://lichess.org/nq1x9tln/black#76
        self.get_puzzle("3R4/1Q2nk2/4p2p/4n3/BP3ppP/P7/5PP1/2r3K1 w - - 2 39",
                Cp(-1000), "g1h2", Mate(4), "g4g3 f2g3 e5g4 h2h3 g4f2 h3h2 c1h1")

    def test_puzzle_3(self) -> None:
        # https://lichess.org/wQptHOX6/white#61
        self.get_puzzle("1r4k1/5p1p/pr1p2p1/q2Bb3/2P5/P1R3PP/KB1R1Q2/8 b - - 1 31",
                Cp(-4), "e5c3", Mate(3), "f2f7 g8h8 f7f6 c3f6 b2f6")

    def test_puzzle_4(self) -> None:
        # https://lichess.org/eVww5aBo#122
        self.get_puzzle("8/8/3Rpk2/2PpNp2/KP1P4/4r3/P1n5/8 w - - 3 62",
                Cp(0), "d6d7", Cp(580), "e3a3 a4b5 c2d4 b5b6 f6e5")

    # can't be done because there are 2 possible defensive moves
    def test_puzzle_5(self) -> None:
        # https://lichess.org/2YRgIXwk/black#32
        self.get_puzzle("r1b3k1/pp3p1p/2pp2p1/8/2P2q2/2N1r2P/PP2BPP1/R2Q1K1R w - - 0 17",
                Cp(-520), "d1d2", Cp(410), "e3h3 h1h3 f4d2")

    def test_puzzle_6(self) -> None:
        self.get_puzzle("4nr1k/2r1qNpp/p3pn2/1b2N2Q/1p6/7P/BP1R1PP1/4R1K1 b - - 0 1",
                Cp(130), "f8f7", Cp(550), "e5g6 h8g8 g6e7")

    # https://lichess.org/YCjcYuK6#81
    # def test_puzzle_7(self) -> None:
    #     self.get_puzzle("7r/1k6/pPp1qp2/2Q3p1/P4p2/5P2/5KP1/1RR4r b - - 5 41",
    #             Cp(-1500), "e6a2", Cp(530), "c1c2 a2e6 b1h1 h8h1 c2e2 e6d7 e2e7 d7e7 c5e7")

    # r1bq3r/pppp1kpp/2n5/2b1P1N1/3p2n1/2P5/P4PPP/RNBQ1RK1 b - - 1 10
    def test_puzzle_8(self) -> None:
        self.get_puzzle("r1bq3r/pppp1kpp/2n5/2b1P1N1/3p2n1/2P5/P4PPP/RNBQ1RK1 b - - 1 10",
                Cp(0), "f7g8", Mate(4), "d1b3 d7d5 e5d6 c8e6 b3e6 g8f8 e6f7")

    def test_puzzle_9(self) -> None:
        self.get_puzzle("7k/p3r1bP/1p1rp2q/8/2PBB3/4P3/P3KQ2/6R1 b - - 0 38",
                Cp(-110), "e6e5", Mate(2), "f2f8 g7f8 g1g8")

    # https://lichess.org/ejvEklSH/black#50
    def test_puzzle_10(self) -> None:
        self.get_puzzle("5rk1/pp3p2/1q1R3p/6p1/5pBb/2P4P/PPQ2PP1/3Rr1K1 w - - 6 26",
                Cp(-450), "g1h2", Mate(2), "h4g3 f2g3 b6g1")

    # https://lichess.org/f5s6c57d/white#53
    def test_puzzle_11(self) -> None:
        self.get_puzzle("b4nk1/5p1p/2n1pPpB/q2p2N1/2pP2Q1/1pP5/1P3PPP/3B2K1 b - - 0 27",
                Cp(380), "f8d7", Mate(4), "g4e6 f7e6 f6f7 g8h8 g5e6 g6g5 h6g7")

    def test_puzzle_12(self) -> None:
        self.get_puzzle("2kr3r/ppp2pp1/1b6/1P2p3/4P3/P2B2P1/2P2PP1/R4RK1 w - - 0 18",
                Cp(20), "f1d1", Mate(4), "h8h1 g1h1 b6f2 d3e2 d8h8 e2h5 h8h5")


    def test_not_puzzle_1(self) -> None:
        # https://lichess.org/LywqL7uc#32
        self.not_puzzle("r2q1rk1/1pp2pp1/p4n1p/b1pP4/4PB2/P3RQ2/1P3PPP/RN4K1 w - - 1 17",
                Cp(-230), "b1c3", Cp(160))

    def test_not_puzzle_2(self) -> None:
        # https://lichess.org/TIH1K2BQ#51
        self.not_puzzle("5b1r/kpQ2ppp/4p3/4P3/1P4q1/8/P3N3/1nK2B2 b - - 0 26",
                Cp(-1520), "b1a3", Cp(0))

    def test_not_puzzle_3(self) -> None:
        # https://lichess.org/StRzB2gY#59
        self.not_puzzle("7k/p6p/4p1p1/8/1q1p3P/2r1P1P1/P4Q2/5RK1 b - - 1 30",
                Cp(0), "d4e3", Cp(580))

    def test_not_puzzle_4(self) -> None:
        self.not_puzzle("r2qk2r/p1p1bppp/1p1ppn2/8/2PP1B2/3Q1N2/PP3PPP/3RR1K1 b kq - 6 12",
                Cp(-110), "h7h6", Cp(150))

    def get_puzzle(self, fen: str, prev_score: Score, move: str, current_score: Score, moves: str) -> None:
        board = Board(fen)
        game = Game.from_board(board)
        node = game.add_main_variation(Move.from_uci(move))
        current_eval = PovScore(current_score, not board.turn)
        result = generator.analyze_position(self.server, self.engine, node, prev_score, current_eval)
        self.assert_is_puzzle_with_moves(result, [Move.from_uci(x) for x in moves.split()])


    def not_puzzle(self, fen: str, prev_score: Score, move: str, current_score: Score) -> None:
        board = Board(fen)
        game = Game.from_board(board)
        node = game.add_main_variation(Move.from_uci(move))
        current_eval = PovScore(current_score, not board.turn)
        result = generator.analyze_position(self.server, self.engine, node, prev_score, current_eval)
        self.assertIsInstance(result, Score)


    def assert_is_puzzle_with_moves(self, puzzle: Union[Puzzle, Score], moves: List[Move]) -> None:
        self.assertIsInstance(puzzle, generator.Puzzle)
        if isinstance(puzzle, Puzzle):
            self.assertEqual(puzzle.moves, moves)


    @classmethod
    def tearDownClass(cls) -> None:
        cls.engine.close()


if __name__ == '__main__':
    unittest.main()
