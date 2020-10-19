import express from 'express';
import cookieSession from 'cookie-session';
import { config } from './config';
import Env from './env';
import router from './router';

const app = express();
const PORT = 8000;

Env.make().then((env: Env) => {

  app.use(express.static('public'));

  app.use(cookieSession({
    name: 'session',
    keys: [ config.cookie.secret ],
    // Cookie Options
    maxAge: 30 * 24 * 60 * 60 * 1000
  }))

  router(app, env);

  app.listen(PORT, () => {
    console.log(`⚡️[server]: Server is running at http://localhost:${PORT}`);
  });
});
