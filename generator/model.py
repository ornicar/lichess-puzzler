from chess.pgn import GameNode, ChildNode
from chess import Move, Color
from chess.engine import Score
from dataclasses import dataclass
from typing import Tuple, List, Optional

@dataclass
class Puzzle:
    node: ChildNode
    moves: List[Move]
    cp: int

@dataclass
class Line:
    nb: Tuple[int, int]
    letter: str
    password: str

@dataclass
class EngineMove:
    move: Move
    score: Score

@dataclass
class NextMovePair:
    node: GameNode
    winner: Color
    best: EngineMove
    second: Optional[EngineMove]

# More than just a TB probing result, since checking if other moves are also winning
@dataclass
class TbPair(NextMovePair):
    # `True` if the position is winning and only one move wins
    only_winning_move: bool