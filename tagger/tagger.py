import pymongo
import logging
import sys
import argparse
from multiprocessing import Pool
import cook
from chess import Move, Color, Board, WHITE, BLACK
from chess.pgn import Game, GameNode
from typing import List, Optional, Tuple, Literal, Union
from model import Puzzle, TagKind, static_kinds

logger = logging.getLogger(__name__)
logging.basicConfig(format='%(asctime)s %(levelname)-4s %(message)s', datefmt='%m/%d %H:%M')
logger.setLevel(logging.INFO)

def read(doc) -> Puzzle:
    board = Board(doc["fen"])
    node = Game.from_board(board)
    for uci in doc["moves"]:
        move = Move.from_uci(uci)
        node = node.add_main_variation(move)
    return Puzzle(doc["_id"], node.game())

# sys.setrecursionlimit(10000) # else node.deepcopy() sometimes fails?
parser = argparse.ArgumentParser(prog='tagger.py', description='automatically tags lichess puzzles')
parser.add_argument("--dry", "-d", help="dry run")
parser.add_argument("--verbose", "-v", help="increase verbosity", action="count")
args = parser.parse_args()
if args.verbose == 1:
    logger.setLevel(logging.DEBUG)
mongo = pymongo.MongoClient()
db = mongo['puzzler']
puzzle_coll = db['puzzle2']
tag_coll = db['tag']
nb = 0

def tags_of(doc) -> Tuple[Puzzle, List[TagKind]]:
    puzzle = read(doc)
    return puzzle.id, cook.cook(puzzle)

with Pool(processes=8) as pool:
    batch = []
    for doc in puzzle_coll.find():
        if len(batch) < 200:
            batch.append(doc)
            continue
        for id, tags in pool.imap_unordered(tags_of, batch):
            if not args.dry:
                ups = {}
                for tag in tags:
                    if not tag in static_kinds:
                        ups["{}+".format(tag)] = "lichess"
                if ups:
                    tag_coll.update_one({"_id":id},{"$addToSet":ups}, upsert = True)
                if tags:
                    puzzle_coll.update_one({"_id":id},{"$addToSet":{"tags":{"$each":tags}}})
        nb += len(batch)
        if nb % 1000 == 0:
            logger.info(nb)
        batch = []
