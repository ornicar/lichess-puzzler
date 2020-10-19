import { ServerData } from './types';
import { Api as Chessground } from 'chessground/api';
import { Key } from 'chessground/types';

export default class Ctrl {

  chessground: Chessground;

  constructor(readonly data: ServerData, readonly redraw: () => void) {
  }

  setChessground(cg: Chessground) {
    this.chessground = cg;
  }

  onMove = (orig: Key, dest: Key) => {
    console.log(orig, dest);
  }
}
