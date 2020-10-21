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
  return h(`main.puzzle-${puzzle._id}`, [
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
            h('a', { attrs: { href: `https://lichess.org/${puzzle.gameId}#${puzzle.ply}` } }, `#${puzzle.gameId}`)
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
              hook: onClick(ctrl.back)
            }, 'Rewind one move')
          ]),
          h('div', [
            radios('score', 'Quality', [1, 2, 3, 4, 5].map(s => [s, s])),
            radios('comment', 'Comment', comments),
            radios('rating', 'Rating', [800, 1200, 1600, 2000, 2400, 2800].map(s => [s, s])),
            h('button.submit', {
              hook: onClick(ev => {
                const score = parseInt(((ev.target as HTMLElement).parentNode!.querySelector('input[name="score"]:checked') as HTMLInputElement)?.value);
                const comment = ((ev.target as HTMLElement).parentNode!.querySelector('input[name="comment"]:checked') as HTMLInputElement)?.value;
                const rating = parseInt(((ev.target as HTMLElement).parentNode!.querySelector('input[name="rating"]:checked') as HTMLInputElement)?.value);
                if (score && comment) ctrl.review(score, comment, rating);
              })
            }, 'Review & next')
          ])
        ])
      ])
    ])
  ]);
}

const comments: Array<[string, string]> = [
  ['ok', 'OK'],
  ['boring', 'Boring'],
  ['wrong', 'Wrong'],
  ['long', 'Too long'],
  ['short', 'Too short'],
  ['other', 'Other']
];

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

const onClick = (f: (event: MouseEvent) => any) => ({
  insert(vnode: VNode) {
    (vnode.elm as HTMLElement).addEventListener('click', f)
  }
});

const radios = (name: string, title: string, values: Array<[any, any]>) =>
  h(`div.radios.${name}`, [
    h('strong', title),
    h('div.choices',
      values.map(([key, display]) =>
        h('div', [
          h('input', {
            attrs: {
              type: 'radio',
              name: name,
              id: `${name}-${key}`,
              value: key
            }
          }),
          h('label', {
            attrs: {
              for: `${name}-${key}`
            }
          }, display)
        ])
      )
    )
  ])
