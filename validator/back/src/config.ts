import convict from 'convict';

const schema = convict({
  env: {
    format: ['prod', 'dev', 'local'],
    default: 'dev',
    arg: 'env',
    env: 'NODE_ENV',
  },
  http: {
    port: {
      format: 'port',
      default: 8000,
    },
    url: {
      format: String,
      default: 'http://localhost:8000',
    },
  },
  generatorToken: {
    format: String,
    default: 'changeme',
  },
  mongodb: {
    url: {
      format: String,
      default: 'mongodb://localhost:27017',
    },
    name: {
      format: String,
      default: 'puzzler',
    },
  },
});

schema.loadFile(`config/${schema.get('env')}.json`);
schema.validate({ allowed: 'strict' });

interface Config {
  env: string;
  http: {
    port: number;
    url: string;
  };
  generatorToken: string;
  mongodb: {
    url: string;
    name: string;
  };
}

export const config: Config = {
  env: schema.get('env'),
  http: schema.get('http'),
  generatorToken: schema.get('generatorToken'),
  mongodb: schema.get('mongodb'),
};
