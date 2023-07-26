import express from 'express';
import bodyParser from 'body-parser';
import { config } from './config';
import Env from './env';
import router from './router';

const app = express();

Env.make().then((env: Env) => {
  app.use(express.static('public'));

  app.use(bodyParser.json());

  router(app, env);

  app.listen(config.http.port, () => {
    console.log(`⚡️[${config.env}]: Server is running at ${config.http.url}`);
  });
});
