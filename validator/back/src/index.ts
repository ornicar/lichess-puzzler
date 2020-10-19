import express from 'express';
import Env from './env';

const app = express();
const PORT = 8000;

Env.make().then((env: Env) => {

  app.get('/', async (_, res) => {
    const stats = await env.mongo.stats();
    res.send(`
<html>
  <head>
    <title>Lichess Puzzle Validator</title>
    <link href="/style.css" rel="stylesheet">
  </head>
  <body>
    <main></main>
    <script src="/dist/puzzle-validator.dev.js"></script>
    <script>PuzzleValidator.start(${JSON.stringify(stats)})</script>
  </body>
</html>`);
  });

  app.use(express.static('public'));

  app.listen(PORT, () => {
    console.log(`⚡️[server]: Server is running at http://localhost:${PORT}`);
  });
});
