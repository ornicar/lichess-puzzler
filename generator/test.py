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

    def test_mate_in_2(self) -> None:
        self.run_puzzle("3q1k2/p7/1p2Q2p/5P1K/1P4P1/P7/8/8 w - - 5 57", "h5g6", Cp(1000), PovScore(Mate(2), BLACK), ["d8g5", "g6h7", "g5g7"])


    def test_material(self) -> None:
        # https://lichess.org/eVww5aBo#122
        self.run_puzzle("8/8/3Rpk2/2PpNp2/KP1P4/4r3/P1n5/8 w - - 3 62", "d6d7", Cp(0), PovScore(Cp(580), BLACK), ["e3a3", "a4b5", "c2d4", "b5b6", "f6e5"])

    def run_puzzle(self, fen: str, move: str, prev_score: Score, current_eval: PovScore, moves: List[str]) -> None:
        game = Game.from_board(Board(fen))
        node = game.add_main_variation(Move.from_uci(move))
        result = generator.analyze_position(self.engine, node, prev_score, current_eval)
        self.assert_is_puzzle_with_moves(result, [Move.from_uci(x) for x in moves])
    

    def assert_is_puzzle_with_moves(self, puzzle: Union[Puzzle, Score], moves: List[Move]) -> None:
        self.assertIsInstance(puzzle, generator.Puzzle)
        if isinstance(puzzle, Puzzle):
            self.assertEqual(puzzle.moves, moves)


    @classmethod
    def tearDownClass(cls) -> None:
        cls.engine.close()


if __name__ == '__main__':
    unittest.main()
