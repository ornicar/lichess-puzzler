import Express from 'express';
import Env from './env';
import * as oauth from './oauth';
import { Puzzle, randomId } from './puzzle';
import { Response as ExResponse } from 'express';
import { config } from './config';

type HttpResponse = ExResponse<string>

export default function(app: Express.Express, env: Env) {

  app.get('/', async (req, res) => {
    const puzzle = await env.mongo.puzzle.next();
    renderPuzzle(req.session, res, puzzle);
  });

  app.get('/puzzle/:id', async (req, res) => {
    const puzzle = await env.mongo.puzzle.get(req.params.id);
    renderPuzzle(req.session, res, puzzle);
  });

  const renderPuzzle = async (session: any, res: HttpResponse, puzzle: Puzzle | null) => {
    if (!puzzle) return res.status(404).end('No puzzle in DB');
    const username = await env.mongo.auth.username(session?.authId || '');
    if (!username) return res.send(htmlPage(`<a href="/auth">Login with Lichess to continue</a>`));
    const data = { username, puzzle };
    return res.send(htmlPage(`
    <main></main>
    <script src="/dist/puzzle-validator.dev.js"></script>
    <script>PuzzleValidator.start(${JSON.stringify(data)})</script>
`));
  }

  app.post('/review/:id', async (req, res) => {
    const puzzle = await env.mongo.puzzle.get(req.params.id);
    if (!puzzle) return res.status(404).end();
    const username = await env.mongo.auth.username(req.session?.authId || '');
    if (!username) return res.status(403).end();
    await env.mongo.puzzle.review(puzzle, {
      by: username,
      at: new Date(),
      approved: req.query.approved == '1'
    });
    const next = await env.mongo.puzzle.next();
    if (!next) return res.status(404).end();
    res.send(JSON.stringify({ username, puzzle: next }));
  });

  app.get('/skip', async (req, res) => {
    const username = await env.mongo.auth.username(req.session?.authId || '');
    if (!username) return res.status(403).end();
    const next = await env.mongo.puzzle.next();
    if (!next) return res.status(404).end();
    res.send(JSON.stringify({ username, puzzle: next }));
  });

  app.post('/puzzle', async (req, res) => {
    if (req.query.token as string != config.generatorToken)
      return res.status(400).send('Wrong token');
    const puzzle: Puzzle = {
      _id: randomId(),
      gameId: req.body.game_id,
      fen: req.body.fen,
      ply: req.body.ply,
      moves: req.body.moves,
      kind: req.body.kind,
      generator: req.body.generator_version,
      createdAt: new Date(),
      ip: req.ip
    };
    try {
      await env.mongo.puzzle.insert(puzzle);
      return res.send(`Created ${config.http.url}/puzzle/${puzzle._id}`);
    } catch (e) {
      console.warn('Mongo insert error', e.message);
      console.warn(puzzle);
      const msg = e.code == 11000 ? `Game ${puzzle.gameId} already in the puzzle DB!` : e;
      return res.status(400).send(msg);
    }
  });

  app.get('/seen', async (req, res) => {
    if (req.query.token as string != config.generatorToken)
      return res.status(400).send('Wrong token');
    const exists = await env.mongo.seen.exists(req.query.id as string);
    return exists ? res.status(200).send() : res.status(404).send();
  });
  app.post('/seen', async (req, res) => {
    if (req.query.token as string != config.generatorToken)
      return res.status(400).send('Wrong token');
    env.mongo.seen.set(req.query.id as string);
    return res.status(201).send();
  });

  app.get('/logout', (req, res) => {
    req.session!.authId = '';
    res.redirect('/');
  });

  app.get('/auth', (_, res) => res.redirect(oauth.authorizationUri));

  app.get('/oauth-callback', async (req, res) => {
    try {
      const token = await oauth.getToken(req.query.code as string);
      const user = await oauth.getUserInfo(token);
      const authId = await env.mongo.auth.save(token.token, user.username);
      req.session!.authId = authId;
      res.redirect('/');
    } catch (error) {
      console.error('Access Token Error', error.message);
      res.status(500).json('Authentication failed');
    }
  });
}

const htmlPage = (content: string) => `
<html>
  <head>
    <title>Lichess Puzzle Validator</title>
    <link href="/style.css" rel="stylesheet">
  </head>
  <body>
    ${content}
  </body>
</html>`;
