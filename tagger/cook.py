from typing import List, Optional, Tuple, Literal, Union
from model import Puzzle, TagKind

def cook(puzzle: Puzzle) -> List[TagKind]:
    tags : List[TagKind] = []

    mate_tag = mate_in(puzzle)
    if mate_tag:
        tags.append(mate_tag)

    return tags

def mate_in(puzzle: Puzzle) -> Optional[TagKind]:
    if not puzzle.game.end().board().is_checkmate():
        return None
    moves_to_mate = int(len(list(puzzle.game.mainline_moves())) / 2)
    if moves_to_mate == 2:
        return "mateIn2"
    elif moves_to_mate == 2:
        return "mateIn2"
    elif moves_to_mate == 3:
        return "mateIn3"
    elif moves_to_mate == 4:
        return "mateIn4"
    elif moves_to_mate == 5:
        return "mateIn5"
    return "mateIn6+"
