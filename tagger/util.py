import chess
from chess import square_rank, Move, WHITE, BLACK
from chess.pgn import Game, GameNode

def moved_piece_type(node: GameNode) -> chess.PieceType:
    return node.board().piece_type_at(node.move.to_square)

def is_pawn_move(node: GameNode) -> bool:
    return moved_piece_type(node) == chess.PAWN

def is_king_move(node: GameNode) -> bool:
    return moved_piece_type(node) == chess.KING

def is_capture(node: GameNode) -> bool:
    return "x" in node.san()
