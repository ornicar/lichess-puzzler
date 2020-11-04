import pymongo
import logging
import sys
import argparse
import cook
from chess import Move, Color, Board, WHITE, BLACK
from chess.pgn import Game, GameNode
from typing import List, Optional, Tuple, Literal, Union
from model import Puzzle

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

def main() -> None:
    sys.setrecursionlimit(10000) # else node.deepcopy() sometimes fails?
    parser = argparse.ArgumentParser(prog='tagger.py', description='automatically tags lichess puzzles')
    parser.add_argument("--verbose", "-v", help="increase verbosity", action="count")
    args = parser.parse_args()
    if args.verbose == 1:
        logger.setLevel(logging.DEBUG)
    mongo = pymongo.MongoClient()
    db = mongo['puzzler']
    puzzle_coll = db['puzzle2']
    tag_coll = db['tag']

    for doc in puzzle_coll.find():
    # for doc in puzzle_coll.find({"_id":"yUM8F"}):
        puzzle = read(doc)
        tags = cook.cook(puzzle)
        for tag in tags:
            tag_coll.update_one({"_id":puzzle.id},{"$addToSet":{tag: "lichess"}}, upsert = True)

if __name__ == "__main__":
    main()
