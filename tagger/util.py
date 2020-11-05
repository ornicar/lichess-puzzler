from typing import List, Optional, Tuple, Literal, Union
import chess
from chess import square_rank, Move, Color, Board
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
