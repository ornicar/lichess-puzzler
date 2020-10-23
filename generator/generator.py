import logging
import json
import time
import argparse
import requests
import chess
import chess.pgn
import chess.engine
import math
from chess import Move, Color, Board
from chess.engine import SimpleEngine, Mate, Cp, Score, InfoDict
from chess.pgn import Game, GameNode
from dataclasses import dataclass
from typing import List, Optional, Tuple, Dict, Literal

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
juicy_advantage = Cp(300)

Kind = Literal["mate", "material"]  # Literal["mate", "other"]

@dataclass
class EngineMove:
    move: Move
    score: Score

@dataclass
class NextMovePair:
    best: EngineMove
    second: Optional[EngineMove]
    def is_only_move(self) -> bool:
        return self.second is None or is_much_better(self.best.score, self.second.score)

def setup_logging(args: argparse.Namespace) -> None:
    """
    Sets logging module verbosity according to runtime arguments
    """
    if args.verbose:
        if args.verbose == 2:
            logger.setLevel(logging.DEBUG)
        elif args.verbose == 1:
            logger.setLevel(logging.INFO)


def parse_args() -> argparse.Namespace:
    """
    Define an argument parser and return the parsed arguments
    """
    parser = argparse.ArgumentParser(
        prog='generator.py',
        description='takes a pgn file and produces chess puzzles')
    parser.add_argument("--file", "-f", help="input PGN file", required=True, metavar="FILE.pgn")
    parser.add_argument("--engine", "-e", help="analysis engine", default="stockfish")
    parser.add_argument("--threads", "-t", help="count of cpu threads for engine searches", default="4")
    parser.add_argument("--verbose", "-v", help="increase verbosity", action="count")

    return parser.parse_args()


def material_count(board: Board, side: Color) -> int:
    values = { chess.PAWN: 1, chess.KNIGHT: 3, chess.BISHOP: 3, chess.ROOK: 5, chess.QUEEN: 9 }
    return sum(len(board.pieces(piece_type, side)) * value for piece_type, value in values.items())

def is_down_in_material(board: Board, winner: Color) -> bool:
    return material_count(board, winner) < material_count(board, not winner)


def get_next_move_pair(engine: SimpleEngine, board: Board, winner: Color) -> NextMovePair:
    info = engine.analyse(board, multipv = 2, limit = get_move_limit)
    best = EngineMove(info[0]["pv"][0], info[0]["score"].pov(winner))
    second = EngineMove(info[1]["pv"][0], info[1]["score"].pov(winner)) if len(info) > 1 else None
    return NextMovePair(best, second)


def cook_mate(engine: SimpleEngine, node: GameNode, winner: Color) -> Optional[List[Move]]:
    """
    Recursively calculate mate solution
    """

    if node.board().is_game_over():
        return []

    next = get_next_move_pair(engine, node.board(), winner)

    if not next.is_only_move():
        return None

    if node.board().turn == winner:
        logger.debug("Getting only mate move...")

        if best_move.score < mate_soon:
            logger.info("Best move is not a mate, we're probably not searching deep enough")
            return None

    else:
        logger.debug("Getting defensive move...")

        if best_move.score < Mate(1) and second_move is not None:
            much_worse = second_move.score == Mate(1) and best_move.score < Mate(3)
            if not much_worse:
                logger.debug("A second defensive move is not that worse: {}".format(second_move.move))
                return None

    next_moves = cook_mate(engine, node.add_main_variation(best_move.move), winner)

    if next_moves is None:
        return None

    return [best_move.move] + next_moves


def cook_advantage(engine: SimpleEngine, node: GameNode, winner: Color) -> Optional[List[Move]]:
    """
    Recursively calculate advantage solution
    """

    is_capture = "x" in node.san() # monkaS
    up_in_material = is_down_in_material(node.board(), not winner)

    if not is_capture and up_in_material and len(node.board().checkers()) == 0:
        logger.info("Not a capture and we're up in material, end of the line")
        return []

    next = get_next_move_pair(engine, node.board(), winner)

    if not next.is_only_move():
        return None

    if next.best.score < juicy_advantage:
        logger.info("Best move is not a juicy advantage, we're probably not searching deep enough")
        return None

    if next.best.score.is_mate():
        logger.info("Expected advantage, got mate?!")
        return None

    next_moves = cook_advantage(engine, node.add_main_variation(move), winner)

    if next_moves is None:
        return None

    return [move] + next_moves


def win_chances(score: Score) -> float:
    """
    winning chances from -1 to 1 https://graphsketch.com/?eqn1_color=1&eqn1_eqn=100+*+%282+%2F+%281+%2B+exp%28-0.005+*+x%29%29+-+1%29&eqn2_color=2&eqn2_eqn=100+*+%282+%2F+%281+%2B+exp%28-0.004+*+x%29%29+-+1%29&eqn3_color=3&eqn3_eqn=&eqn4_color=4&eqn4_eqn=&eqn5_color=5&eqn5_eqn=&eqn6_color=6&eqn6_eqn=&x_min=-1000&x_max=1000&y_min=-100&y_max=100&x_tick=100&y_tick=10&x_label_freq=2&y_label_freq=2&do_grid=0&do_grid=1&bold_labeled_lines=0&bold_labeled_lines=1&line_width=4&image_w=850&image_h=525
    """
    mate = score.mate()
    if mate is not None:
        return 1 if mate > 0 else 0

    cp = score.score()
    return 2 / (1 + math.exp(-0.004 * cp)) - 1 if cp is not None else 0


def is_much_better(score: Score, than: Score) -> bool:
    if score == Mate(1) and than < Mate(2):
        return True
    return win_chances(score) > win_chances(than) + 0.3

def is_much_worse(score: Score, than: Score) -> bool:
    return is_much_better(than, score)

def analyze_game(engine: SimpleEngine, game: Game) -> Optional[Tuple[GameNode, List[Move], Kind]]:
    """
    Evaluate the moves in a game looking for puzzles
    """

    game_url = game.headers.get("Site", "?")
    logger.debug("Analyzing game {}...".format(game_url))

    prev_score: Score = Cp(0)

    for node in game.mainline():

        ply = ply_of(node.board())
        ev = node.eval()

        if not ev:
            # logger.debug("Skipping game without eval on ply {}".format(ply_of(node.board())))
            return None

        winner = node.board().turn
        score = ev.pov(winner)

        # was the opponent winning until their last move
        if prev_score > Cp(-100):
            logger.debug("{} no mistake made {} -> {}".format(ply, prev_score, score))
            pass
        elif not is_down_in_material(node.board(), winner):
            logger.debug("{} not down in material {} {} {}".format(ply, winner, material_count(node.board(), winner), material_count(node.board(), not winner)))
            pass
        elif score >= Mate(1):
            logger.debug("{} mate in one".format(ply))
            pass
        elif score > mate_soon:
            # pass
            logger.info("Mate {}#{}. Probing...".format(game_url, ply))
            solution = cook_mate(engine, node, winner)
            if solution is not None:
                return node, solution, "mate"
        elif score > juicy_advantage:
            # logger.info("Advantage {}#{}. {} -> {}. Probing...".format(game_url, ply, prev_score, score))
            solution = cook_advantage(engine, node, winner)
            if solution is not None and len(solution) > 2:
                return node, solution, "material"
        else:
            pass

        prev_score = -score

    return None

def ply_of(board: Board) -> int:
    return board.fullmove_number * 2 - (1 if board.turn == chess.BLACK else 2)

def main() -> None:
    args = parse_args()
    setup_logging(args)

    # setup the engine
    enginepath = args.engine
    engine = SimpleEngine.popen_uci(enginepath)
    engine.configure({'Threads': args.threads})

    with open(args.file) as pgn:
        for game in iter(lambda: chess.pgn.read_game(pgn), None):

            res = analyze_game(engine, game)

            if res is not None:
                node, solution, kind = res
                # Compose and print the puzzle
                puzzle = {
                    'game_id': game.headers.get("Site", "?")[20:],
                    'fen': node.board().fen(),
                    'ply': ply_of(node.board()),
                    'moves': list(map(lambda m : m.uci(), solution)),
                    'kind': kind,
                    'generator_version': version,
                }
                r = requests.post(post_url, json=puzzle)
                logger.info(r.text if r.ok else "FAILURE {}".format(r.text))


if __name__ == "__main__":
    main()

# vim: ft=python expandtab smarttab shiftwidth=4 softtabstop=4 fileencoding=UTF-8:
