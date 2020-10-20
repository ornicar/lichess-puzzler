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
    const setup = parseFen(data.puzzle.fen).unwrap();
    this.chess = Chess.fromSetup(setup).unwrap();
    this.solution = makeSanVariation(this.chess, this.data.puzzle.moves.map(uci => parseUci(uci)!)).replace(/\d\.+ /g, '').split(' ');
  }

  setChessground(cg: Chessground) {
    this.chessground = cg;
  }

  onMove = (uci: Uci) => {
    this.moves.push(uci);
    this.chess.play(parseUci(uci)!);
    this.chessground.set({
      fen: makeFen(this.chess.toSetup()),
      turnColor: this.chess.turn,
      movable: {
        color: this.chess.turn,
        dests: chessgroundDests(this.chess)
      },
      check: this.chess.isCheck(),
      lastMove: [uci.substr(0, 2) as Key, uci.substr(2, 2) as Key]
    });
    const reply = this.findReply();
    if (reply) setTimeout(() => this.onMove(reply) , 200);
    this.redraw();
  }

  private findReply = (): Uci | undefined => {
    if (this.moves.length % 2 == 0 || this.moves.length >= this.data.puzzle.moves.length) return;
    if (this.moves.join(' ') != this.data.puzzle.moves.slice(0, this.moves.length).join(' ')) return;
    return this.data.puzzle.moves[this.moves.length];
  }

  nbMovesIn = () => {
    let nb = 0;
    for (let move of this.moves) {
      if (move == this.data.puzzle.moves[nb]) nb++;
      else break;
    }
    return nb;
  }
}
