from dataclasses import dataclass
import math
import chess
import chess.engine
from model import EngineMove, NextMovePair
from chess import Color, Board
from chess.pgn import GameNode
from chess.engine import SimpleEngine, Score
from typing import Optional

nps = []

def material_count(board: Board, side: Color) -> int:
    """ Weighted sum of the chess pieces for `side`.
    It does not count the value for a king.

    Args:
        board (Board): The board to analyse.
        side (Color): Player to check the material for.

    Returns:
        int: The material count for the player.
    """
    values = { chess.PAWN: 1, chess.KNIGHT: 3, chess.BISHOP: 3, chess.ROOK: 5, chess.QUEEN: 9 }
    return sum(len(board.pieces(piece_type, side)) * value for piece_type, value in values.items())

def material_diff(board: Board, side: Color) -> int:
    """ Calculates the difference in material between the player and the opponent.
    
    Args:
        board (Board): The board to analyse.
        side (Color): Player to check the material for.

    Returns:
        int: Difference in material count for the player.
    """
    return material_count(board, side) - material_count(board, not side)

def is_up_in_material(board: Board, side: Color) -> bool:
    """ Returns true if the `side` has more material on the board than the opponent.

    Args:
        board (Board): The board to analyse.
        side (Color): Player to check the material for.

    Returns:
        bool: True if `side` is up in material, False if not
    """
    return material_diff(board, side) > 0


def get_next_move_pair(engine: SimpleEngine, node: GameNode, winner: Color, limit: chess.engine.Limit) -> NextMovePair:
    """Calculates the next two best moves for player `winner` in the game `node`.

    Args:
        engine (SimpleEngine): Engine used to analyse the position.
        node (GameNode): The game being analysed.
        winner (Color): The player for which the best moves are calculated.
        limit (chess.engine.Limit): Time or resource limits for the engine when looking for moves.

    Returns:
        NextMovePair: The next move pair for the game.
    """
    info = engine.analyse(node.board(), multipv = 2, limit = limit)
 ÷  global nps
    nps.append(info[0]["nps"])
    nps = nps[-20:]
    best = EngineMove(info[0]["pv"][0], info[0]["score"].pov(winner))
    second = EngineMove(info[1]["pv"][0], info[1]["score"].pov(winner)) if len(info) > 1 else None
    return NextMovePair(node, winner, best, second)

def avg_knps() -> float:
    """Calculates the average kilonodes per second.
    The calculation is based on the global `nps` variable,
    which contains the 20 latest NPS values observed for analysing main lines.

    Returns:
        float: Observed average kilonodes per second
    """
    global nps
    return round(sum(nps) / len(nps) / 1000) if nps else 0

def win_chances(score: Score) -> float:
    """ Calculates winning chances from -1 to 1 based on a score.
    The function used to transform the centipawn score into a chance is
    :math: f(x) = \\frac{2}{1+e^{-0.004*x}} - 1
    A graph representation of the transformation can be found on:
    https://graphsketch.com/?eqn1_color=1&eqn1_eqn=100+*+%282+%2F+%281+%2B+exp%28-0.004+*+x%29%29+-+1%29&eqn2_color=2&eqn2_eqn=&eqn3_color=3&eqn3_eqn=&eqn4_color=4&eqn4_eqn=&eqn5_color=5&eqn5_eqn=&eqn6_color=6&eqn6_eqn=&x_min=-1000&x_max=1000&y_min=-100&y_max=100&x_tick=100&y_tick=10&x_label_freq=2&y_label_freq=2&do_grid=0&do_grid=1&bold_labeled_lines=0&bold_labeled_lines=1&line_width=4&image_w=850&image_h=525
    
    Args:
        score (Score): The score to base the chance on.

    Float: The transformed winning chance for the player.
    """
    mate = score.mate()
    if mate is not None:
        return 1 if mate > 0 else -1

    cp = score.score()
    return 2 / (1 + math.exp(-0.004 * cp)) - 1 if cp is not None else 0

def time_control_tier(line: str) -> Optional[int]:
    """ Function to check the time control tier for a pgn line.
    Only applies if the line specifies the timecontrol ([TimeControl] field),
    if the field is not present the function returns None.
    The tiers are based on the total time used for the first 40 moves:
        0.  time < 60 seconds 
        1.  60 seconds <= time < 180
        2.  180 seconds <= time < 480
        3.  480 seconds <= time

    Args:
        line (str): The PGN line to analyse.

    Returns:
        Optional[int]: The time control tier, or None if this does not apply.
    """
    if not line.startswith("[TimeControl "):
        return None
    try:
        seconds, increment = line[1:][:-2].split()[1].replace("\"", "").split("+")
        total = int(seconds) + int(increment) * 40
        if total >= 480:
            return 3
        if total >= 180:
            return 2
        if total > 60:
            return 1
        return 0
    except:
        return 0

def rating_tier(line: str) -> Optional[int]:
    """ Function to check the rating tier tier for a pgn line.
    Only applies if the line specifies the rating of a player (WhiteElo or BlackElo),
    otherwise the function returns None.
    The tiers are based on the ELO rating:
        0.  ELO < 1500 
        1.  1500 <= ELO < 1600
        2.  1600 <= ELO < 1750
        3.  1750 <= ELO
    Args:
        line (str): The PGN line to analyse.

    Returns:
        Optional[int]: The rating tier, or None if this does not apply.
    """
    if not line.startswith("[WhiteElo ") and not line.startswith("[BlackElo "):
        return None
    try:
        rating = int(line[11:15])
        if rating > 1750:
            return 3
        if rating > 1600:
            return 2
        if rating > 1500:
            return 1
        return 0
    except:
        return 0
