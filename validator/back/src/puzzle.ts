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
  review?: Review;
  generator: number;
  ip?: string;
  tags?: string[];
}

export interface Review {
  by: UserId;
  at: Date;
  approved: boolean;
}

const idChars = '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ';
const idLength = 5;

export function randomId() {
  let result = '';
  for (let i = idLength; i > 0; --i) result += idChars[Math.floor(Math.random() * idChars.length)];
  return result;
}
