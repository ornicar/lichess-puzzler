from chess.pgn import GameNode
from chess import Move
from chess.engine import Score, Mate, Cp
from dataclasses import dataclass
from typing import List, Optional, Tuple, Literal, Union

@dataclass
class Puzzle:
    node: GameNode
    moves: List[Move]

@dataclass
class EngineMove:
    move: Move
    score: Score

@dataclass
class NextMovePair:
    node: GameNode
    best: EngineMove
    second: Optional[EngineMove]
