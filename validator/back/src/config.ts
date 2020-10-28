import convict from 'convict';

const schema = convict({
  env: {
    format: ['prod', 'dev', 'local'],
    default: 'dev',
    arg: 'env',
    env: 'NODE_ENV'
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
    cookieSecret: {
      format: String,
      default: 'changeme'
    }
  },
  mongodb: {
    url: {
      format: String,
      default: 'mongodb://localhost:27017',
    },
    name: {
      format: String,
      default: 'puzzler',
    }
  },
  oauth: {
    app: {
      id: { format: String, default: '' },
      secret: { format: String, default: '' }
    }
  }
});

schema.loadFile(`config/${schema.get('env')}.json`);
schema.validate({ allowed: 'strict' });

interface Config {
  env: string;
  http: {
    port: number;
    url: string;
    cookieSecret: string;
  };
  mongodb: {
    url: string;
    name: string;
  };
  oauth: {
    app: {
      id: string;
      secret: string;
      redirectUri: string;
      scopes: string[];
    }
    server: {
      tokenHost: string;
      authorizePath: string;
      tokenPath: string;
    }
  }
}

export const config: Config = {
  env: schema.get('env'),
  http: schema.get('http'),
  mongodb: schema.get('mongodb'),
  oauth: {
    app: {
      id: schema.get('oauth.app.id'),
      secret: schema.get('oauth.app.secret'),
      redirectUri: `http://localhost:${schema.get('http.port')}/oauth-callback`,
      scopes: ['preference:read']
    },
    server: {
      tokenHost: 'https://oauth.lichess.org',
      authorizePath: '/oauth/authorize',
      tokenPath: '/oauth'
    }
  }
};
