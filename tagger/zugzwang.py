import chess
import chess.engine
import math
from chess import Board, Move, Color
from chess.engine import SimpleEngine, Score
from model import Puzzle

engine_limit = chess.engine.Limit(depth = 30, time = 10, nodes = 12_000_000)

def zugzwang(engine: SimpleEngine, puzzle: Puzzle) -> bool:
    for node in puzzle.mainline[1::2]:
        board = node.board()
        if board.is_check():
            continue
        if len(list(board.legal_moves)) > 15:
            continue

        score = score_of(engine, board, not puzzle.pov)

        rev_board = node.board()
        rev_board.push(Move.null())
        rev_score = score_of(engine, rev_board, not puzzle.pov)

        if win_chances(score) < win_chances(rev_score) - 0.3:
            return True

    return False

def score_of(engine: SimpleEngine, board: Board, pov: Color):
    info = engine.analyse(board, limit = engine_limit)
    if "nps" in info:
        print(f'knps: {int(info["nps"] / 1000)} kn: {int(info["nodes"] / 1000)} depth: {info["depth"]} time: {info["time"]}')
    return info["score"].pov(pov)

def win_chances(score: Score) -> float:
    """
    winning chances from -1 to 1 https://graphsketch.com/?eqn1_color=1&eqn1_eqn=100+*+%282+%2F+%281+%2B+exp%28-0.004+*+x%29%29+-+1%29&eqn2_color=2&eqn2_eqn=&eqn3_color=3&eqn3_eqn=&eqn4_color=4&eqn4_eqn=&eqn5_color=5&eqn5_eqn=&eqn6_color=6&eqn6_eqn=&x_min=-1000&x_max=1000&y_min=-100&y_max=100&x_tick=100&y_tick=10&x_label_freq=2&y_label_freq=2&do_grid=0&do_grid=1&bold_labeled_lines=0&bold_labeled_lines=1&line_width=4&image_w=850&image_h=525
    """
    mate = score.mate()
    if mate is not None:
        return 1 if mate > 0 else -1

    cp = score.score()
    return 2 / (1 + math.exp(-0.004 * cp)) - 1 if cp is not None else 0
