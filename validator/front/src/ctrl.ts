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
    this.init(data);
  }

  private init = (data: ServerData) => {
    this.data = data;
    this.moves = [];
    this.chess = this.initialChess();
    this.solution = makeSanVariation(this.chess, this.data.puzzle.moves.map(uci => parseUci(uci)!)).replace(/\d+\.+ /g, '').split(' ');
  }

  review = async (score: number, comment: string, rating: number) => {
    const data = await fetch(`/review/${this.data.puzzle._id}?score=${score}&comment=${comment}&rating=${rating}`, {
      method: 'post'
    }).then(res => res.json());
    this.init(data);
    this.redraw();
    history.replaceState({}, '', `/puzzle/${data.puzzle._id}`);
  }

  setChessground(cg: Chessground) {
    this.chessground = cg;
  }

  onMove = (uci: Uci, autoReply: boolean = true) => {
    this.moves.push(uci);
    this.chess.play(parseUci(uci)!);
    this.chessground.set(this.cgConfig(uci));
    const reply = this.findReply();
    if (reply && autoReply) setTimeout(() => this.onMove(reply), 200);
    this.redraw();
  }

  orientation = () => this.data.puzzle.ply % 2 == 0 ? 'white' : 'black';

  isComplete = () =>
    this.moves.join(' ') == this.data.puzzle.moves.join(' ');

  isInVariation = () => !this.isComplete() && !this.canForward();

  back = () => {
    if (!this.moves.length) return;
    this.moves = this.moves.slice(0, -1);
    this.chess = this.initialChess();
    this.moves.forEach(move => this.chess.play(parseUci(move)!));
    this.chessground.set(this.cgConfig(this.moves[this.moves.length - 1]));
    this.redraw();
  }

  canForward = () =>
    this.moves.length < this.data.puzzle.moves.length &&
    this.moves.join(' ') == this.data.puzzle.moves.slice(0, this.moves.length).join(' ');

  forward = () => {
    if (!this.canForward()) return;
    const move = this.data.puzzle.moves[this.moves.length];
    if (move) this.onMove(move, false);
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
