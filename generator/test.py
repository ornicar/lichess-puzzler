import unittest
import argparse
from generator import Puzzle
from chess.engine import SimpleEngine, Mate, Cp, Score, PovScore
from chess import Move, Color, Board, WHITE, BLACK
from chess.pgn import Game, GameNode
from typing import List, Optional, Tuple, Literal, Union

import generator

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog='test.py')
    parser.add_argument("--threads", "-t", help="count of cpu threads for engine searches", default="4")
    parser.add_argument("--verbose", "-v", help="increase verbosity", action="count")
    return parser.parse_args()


class TestGenerator(unittest.TestCase):

    args = parse_args()
    generator.setup_logging(args)
    engine = generator.make_engine(args)

    def test_puzzles(self) -> None:
        # https://lichess.org/analysis/standard/3q1k2/p7/1p2Q2p/5P1K/1P4P1/P7/8/8_w_-_-_5_57#112
        self.run_puzzle("3q1k2/p7/1p2Q2p/5P1K/1P4P1/P7/8/8 w - - 5 57", 
                Cp(-1000), "h5g6", Mate(2), "d8g5 g6h7 g5g7")
        # https://lichess.org/nq1x9tln/black#76
        self.run_puzzle("3R4/1Q2nk2/4p2p/4n3/BP3ppP/P7/5PP1/2r3K1 w - - 2 39", 
                Cp(-1000), "g1h2", Mate(4), "g4g3 f2g3 e5g4 h2h3 g4f2 h3h2 c1h1")
        # https://lichess.org/wQptHOX6/white#61
        self.run_puzzle("1r4k1/5p1p/pr1p2p1/q2Bb3/2P5/P1R3PP/KB1R1Q2/8 b - - 1 31", 
                Cp(-4), "e5c3", Mate(3), "f2f7 g8h8 f7f6 c3f6 b2f6")
        # https://lichess.org/eVww5aBo#122
        self.run_puzzle("8/8/3Rpk2/2PpNp2/KP1P4/4r3/P1n5/8 w - - 3 62", 
                Cp(0), "d6d7", Cp(580), "e3a3 a4b5 c2d4 b5b6 f6e5")
        # https://lichess.org/2YRgIXwk/black#32
        self.run_puzzle("r1b3k1/pp3p1p/2pp2p1/8/2P2q2/2N1r2P/PP2BPP1/R2Q1K1R w - - 0 17",
                Cp(-520), "d1d2", Cp(410), "e3h3 h1h3 f4d2")
        # https://lichess.org/LywqL7uc#32
        self.not_puzzle("r2q1rk1/1pp2pp1/p4n1p/b1pP4/4PB2/P3RQ2/1P3PPP/RN4K1 w - - 1 17",
                Cp(-230), "b1c3", Cp(160))
        self.not_puzzle("5b1r/kpQ2ppp/4p3/4P3/1P4q1/8/P3N3/1nK2B2 b - - 0 26",
                Cp(-1520), "b1a3", Cp(0))

    def run_puzzle(self, fen: str, prev_score: Score, move: str, current_score: Score, moves: str) -> None:
        board = Board(fen)
        game = Game.from_board(board)
        node = game.add_main_variation(Move.from_uci(move))
        current_eval = PovScore(current_score, not board.turn)
        result = generator.analyze_position(self.engine, node, prev_score, current_eval)
        self.assert_is_puzzle_with_moves(result, [Move.from_uci(x) for x in moves.split()])
    

    def not_puzzle(self, fen: str, prev_score: Score, move: str, current_score: Score) -> None:
        board = Board(fen)
        game = Game.from_board(board)
        node = game.add_main_variation(Move.from_uci(move))
        current_eval = PovScore(current_score, not board.turn)
        result = generator.analyze_position(self.engine, node, prev_score, current_eval)
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
