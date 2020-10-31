import { Chessground } from 'chessground';
import { h } from 'snabbdom'
import { VNode } from 'snabbdom/vnode';
import Ctrl from './ctrl';
import { chessgroundDests } from 'chessops/compat';
import { Key } from 'chessground/types';

export default function(ctrl: Ctrl): VNode {
  const puzzle = ctrl.data.puzzle,
    nbMovesIn = ctrl.nbMovesIn(),
    gameUrl = `https://lichess.org/${puzzle.gameId}${ctrl.orientation() == 'white' ? '' : '/black'}#${puzzle.ply}`;
  return h(`main.puzzle-${puzzle._id}`, [
    h('section.top', [
      h('h1', h('a', { attrs: { href: '/' } }, 'Lichess Puzzle Validator')),
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
        })
      ]),
      h('div.puzzle__ui', [
        h('div.puzzle__info', [
          h('p.puzzle__info__title', [
            h('a', {
              attrs: { href: `/puzzle/${puzzle._id}` }
            }, `Candidate #${puzzle._id}`),
            h('em', puzzle.kind),
            h('em', {
              attrs: { title: 'Generator version' }
            }, `v${puzzle.generator}`)
          ]),
          h('p', [
            'From game ',
            h('a.analyse', {
              attrs: {
                href: gameUrl,
                target: '_blank'
              }
            }, `#${puzzle.gameId}`)
          ]),
          h('p', [
            'Solution: ',
            ...ctrl.solution.map((san, i) =>
              h('san', {
                class: { done: i < nbMovesIn }
              }, san)
            )
          ])
        ]), ,
        h('div.puzzle__review', [
          h('button.reject', {
            hook: onClick(() => ctrl.review(false)),
            class: { active: puzzle.review?.approved === false }
          }, [
            h('em', 'Reject'),
            h('strong', '✗'),
            h('em', '[backspace]')
          ]),
          h('button.approve', {
            hook: onClick(() => ctrl.review(true)),
            class: { active: puzzle.review?.approved === true }
          }, [
            h('em', 'Approve'),
            h('strong', '✓'),
            h('em', '[enter]')
          ])
        ]),
        h('div.puzzle__skip', [
          h('button', { hook: onClick(ctrl.skip) }, 'Skip')
        ]),
        h('div.puzzle__help', [
          h('p', 'Does the puzzle feel a bit off, computer-like, or frustrating? Just reject it.'),
          h('p', 'Too difficult and you\'re not sure if interesting? Skip it.'),
          h('p', 'Use arrow keys to replay, backspace/enter to review, a to analyse.')
        ])
      ])
    ]),
    h('p.replay', [
      h('button', {
        attrs: {
          disabled: !ctrl.moves.length
        },
        class: {
          variation: ctrl.isInVariation()
        },
        hook: onClick(ctrl.back)
      }, '< Rewind'),
      h('button', {
        attrs: {
          disabled: !ctrl.canForward()
        },
        hook: onClick(ctrl.forward)
      }, 'Forward >')
    ])
  ]);
}

const cgConfig = (ctrl: Ctrl) => {
  const p = ctrl.data.puzzle,
    chess = ctrl.initialChess();
  return {
    fen: ctrl.currentFen(),
    orientation: chess.turn,
    turnColor: chess.turn,
    check: chess.isCheck(),
    movable: {
      free: false,
      color: chess.turn,
      dests: chessgroundDests(chess)
    },
    lastMove: ctrl.cgLastMove(p.moves[0]),
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

const onClick = (f: (event: MouseEvent) => any) => ({
  insert(vnode: VNode) {
    (vnode.elm as HTMLElement).addEventListener('click', f)
  }
});
