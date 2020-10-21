import logging
import json
import time
import argparse
import requests
import chess
import chess.pgn
import chess.engine
from chess import Move, Color, Board
from chess.engine import SimpleEngine
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
get_move_limit = chess.engine.Limit(depth = 20)
has_mate_limit = chess.engine.Limit(depth = 20)

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
    """
    Returns a boolean indicating whether the side to move has a mating line available
    """
    ev = node.eval()
    if not ev or not ev.is_mate():
        return False

    found = ev.relative != chess.engine.Mate(-1) and ev.relative < chess.engine.Mate(1)

    if found:
        print(ev.relative)

    return found


def get_only_defensive_move(engine: SimpleEngine, node: GameNode) -> Optional[Move]:
    """
    Get a move for a position presumed to be defending during a mating attack
    """
    logger.debug("Getting defensive move...")
    info = engine.analyse(node.board(), multipv = 2, limit = get_move_limit)

    if not info[0]:
        return None

    if len(info) > 1:
        return None

    return info[0]["pv"][0]


# notes for if I ever refactor this function
#
#   while time.time() <= end_time and threads <= 50:
#       threads = threads+1
#       pmate,mate = determine_mates(..., threads)
#       moves = analyze_mates(pmate,mate,info_handler)
#       if moves is not None:
#           return moves
#   throw TimeoutError
def get_only_mate_move(engine: SimpleEngine, node: GameNode) -> Optional[Move]:
    """
    Takes a GameNode and returns an only moves leading to mate
    """
    logger.debug("Getting only mate move...")
    info = engine.analyse(node.board(), multipv = 2, limit = get_move_limit)

    if not info[0] or not info[0]["score"].is_mate():
        logger.debug("Best move is not a mate")
        return None

    if len(info) > 1 and info[1]["score"].is_mate():
        logger.debug("Second best move is also a mate")
        return None

    return info[0]["pv"][0]


def cook(engine: SimpleEngine, node: GameNode, side_to_mate: Color) -> Optional[List[Move]]:
    """
    Recursively calculate puzzle solution
    """

    if node.board().is_game_over():
        return []

    if node.board().turn == side_to_mate:
        move = get_only_mate_move(engine, node)
    else:
        move = get_only_defensive_move(engine, node)

    if move is None:
        return None

    next_moves = cook(engine, node.add_main_variation(move), side_to_mate)

    if next_moves is None:
        return None

    return [move] + next_moves


def analyze_game(engine: SimpleEngine, game: Game) -> Optional[Tuple[GameNode, List[Move], Kind]]:
    """
    Evaluate the moves in a game looking for puzzles
    """

    logger.debug("Analyzing game {}...".format(game.headers.get("Site", "?")))

    for node in game.mainline():

        if has_mate_in_more_than_one(engine, node):
            logger.debug("Mate found on ply {}. Probing...".format(ply_of(node.board())))
            solution = cook(engine, node, node.board().turn)
            if solution:
                return node, solution, Kind("mate")

    return None

def ply_of(board: Board) -> int:
    return board.fullmove_number * 2 - 1 if board.turn == chess.BLACK else 2

def main() -> None:
    args = parse_args()
    setup_logging(args)

    # setup the engine
    enginepath = args.engine
    engine = chess.engine.SimpleEngine.popen_uci(enginepath)
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
