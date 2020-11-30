import { Collection, Db, UpdateWriteOpResult } from 'mongodb';
import { Token } from 'simple-oauth2';
import { Puzzle, Review } from './puzzle';
import * as crypto from "crypto";

interface Stats {
  nbCandidates: number;
  nbReviewed: number;
}

export default class Mongo {

  puzzle: PuzzleMongo;
  auth: AuthMongo;
  seen: SeenMongo;

  constructor(readonly db: Db) {
    this.puzzle = new PuzzleMongo(this.db.collection('puzzle2'));
    this.auth = new AuthMongo(this.db.collection('authentication'));
    this.seen = new SeenMongo(this.db.collection('seen'), this.db.collection('puzzle2'));
  }
}

export class PuzzleMongo {

  constructor(readonly coll: Collection) {
    this.coll.createIndex({ gameId: 1 }, { unique: true });
  }

  get = (id: string): Promise<Puzzle | null> =>
    this.coll.findOne({ _id: id });

  next = async (): Promise<Puzzle | null> => {
    let p = await this.nextSkip(Math.round(Math.random() * 100));
    if (!p) p = await this.nextSkip(0);
    return p;
  }

  nextSkip = (skip: number): Promise<Puzzle | null> =>
    this.coll.find(this.selectReviewed(false)).sort({createdAt:-1}).skip(skip).limit(1).next();

  review = (puzzle: Puzzle, review: Review): Promise<UpdateWriteOpResult> =>
    this.coll.updateOne({ _id: puzzle._id }, { $set: { review: review } });

  stats = (): Promise<Stats> =>
    Promise.all(
      [false, true]
        .map(this.selectReviewed)
        .map(sel => this.coll.countDocuments(sel))
    ).then(([nbCandidates, nbReviewed]) => ({
      nbCandidates,
      nbReviewed
    }));

  insert = (puzzle: Puzzle): Promise<any> =>
    this.coll.insertOne(puzzle);

  private selectReviewed = (v: boolean) => ({ review: { $exists: v } });
}

export type AuthId = string;

export class AuthMongo {

  private idSize = 32;

  constructor(readonly coll: Collection) { }

  get = (id: AuthId): Promise<Token | null> => this.coll.findOne({ _id: id });

  username = (id: AuthId): Promise<string | null> =>
    this.get(id).then((o: any) => o && o.username);

  save = async (token: Token, username: string): Promise<AuthId> => {
    const id = crypto.randomBytes(this.idSize).toString('base64').slice(0, this.idSize);
    await this.coll.insertOne({
      ...token,
      _id: id,
      username
    });
    return id;
  }
}

export class SeenMongo {

  constructor(readonly seenColl: Collection, readonly puzzleColl: Collection) { }

  exists = (id: string): Promise<boolean> => this.seenColl.countDocuments({ _id: id }).then(n => n > 0);

  positionExists = (fen: string, move: string): Promise<boolean> => 
    this.puzzleColl.countDocuments({ fen: fen, 'moves.0': move }).then(n => n > 0);

  set = (id: string) => this.seenColl.insertOne({_id: id}).catch(() => {});
}
