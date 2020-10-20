import { ServerData } from './types';
import { Uci, San } from '../../back/src/puzzle';
import { Api as Chessground } from 'chessground/api';
import { Key } from 'chessground/types';
import { Chess, parseUci } from 'chessops';
import { makeFen, parseFen } from 'chessops/fen';
import { makeSanVariation } from 'chessops/san';
import { chessgroundDests } from 'chessops/compat';

export default class Ctrl {

  chessground: Chessground;
  chess: Chess;
  solution: San[];
  moves: Uci[] = [];

  constructor(readonly data: ServerData, readonly redraw: () => void) {
    this.chess = this.initialChess();
    this.solution = makeSanVariation(this.chess, this.data.puzzle.moves.map(uci => parseUci(uci)!)).replace(/\d\.+ /g, '').split(' ');
  }

  setChessground(cg: Chessground) {
    this.chessground = cg;
  }

  onMove = (uci: Uci) => {
    this.moves.push(uci);
    this.chess.play(parseUci(uci)!);
    this.chessground.set(this.cgConfig(uci));
    const reply = this.findReply();
    if (reply) setTimeout(() => this.onMove(reply), 200);
    this.redraw();
  }

  back = () => {
    if (!this.moves.length) return;
    this.moves = this.moves.slice(0, -1);
    this.chess = this.initialChess();
    this.moves.forEach(move => this.chess.play(parseUci(move)!));
    this.chessground.set(this.cgConfig(this.moves[this.moves.length - 1]));
    this.redraw();
  }

  private findReply = (): Uci | undefined => {
    if (this.moves.length % 2 == 0 || this.moves.length >= this.data.puzzle.moves.length) return;
    if (this.moves.join(' ') != this.data.puzzle.moves.slice(0, this.moves.length).join(' ')) return;
    return this.data.puzzle.moves[this.moves.length];
  }

  currentFen = () => makeFen(this.chess.toSetup());

  nbMovesIn = () => {
    let nb = 0;
    for (let move of this.moves) {
      if (move == this.data.puzzle.moves[nb]) nb++;
      else break;
    }
    return nb;
  }

  private cgConfig = (lastMove?: Uci) => ({
    fen: this.currentFen(),
    turnColor: this.chess.turn,
    movable: {
      color: this.chess.turn,
      dests: chessgroundDests(this.chess)
    },
    check: this.chess.isCheck(),
    lastMove: lastMove ? [lastMove.substr(0, 2) as Key, lastMove.substr(2, 2) as Key] : undefined
  });

  private initialChess = () => Chess.fromSetup(parseFen(this.data.puzzle.fen).unwrap()).unwrap();
}
