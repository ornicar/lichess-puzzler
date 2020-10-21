export const config = {
  http: {
    port: 8000,
    url: 'http://localhost:8000'
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
      redirectUri: 'http://localhost:8000/oauth-callback',
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
