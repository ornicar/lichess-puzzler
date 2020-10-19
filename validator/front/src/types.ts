export interface ServerData {
  stats: Stats;
  username: string;
}

export interface Stats {
  nbCandidates: number;
  nbReviewed: number;
}
