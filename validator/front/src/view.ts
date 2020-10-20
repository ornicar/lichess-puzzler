import { Chessground } from 'chessground';
import { h } from 'snabbdom'
import { VNode } from 'snabbdom/vnode';
import Ctrl from './ctrl';
import { parseFen } from 'chessops/fen';
import { Chess } from 'chessops/chess';
import { chessgroundDests } from 'chessops/compat';
import { Color, Key } from 'chessground/types';

export default function(ctrl: Ctrl): VNode {
  const puzzle = ctrl.data.puzzle,
    nbMovesIn = ctrl.nbMovesIn();
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
          h('p', [
            h('a', { attrs: { href: `/puzzle/${puzzle._id}` } }, `Candidate #${puzzle._id}`)
          ]),
          h('p', [
            'From game ',
            h('a', { attrs: { href: `https://lichess.org/${puzzle.gameId}` } }, `#${puzzle.gameId}`)
          ]),
          h('p', [
            'Solution: ',
            ...ctrl.solution.map((san, i) =>
              h('san', {
                class: { done: i < nbMovesIn }
              }, san)
            )
          ]),
          h('p', [
            h('a', {
              attrs: {
                href: `http://lichess.org/analysis/${ctrl.currentFen().replace(' ', '_')}`,
                target: '_blank'
              }
            }, 'Analyse on Lichess')
          ]),
          h('p', [
            h('button', {
              attrs: {
                disabled: !ctrl.moves.length
              },
              hook: {
                insert(vnode) {
                  (vnode.elm as HTMLElement).addEventListener('click', ctrl.back)
                }
              }
            }, 'Rewind one move')
          ])
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
      move(orig: Key, dest: Key) {
        ctrl.onMove(`${orig}${dest}`);
      }
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
