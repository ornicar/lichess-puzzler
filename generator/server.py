import logging
from chess.pgn import Game, GameNode
from model import Puzzle
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

retry_strategy = Retry(
    total=12,
    backoff_factor=2,
    status_forcelist=[429, 500, 502, 503, 504],
    method_whitelist=["GET", "POST"]
)
adapter = HTTPAdapter(max_retries=retry_strategy)
http = requests.Session()
http.mount("https://", adapter)
http.mount("http://", adapter)

class Server:

    def __init__(self, logger: logging.Logger, url: str, token: str, version: int) -> None:
        self.logger = logger
        self.url = url
        self.token = token
        self.version = version

    def is_seen(self, id: str) -> bool:
        if not self.url:
            return False
        try:
            status = http.get(self._seen_url(id)).status_code
            return status == 200
        except Exception as e:
            self.logger.error(e)
            return False

    def set_seen(self, game: Game) -> None:
        try:
            if self.url:
                http.post(self._seen_url(game.headers.get("Site", "?")[20:]))
        except Exception as e:
            self.logger.error(e)

    def _seen_url(self, id: str) -> str:
        return "{}/seen?token={}&id={}".format(self.url, self.token, id)

    def post(self, game_id: str, puzzle: Puzzle) -> None:
        parent : GameNode = puzzle.node.parent
        json = {
            'game_id': game_id,
            'fen': parent.board().fen(),
            'ply': parent.ply(),
            'moves': [puzzle.node.uci()] + list(map(lambda m : m.uci(), puzzle.moves)),
            'generator_version': self.version,
        }
        try:
            r = http.post("{}/puzzle?token={}".format(self.url, self.token), json=json)
            self.logger.info(r.text if r.ok else "FAILURE {}".format(r.text))
        except Exception as e:
            self.logger.error("Couldn't post puzzle: {}".format(e))
