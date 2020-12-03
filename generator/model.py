from chess.pgn import GameNode
from chess import Move, Color
from chess.engine import Score, Mate, Cp
from dataclasses import dataclass
from typing import Tuple, Literal, Union

@dataclass
class Puzzle:
    node: GameNode
    moves: List[Move]

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
