export type Uci = string;
export type San = string;
type Score = number;
type Comment = string;
type Rating = number;
type UserId = string;

export interface Puzzle {
  _id: number;
  createdAt: Date;
  gameId: string;
  fen: string;
  ply: number;
  moves: Uci[];
  review?: Review;
}

export interface Review {
  by: UserId;
  at: Date;
  score: Score;
  comment: Comment;
  rating: Rating;
}
