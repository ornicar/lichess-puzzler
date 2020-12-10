import logging
import argparse
import chess
import chess.pgn
import chess.engine
import copy
import sys
import util
import bz2
from model import Puzzle, NextMovePair
from io import StringIO
from chess import Move, Color
from chess.engine import SimpleEngine, Mate, Cp, Score, PovScore
from chess.pgn import Game, ChildNode
from typing import List, Optional, Union
from util import get_next_move_pair, material_count, material_diff, is_up_in_material, win_chances
from server import Server

version = 29

logger = logging.getLogger(__name__)
logging.basicConfig(format='%(asctime)s %(levelname)-4s %(message)s', datefmt='%m/%d %H:%M')

get_move_limit = chess.engine.Limit(depth = 50, time = 30, nodes = 40_000_000)
mate_soon = Mate(15)
allow_one_mater = False
allow_one_mover = False

# is pair.best the only continuation?
def is_valid_attack(pair: NextMovePair, engine: SimpleEngine) -> bool:
    return (
        pair.second is None or 
        is_valid_mate_in_one(pair, engine) or 
        win_chances(pair.best.score) > win_chances(pair.second.score) + 0.64
    )

def is_valid_mate_in_one(pair: NextMovePair, engine: SimpleEngine) -> bool:
    if pair.best.score != Mate(1):
        return False
    non_mate_win_threshold = 0.5
    if not pair.second or win_chances(pair.second.score) <= non_mate_win_threshold:
        return True
    if pair.second.score == Mate(1):
        # if there's more than one mate in one, gotta look if the best non-mating move is bad enough
        logger.info('Looking for best non-mating move...')
        info = engine.analyse(pair.node.board(), multipv = 5, limit = get_move_limit)
        for score in [pv["score"].pov(pair.winner) for pv in info]:
            if score < Mate(1) and win_chances(score) > non_mate_win_threshold:
                return False
        return True
    return False

def is_valid_defense(_pair: NextMovePair) -> bool:
    return True

def get_next_move(engine: SimpleEngine, node: ChildNode, winner: Color) -> Optional[NextMovePair]:
    board = node.board()
    pair = get_next_move_pair(engine, node, winner, get_move_limit)
    logger.debug("{} {} {}".format("attack" if board.turn == winner else "defense", pair.best, pair.second))
    if board.turn == winner and not is_valid_attack(pair, engine):
        logger.debug("No valid attack {}".format(pair))
        return None
    if board.turn != winner and not is_valid_defense(pair):
        logger.debug("No valid defense {}".format(pair))
        return None
    return pair

def cook_mate(engine: SimpleEngine, node: ChildNode, winner: Color) -> Optional[List[Move]]:

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


def cook_advantage(engine: SimpleEngine, node: ChildNode, winner: Color) -> Optional[List[NextMovePair]]:

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


def analyze_position(server: Server, engine: SimpleEngine, node: ChildNode, prev_score: Score, current_eval: PovScore) -> Union[Puzzle, Score]:

    board = node.board()
    winner = board.turn
    score = current_eval.pov(winner)

    if board.legal_moves.count() < 2:
        return score

    game_url = node.game().headers.get("Site")

    logger.debug("{} {} to {}".format(node.ply(), node.move.uci() if node.move else None, score))

    if prev_score > Cp(300) and score < mate_soon:
        logger.debug("{} Too much of a winning position to start with {} -> {}".format(node.ply(), prev_score, score))
        return score
    if is_up_in_material(board, winner):
        logger.debug("{} already up in material {} {} {}".format(node.ply(), winner, material_count(board, winner), material_count(board, not winner)))
        return score
    elif score >= Mate(1) and not allow_one_mover and not allow_one_mater:
        logger.debug("{} mate in one".format(node.ply()))
        return score
    elif score > mate_soon:
        logger.info("Mate {}#{} Probing...".format(game_url, node.ply()))
        if server.is_seen_pos(node):
            logger.info("Skip duplicate position")
            return score
        mate_solution = cook_mate(engine, copy.deepcopy(node), winner)
        server.set_seen(node.game())
        return Puzzle(node, mate_solution, 999999999) if mate_solution is not None else score
    elif score >= Cp(0) and win_chances(score) > win_chances(prev_score) + 0.5:
        if score < Cp(400) and material_diff(board, winner) > -1:
            logger.info("Not clearly winning and not from being down in material, aborting")
            return score
        logger.info("Advantage {}#{} {} -> {}. Probing...".format(game_url, node.ply(), prev_score, score))
        if server.is_seen_pos(node):
            logger.info("Skip duplicate position")
            return score
        puzzle_node = copy.deepcopy(node)
        solution : Optional[List[NextMovePair]] = cook_advantage(engine, puzzle_node, winner)
        server.set_seen(node.game())
        if not solution:
            return score
        while len(solution) % 2 == 0 or not solution[-1].second:
            if not solution[-1].second:
                logger.info("Remove final only-move")
            solution = solution[:-1]
        if not solution or (len(solution) == 1 and not allow_one_mover):
            logger.info("Discard one-mover")
            return score
        cp = solution[len(solution) - 1].best.score.score()
        return Puzzle(node, [p.best.move for p in solution], 999999998 if cp is None else cp)
    else:
        return score


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog='generator.py',
        description='takes a pgn file and produces chess puzzles')
    parser.add_argument("--file", "-f", help="input PGN file", required=True, metavar="FILE.pgn")
    parser.add_argument("--engine", "-e", help="analysis engine", default="stockfish")
    parser.add_argument("--threads", "-t", help="count of cpu threads for engine searches", default="4")
    parser.add_argument("--url", "-u", help="URL where to post puzzles", default="http://localhost:8000")
    parser.add_argument("--token", help="Server secret token", default="changeme")
    parser.add_argument("--skip", help="How many games to skip from the source", default="0")
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
    if args.verbose == 2:
        logger.setLevel(logging.DEBUG)
    elif args.verbose == 1:
        logger.setLevel(logging.INFO)
    engine = make_engine(args.engine, args.threads)
    server = Server(logger, args.url, args.token, version)
    games = 0
    site = "?"
    skip = int(args.skip)
    logger.info("Skipping first {} games".format(skip))

    try:
        with open_file(args.file) as pgn:
            skip_next = False
            for line in pgn:
                if line.startswith("[Site "):
                    site = line
                    games = games + 1
                elif games < skip:
                    continue
                elif util.exclude_time_control(line) or util.exclude_rating(line):
                    skip_next = True
                elif line.startswith("1. ") and skip_next:
                    logger.debug("Skip {}".format(site))
                    skip_next = False
                elif "%eval" in line:
                    game = chess.pgn.read_game(StringIO("{}\n{}".format(site, line)))
                    assert(game)
                    game_id = game.headers.get("Site", "?")[20:]
                    if server.is_seen(game_id):
                        logger.info("Game was already seen before, skipping a bunch")
                        skip = games + 1000
                        continue

                    try:
                        puzzle = analyze_game(server, engine, game)
                        if puzzle is not None:
                            print(f'v{version} {args.file} {util.avg_knps()} knps, Game {games}')
                            server.post(game_id, puzzle)
                    except Exception as e:
                        logger.error("Exception on {}: {}".format(game_id, e))
    except KeyboardInterrupt:
        print(f'v{version} {args.file} Game {games}')
        sys.exit(1)

    engine.close()

if __name__ == "__main__":
    main()
