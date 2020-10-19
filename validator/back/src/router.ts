import Express from 'express';
import Env from './env';
import * as oauth from './oauth';
import { Puzzle } from './puzzle';
import { Response as ExResponse } from 'express';

type HttpResponse = ExResponse<string>

export default function(app: Express.Express, env: Env) {

  app.get('/', async (req, res) => {
    const puzzle = await env.mongo.puzzle.next();
    renderPuzzle(req.session, res, puzzle);
  });

  app.get('/puzzle/:id', async (req, res) => {
    const puzzle = await env.mongo.puzzle.get(parseInt(req.params.id));
    renderPuzzle(req.session, res, puzzle);
  });

  const renderPuzzle = async (session: any, res: HttpResponse, puzzle: Puzzle | null) => {
    if (!puzzle) return res.status(404).end();
    const username = await env.mongo.auth.username(session?.authId || '');
    if (!username) return res.send(htmlPage(`<a href="/auth">Login with Lichess to continue</a>`));
    const stats = await env.mongo.puzzle.stats();
    const data = { stats, username, puzzle };
    return res.send(htmlPage(`
    <main></main>
    <script src="/dist/puzzle-validator.dev.js"></script>
    <script>PuzzleValidator.start(${JSON.stringify(data)})</script>
`));
  }

  app.get('/auth', (_, res) => {
    console.log(oauth.authorizationUri);
    res.redirect(oauth.authorizationUri);
  });

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
