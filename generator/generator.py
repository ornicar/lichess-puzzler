import logging
import json
import time
import argparse
import requests
import chess
import chess.pgn
import chess.engine
import copy
import sys
import util
import bz2
from model import Puzzle, Kind, EngineMove, NextMovePair
from io import StringIO
from chess import Move, Color, Board
from chess.engine import SimpleEngine, Mate, Cp, Score, PovScore
from chess.pgn import Game, GameNode
from typing import List, Optional, Tuple, Literal, Union
from util import EngineMove, get_next_move_pair, material_count, material_diff, is_up_in_material, win_chances
from server import Server

# Initialize Logging Module
logger = logging.getLogger(__name__)
logging.basicConfig(format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                    datefmt='%m-%d %H:%M')

version = 15
get_move_limit = chess.engine.Limit(depth = 50, time = 30, nodes = 40_000_000)
mate_soon = Mate(15)

# is pair.best the only continuation?
def is_valid_attack(pair: NextMovePair) -> bool:
    if pair.second is None:
        return True
    if pair.best.score == Mate(1):
        return True
    if pair.best.score == Mate(2):
        return pair.second.score < Cp(500)
    if pair.best.score == Mate(3):
        return pair.second.score < Cp(300)
    if win_chances(pair.best.score) > win_chances(pair.second.score) + 0.42:
        return True
    # if best move is mate, and second move still good but doesn't win material,
    # then best move is valid attack
    if pair.best.score.is_mate() and pair.second.score < Cp(400):
        next_node = pair.node.add_variation(pair.second.move)
        return not "x" in next_node.san()
    return False

def is_valid_defense(pair: NextMovePair) -> bool:
    return True
    if pair.second is None or pair.second.score == Mate(1):
        return True
    return win_chances(pair.second.score) > win_chances(pair.best.score) + 0.25

def get_next_move(engine: SimpleEngine, node: GameNode, winner: Color) -> Optional[NextMovePair]:
    board = node.board()
    pair = get_next_move_pair(engine, node, winner, get_move_limit)
    logger.debug("{} {} {}".format("attack" if board.turn == winner else "defense", pair.best, pair.second))
    if board.turn == winner and not is_valid_attack(pair):
        logger.debug("No valid attack {}".format(pair))
        return None
    if board.turn != winner and not is_valid_defense(pair):
        logger.debug("No valid defense {}".format(pair))
        return None
    return pair

def cook_mate(engine: SimpleEngine, node: GameNode, winner: Color) -> Optional[List[Move]]:

    if node.board().is_game_over():
        return []

    pair = get_next_move(engine, node, winner)

    if not pair:
        return None

    next = pair.best

    if next.score < mate_soon:
        logger.info("Best move is not a mate, we're probably not searching deep enough")
        return None

    follow_up = cook_mate(engine, node.add_main_variation(next.move), winner)

    if follow_up is None:
        return None

    return [next.move] + follow_up


def cook_advantage(engine: SimpleEngine, node: GameNode, winner: Color) -> Optional[List[NextMovePair]]:

    is_capture = "x" in node.san() # monkaS
    up_in_material = is_up_in_material(node.board(), winner)

    if node.board().is_repetition(2):
        logger.info("Found repetition, canceling")
        return None

    # if not is_capture and up_in_material and len(node.board().checkers()) == 0:
    #     logger.info("Not a capture and we're up in material, end of the line")
    #     return []

    next = get_next_move(engine, node, winner)

    if not next:
        logger.debug("No next move")
        return []

    if next.best.score.is_mate():
        logger.info("Expected advantage, got mate?!")
        return None

    follow_up = cook_advantage(engine, node.add_main_variation(next.best.move), winner)

    if follow_up is None:
        return None

    return [next] + follow_up


def analyze_game(server: Server, engine: SimpleEngine, game: Game) -> Optional[Puzzle]:

    logger.debug("Analyzing game {}...".format(game.headers.get("Site")))

    prev_score: Score = Cp(20)

    for node in game.mainline():

        current_eval = node.eval()

        if not current_eval:
            logger.debug("Skipping game without eval on ply {}".format(node.ply()))
            return None

        result = analyze_position(server, engine, node, prev_score, current_eval)

        if isinstance(result, Puzzle):
            return result

        prev_score = -result

    logger.debug("Found nothing from {}".format(game.headers.get("Site")))

    return None


def analyze_position(server: Server, engine: SimpleEngine, node: GameNode, prev_score: Score, current_eval: PovScore) -> Union[Puzzle, Score]:

    board = node.board()
    winner = board.turn
    score = current_eval.pov(winner)

    if board.legal_moves.count() < 2:
        return score

    game_url = node.game().headers.get("Site")

    logger.debug("{} {} to {}".format(node.ply(), node.move.uci() if node.move else None, score))

    if prev_score > Cp(400):
        logger.debug("{} Too much of a winning position to start with {} -> {}".format(node.ply(), prev_score, score))
        return score
    if is_up_in_material(board, winner):
        logger.debug("{} already up in material {} {} {}".format(node.ply(), winner, material_count(board, winner), material_count(board, not winner)))
        return score
    elif score >= Mate(1):
        logger.debug("{} mate in one".format(node.ply()))
        return score
    elif score > mate_soon:
        logger.info("Mate {}#{} Probing...".format(game_url, node.ply()))
        mate_solution = cook_mate(engine, copy.deepcopy(node), winner)
        server.set_seen(node.game())
        return Puzzle(node, mate_solution, "mate") if mate_solution is not None else score
    elif score >= Cp(0) and win_chances(score) > win_chances(prev_score) + 0.5:
        if score < Cp(400) and material_diff(board, winner) > -1:
            logger.info("Not clearly winning and not from being down in material, aborting")
            return score
        logger.info("Advantage {}#{} {} -> {}. Probing...".format(game_url, node.ply(), prev_score, score))
        puzzle_node = copy.deepcopy(node)
        solution : Optional[List[NextMovePair]] = cook_advantage(engine, puzzle_node, winner)
        server.set_seen(node.game())
        if solution is None or len(solution) < 3:
            return score
        while len(solution) % 2 == 0 or solution[-1].second is None:
            solution = solution[:-1]
        if len(solution) < 3:
            return score
        last = list(puzzle_node.mainline())[len(solution)]
        gain = material_diff(last.board(), winner) - material_diff(board, winner)
        return Puzzle(node, [p.best.move for p in solution], "material") if gain > 1 else score
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
    parser.add_argument("--engine", "-e", help="analysis engine", default="stockfish")
    parser.add_argument("--threads", "-t", help="count of cpu threads for engine searches", default="4")
    parser.add_argument("--url", "-u", help="URL where to post puzzles", default="http://localhost:8000")
    parser.add_argument("--token", help="Server secret token", default="changeme")
    parser.add_argument("--verbose", "-v", help="increase verbosity", action="count")

    return parser.parse_args()


def make_engine(executable: str, threads: int) -> SimpleEngine:
    engine = SimpleEngine.popen_uci(executable)
    engine.configure({'Threads': threads})
    return engine


def open_file(file: str):
    if file.endswith(".bz2"):
        return bz2.open(file, "rt")
    return open(file)

def main() -> None:
    sys.setrecursionlimit(10000) # else node.deepcopy() sometimes fails?
    args = parse_args()
    setup_logging(args)
    engine = make_engine(args.engine, args.threads)
    server = Server(logger, args.url, args.token, version)
    games = 0

    with open_file(args.file) as pgn:
        skip_next = False
        for line in pgn:
            if line.startswith("[Site "):
                site = line
                games = games + 1
            elif util.exclude_time_control(line) or util.exclude_rating(line):
                skip_next = True
            elif line.startswith("1. ") and skip_next:
                logger.debug("Skip {}".format(site))
                skip_next = False
            elif "%eval" in line:
                game = chess.pgn.read_game(StringIO("{}\n{}".format(site, line)))
                game_id = game.headers.get("Site", "?")[20:]
                if server.is_seen(game_id):
                    logger.info("Game was already seen before")
                    continue

                try:
                    puzzle = analyze_game(server, engine, game)
                    if puzzle is not None:
                        print("Game {}".format(games))
                        server.post(game_id, puzzle)
                except Exception as e:
                    logger.error("Exception on {}".format(game_id))

    engine.close()

if __name__ == "__main__":
    main()
