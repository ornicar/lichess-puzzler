from chess.pgn import GameNode
from chess import Move
from chess.engine import Score, Mate, Cp
from dataclasses import dataclass
from typing import List, Optional, Tuple, Literal, Union

Kind = Literal["mate", "material"]  # Literal["mate", "other"]

@dataclass
class Puzzle:
    node: GameNode
    moves: List[Move]
    kind: Kind

@dataclass
class EngineMove:
    move: Move
    score: Score

@dataclass
class NextMovePair:
    node: GameNode
    best: EngineMove
    second: Optional[EngineMove]
