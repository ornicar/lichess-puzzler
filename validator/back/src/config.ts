const port = process.env.PORT || 8000;
export const config = {
  http: {
    port: port,
    url: `http://localhost:${port}`
  },
  mongodb: {
    url: 'mongodb://localhost:27017',
    dbName: 'puzzler'
  },
  cookie: {
    secret: process.env.COOKIE_SECRET!
  },
  oauth: {
    client: {
      id: 'QUH0Q8AYGOGHEcNT',
      secret: process.env.OAUTH_APP_SECRET!,
      redirectUri: `http://localhost:${port}/oauth-callback`,
      scopes: ['preference:read']
    },
    server: {
      tokenHost: 'https://oauth.lichess.org',
      authorizePath: '/oauth/authorize',
      tokenPath: '/oauth',
      url: {
        userInfo: 'https://lichess.org/api/account'
      }
    }
  }
};
