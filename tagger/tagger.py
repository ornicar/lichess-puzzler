import pymongo
import logging
import argparse
from multiprocessing import Process, Queue, Pool, Manager
from datetime import datetime
from chess import Move, Board
from chess.pgn import Game, GameNode
from chess.engine import SimpleEngine
from typing import List, Tuple, Dict, Any
from model import Puzzle, TagKind
import cook
import chess.engine
from zugzwang import zugzwang

logger = logging.getLogger(__name__)
logging.basicConfig(format='%(asctime)s %(levelname)-4s %(message)s', datefmt='%m/%d %H:%M')
logger.setLevel(logging.INFO)

def read(doc) -> Puzzle:
    board = Board(doc["fen"])
    node: GameNode = Game.from_board(board)
    for uci in (doc["line"].split(' ') if "line" in doc else doc["moves"]):
        move = Move.from_uci(uci)
        node = node.add_main_variation(move)
    return Puzzle(doc["_id"], node.game(), int(doc["cp"]) if "cp" in doc and doc["cp"] else None)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog='tagger.py', description='automatically tags lichess puzzles')
    parser.add_argument("--zug", "-z", help="only zugzwang", action="store_true")
    parser.add_argument("--eval", "-e", help="only evals", action="store_true")
    parser.add_argument("--dry", "-d", help="dry run", action="store_true")
    parser.add_argument("--all", "-a", help="don't skip existing", action="store_true")
    parser.add_argument("--threads", "-t", help="count of cpu threads for engine searches", default="4")
    args = parser.parse_args()
    mongo = pymongo.MongoClient()
    db = mongo['puzzler']
    build_coll = db['puzzle2']
    play_coll = db['puzzle2_puzzle']
    round_coll = db['puzzle2_round']
    nb = 0

    if args.zug:
        threads = int(args.threads)
        def cruncher(thread_id: int):
            db = pymongo.MongoClient()['puzzler']
            round_coll = db['puzzle2_round']
            play_coll = db['puzzle2_puzzle']
            engine = SimpleEngine.popen_uci('./stockfish')
            engine.configure({'Threads': 2})
            for doc in round_coll.aggregate([
                {"$match":{"_id":{"$regex":"^lichess:"},"t":{"$nin":['+zugzwang','-zugzwang']}}},
                {'$lookup':{'from':'puzzle2_puzzle','as':'puzzle','localField':'p','foreignField':'_id'}},
                {'$unwind':'$puzzle'},{'$replaceRoot':{'newRoot':'$puzzle'}}
            ]):
                try:
                    if ord(doc["_id"][4]) % threads != thread_id:
                        continue
                    puzzle = read(doc)
                    round_id = f'lichess:{puzzle.id}'
                    zug = zugzwang(engine, puzzle)
                    if zug:
                        cook.log(puzzle)
                    round_coll.update_one(
                        { "_id": round_id }, 
                        {"$addToSet": {"t": "+zugzwang" if zug else "-zugzwang"}}
                    )
                    play_coll.update_one({"_id":puzzle.id},{"$set":{"dirty":True}})
                except Exception as e:
                    print(doc)
                    logger.error(e)
        with Pool(processes=threads) as pool:
            for i in range(int(args.threads)):
                Process(target=cruncher, args=(i,)).start()
        exit(0)

    if args.eval:
        threads = int(args.threads)
        def cruncher(thread_id: int):
            eval_nb = 0
            build_coll = pymongo.MongoClient()['puzzler']['puzzle2']
            engine = SimpleEngine.popen_uci('./stockfish')
            engine.configure({'Threads': 4})
            engine_limit = chess.engine.Limit(depth = 30, time = 15, nodes = 12_000_000)
            for doc in build_coll.find({"cp": None}):
                try:
                    if ord(doc["_id"][4]) % threads != thread_id:
                        continue
                    puzzle = read(doc)
                    board = puzzle.game.end().board()
                    if board.is_checkmate():
                        cp = 999999999
                        eval_nb += 1
                        logger.info(f'{thread_id} {eval_nb} {puzzle.id}: mate')
                    else:
                        info = engine.analyse(board, limit = engine_limit)
                        score = info["score"].pov(puzzle.pov)
                        score_cp = score.score()
                        cp = 999999999 if score.is_mate() else (999999998 if score_cp is None else score_cp)
                        eval_nb += 1
                        logger.info(f'{thread_id} {eval_nb} {puzzle.id}: {cp} knps: {int(info["nps"] / 1000)} kn: {int(info["nodes"] / 1000)} depth: {info["depth"]} time: {info["time"]}')
                    build_coll.update_one({"_id":puzzle.id},{"$set":{"cp":cp}})
                except Exception as e:
                    print(doc)
                    logger.error(e)
        with Pool(processes=threads) as pool:
            for i in range(int(args.threads)):
                Process(target=cruncher, args=(i,)).start()
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
            if len(batch) < 2048:
                batch.append(doc)
                continue
            process_batch(batch)
            nb += len(batch)
            logger.info(nb)
            batch = []
        process_batch(batch)
