import { ServerData } from './types';
import { Uci, San } from '../../back/src/puzzle';
import { Api as Chessground } from 'chessground/api';
import { Key } from 'chessground/types';
import { Chess, parseUci } from 'chessops';
import { makeFen, parseFen } from 'chessops/fen';
import { makeSanVariation } from 'chessops/san';
import { chessgroundDests } from 'chessops/compat';

export default class Ctrl {

  data: ServerData;
  chessground: Chessground;
  chess: Chess;
  solution: San[];
  moves: Uci[] = [];

  constructor(data: ServerData, readonly redraw: () => void) {
    this.init(data, true);
  }

  private init = (data: ServerData, first: boolean = false) => {
    this.data = data;
    this.moves = [];
    this.chess = this.initialChess();
    this.solution = makeSanVariation(this.chess, this.data.puzzle.moves.slice(1).map(uci => parseUci(uci)!)).replace(/\d+\.+ /g, '').split(' ');
    if (!first) this.redraw();
    history.replaceState({}, '', `/puzzle/${data.puzzle._id}`);
  }

  review = async (approved: boolean) => {
    this.data.puzzle.review = { 
      approved,
      by: this.data.username,
      at: new Date()
    };
    this.redraw();
    const data = await fetch(`/review/${this.data.puzzle._id}?approved=${approved ? 1 : 0}`, {
      method: 'post'
    }).then(res => res.json());
    this.init(data);
  }

  skip = () => fetch('/skip').then(res => res.json()).then(this.init);

  setChessground(cg: Chessground) {
    this.chessground = cg;
  }

  onMove = (uci: Uci, autoReply: boolean = true) => {
    this.moves.push(uci);
    this.chess.play(parseUci(uci)!);
    this.chessground.set(this.cgConfig(uci));
    const reply = autoReply && this.findReply();
    if (reply) this.onMove(reply, false);
    else this.redraw();
  }

  orientation = () => this.data.puzzle.ply % 2 == 1 ? 'white' : 'black';

  isComplete = () =>
    this.moves.join(' ') == this.data.puzzle.moves.slice(1).join(' ');

  isInVariation = () => !this.isComplete() && !this.canForward();

  back = () => {
    if (!this.moves.length) return;
    this.moves = this.moves.slice(0, -1);
    this.chess = this.initialChess();
    this.moves.forEach(move => this.chess.play(parseUci(move)!));
    const lastMove = this.moves[this.moves.length - 1] || this.data.puzzle.moves[0];
    this.chessground.set(this.cgConfig(lastMove));
    this.redraw();
  }

  canForward = () =>
    this.moves.length < this.data.puzzle.moves.slice(1).length &&
    this.moves.join(' ') == this.data.puzzle.moves.slice(1, this.moves.length + 1).join(' ');

  forward = () => {
    if (!this.canForward()) return;
    const move = this.data.puzzle.moves[this.moves.length + 1];
    if (move) this.onMove(move, false);
    this.redraw();
  }

  private findReply = (): Uci | undefined => {
    if (this.moves.length % 2 == 0 || this.moves.length > this.data.puzzle.moves.length) return;
    if (this.moves.join(' ') != this.data.puzzle.moves.slice(1, this.moves.length + 1).join(' ')) return;
    return this.data.puzzle.moves[this.moves.length + 1];
  }

  currentFen = () => makeFen(this.chess.toSetup());

  nbMovesIn = () => {
    let nb = 0;
    for (let move of this.moves) {
      if (move == this.data.puzzle.moves[nb + 1]) nb++;
      else break;
    }
    return nb;
  }

  private cgConfig = (lastMove: Uci) => ({
    fen: this.currentFen(),
    turnColor: this.chess.turn,
    movable: {
      color: this.chess.turn,
      dests: chessgroundDests(this.chess)
    },
    check: this.chess.isCheck(),
    lastMove: this.cgLastMove(lastMove)
  });

  cgLastMove = (move: Uci) => ([move.substr(0, 2) as Key, move.substr(2, 2) as Key]);

  initialChess = () => {
    const c = Chess.fromSetup(parseFen(this.data.puzzle.fen).unwrap()).unwrap();
    c.play(parseUci(this.data.puzzle.moves[0])!);
    return c;
  }
}
