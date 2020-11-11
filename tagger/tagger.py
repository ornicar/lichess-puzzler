import pymongo
import logging
import sys
import argparse
from multiprocessing import Pool
from datetime import datetime
import cook
from chess import Move, Color, Board, WHITE, BLACK
from chess.pgn import Game, GameNode
from typing import List, Optional, Tuple, Literal, Union, Dict, Any
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

if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog='tagger.py', description='automatically tags lichess puzzles')
    parser.add_argument("--dry", "-d", help="dry run")
    parser.add_argument("--verbose", "-v", help="increase verbosity", action="count")
    args = parser.parse_args()
    if args.verbose == 1:
        logger.setLevel(logging.DEBUG)
    mongo = pymongo.MongoClient()
    db = mongo['puzzler']
    puzzle_coll = db['puzzle2']
    round_coll = db['round']
    nb = 0

    def tags_of(doc) -> Tuple[Puzzle, List[TagKind]]:
        puzzle = read(doc)
        return puzzle.id, cook.cook(puzzle)

    def process_batch(batch: List[Dict[str, Any]]):
        for id, tags in pool.imap_unordered(tags_of, batch):
            if not args.dry:
                round_coll.insert_one({
                    "_id": f"lichess:{id}",
                    # "u": "lichess",
                    "p": id,
                    "d": datetime.now(),
                    "w": 10,
                    "t": [f"+{t}" for t in tags if not t in static_kinds]
                })
                puzzle_coll.update_one({"_id":id},{"$addToSet":{"tags":{"$each":tags}}})

    with Pool(processes=8) as pool:
        batch = []
        for doc in puzzle_coll.find():
            id = doc["_id"]
            if round_coll.count_documents({"_id":f"lichess:{id}"}) > 0:
                continue
            if len(batch) < 200:
                batch.append(doc)
                continue
            process_batch(batch)
            nb += len(batch)
            if nb % 1000 == 0:
                logger.info(nb)
            batch = []
        process_batch(batch)
