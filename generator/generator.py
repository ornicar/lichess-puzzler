import logging
import json
import time
import argparse
import requests
import chess
import chess.pgn
import chess.engine
from chess import Move, Color, Board
from chess.engine import SimpleEngine, Mate, Cp, Score
from chess.pgn import Game, GameNode
from typing import List, Any, Optional, Tuple, Dict, NewType

# Initialize Logging Module
logger = logging.getLogger(__name__)
logging.basicConfig(format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                    datefmt='%m-%d %H:%M')
# Uncomment this for very verbose python-chess logging
# logging.basicConfig(level=logging.DEBUG)

version = "0.0.1"
post_url = "http://localhost:8000/puzzle"
get_move_limit = chess.engine.Limit(depth = 30, time = 5)
has_mate_limit = chess.engine.Limit(depth = 30, time = 5)
mate_soon = Mate(20)

Kind = NewType('Kind', str)

def setup_logging(args: Any) -> None:
    """
    Sets logging module verbosity according to runtime arguments
    """
    if args.verbose:
        if args.verbose == 2:
            logger.setLevel(logging.DEBUG)
        elif args.verbose == 1:
            logger.setLevel(logging.INFO)


def parse_args() -> Any:
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


def has_mate_in_more_than_one(engine: SimpleEngine, node: GameNode) -> bool:
    score = node.eval()
    return score is not None and mate_soon < score.relative < Mate(1)


def get_only_defensive_move(engine: SimpleEngine, node: GameNode, winner: Color) -> Optional[Move]:
    """
    only returns a move if all other moves are utterly terrible
    """
    logger.debug("Getting defensive move...")
    info = engine.analyse(node.board(), multipv = 2, limit = get_move_limit)

    if len(info) < 1:
        return None

    best_move = info[0]
    best_score = best_move["score"].pov(winner)

    if best_score < Mate(1) and len(info) > 1:
        second_move = info[1]
        second_score = second_move["score"].pov(winner)
        much_worse = second_score == Mate(1) and best_score < Mate(3)
        if not much_worse:
            print("A second defensive move is not that worse")
            return None
        print("The second defensive move is much worse")

    return info[0]["pv"][0]


def get_only_mate_move(engine: SimpleEngine, node: GameNode, winner: Color) -> Optional[Move]:
    logger.debug("Getting only mate move...")
    info = engine.analyse(node.board(), multipv = 2, limit = get_move_limit)

    if len(info) < 1 or info[0]["score"].pov(winner) < mate_soon:
        logger.info("Best move is not a mate, we're probably not searching deep enough")
        return None

    if len(info) > 1 and info[1]["score"].pov(winner) > Cp(-400):
        logger.debug("Second best move is not terrible")
        return None

    return info[0]["pv"][0]


def material_count(board: Board, side: Color) -> int:
    values = { chess.PAWN: 1, chess.KNIGHT: 3, chess.BISHOP: 3, chess.ROOK: 5, chess.QUEEN: 9 }
    material = 0
    for piece_type in values:
        material += len(board.pieces(piece_type, side)) * values[piece_type]
    return material

def is_down_in_material(board: Board, winner: Color) -> bool:
    return material_count(board, winner) < material_count(board, not winner)

def cook(engine: SimpleEngine, node: GameNode, winner: Color) -> Optional[List[Move]]:
    """
    Recursively calculate puzzle solution
    """

    if node.board().is_game_over():
        return []

    if node.board().turn == winner:
        move = get_only_mate_move(engine, node, winner)
    else:
        move = get_only_defensive_move(engine, node, winner)

    if move is None:
        return None

    next_moves = cook(engine, node.add_main_variation(move), winner)

    if next_moves is None:
        return None

    return [move] + next_moves


def analyze_game(engine: SimpleEngine, game: Game) -> Optional[Tuple[GameNode, List[Move], Kind]]:
    """
    Evaluate the moves in a game looking for puzzles
    """

    game_url = game.headers.get("Site", "?")
    logger.debug("Analyzing game {}...".format(game_url))

    prev_score: Score = Cp(0)

    for node in game.mainline():

        ev = node.eval()

        if not ev:
            logger.debug("Skipping game without eval on move {}".format(node.board().fullmove_number))
            return None

        score = ev.relative
        winner = node.board().turn

        # was the opponent winning until their last move
        # and now I have a mate
        if prev_score < Cp(-300) and is_down_in_material(node.board(), winner) and has_mate_in_more_than_one(engine, node):
            logger.info("Mate found on {}#{}. Probing...".format(game_url, ply_of(node.board())))
            solution = cook(engine, node, winner)
            if solution:
                return node, solution, Kind("mate")

        prev_score = score

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

            if res is None:
                logger.debug("No only move sequence found.")
            else:
                node, solution, kind = res
                # Compose and print the puzzle
                puzzle : Dict[str, Any] = {
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
