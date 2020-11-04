import logging
from typing import List, Optional, Tuple, Literal, Union
from model import Puzzle, TagKind
import chess
from chess import square_rank, Move, WHITE, BLACK
from chess.pgn import Game, GameNode

logger = logging.getLogger(__name__)
logging.basicConfig(format='%(asctime)s %(levelname)-4s %(message)s', datefmt='%m/%d %H:%M')
logger.setLevel(logging.INFO)

def cook(puzzle: Puzzle) -> List[TagKind]:
    game = puzzle.game
    tags : List[TagKind] = []

    mate_tag = mate_in(game)
    if mate_tag:
        tags.append(mate_tag)

    if advanced_pawn(game):
        logger.info("http://godot.lichess.ovh:9371/puzzle/{}".format(puzzle.id))
        tags.append("advancedPawn")

    return tags

def advanced_pawn(game: Game) -> bool:
    for node in game.mainline():
        if is_pawn_move(node):
            rank = square_rank(node.move.to_square)
            if rank > 5 and node.turn() == BLACK:
                return True
            if rank < 3 and node.turn() == WHITE:
                return True
    return False

def is_pawn_move(node: GameNode) -> bool:
    return node.board().piece_type_at(node.move.to_square) == chess.PAWN

def mate_in(game: Game) -> Optional[TagKind]:
    if not game.end().board().is_checkmate():
        return None
    moves_to_mate = int(len(list(game.mainline_moves())) / 2)
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
