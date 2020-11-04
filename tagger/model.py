from dataclasses import dataclass
import chess
from chess.pgn import Game
from chess import Move
from typing import List, Optional, Tuple, Literal, Union

PuzzleKind = Literal["mate", "material"]  # Literal["mate", "other"]

TagKind = Literal[
    "advancedPawn", 
    "attraction",
    "blocking",
    "capturingDefender",
    "clearance",
    "coercion",
    "defensiveMove",
    "discoveredAttack",
    "deflection",
    "doubleCheck",
    "exposedKing",
    "fork",
    "hangingPiece",
    "interference",
    "mateIn6+",
    "mateIn5",
    "mateIn4",
    "mateIn3",
    "mateIn2",
    "overloading",
    "pin",
    "quietMove",
    "sacrifice",
    "simplification",
    "skewer",
    "trappedPiece",
    "zugzwang"
]

@dataclass
class Puzzle:
    id: str
    game: Game

    def pov(self) -> chess.Color:
        return not self.game.turn()
