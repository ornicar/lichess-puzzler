import { ServerData } from './types';
import { Api as Chessground } from 'chessground/api';
import { Key } from 'chessground/types';
import { Chess, parseUci } from 'chessops';
import { parseFen } from 'chessops/fen';
import { makeSanVariation } from 'chessops/san';

export default class Ctrl {

  chessground: Chessground;
  chess: Chess;

  constructor(readonly data: ServerData, readonly redraw: () => void) {
    const setup = parseFen(data.puzzle.fen).unwrap();
    this.chess = Chess.fromSetup(setup).unwrap();
  }

  setChessground(cg: Chessground) {
    this.chessground = cg;
  }

  onMove = (orig: Key, dest: Key) => {
    console.log(orig, dest);
  }

  movesAsSan = () => {
    debugger;
    makeSanVariation(this.chess, this.data.puzzle.moves.map(uci => parseUci(uci)!));
  }
    /* makeSanVariation(this.chess, this.data.puzzle.moves.map(uci => parseUci(uci)!)); */
}
