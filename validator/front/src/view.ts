import { Chessground } from 'chessground';
import { h } from 'snabbdom'
import { VNode } from 'snabbdom/vnode';
import Ctrl from './ctrl';
import { parseFen } from 'chessops/fen';
import { Chess } from 'chessops/chess';
import { chessgroundDests } from 'chessops/compat';
import { Color, Key } from 'chessground/types';
import {Review} from '../../back/src/puzzle';

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
            }, `gen v${puzzle.generator}`)
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
          h('div', [
            radios('score', 'Quality (required)', [1, 2, 3, 4, 5].map(s => [s, s]), puzzle.review),
            radios('comment', 'Comment', comments, puzzle.review),
            /* radios('rating', 'Rating', [800, 1200, 1600, 2000, 2400, 2800].map(s => [s, s]), puzzle.review), */
            h('button.submit', {
              hook: onClick(ev => {
                const score = parseInt(((ev.target as HTMLElement).parentNode!.querySelector('input[name="score"]:checked') as HTMLInputElement)?.value);
                const comment = ((ev.target as HTMLElement).parentNode!.querySelector('input[name="comment"]:checked') as HTMLInputElement)?.value;
                /* const rating = parseInt(((ev.target as HTMLElement).parentNode!.querySelector('input[name="rating"]:checked') as HTMLInputElement)?.value); */
                const rating = 0;
                if (score) ctrl.review(score, comment, rating);
              })
            }, 'Review & next')
          ])
        ])
      ])
    ]),
    h('p', [
      h('button', {
        attrs: {
          disabled: !ctrl.moves.length
        },
        hook: onClick(ctrl.back)
      }, '< Rewind')
    ])
  ]);
}

const comments: Array<[string, string]> = [
  ['', 'N/A'],
  ['boring', 'Boring'],
  ['weird', 'Weird'],
  ['wrong', 'Wrong'],
  ['long', 'Too long'],
  ['short', 'Too short']
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

const radios = (name: string, title: string, values: Array<[any, any]>, review?: Review) =>
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
              value: key,
              checked: review ? (review as any)[name] == key : key == ''
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
