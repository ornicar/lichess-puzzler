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

    def test_mate_in_3(self) -> None:
        game = Game.from_board(Board("B5k1/8/1p6/1P2p1p1/2P1Nn2/3P1K2/P5r1/3R1R2 b - - 1 33"))
        result = generator.analyze_position(self.engine, game, Cp(1250), PovScore(Mate(2), BLACK))
        self.assert_is_puzzle_with_moves(result, [Move.from_uci(x) for x in ["g5g4", "f3e3", "g2e2"]])
    
    def assert_is_puzzle_with_moves(self, puzzle: Union[Puzzle, Score], moves: List[Move]) -> None:
        self.assertIsInstance(puzzle, generator.Puzzle)
        if isinstance(puzzle, Puzzle):
            self.assertEqual(puzzle.moves, moves)


if __name__ == '__main__':
    unittest.main()
