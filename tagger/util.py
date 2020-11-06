from typing import List, Optional, Tuple, Literal, Union
import chess
from chess import square_rank, Move, Color, Board, Square, Piece
from chess.pgn import Game, GameNode

def moved_piece_type(node: GameNode) -> chess.PieceType:
    return node.board().piece_type_at(node.move.to_square)

def is_pawn_move(node: GameNode) -> bool:
    return moved_piece_type(node) == chess.PAWN

def is_advanced_pawn_move(node: GameNode) -> bool:
    if node.move.promotion:
        return True
    if not is_pawn_move(node):
        return False
    to_rank = square_rank(node.move.to_square)
    return to_rank < 5 if node.turn() else to_rank > 4

def is_king_move(node: GameNode) -> bool:
    return moved_piece_type(node) == chess.KING

def is_capture(node: GameNode) -> bool:
    return "x" in node.san()

def next_node(node: GameNode) -> Optional[GameNode]:
    return node.variations[0] if node.variations else None

def next_next_node(node: GameNode) -> Optional[GameNode]:
    nn = next_node(node)
    return next_node(nn) if nn else None

values = { chess.PAWN: 1, chess.KNIGHT: 3, chess.BISHOP: 3, chess.ROOK: 5, chess.QUEEN: 9 }

def piece_value(piece_type: chess.PieceType) -> int:
    return values[piece_type]

def material_count(board: Board, side: Color) -> int:
    return sum(len(board.pieces(piece_type, side)) * value for piece_type, value in values.items())

def material_diff(board: Board, side: Color) -> int:
    return material_count(board, side) - material_count(board, not side)

def attacked_opponent_pieces(board: Board, from_square: Square, pov: Color) -> List[Piece]:
    return [piece for (piece, square) in attacked_opponent_squares(board, from_square, pov)]

def attacked_opponent_squares(board: Board, from_square: Square, pov: Color) -> List[Tuple[Piece, Square]]:
    pieces = []
    for attacked_square in board.attacks(from_square):
        attacked_piece = board.piece_at(attacked_square)
        if attacked_piece and attacked_piece.color != pov:
            pieces.append((attacked_piece, attacked_square))
    return pieces

def is_defended(board: Board, piece: Piece, square: Square) -> bool:
    return board.attackers(piece.color, square)

def is_hanging(board: Board, piece: Piece, square: Square) -> bool:
    return not is_defended(board, piece, square)

def can_be_taken_by_lower_piece(board: Board, piece: Piece, square: Square) -> bool:
    for attacker_square in board.attackers(not piece.color, square):
        attacker = board.piece_at(attacker_square)
        if attacker.piece_type != chess.KING and values[attacker.piece_type] < values[piece.piece_type]:
            return True
    return False

def is_in_bad_spot(board: Board, square: Square) -> bool:
    # hanging or takeable by lower piece
    piece = board.piece_at(square)
    return (board.attackers(not piece.color, square) and
            (is_hanging(board, piece, square) or can_be_taken_by_lower_piece(board, piece, square)))

def is_trapped(board: Board, square: Square) -> bool:
    if board.is_check() or board.is_pinned(board.turn, square):
        return False
    piece = board.piece_at(square)
    if not is_in_bad_spot(board, square):
        return False
    for escape in board.legal_moves:
        if escape.from_square == square:
            board.push(escape)
            if not is_in_bad_spot(board, escape.to_square):
                return False
            board.pop()
    return True

# def takers(board: Board, square: Square) -> List[Tuple[Piece, Square]]:
#     # pieces that can legally take on a square
#     t = []
#     for attack in board.legal_moves:
#         if attack.to_square == square:
#             t.append((board.piece_at(attack.from_square), attack.from_square))
#     return t
