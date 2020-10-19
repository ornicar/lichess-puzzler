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

  constructor(readonly coll: Collection) { }

  get = (id: number): Promise<Puzzle | null> =>
    this.coll.findOne({ _id: id });

  next = (): Promise<Puzzle | null> =>
    this.coll.findOne(this.selectReviewed(false));

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
