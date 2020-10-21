import logging
import json
import time
import argparse
import requests
import chess
import chess.pgn
import chess.engine
from chess import Move, Color, Board
from chess.engine import SimpleEngine, Mate, Cp, Score, InfoDict
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
get_move_limit = chess.engine.Limit(depth = 40, time = 10, nodes = 12 * 1000 * 1000)
has_mate_limit = get_move_limit
mate_soon = Mate(20)
juicy_advantage = Cp(500)

Kind = NewType('Kind', str)

class EngineMove:
    def __init__(self, move: Move, score: Score) -> None:
        self.move = move
        self.score = score

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


def material_count(board: Board, side: Color) -> int:
    values = { chess.PAWN: 1, chess.KNIGHT: 3, chess.BISHOP: 3, chess.ROOK: 5, chess.QUEEN: 9 }
    material = 0
    for piece_type in values:
        material += len(board.pieces(piece_type, side)) * values[piece_type]
    return material

def is_down_in_material(board: Board, winner: Color) -> bool:
    return material_count(board, winner) < material_count(board, not winner)


def get_two_best_moves(engine: SimpleEngine, board: Board, winner: Color) -> Tuple[EngineMove, Optional[EngineMove]]:
    info = engine.analyse(board, multipv = 2, limit = get_move_limit)
    best_move = EngineMove(info[0]["pv"][0], info[0]["score"].pov(winner))
    second_move = EngineMove(info[1]["pv"][0], info[1]["score"].pov(winner)) if len(info) > 1 else None
    return best_move, second_move


def cook_mate(engine: SimpleEngine, node: GameNode, winner: Color) -> Optional[List[Move]]:
    """
    Recursively calculate mate solution
    """

    if node.board().is_game_over():
        return []

    best_move, second_move = get_two_best_moves(engine, node.board(), winner)

    if node.board().turn == winner:
        logger.debug("Getting only mate move...")

        if best_move.score < mate_soon:
            logger.info("Best move is not a mate, we're probably not searching deep enough")
            return None

        if second_move is not None and second_move.score > Cp(-300):
            logger.debug("Second best move is not terrible")
            return None

    else:
        logger.debug("Getting defensive move...")

        if best_move.score < Mate(1) and second_move is not None:
            much_worse = second_move.score == Mate(1) and best_move.score < Mate(3)
            if not much_worse:
                logger.info("A second defensive move is not that worse")
                return None

    next_moves = cook_mate(engine, node.add_main_variation(best_move.move), winner)

    if next_moves is None:
        return None

    return [best_move.move] + next_moves


def cook_advantage(engine: SimpleEngine, node: GameNode, winner: Color) -> Optional[List[Move]]:
    """
    Recursively calculate advantage solution
    """

    best_move, second_move = get_two_best_moves(engine, node.board(), winner)

    if node.board().turn == winner:
        logger.debug("Getting only advantage move...")

        if best_move.score < juicy_advantage:
            logger.info("Best move is not a juicy advantage, we're probably not searching deep enough")
            return None

        if second_move is not None and second_move.score > Cp(-300):
            logger.debug("Second best move is not terrible")
            return None

    else:
        logger.debug("Getting defensive move...")

        if best_move.score.is_mate():
            logger.info("Expected advantage, got mate?!")
            return None

        if second_move is not None:
            much_worse = second_move.score < Mate(2)
            if not much_worse:
                logger.info("A second defensive move is not that worse")
                return None

    next_moves = cook_advantage(engine, node.add_main_variation(best_move.move), winner)

    if next_moves is None:
        return None

    return [best_move.move] + next_moves


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

        winner = node.board().turn
        score = ev.pov(winner)

        # was the opponent winning until their last move
        if prev_score > Cp(-300) or not is_down_in_material(node.board(), winner):
            pass
        elif mate_soon < score < Mate(1):
            logger.info("Mate found on {}#{}. Probing...".format(game_url, ply_of(node.board())))
            solution = cook_mate(engine, node, winner)
            if solution is not None:
                return node, solution, Kind("mate")
        elif score > juicy_advantage:
            logger.info("Advantage found on {}#{}. Probing...".format(game_url, ply_of(node.board())))
            solution = cook_advantage(engine, node, winner)
            if solution is not None:
                return node, solution, Kind("mate")
        else:
            print(score)

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
