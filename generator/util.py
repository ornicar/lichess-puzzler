from dataclasses import dataclass
import math
import chess
import chess.engine
from model import EngineMove, NextMovePair
from chess import Color, Board
from chess.pgn import GameNode
from chess.engine import SimpleEngine, Score

nps = []

def material_count(board: Board, side: Color) -> int:
    values = { chess.PAWN: 1, chess.KNIGHT: 3, chess.BISHOP: 3, chess.ROOK: 5, chess.QUEEN: 9 }
    return sum(len(board.pieces(piece_type, side)) * value for piece_type, value in values.items())

def material_diff(board: Board, side: Color) -> int:
    return material_count(board, side) - material_count(board, not side)

def is_up_in_material(board: Board, side: Color) -> bool:
    return material_diff(board, side) > 0


def get_next_move_pair(engine: SimpleEngine, node: GameNode, winner: Color, limit: chess.engine.Limit) -> NextMovePair:
    info = engine.analyse(node.board(), multipv = 2, limit = limit)
    global nps
    nps.append(info[0]["nps"])
    nps = nps[-20:]
    # print(info)
    best = EngineMove(info[0]["pv"][0], info[0]["score"].pov(winner))
    second = EngineMove(info[1]["pv"][0], info[1]["score"].pov(winner)) if len(info) > 1 else None
    return NextMovePair(node, winner, best, second)

def avg_knps():
    global nps
    return round(sum(nps) / len(nps) / 1000) if nps else 0

def win_chances(score: Score) -> float:
    """
    winning chances from -1 to 1 https://graphsketch.com/?eqn1_color=1&eqn1_eqn=100+*+%282+%2F+%281+%2B+exp%28-0.004+*+x%29%29+-+1%29&eqn2_color=2&eqn2_eqn=&eqn3_color=3&eqn3_eqn=&eqn4_color=4&eqn4_eqn=&eqn5_color=5&eqn5_eqn=&eqn6_color=6&eqn6_eqn=&x_min=-1000&x_max=1000&y_min=-100&y_max=100&x_tick=100&y_tick=10&x_label_freq=2&y_label_freq=2&do_grid=0&do_grid=1&bold_labeled_lines=0&bold_labeled_lines=1&line_width=4&image_w=850&image_h=525
    """
    mate = score.mate()
    if mate is not None:
        return 1 if mate > 0 else -1

    cp = score.score()
    return 2 / (1 + math.exp(-0.004 * cp)) - 1 if cp is not None else 0

CORRESP_TIME = 999999

def read_game_time(line: str):
    if not line.startswith("[TimeControl "):
        return None
    try:
        seconds, increment = line[1:][:-2].split()[1].replace("\"", "").split("+")
        return int(seconds) + int(increment) * 40
    except:
        # correspondence probably
        return CORRESP_TIME

def exclude_time_control(line: str) -> bool:
    t = read_game_time(line)
    return t == CORRESP_TIME or (t and t < 480)

def exclude_master_time_control(line: str) -> bool:
    t = read_game_time(line)
    return t == CORRESP_TIME or (t and (t < 160 or t >=480))

def exclude_rating(line: str) -> bool:
    if not line.startswith("[WhiteElo ") and not line.startswith("[BlackElo "):
        return False
    try:
        return int(line[11:15]) < 1600
    except:
        return False
