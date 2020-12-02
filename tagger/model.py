from dataclasses import dataclass, field
import chess
from chess.pgn import Game, ChildNode
from chess import Move, Color
from typing import List, Optional, Tuple, Literal, Union

PuzzleKind = Literal["mate", "material"]  # Literal["mate", "other"]

TagKind = Literal[
    "advancedPawn",
    "attackingF2F7",
    "attraction",
    "blocking",
    "capturingDefender",
    "clearance",
    "coercion",
    "defensiveMove",
    "discoveredAttack",
    "deflection",
    "doubleCheck",
    "enPassant",
    "exposedKing",
    "fork",
    "hangingPiece",
    "interference",
    "long",
    "mateIn5",
    "mateIn4",
    "mateIn3",
    "mateIn2",
    "mateIn1",
    "oneMove",
    "overloading",
    "pin",
    "promotion",
    "quietMove",
    "rookEndgame",
    "sacrifice",
    "short",
    "simplification",
    "skewer",
    "trappedPiece",
    "veryLong",
    "zugzwang"
]

static_kinds = [
    "enPassant",
    "mateIn5",
    "mateIn4",
    "mateIn3",
    "mateIn2",
    "mateIn1",
    "oneMove",
    "promotion",
    "short",
    "long",
    "veryLong"
]

@dataclass
class Puzzle:
    id: str
    game: Game
    pov : Color = field(init=False)
    mainline: List[ChildNode] = field(init=False)

    def __post_init__(self):
        self.pov = not self.game.turn()
        self.mainline = list(self.game.mainline())
