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

version = 47

logger = logging.getLogger(__name__)
logging.basicConfig(format='%(asctime)s %(levelname)-4s %(message)s', datefmt='%m/%d %H:%M')

pair_limit = chess.engine.Limit(depth = 50, time = 30, nodes = 30_000_000)
mate_defense_limit = chess.engine.Limit(depth = 15, time = 10, nodes = 10_000_000)

mate_soon = Mate(15)

def is_valid_mate_in_one(pair: NextMovePair, engine: SimpleEngine) -> bool:
    if pair.best.score != Mate(1):
        return False
    non_mate_win_threshold = 0.6
    if not pair.second or win_chances(pair.second.score) <= non_mate_win_threshold:
        return True
    if pair.second.score == Mate(1):
        # if there's more than one mate in one, gotta look if the best non-mating move is bad enough
        logger.debug('Looking for best non-mating move...')
        info = engine.analyse(pair.node.board(), multipv = 5, limit = pair_limit)
        for score in [pv["score"].pov(pair.winner) for pv in info]:
            if score < Mate(1) and win_chances(score) > non_mate_win_threshold:
                return False
        return True
    return False

# is pair.best the only continuation?
def is_valid_attack(pair: NextMovePair, engine: SimpleEngine) -> bool:
    return (
        pair.second is None or 
        is_valid_mate_in_one(pair, engine) or 
        win_chances(pair.best.score) > win_chances(pair.second.score) + 0.7
    )

def get_next_pair(engine: SimpleEngine, node: ChildNode, winner: Color) -> Optional[NextMovePair]:
    pair = get_next_move_pair(engine, node, winner, pair_limit)
    if node.board().turn == winner and not is_valid_attack(pair, engine):
        logger.debug("No valid attack {}".format(pair))
        return None
    return pair

def get_next_move(engine: SimpleEngine, node: ChildNode, limit: chess.engine.Limit) -> Optional[Move]:
    result = engine.play(node.board(), limit = limit)
    return result.move if result else None

def cook_mate(engine: SimpleEngine, node: ChildNode, winner: Color) -> Optional[List[Move]]:
    
    board = node.board()

    if board.is_game_over():
        return []

    if board.turn == winner:
        pair = get_next_pair(engine, node, winner)
        if not pair:
            return None
        if pair.best.score < mate_soon:
            logger.debug("Best move is not a mate, we're probably not searching deep enough")
            return None
        move = pair.best.move
    else:
        next = get_next_move(engine, node, mate_defense_limit)
        if not next:
            return None
        move = next

    follow_up = cook_mate(engine, node.add_main_variation(move), winner)

    if follow_up is None:
        return None

    return [move] + follow_up


def cook_advantage(engine: SimpleEngine, node: ChildNode, winner: Color) -> Optional[List[NextMovePair]]:
    
    board = node.board()

    if board.is_repetition(2):
        logger.debug("Found repetition, canceling")
        return None

    pair = get_next_pair(engine, node, winner)
    if not pair:
        return []
    if pair.best.score < Cp(200):
        logger.debug("Not winning enough, aborting")
        return None

    follow_up = cook_advantage(engine, node.add_main_variation(pair.best.move), winner)

    if follow_up is None:
        return None

    return [pair] + follow_up


def analyze_game(server: Server, engine: SimpleEngine, game: Game, tier: int) -> Optional[Puzzle]:

    logger.debug(f'Analyzing tier {tier} {game.headers.get("Site")}...')

    prev_score: Score = Cp(20)

    for node in game.mainline():

        current_eval = node.eval()

        if not current_eval:
            logger.debug("Skipping game without eval on ply {}".format(node.ply()))
            return None

        result = analyze_position(server, engine, node, prev_score, current_eval, tier)

        if isinstance(result, Puzzle):
            return result

        prev_score = -result

    logger.debug("Found nothing from {}".format(game.headers.get("Site")))

    return None


def analyze_position(server: Server, engine: SimpleEngine, node: ChildNode, prev_score: Score, current_eval: PovScore, tier: int) -> Union[Puzzle, Score]:

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
    elif score >= Mate(1) and tier < 3:
        logger.debug("{} mate in one".format(node.ply()))
        return score
    elif score > mate_soon:
        logger.debug("Mate {}#{} Probing...".format(game_url, node.ply()))
        if server.is_seen_pos(node):
            logger.debug("Skip duplicate position")
            return score
        mate_solution = cook_mate(engine, copy.deepcopy(node), winner)
        if mate_solution is None or (tier == 1 and len(mate_solution) == 3):
            return score
        return Puzzle(node, mate_solution, 999999999)
    elif score >= Cp(200) and win_chances(score) > win_chances(prev_score) + 0.6:
        if score < Cp(400) and material_diff(board, winner) > -1:
            logger.debug("Not clearly winning and not from being down in material, aborting")
            return score
        logger.debug("Advantage {}#{} {} -> {}. Probing...".format(game_url, node.ply(), prev_score, score))
        if server.is_seen_pos(node):
            logger.debug("Skip duplicate position")
            return score
        puzzle_node = copy.deepcopy(node)
        solution : Optional[List[NextMovePair]] = cook_advantage(engine, puzzle_node, winner)
        server.set_seen(node.game())
        if not solution:
            return score
        while len(solution) % 2 == 0 or not solution[-1].second:
            if not solution[-1].second:
                logger.debug("Remove final only-move")
            solution = solution[:-1]
        if not solution or len(solution) == 1 :
            logger.debug("Discard one-mover")
            return score
        if tier < 3 and len(solution) == 3:
            logger.debug("Discard two-mover")
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
    parser.add_argument("--engine", "-e", help="analysis engine", default="./stockfish")
    parser.add_argument("--threads", "-t", help="count of cpu threads for engine searches", default="4")
    parser.add_argument("--url", "-u", help="URL where to post puzzles", default="http://localhost:8000")
    parser.add_argument("--token", help="Server secret token", default="changeme")
    parser.add_argument("--skip", help="How many games to skip from the source", default="0")
    parser.add_argument("--verbose", "-v", help="increase verbosity", action="count")
    parser.add_argument("--parts", help="how many parts", default="8")
    parser.add_argument("--part", help="which one of the parts", default="0")

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
    else:
        logger.setLevel(logging.INFO)
    engine = make_engine(args.engine, args.threads)
    server = Server(logger, args.url, args.token, version)
    games = 0
    site = "?"
    has_master = False
    tier = 0
    skip = int(args.skip)
    logger.info("Skipping first {} games".format(skip))

    parts = int(args.parts)
    part = int(args.part)
    print(f'v{version} {args.file} {part}/{parts}')

    try:
        with open_file(args.file) as pgn:
            skip_next = False
            for line in pgn:
                if line.startswith("[Site "):
                    site = line
                    games = games + 1
                    has_master = False
                    tier = 4
                elif games < skip:
                    continue
                elif games % parts != part - 1:
                    continue
                if tier == 0:
                    skip_next = True
                elif line.startswith("[Variant ") and not line.startswith("[Variant \"Standard\"]"):
                    skip_next = True
                elif (
                        (line.startswith("[WhiteTitle ") or line.startswith("[BlackTitle ")) and
                        "BOT" not in line
                    ):
                    has_master = True
                else:
                    r_tier = util.rating_tier(line)
                    t_tier = util.time_control_tier(line)
                    if r_tier is not None:
                        tier = min(tier, r_tier)
                    elif t_tier is not None:
                        tier = min(tier, t_tier)
                    elif line.startswith("1. ") and skip_next:
                        logger.debug("Skip {}".format(site))
                        skip_next = False
                    elif "%eval" in line:
                        tier = tier + 1 if has_master else tier
                        game = chess.pgn.read_game(StringIO("{}\n{}".format(site, line)))
                        assert(game)
                        game_id = game.headers.get("Site", "?")[20:]
                        if server.is_seen(game_id):
                            to_skip = 0
                            logger.info(f'Game was already seen before, skipping {to_skip} - {games}')
                            skip = games + to_skip
                            continue

                        # logger.info(f'https://lichess.org/{game_id} tier {tier}')
                        try:
                            puzzle = analyze_game(server, engine, game, tier)
                            if puzzle is not None:
                                logger.info(f'v{version} {args.file} {part}/{parts} {util.avg_knps()} knps, tier {tier}, game {games}')
                                server.post(game_id, puzzle)
                        except Exception as e:
                            logger.error("Exception on {}: {}".format(game_id, e))
    except KeyboardInterrupt:
        print(f'v{version} {args.file} Game {games}')
        sys.exit(1)

    engine.close()

if __name__ == "__main__":
    main()
