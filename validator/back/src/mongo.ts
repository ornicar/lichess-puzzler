import { Collection, Db, UpdateWriteOpResult } from 'mongodb';
import { Puzzle, Review } from './puzzle';

interface Stats {
  nbCandidates: number;
  nbReviewed: number;
}

export default class Mongo {

  puzzleColl: Collection;

  constructor(readonly db: Db) {
    this.puzzleColl = this.db.collection('puzzle');
  }

  get = (id: number): Promise<Puzzle | null> =>
    this.puzzleColl.findOne({ _id: id });

  next = (): Promise<Puzzle | null> =>
    this.puzzleColl.findOne(this.selectReviewed(false));

  review = (puzzle: Puzzle, review: Review): Promise<UpdateWriteOpResult> =>
    this.puzzleColl.updateOne({ _id: puzzle.id }, { $set: { review: review } });

  stats = (): Promise<Stats> =>
    Promise.all(
      [false, true]
      .map(this.selectReviewed)
      .map(sel => this.puzzleColl.count(sel))
    ).then(([nbCandidates, nbReviewed]) =>({
      nbCandidates,
      nbReviewed
    }));

  private selectReviewed = (v: boolean) => ({ review: { $exists: v } });
}
