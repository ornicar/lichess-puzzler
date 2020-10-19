import { Collection, UpdateWriteOpResult } from 'mongodb';
import { Puzzle, Review } from './puzzle';

export default class Mongo {

  constructor(readonly coll: Collection) {
  }

  get = (id: number): Promise<Puzzle | null> =>
    this.coll.findOne({ _id: id });

  next = (): Promise<Puzzle | null> =>
    this.coll.findOne({ review: { $exists: false } });

  review = (puzzle: Puzzle, review: Review): Promise<UpdateWriteOpResult> =>
    this.coll.updateOne({ _id: puzzle.id }, { $set: { review: review } });
}
