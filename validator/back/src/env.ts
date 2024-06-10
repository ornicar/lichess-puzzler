import { MongoClient, Db } from 'mongodb';
import { config } from './config';
import Mongo from './mongo';

export default class Env {
  constructor(readonly mongo: Mongo) { }

  static make = async (): Promise<Env> => new Env(await connectDb(config.mongodb).then(db => new Mongo(db)));
}

async function connectDb(conf: any): Promise<Db> {
  const client = new MongoClient(conf.url, {
    // useUnifiedTopology: true,
    // useNewUrlParser: true,
  });
  console.log('Connecting to', conf.url);
  await client.connect();
  console.log('Connected');
  return client.db(conf.name);
}
