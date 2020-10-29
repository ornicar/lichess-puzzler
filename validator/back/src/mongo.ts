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

  constructor(readonly db: Db) {
    this.puzzle = new PuzzleMongo(this.db.collection('puzzle'));
    this.auth = new AuthMongo(this.db.collection('authentication'));
  }
}

export class PuzzleMongo {

  constructor(readonly coll: Collection) {
    this.coll.createIndex({ gameId: 1 }, { unique: true });
  }

  get = (id: number): Promise<Puzzle | null> =>
    this.coll.findOne({ _id: id });

  next = async (): Promise<Puzzle | null> => {
    let p = await this.nextSkip(Math.round(Math.random() * 50));
    if (!p) p = await this.nextSkip(0);
    return p;
  }

  nextSkip = (skip: number): Promise<Puzzle | null> =>
    this.coll.find(this.selectReviewed(false)).skip(skip).limit(1).next();

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

  nextId = async (): Promise<number> => {
    const last = await this.coll.find().sort({ _id: -1 }).limit(1).next();
    return last ? last._id + 1 : 1;
  }

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
