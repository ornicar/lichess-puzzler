from chess.pgn import GameNode
from chess import Move
from dataclasses import dataclass
from typing import List, Optional, Tuple, Literal, Union

Kind = Literal["mate", "material"]  # Literal["mate", "other"]

@dataclass
class Puzzle:
    node: GameNode
    moves: List[Move]
    kind: Kind
