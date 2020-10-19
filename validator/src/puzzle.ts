type Uci = string;
type Score = number;
type Rating = number;
type Topic = string;
type UserId = string;

export interface Puzzle {
  id: number;
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
  rating: Rating;
  topics: Topic[];
}
