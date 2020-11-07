import logging
from copy import deepcopy
from typing import List, Optional, Tuple, Literal, Union
import chess
from chess import square_rank, Move, SquareSet, Piece, PieceType
from chess import KING, QUEEN, ROOK, BISHOP, KNIGHT, PAWN
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

    if deflection(puzzle):
        tags.append("deflection")

    if advanced_pawn(puzzle):
        tags.append("advancedPawn")

    if double_check(puzzle):
        tags.append("doubleCheck")

    if quiet_move(puzzle):
        tags.append("quietMove")

    if defensive_move(puzzle):
        tags.append("defensiveMove")

    if sacrifice(puzzle):
        tags.append("sacrifice")

    if fork(puzzle):
        tags.append("fork")

    if hanging_piece(puzzle):
        tags.append("hangingPiece")

    if trapped_piece(puzzle):
        tags.append("trappedPiece")

    if discovered_attack(puzzle):
        tags.append("discoveredAttack")

    if exposed_king(puzzle):
        tags.append("exposedKing")

    if skewer(puzzle):
        tags.append("skewer")

    if len(puzzle.mainline) == 2:
        tags.append("oneMove")

    if len(puzzle.mainline) == 4:
        tags.append("short")

    if len(puzzle.mainline) >= 8:
        tags.append("long")

    return tags

def advanced_pawn(puzzle: Puzzle) -> bool:
    for node in puzzle.mainline:
        if util.is_advanced_pawn_move(node):
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

def fork(puzzle: Puzzle) -> bool:
    for node in puzzle.mainline[1::2][:-1]:
        if util.moved_piece_type(node) is not KING:
            board = node.board()
            if board.is_checkmate():
                return False
            nb = 0
            for (piece, square) in util.attacked_opponent_squares(board, node.move.to_square, puzzle.pov):
                if piece.piece_type == PAWN:
                    continue
                if (piece.piece_type == KING or
                    util.values[piece.piece_type] > util.values[util.moved_piece_type(node)] or
                    util.is_hanging(board, piece, square)):
                    nb += 1
            if nb > 1:
                return True
    return False

def hanging_piece(puzzle: Puzzle) -> bool:
    if util.is_capture(puzzle.mainline[0]):
        return False
    to = puzzle.mainline[1].move.to_square
    captured = puzzle.mainline[0].board().piece_at(to)
    if captured and captured.piece_type != PAWN:
        if util.is_hanging(puzzle.mainline[0].board(), captured, to):
            if len(puzzle.mainline) < 3:
                return True
            if not util.is_capture(puzzle.mainline[2]) and not puzzle.mainline[2].board().is_check():
                return True
    return False

def trapped_piece(puzzle: Puzzle) -> bool:
    for node in puzzle.mainline[1::2][1:]:
        square = node.move.to_square
        captured = node.parent.board().piece_at(square)
        if captured and captured.piece_type != PAWN:
            prev = node.parent
            if prev.move.to_square == square:
                square = prev.move.from_square
            if util.is_trapped(prev.parent.board(), square):
                return True
    return False

def discovered_attack(puzzle: Puzzle) -> bool:
    if discovered_check(puzzle):
        return True
    for node in puzzle.mainline[1::2][1:]:
        if util.is_capture(node):
            between = SquareSet.between(node.move.from_square, node.move.to_square)
            if node.parent.move.to_square == node.move.to_square:
                return False
            prev = node.parent.parent
            if prev.move.from_square in between and node.move.to_square != prev.move.to_square:
                return True
    return False

def discovered_check(puzzle: Puzzle) -> bool:
    for node in puzzle.mainline[1::2]:
        board = node.board()
        checkers = board.checkers()
        if checkers and not node.move.to_square in checkers:
            return True
    return False

def quiet_move(puzzle: Puzzle) -> bool:
    for node in puzzle.mainline:
        # on player move, not the last move of the puzzle
        if node.turn() != puzzle.pov and not node.is_end():
            # no check given or escaped
            if not node.board().checkers() and not node.parent.board().checkers():
                # no capture made or threatened
                if not util.is_capture(node):
                    return not util.attacked_opponent_pieces(node.board(), node.move.to_square, puzzle.pov)
    return False

def defensive_move(puzzle: Puzzle) -> bool:
    # like quiet_move, but on last move
    # at least 3 legal moves
    if puzzle.mainline[-2].board().legal_moves.count() < 3:
        return False
    node = puzzle.mainline[-1]
    # no check given, no piece taken
    if node.board().checkers() or util.is_capture(node):
        return False
    # no piece attacked
    if util.attacked_opponent_pieces(node.board(), node.move.to_square, puzzle.pov):
        return False
    # no advanced pawn push
    return not util.is_advanced_pawn_move(node)

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
            if attracted_piece in [KING, QUEEN, ROOK]:
                attracted_to_square = opponent_reply.move.to_square
                next_node = util.next_node(opponent_reply)
                if next_node:
                    attackers = next_node.board().attackers(puzzle.pov, attracted_to_square)
                    # 3. player attacks that square
                    if next_node.move.to_square in attackers:
                        # 4. player checks on that square
                        if attracted_piece == KING:
                            return True
                        n3 = util.next_next_node(next_node)
                        # 4. or player later captures on that square
                        if n3 and n3.move.to_square == attracted_to_square:
                            return True
    return False

def deflection(puzzle: Puzzle) -> bool:
    for node in puzzle.mainline[1::2][1:]:
        capture = node.parent.board().piece_at(node.move.to_square)
        if capture or node.move.promotion:
            piece = util.moved_piece_type(node)
            if capture and piece != KING and util.values[capture.piece_type] > util.values[piece]:
                continue
            square = node.move.to_square
            prev_op_move = node.parent.move
            prev_player_move = node.parent.parent.move
            prev_player_capture = node.parent.parent.parent.board().piece_at(prev_player_move.to_square)
            if (
                (not prev_player_capture or util.values[prev_player_capture.piece_type] < util.moved_piece_type(node.parent.parent)) and
                (square != prev_op_move.to_square and square != prev_player_move.to_square) and
                (prev_op_move.to_square == prev_player_move.to_square) and
                (square in node.parent.parent.board().attacks(prev_op_move.from_square)) and
                (not square in node.parent.board().attacks(prev_op_move.to_square))
            ):
                return True
    return False

def exposed_king(puzzle: Puzzle) -> bool:
    if puzzle.pov:
        pov = puzzle.pov
        board = puzzle.mainline[0].board()
    else:
        pov = not puzzle.pov
        board = puzzle.mainline[0].board().mirror()
    king = board.king(not pov)
    if chess.square_rank(king) < 5:
        return False
    squares = SquareSet.from_square(king - 8)
    if chess.square_file(king) > 0:
        squares.add(king - 1)
        squares.add(king - 9)
    if chess.square_file(king) < 7:
        squares.add(king + 1)
        squares.add(king - 7)
    for square in squares:
        if board.piece_at(square) == Piece(PAWN, not pov):
            return False
    for node in puzzle.mainline[1::2][1:-1]:
        if node.board().is_check():
            return True
    return False

def skewer(puzzle: Puzzle) -> bool:
    def value(pt: PieceType):
        return 10 if pt == KING else util.values[pt]
    for node in puzzle.mainline[1::2][1:]:
        prev = node.parent
        capture = prev.board().piece_at(node.move.to_square)
        if capture and util.moved_piece_type(node) in [QUEEN, BISHOP, ROOK] and not node.board().is_checkmate():
            between = SquareSet.between(node.move.from_square, node.move.to_square)
            op_move = prev.move
            if (op_move.to_square == node.move.to_square or not op_move.from_square in between):
                continue
            if value(util.moved_piece_type(prev)) > value(capture.piece_type):
                return True
    return False

def mate_in(puzzle: Puzzle) -> Optional[TagKind]:
    if not puzzle.game.end().board().is_checkmate():
        return None
    moves_to_mate = len(puzzle.mainline) // 2
    if moves_to_mate == 1:
        return "mateIn1"
    elif moves_to_mate == 2:
        return "mateIn2"
    elif moves_to_mate == 3:
        return "mateIn3"
    elif moves_to_mate == 4:
        return "mateIn4"
    return "mateIn5+"
