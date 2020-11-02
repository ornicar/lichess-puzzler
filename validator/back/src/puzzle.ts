export type Uci = string;
export type San = string;
type UserId = string;

type Kind = 'mate' | 'material';

export interface Puzzle {
  _id: number;
  createdAt: Date;
  gameId: string;
  fen: string;
  ply: number;
  moves: Uci[];
  kind: Kind;
  review?: Review;
  generator: number;
  ip?: string;
}

export interface Review {
  by: UserId;
  at: Date;
  approved: boolean;
}
