import pymongo
import logging
import argparse
from multiprocessing import Pool
from datetime import datetime
from chess import Move, Board
from chess.pgn import Game, GameNode
from chess.engine import SimpleEngine
from typing import List, Tuple, Dict, Any
from model import Puzzle, TagKind
import cook
from zugzwang import zugzwang

logger = logging.getLogger(__name__)
logging.basicConfig(format='%(asctime)s %(levelname)-4s %(message)s', datefmt='%m/%d %H:%M')
logger.setLevel(logging.INFO)

def read(doc) -> Puzzle:
    board = Board(doc["fen"])
    node: GameNode = Game.from_board(board)
    for uci in doc["line"].split(' '):
        move = Move.from_uci(uci)
        node = node.add_main_variation(move)
    return Puzzle(doc["_id"], node.game())

if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog='tagger.py', description='automatically tags lichess puzzles')
    parser.add_argument("--zug", "-z", help="only zugzwang", action="store_true")
    parser.add_argument("--dry", "-d", help="dry run", action="store_true")
    parser.add_argument("--all", "-a", help="don't skip existing", action="store_true")
    parser.add_argument("--threads", "-t", help="count of cpu threads for engine searches", default="4")
    args = parser.parse_args()
    mongo = pymongo.MongoClient()
    db = mongo['puzzler']
    play_coll = db['puzzle2_puzzle']
    round_coll = db['puzzle2_round']
    nb = 0

    if args.zug:
        engine = SimpleEngine.popen_uci('./stockfish')
        engine.configure({'Threads': args.threads})
        theme = {"t":"+zugzwang"}
        for doc in play_coll.find():
            puzzle = read(doc)
            round_id = f'lichess:{puzzle.id}'
            if round_coll.count_documents({"_id": round_id, "t": {"$in": ["+zugzwang", "-zugzwang"]}}):
                continue
            zug = zugzwang(engine, puzzle)
            if zug:
                cook.log(puzzle)
            round_coll.update_one(
                { "_id": round_id }, 
                {"$addToSet": {"t": "+zugzwang" if zug else "-zugzwang"}}
            )
            play_coll.update_one({"_id":puzzle.id},{"$set":{"dirty":True}})
            nb += 1
            if nb % 1024 == 0:
                logger.info(nb)
        exit(0)

    def tags_of(doc) -> Tuple[str, List[TagKind]]:
        puzzle = read(doc)
        try:
            tags = cook.cook(puzzle)
        except Exception as e:
            logger.error(puzzle)
            logger.error(e)
            tags = []
        return puzzle.id, tags

    def process_batch(batch: List[Dict[str, Any]]):
        puzzle_ids = []
        for id, tags in pool.imap_unordered(tags_of, batch):
            round_id = f"lichess:{id}"
            if not args.dry:
                existing = round_coll.find_one({"_id": round_id})
                zugs = [t for t in existing["t"] if t in ['+zugzwang', '-zugzwang']] if existing else []
                round_coll.update_one({
                    "_id": round_id
                }, {
                    "$set": {
                        "p": id,
                        "d": datetime.now(),
                        "e": 50,
                        "t": [f"+{t}" for t in tags] + zugs
                    }
                }, upsert = True);
                puzzle_ids.append(id)
        if puzzle_ids:
            play_coll.update_many({"_id":{"$in":puzzle_ids}},{"$set":{"dirty":True}})

    with Pool(processes=int(args.threads)) as pool:
        batch: List[Dict[str, Any]] = []
        for doc in play_coll.find():
            id = doc["_id"]
            if not args.all and round_coll.count_documents({"_id": f"lichess:{id}", "t.1": {"$exists":True}}):
                continue
            if len(batch) < 1024:
                batch.append(doc)
                continue
            process_batch(batch)
            nb += len(batch)
            logger.info(nb)
            batch = []
        process_batch(batch)
