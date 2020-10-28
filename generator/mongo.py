import pymongo
from chess.pgn import Game

client = pymongo.MongoClient('mongodb://localhost:27017/')
db = client.puzzler

def is_seen(id: str) -> bool:
    return db.seen.count({"_id": id}) > 0

def set_seen(game: Game) -> None:
    try:
        db.seen.insert({"_id": id_of(game)})
    except pymongo.errors.DuplicateKeyError:
        pass

def id_of(game: Game) -> str:
    return game.headers.get("Site", "?")[20:]
