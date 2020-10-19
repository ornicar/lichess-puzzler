import { Chessground } from 'chessground';
import { h } from 'snabbdom'
import { VNode } from 'snabbdom/vnode';
import Ctrl from './ctrl';
import { parseFen } from 'chessops/fen';
import { Chess } from 'chessops/chess';
import { chessgroundDests } from 'chessops/compat';
import { Color } from 'chessground/types';

export default function(ctrl: Ctrl): VNode {
  const puzzle = ctrl.data.puzzle;
  return h('main', [
    h('section.top', [
      h('h1', 'Lichess Puzzle Validator'),
      h('div.top__right', [
        h('strong', ctrl.data.username),
        h('a', { attrs: { href: '/logout' } }, 'Log out')
      ])
    ]),
    h('section.puzzle', [
      h('div.puzzle__board.chessground.merida.blue', [
        h('div.cg-wrap', {
          hook: {
            insert(vnode) {
              ctrl.setChessground(Chessground(vnode.elm as HTMLElement, cgConfig(ctrl)));
            }
          }
        }, 'chessground here')
      ]),
      h('div.puzzle__ui', [
        h('div.puzzle__info', [
          'From game ',
          h('a', { attrs: { href: `https://lichess.org/${puzzle.gameId}` } }, `#${puzzle.gameId}`) 
        ])
      ])
    ])
  ]);
}

const cgConfig = (ctrl: Ctrl) => {
  const p = ctrl.data.puzzle,
    color: Color = p.ply % 2 == 0 ? 'white' : 'black',
    setup = parseFen(p.fen).unwrap(),
    chess = Chess.fromSetup(setup).unwrap();
  return {
    fen: p.fen,
    orientation: color,
    turnColor: color,
    check: chess.isCheck(),
    movable: {
      free: false,
      color: color,
      dests: chessgroundDests(chess)
    },
    events: {
      move: ctrl.onMove
    },
    premovable: {
      enabled: false
    },
    drawable: {
      enabled: true
    },
    disableContextMenu: true
  }
}
