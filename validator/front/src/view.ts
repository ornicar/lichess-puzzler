import { h } from 'snabbdom'
import { VNode } from 'snabbdom/vnode';
import Ctrl from './ctrl';

export default function(ctrl: Ctrl): VNode {
  return h('main', [
    h('h1', 'Lichess Puzzle Validator'),
    'snabbdom view',
    JSON.stringify(ctrl.data)
  ]);
}
