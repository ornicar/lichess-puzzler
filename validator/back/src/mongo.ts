import { Collection, Db } from 'mongodb';
import { Puzzle } from './puzzle';

interface Stats {
  nbCandidates: number;
  nbReviewed: number;
}

export default class Mongo {
  puzzle: PuzzleMongo;
  seen: SeenMongo;

  constructor(readonly db: Db) {
    this.puzzle = new PuzzleMongo(this.db.collection('puzzle2'));
    this.seen = new SeenMongo(this.db.collection('seen'), this.db.collection('puzzle2'));
  }
}

export class PuzzleMongo {
  constructor(readonly coll: Collection) {
    this.coll.createIndex({ gameId: 1 }, { unique: true });
  }

  get = (id: string): Promise<Puzzle | null> => this.coll.findOne({ _id: id } as any) as Promise<Puzzle | null>;

  stats = (): Promise<Stats> =>
    Promise.all([false, true].map(this.selectReviewed).map(sel => this.coll.countDocuments(sel))).then(
      ([nbCandidates, nbReviewed]) => ({
        nbCandidates,
        nbReviewed,
      })
    );

  insert = (puzzle: Puzzle): Promise<any> => this.coll.insertOne(puzzle as any);

  private selectReviewed = (v: boolean) => ({ review: { $exists: v } });
}

export class SeenMongo {
  constructor(readonly seenColl: Collection, readonly puzzleColl: Collection) { }

  exists = (id: string): Promise<boolean> =>
    this.seenColl.countDocuments({ _id: (id as any) }).then(n => n > 0);

  positionExists = (fen: string, move: string): Promise<boolean> =>
    this.puzzleColl.countDocuments({ fen: fen, 'moves.0': move }).then(n => n > 0);

  set = (id: string) => this.seenColl.insertOne({ _id: id } as any).catch(() => { });
}
