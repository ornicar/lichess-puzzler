import Express from 'express';
import Env from './env';
import { Puzzle, randomId } from './puzzle';
import { Response as ExResponse } from 'express';
import { config } from './config';

export default function (app: Express.Express, env: Env) {
  let duplicates = 0;
  app.post('/puzzle', async (req, res) => {
    if ((req.query.token as string) != config.generatorToken) return res.status(400).send('Wrong token');
    console.log(req.body);
    const puzzle: Puzzle = {
      _id: randomId(),
      gameId: req.body.game_id,
      fen: req.body.fen,
      ply: req.body.ply,
      moves: req.body.moves,
      cp: req.body.cp,
      generator: req.body.generator_version,
      createdAt: new Date(),
      ip: req.ip,
    };
    console.log(puzzle);
    try {
      await env.mongo.puzzle.insert(puzzle);
      return res.send(`Created ${config.http.url}/puzzle/${puzzle._id}`);
    } catch (e: any) {
      const msg = e.code == 11000 ? `Game ${puzzle.gameId} already in the puzzle DB!` : e.message;
      if (e.code == 11000) {
        duplicates++;
        console.info(`${duplicates} duplicates detected.`);
      } else console.warn(`Mongo insert error: ${msg}`);
      return res.status(200).send(msg);
    }
  });

  app.get('/seen', async (req, res) => {
    if ((req.query.token as string) != config.generatorToken) return res.status(400).send('Wrong token');
    const id = req.query.id as string;
    let exists = false;
    if (id.length == 8) exists = await env.mongo.seen.exists(id);
    else {
      const [fen, move] = id.split(':');
      exists = await env.mongo.seen.positionExists(fen, move);
    }
    return exists ? res.status(200).send() : res.status(404).send();
  });
  app.post('/seen', async (req, res) => {
    if ((req.query.token as string) != config.generatorToken) return res.status(400).send('Wrong token');
    env.mongo.seen.set(req.query.id as string);
    return res.status(201).send();
  });
}
