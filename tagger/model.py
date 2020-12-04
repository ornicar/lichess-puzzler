from dataclasses import dataclass, field
from chess.pgn import Game, ChildNode
from chess import Color
from typing import List, Literal, Union

TagKind = Literal[
    "advancedPawn",
    "attackingF2F7",
    "attraction",
    "bishopEndgame",
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
    "kingsideAttack",
    "knightEndgame",
    "long",
    "mateIn5",
    "mateIn4",
    "mateIn3",
    "mateIn2",
    "mateIn1",
    "oneMove",
    "overloading",
    "pawnEndgame",
    "pin",
    "promotion",
    "queenEndgame",
    "queensideAttack",
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

@dataclass
class Puzzle:
    id: str
    game: Game
    pov : Color = field(init=False)
    mainline: List[ChildNode] = field(init=False)

    def __post_init__(self):
        self.pov = not self.game.turn()
        self.mainline = list(self.game.mainline())
