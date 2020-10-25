import logging
import json
import time
import argparse
import requests
import chess
import chess.pgn
import chess.engine
import math
import copy
from chess import Move, Color, Board
from chess.engine import SimpleEngine, Mate, Cp, Score, PovScore
from chess.pgn import Game, GameNode
from dataclasses import dataclass
from typing import List, Optional, Tuple, Literal, Union

# Initialize Logging Module
logger = logging.getLogger(__name__)
logging.basicConfig(format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                    datefmt='%m-%d %H:%M')
# Uncomment this for very verbose python-chess logging
# logging.basicConfig(level=logging.DEBUG)

version = "0.0.1"
post_url = "http://localhost:8000/puzzle"
get_move_limit = chess.engine.Limit(depth = 40, time = 10, nodes = 12_000_000)
has_mate_limit = get_move_limit
mate_soon = Mate(20)
juicy_advantage = Cp(500)

Kind = Literal["mate", "material"]  # Literal["mate", "other"]

@dataclass
class Puzzle:
    node: GameNode
    moves: List[Move]
    kind: Kind

@dataclass
class EngineMove:
    move: Move
    score: Score

@dataclass
class NextMovePair:
    best: EngineMove
    second: Optional[EngineMove]

    def is_valid_attack(self) -> bool:
        if self.second is None:
            return True
        if self.best.score == Mate(1) and self.second.score < Mate(2):
            return True
        return win_chances(self.best.score) > win_chances(self.second.score) + 0.3

    def is_valid_defense(self) -> bool:
        if self.second is None or self.second.score == Mate(1):
            return True
        return win_chances(self.second.score) > win_chances(self.best.score) + 0.3


def material_count(board: Board, side: Color) -> int:
    values = { chess.PAWN: 1, chess.KNIGHT: 3, chess.BISHOP: 3, chess.ROOK: 5, chess.QUEEN: 9 }
    return sum(len(board.pieces(piece_type, side)) * value for piece_type, value in values.items())

def is_up_in_material(board: Board, side: Color) -> bool:
    return material_count(board, side) > material_count(board, not side)


def get_next_move_pair(engine: SimpleEngine, board: Board, winner: Color) -> NextMovePair:
    info = engine.analyse(board, multipv = 2, limit = get_move_limit)
    best = EngineMove(info[0]["pv"][0], info[0]["score"].pov(winner))
    second = EngineMove(info[1]["pv"][0], info[1]["score"].pov(winner)) if len(info) > 1 else None
    return NextMovePair(best, second)


def get_next_move(engine: SimpleEngine, board: Board, winner: Color) -> Optional[EngineMove]:
    next = get_next_move_pair(engine, board, winner)
    if board.turn == winner and not next.is_valid_attack():
        return None
    if board.turn != winner and not next.is_valid_defense():
        return None
    return next.best

def cook_mate(engine: SimpleEngine, node: GameNode, winner: Color) -> Optional[List[Move]]:

    if node.board().is_game_over():
        return []

    next = get_next_move(engine, node.board(), winner)

    if not next:
        return None

    if next.score < mate_soon:
        logger.info("Best move is not a mate, we're probably not searching deep enough")
        return None

    next_moves = cook_mate(engine, node.add_main_variation(next.move), winner)

    if next_moves is None:
        return None

    return [next.move] + next_moves


def cook_advantage(engine: SimpleEngine, node: GameNode, winner: Color) -> Optional[List[Move]]:

    is_capture = "x" in node.san() # monkaS
    up_in_material = is_up_in_material(node.board(), winner)

    if not is_capture and up_in_material and len(node.board().checkers()) == 0:
        logger.info("Not a capture and we're up in material, end of the line")
        return []

    next = get_next_move(engine, node.board(), winner)

    if not next:
        return []

    if next.score < juicy_advantage:
        logger.info("Best move is not a juicy advantage, we're probably not searching deep enough")
        return None

    if next.score.is_mate():
        logger.info("Expected advantage, got mate?!")
        return None

    next_moves = cook_advantage(engine, node.add_main_variation(next.move), winner)

    if next_moves is None:
        return None

    return [next.move] + next_moves


def win_chances(score: Score) -> float:
    """
    winning chances from -1 to 1 https://graphsketch.com/?eqn1_color=1&eqn1_eqn=100+*+%282+%2F+%281+%2B+exp%28-0.005+*+x%29%29+-+1%29&eqn2_color=2&eqn2_eqn=100+*+%282+%2F+%281+%2B+exp%28-0.004+*+x%29%29+-+1%29&eqn3_color=3&eqn3_eqn=&eqn4_color=4&eqn4_eqn=&eqn5_color=5&eqn5_eqn=&eqn6_color=6&eqn6_eqn=&x_min=-1000&x_max=1000&y_min=-100&y_max=100&x_tick=100&y_tick=10&x_label_freq=2&y_label_freq=2&do_grid=0&do_grid=1&bold_labeled_lines=0&bold_labeled_lines=1&line_width=4&image_w=850&image_h=525
    """
    mate = score.mate()
    if mate is not None:
        return 1 if mate > 0 else 0

    cp = score.score()
    return 2 / (1 + math.exp(-0.004 * cp)) - 1 if cp is not None else 0


def analyze_game(engine: SimpleEngine, game: Game) -> Optional[Puzzle]:

    logger.debug("Analyzing game {}...".format(game.headers.get("Site")))

    prev_score: Score = Cp(20)

    for node in game.mainline():

        current_eval = node.eval()

        if not current_eval:
            logger.debug("Skipping game without eval on ply {}".format(node.ply()))
            return None

        result = analyze_position(engine, node, prev_score, current_eval)

        if isinstance(result, Puzzle):
            return result

        prev_score = -result

    return None


def analyze_position(engine: SimpleEngine, node: GameNode, prev_score: Score, current_eval: PovScore) -> Union[Puzzle, Score]:

    winner = node.board().turn
    score = current_eval.pov(winner)
    game_url = node.game().headers.get("Site")

    logger.debug("{} {} to {}".format(node.ply(), node.move.uci() if node.move else None, score))

    # # was the opponent winning until their last move
    if prev_score > Cp(0):
        logger.debug("{} no losing position to start with {} -> {}".format(node.ply(), prev_score, score))
        return score
    if is_up_in_material(node.board(), winner):
        # logger.debug("{} not down in material {} {} {}".format(node.ply(), winner, material_count(node.board(), winner), material_count(node.board(), not winner)))
        return score
    elif score >= Mate(1):
        logger.debug("{} mate in one".format(node.ply()))
        return score
    elif score > mate_soon:
        logger.info("Mate {}#{}. Probing...".format(game_url, node.ply()))
        solution = cook_mate(engine, copy.deepcopy(node), winner)
        return Puzzle(node, solution, "mate") if solution is not None else score
    elif score > juicy_advantage:
        logger.info("Advantage {}#{}. {} -> {}. Probing...".format(game_url, node.ply(), prev_score, score))
        solution = cook_advantage(engine, copy.deepcopy(node), winner)
        return Puzzle(node, solution, "material") if solution is not None and len(solution) > 2 else score
    else:
        return score


def setup_logging(args: argparse.Namespace) -> None:
    if args.verbose:
        if args.verbose == 2:
            logger.setLevel(logging.DEBUG)
        elif args.verbose == 1:
            logger.setLevel(logging.INFO)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog='generator.py',
        description='takes a pgn file and produces chess puzzles')
    parser.add_argument("--file", "-f", help="input PGN file", required=True, metavar="FILE.pgn")
    parser.add_argument("--threads", "-t", help="count of cpu threads for engine searches", default="4")
    parser.add_argument("--verbose", "-v", help="increase verbosity", action="count")

    return parser.parse_args()


def make_engine(args: argparse.Namespace) -> SimpleEngine:
    engine = SimpleEngine.popen_uci("stockfish")
    engine.configure({'Threads': args.threads})
    return engine


def main() -> None:
    args = parse_args()
    setup_logging(args)
    engine = make_engine(args)

    with open(args.file) as pgn:
        for game in iter(lambda: chess.pgn.read_game(pgn), None):

            puzzle = analyze_game(engine, game)

            if puzzle is not None:
                # Compose and print the puzzle
                json = {
                    'game_id': game.headers.get("Site", "?")[20:],
                    'fen': puzzle.node.board().fen(),
                    'ply': puzzle.node.ply(),
                    'moves': list(map(lambda m : m.uci(), puzzle.moves)),
                    'kind': puzzle.kind,
                    'generator_version': version,
                }
                r = requests.post(post_url, json=json)
                logger.info(r.text if r.ok else "FAILURE {}".format(r.text))

    engine.close()

if __name__ == "__main__":
    main()

# vim: ft=python expandtab smarttab shiftwidth=4 softtabstop=4 fileencoding=UTF-8:
