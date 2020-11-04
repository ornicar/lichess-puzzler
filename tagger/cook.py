import logging
from typing import List, Optional, Tuple, Literal, Union
import chess
from chess import square_rank, Move, WHITE, BLACK
from chess.pgn import Game, GameNode
from model import Puzzle, TagKind
import util

logger = logging.getLogger(__name__)
logging.basicConfig(format='%(asctime)s %(levelname)-4s %(message)s', datefmt='%m/%d %H:%M')
logger.setLevel(logging.INFO)

def log(puzzle: Puzzle) -> None:
    logger.info("http://godot.lichess.ovh:9371/puzzle/{}".format(puzzle.id))

def cook(puzzle: Puzzle) -> List[TagKind]:
    game = puzzle.game
    tags : List[TagKind] = []

    mate_tag = mate_in(game)
    if mate_tag:
        tags.append(mate_tag)

    if attraction(puzzle):
        log(puzzle)
        tags.append("attraction")

    if advanced_pawn(game):
        tags.append("advancedPawn")

    return tags

def advanced_pawn(game: Game) -> bool:
    for node in game.mainline():
        if util.is_pawn_move(node):
            rank = square_rank(node.move.to_square)
            if rank > 5 and node.turn() == BLACK:
                return True
            if rank < 3 and node.turn() == WHITE:
                return True
    return False

def attraction(puzzle: Puzzle) -> bool:
    for node in list(puzzle.game.mainline())[1:]:
        if node.turn() == puzzle.pov():
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
                    attackers = next_node.board().attackers(puzzle.pov(), attracted_to_square)
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
