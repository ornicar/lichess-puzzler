import { Puzzle } from '../../back/src/puzzle';

export interface ServerData {
  stats: Stats;
  username: string;
  puzzle: Puzzle;
}

export interface Stats {
  nbCandidates: number;
  nbReviewed: number;
}
