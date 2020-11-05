import logging
from typing import List, Optional, Tuple, Literal, Union
import chess
from chess import square_rank, Move, WHITE, BLACK
from chess.pgn import Game, GameNode
from model import Puzzle, TagKind
import util
from util import material_diff

logger = logging.getLogger(__name__)
logging.basicConfig(format='%(asctime)s %(levelname)-4s %(message)s', datefmt='%m/%d %H:%M')
logger.setLevel(logging.INFO)

def log(puzzle: Puzzle) -> None:
    logger.info("http://godot.lichess.ovh:9371/puzzle/{}".format(puzzle.id))

def cook(puzzle: Puzzle) -> List[TagKind]:
    tags : List[TagKind] = []

    mate_tag = mate_in(puzzle)
    if mate_tag:
        tags.append(mate_tag)

    if attraction(puzzle):
        tags.append("attraction")

    if advanced_pawn(puzzle):
        tags.append("advancedPawn")

    if double_check(puzzle):
        tags.append("doubleCheck")

    if quiet_move(puzzle):
        tags.append("quietMove")

    if sacrifice(puzzle):
        tags.append("sacrifice")

    if len(puzzle.mainline) == 4:
        tags.append("short")
    elif len(puzzle.mainline) >= 8:
        tags.append("long")

    return tags

def advanced_pawn(puzzle: Puzzle) -> bool:
    for node in puzzle.mainline:
        if util.is_pawn_move(node):
            rank = square_rank(node.move.to_square)
            if rank > 5 and node.turn() == BLACK:
                return True
            if rank < 3 and node.turn() == WHITE:
                return True
    return False

def double_check(puzzle: Puzzle) -> bool:
    for node in puzzle.mainline:
        if node.turn() != puzzle.pov and len(node.board().checkers()) > 1:
            return True
    return False

def sacrifice(puzzle: Puzzle) -> bool:
    # down in material compared to initial position, after moving
    diffs = [material_diff(n.board(), puzzle.pov) for n in puzzle.mainline]
    initial = diffs[0]
    for d in diffs[1::2][1:]:
        if d - initial <= -2:
            return True
    return False

def quiet_move(puzzle: Puzzle) -> bool:
    for node in puzzle.mainline:
        # on player move, not the last move of the puzzle
        if node.turn() != puzzle.pov and not node.is_end():
            board = node.board()
            # no check given or escaped
            if not board.checkers() and not node.parent.board().checkers():
                # no capture made or threatened
                if not util.is_capture(node):
                    for attacked_square in board.attacks(node.move.to_square):
                        attacked_piece = board.piece_at(attacked_square)
                        if attacked_piece and attacked_piece.color != puzzle.pov:
                            return False
                    return True
    return False

def attraction(puzzle: Puzzle) -> bool:
    for node in puzzle.mainline[1:]:
        if node.turn() == puzzle.pov:
            continue
        # 1. player moves to a square
        first_move_to = node.move.to_square
        opponent_reply = util.next_node(node)
        # 2. opponent captures on that square
        if opponent_reply and opponent_reply.move.to_square == first_move_to:
            attracted_piece = util.moved_piece_type(opponent_reply)
            if attracted_piece in [chess.KING, chess.QUEEN, chess.ROOK]:
                attracted_to_square = opponent_reply.move.to_square
                next_node = util.next_node(opponent_reply)
                if next_node:
                    attackers = next_node.board().attackers(puzzle.pov, attracted_to_square)
                    # 3. player attacks that square
                    if next_node.move.to_square in attackers:
                        # 4. player checks on that square
                        if attracted_piece == chess.KING:
                            return True
                        n3 = util.next_next_node(next_node)
                        # 4. or player later captures on that square
                        if n3 and n3.move.to_square == attracted_to_square:
                            return True
    return False

def mate_in(puzzle: Puzzle) -> Optional[TagKind]:
    if not puzzle.game.end().board().is_checkmate():
        return None
    moves_to_mate = int(len(puzzle.mainline) / 2)
    if moves_to_mate == 2:
        return "mateIn2"
    elif moves_to_mate == 3:
        return "mateIn3"
    elif moves_to_mate == 4:
        return "mateIn4"
    elif moves_to_mate == 5:
        return "mateIn5"
    return "mateIn6+"
