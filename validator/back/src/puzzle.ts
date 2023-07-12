export type Uci = string;
export type San = string;
type UserId = string;

export interface Puzzle {
  _id: string;
  createdAt: Date;
  gameId: string;
  fen: string;
  ply: number;
  moves: Uci[];
  cp?: number;
  generator: number;
  ip?: string;
  tags?: string[];
}

const idChars = '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ';
const idLength = 5;

export function randomId() {
  let result = '';
  for (let i = idLength; i > 0; --i) result += idChars[Math.floor(Math.random() * idChars.length)];
  return result;
}
