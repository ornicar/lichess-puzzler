import logging
from typing import List, Optional
import chess
from chess import square_rank, square_file, SquareSet, Piece, PieceType, Board, square_distance
from chess import KING, QUEEN, ROOK, BISHOP, KNIGHT, PAWN
from chess import WHITE, BLACK
from chess.pgn import ChildNode
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
        if smothered_mate(puzzle):
            tags.append("smotheredMate")

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

    if self_interference(puzzle) or interference(puzzle):
        tags.append("interference")

    if pin_prevents_attack(puzzle) or pin_prevents_escape(puzzle):
        tags.append("pin")

    if attacking_f2_f7(puzzle):
        tags.append("attackingF2F7")

    if kingside_attack(puzzle):
        tags.append("kingsideAttack")
    elif queenside_attack(puzzle):
        tags.append("queensideAttack")

    if clearance(puzzle):
        tags.append("clearance")

    if en_passant(puzzle):
        tags.append("enPassant")

    if promotion(puzzle):
        tags.append("promotion")

    if capturing_defender(puzzle):
        tags.append("capturingDefender")

    if piece_endgame(puzzle, PAWN):
        tags.append("pawnEndgame")
    elif piece_endgame(puzzle, QUEEN):
        tags.append("queenEndgame")
    elif piece_endgame(puzzle, ROOK):
        tags.append("rookEndgame")
    elif piece_endgame(puzzle, BISHOP):
        tags.append("bishopEndgame")
    elif piece_endgame(puzzle, KNIGHT):
        tags.append("knightEndgame")

    if len(puzzle.mainline) == 2:
        tags.append("oneMove")
    elif len(puzzle.mainline) == 4:
        tags.append("short")
    elif len(puzzle.mainline) >= 8:
        tags.append("veryLong")
    else:
        tags.append("long")

    return tags

def advanced_pawn(puzzle: Puzzle) -> bool:
    for node in puzzle.mainline[1::2]:
        if util.is_very_advanced_pawn_move(node):
            return True
    return False

def double_check(puzzle: Puzzle) -> bool:
    for node in puzzle.mainline[1::2]:
        if len(node.board().checkers()) > 1:
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
    if util.is_capture(puzzle.mainline[0]) or puzzle.mainline[0].board().is_check():
        return False
    to = puzzle.mainline[1].move.to_square
    captured = puzzle.mainline[0].board().piece_at(to)
    if captured and captured.piece_type != PAWN:
        if util.is_hanging(puzzle.mainline[0].board(), captured, to):
            if len(puzzle.mainline) < 3:
                return True
            if material_diff(puzzle.mainline[3].board(), puzzle.pov) >= material_diff(puzzle.mainline[1].board(), puzzle.pov):
                return True
    return False

def trapped_piece(puzzle: Puzzle) -> bool:
    for node in puzzle.mainline[1::2][1:]:
        square = node.move.to_square
        captured = node.parent.board().piece_at(square)
        if captured and captured.piece_type != PAWN:
            prev = node.parent
            assert isinstance(prev, ChildNode)
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
            assert isinstance(node.parent, ChildNode)
            if node.parent.move.to_square == node.move.to_square:
                return False
            prev = node.parent.parent
            assert isinstance(prev, ChildNode)
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
            assert(prev_op_move)
            grandpa = node.parent.parent
            assert isinstance(grandpa, ChildNode)
            prev_player_move = grandpa.move
            prev_player_capture = grandpa.parent.board().piece_at(prev_player_move.to_square)
            if (
                (not prev_player_capture or util.values[prev_player_capture.piece_type] < util.moved_piece_type(grandpa)) and
                (square != prev_op_move.to_square and square != prev_player_move.to_square) and
                (prev_op_move.to_square == prev_player_move.to_square) and
                (square in grandpa.board().attacks(prev_op_move.from_square)) and
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
    assert king is not None
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
        assert isinstance(prev, ChildNode)
        capture = prev.board().piece_at(node.move.to_square)
        if capture and util.moved_piece_type(node) in util.ray_piece_types and not node.board().is_checkmate():
            between = SquareSet.between(node.move.from_square, node.move.to_square)
            op_move = prev.move
            assert op_move
            if (op_move.to_square == node.move.to_square or not op_move.from_square in between):
                continue
            if value(util.moved_piece_type(prev)) > value(capture.piece_type):
                return True
    return False

def self_interference(puzzle: Puzzle) -> bool:
    # intereference by opponent piece
    for node in puzzle.mainline[1::2][1:]:
        prev_board = node.parent.board()
        square = node.move.to_square
        capture = prev_board.piece_at(square)
        if capture and util.is_hanging(prev_board, capture, square):
            grandpa = node.parent.parent
            assert grandpa
            init_board = grandpa.board()
            defenders = init_board.attackers(capture.color, square)
            defender = defenders.pop() if defenders else None
            defender_piece = init_board.piece_at(defender) if defender else None
            if defender and defender_piece and defender_piece.piece_type in util.ray_piece_types:
                if node.parent.move and node.parent.move.to_square in SquareSet.between(square, defender):
                    return True
    return False

def interference(puzzle: Puzzle) -> bool:
    # intereference by player piece
    for node in puzzle.mainline[1::2][1:]:
        prev_board = node.parent.board()
        square = node.move.to_square
        capture = prev_board.piece_at(square)
        assert node.parent.move
        if capture and square != node.parent.move.to_square and util.is_hanging(prev_board, capture, square):
            assert node.parent
            assert node.parent.parent
            assert node.parent.parent.parent
            init_board = node.parent.parent.parent.board()
            defenders = init_board.attackers(capture.color, square)
            defender = defenders.pop() if defenders else None
            defender_piece = init_board.piece_at(defender) if defender else None
            if defender and defender_piece and defender_piece.piece_type in util.ray_piece_types:
                interfering = node.parent.parent
                if interfering.move and interfering.move.to_square in SquareSet.between(square, defender):
                    return True
    return False

# the pinned piece can't attack a player piece
def pin_prevents_attack(puzzle: Puzzle) -> bool:
    for node in puzzle.mainline[1::2][:-1]:
        board = node.board()
        for square, piece in board.piece_map().items():
            if piece.color == puzzle.pov:
                continue
            pin_dir = board.pin(piece.color, square)
            if pin_dir == chess.BB_ALL:
                continue
            for attack in board.attacks(square):
                attacked = board.piece_at(attack)
                if attacked and attacked.color == puzzle.pov and not attack in pin_dir and (
                        util.values[attacked.piece_type] > util.values[piece.piece_type] or
                        util.is_hanging(board, attacked, attack)
                    ):
                    return True
    return False

# the pinned piece can't escape the attack
def pin_prevents_escape(puzzle: Puzzle) -> bool:
    for node in puzzle.mainline[1::2][:-1]:
        board = node.board()
        for pinned_square, pinned_piece in board.piece_map().items():
            if pinned_piece.color == puzzle.pov:
                continue
            pin_dir = board.pin(pinned_piece.color, pinned_square)
            if pin_dir == chess.BB_ALL:
                continue
            for attacker_square in board.attackers(puzzle.pov, pinned_square):
                if attacker_square in pin_dir:
                    attacker = board.piece_at(attacker_square)
                    assert(attacker)
                    if util.values[pinned_piece.piece_type] > util.values[attacker.piece_type]:
                        return True
                    if (util.is_hanging(board, pinned_piece, pinned_square) and 
                        pinned_square not in board.attackers(not puzzle.pov, attacker_square)):
                        return True
    return False

def attacking_f2_f7(puzzle: Puzzle) -> bool:
    for node in puzzle.mainline[1::2]:
        square = node.move.to_square
        if node.parent.board().piece_at(node.move.to_square) and square in [chess.F2, chess.F7]:
            king = node.board().piece_at(chess.E8 if square == chess.F7 else chess.E1)
            return king is not None and king.piece_type == KING and king.color != puzzle.pov
    return False

def kingside_attack(puzzle: Puzzle) -> bool:
    return side_attack(puzzle, [6, 7], 20)

def queenside_attack(puzzle: Puzzle) -> bool:
    return side_attack(puzzle, [0, 1, 2], 16)

def side_attack(puzzle: Puzzle, king_files: List[int], nb_pieces: int) -> bool:
    for node in puzzle.mainline[1::2]:
        if node.board().is_check():
            board = node.board()
            king_square = board.king(not puzzle.pov)
            assert king_square is not None
            back_rank = 7 if puzzle.pov else 0
            return (
                    square_rank(king_square) == back_rank and 
                    square_file(king_square) in king_files and
                    len(board.piece_map()) >= nb_pieces # no endgames
                )
    return False

def clearance(puzzle: Puzzle) -> bool:
    for node in puzzle.mainline[1::2][1:]:
        board = node.board()
        if not node.parent.board().piece_at(node.move.to_square):
            piece = board.piece_at(node.move.to_square)
            if piece and piece.piece_type in util.ray_piece_types:
                prev = node.parent.parent
                assert prev
                prev_move = prev.move
                assert prev_move
                assert isinstance(node.parent, ChildNode)
                if (not prev_move.promotion and
                    prev_move.to_square != node.move.from_square and
                    prev_move.to_square != node.move.to_square and
                    not node.parent.board().is_check() and
                    (not board.is_check() or util.moved_piece_type(node.parent) != KING)):
                    if (prev_move.from_square == node.move.to_square or 
                        prev_move.from_square in SquareSet.between(node.move.from_square, node.move.to_square)):
                        if prev.parent and not prev.parent.board().piece_at(prev_move.to_square) or util.is_in_bad_spot(prev.board(), prev_move.to_square):
                            return True
    return False

def en_passant(puzzle: Puzzle) -> bool:
    for node in puzzle.mainline[1::2]:
        if (util.moved_piece_type(node) == PAWN and 
            square_file(node.move.from_square) != square_file(node.move.to_square) and
            not node.parent.board().piece_at(node.move.to_square)
        ):
            return True
    return False

def promotion(puzzle: Puzzle) -> bool:
    for node in puzzle.mainline[1::2]:
        if node.move.promotion:
            return True
    return False

def capturing_defender(puzzle: Puzzle) -> bool:
    for node in puzzle.mainline[1::2][1:]:
        board = node.board()
        capture = node.parent.board().piece_at(node.move.to_square)
        if board.is_checkmate() or (
            capture and 
            util.moved_piece_type(node) != KING and
            util.values[capture.piece_type] <= util.values[util.moved_piece_type(node)] and
            util.is_hanging(node.parent.board(), capture, node.move.to_square)):
            prev = node.parent.parent
            assert isinstance(prev, ChildNode)
            if not prev.board().is_check() and prev.move.to_square != node.move.from_square:
                assert node.parent.parent
                assert node.parent.parent.parent
                init_board = node.parent.parent.parent.board()
                defender_square = prev.move.to_square
                defender = init_board.piece_at(defender_square)
                if (defender and 
                    defender_square in init_board.attackers(defender.color, node.move.to_square) and
                    not init_board.is_check()):
                    return True
    return False

def piece_endgame(puzzle: Puzzle, piece_type: PieceType) -> bool:
    board: Board = puzzle.mainline[0].board()
    if not board.pieces(piece_type, WHITE) and not board.pieces(piece_type, BLACK):
        return False
    for piece in board.piece_map().values():
        if not piece.piece_type in [KING, PAWN, piece_type]:
            return False
    return True

def smothered_mate(puzzle: Puzzle) -> bool:
    board = puzzle.game.end().board()
    king_square = board.king(not puzzle.pov)
    assert king_square is not None
    for checker_square in board.checkers():
        piece = board.piece_at(checker_square)
        assert piece
        if piece.piece_type == KNIGHT:
            for escape_square in [s for s in chess.SQUARES if square_distance(s, king_square) == 1]:
                blocker = board.piece_at(escape_square)
                if not blocker or blocker.color == puzzle.pov:
                    return False
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
    return "mateIn5"
