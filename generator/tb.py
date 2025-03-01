import datetime
import logging
import time

import chess
import requests

from typing import Optional, Literal, Dict, Any

from chess import Color
from chess.pgn import GameNode
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

from model import NextMovePair, TbPair, EngineMove

TB_API = "http://tablebase.lichess.ovh/standard?fen={}"


WDL = Literal["win", "draw", "loss", "unknown", "maybe-win", "blessed-loss", "maybe-loss", "cursed-win"]

RETRY_STRAT = Retry(
    total=5,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504],
    # in future versions `method_whitelist` is removed and replaced by `allowed_methods`
    method_whitelist=["GET"]
)
ADAPTER = HTTPAdapter(max_retries=RETRY_STRAT)

class TbChecker:

    def __init__(self, log: logging.Logger) -> None:
        self.session = requests.Session()
        self.session.mount("http://", ADAPTER)
        self.session.mount("https://", ADAPTER)
        self.log = log
        self.last_req: Optional[datetime.datetime] = None

    def _probe(self, fen: str) -> Dict[str, Any]:
        if self.last_req is not None:
            wait = (self.last_req + datetime.timedelta(milliseconds=550) - datetime.datetime.now()).total_seconds()
            if wait > 0:
                time.sleep(wait)
        resp = self.session.get(TB_API.format(fen),timeout=5).json()
        # conservative to take last_req after the end of the request
        self.last_req = datetime.datetime.now()
        return resp

    # `*` is used to force kwarg only for `looking_for_mate`
    def get_only_winning_move(self, node: GameNode, winner: Color, *,looking_for_mate: bool) -> Optional[TbPair]:
        """
        Returns `None` if the check is not applicable:
            - The position has more than 7 pieces.
            - The puzzle is a mate puzzle. DTZ does not garantee the fastest mate. Also a mate in N puzzle
                  can be correct even if there also exists a N+1 mate.
            - It's not `winner`'s turn.
            - There is no legal moves
            - There is an error processing the API result, or if the API is unreachable.
        """
        if looking_for_mate:
            return None
        board = node.board()
        if len(chess.SquareSet(board.occupied)) > 7 or board.turn != winner:
            return None
        fen = board.fen()
        try:
            rep = self._probe(fen)
        except requests.exceptions.RequestException as e:
            self.log.warning(f"req error while checking tb for fen {fen}: {e}")
            return None
        # The API return results in descending order (best move firsts)
        # So only checking for the first two moves should be enough to know 
        # if there are more than one winning move.
        moves = rep.get("moves", [])
        if not moves:
            # No legal moves
            return None
        best = to_engine_move(moves[0], turn=not board.turn, winner=winner)
        second = None
        second_winning = False
        if len(moves) > 1:
            # from opponent's perspective
            second_winning = moves[1]["category"] in ["loss", "maybe-loss"]
            second = to_engine_move(moves[1], turn=not board.turn, winner=winner)
        only_winning_move = rep["category"] == "win" and not second_winning
        self.log.debug(f"tb check for {fen}, best move: {best}, second move: {second}, only winning move: {only_winning_move}")
        return TbPair(node=node, winner=winner, best=best, second=second,only_winning_move=only_winning_move)

def to_engine_move(move: Dict[str, Any], *,turn: Color, winner: Color) -> EngineMove:
    pov_score = chess.engine.PovScore(relative=wdl_to_cp(move["category"]),turn=turn)
    return EngineMove(chess.Move.from_uci(move["uci"]), pov_score.pov(winner))

# conservative, because considering maybe-win as a draw, and maybe-loss as a loss
def wdl_to_cp(wdl: WDL) -> chess.engine.Cp:
    if wdl == "win":
        return chess.engine.Cp(999999998)
    # using `or` for mypy
    elif wdl == "maybe-win" or wdl == "cursed-win" or wdl == "draw" or wdl == "blessed-loss":
        return chess.engine.Cp(0)
    # using `or` for mypy
    elif wdl == "unknown" or wdl == "maybe-loss" or wdl == "loss":
        return chess.engine.Cp(-999999998)



