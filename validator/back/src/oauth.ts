import { AuthorizationCode, AccessToken } from 'simple-oauth2';
import { config } from './config';
import fetch from 'node-fetch';

const client = new AuthorizationCode({
  client: {
    id: config.oauth.app.id,
    secret: config.oauth.app.secret
  },
  auth: {
    tokenHost: config.oauth.server.tokenHost,
    tokenPath: config.oauth.server.tokenPath,
    authorizePath: config.oauth.server.authorizePath
  },
  http: {
    json: true
  }
});

export const authorizationUri = client.authorizeURL({
  redirect_uri: config.oauth.app.redirectUri,
  scope: config.oauth.app.scopes,
  state: Math.random().toString(36).substring(2)
});

export const getToken = (code: string): Promise<AccessToken> => 
  client.getToken({
    code,
    redirect_uri: config.oauth.app.redirectUri
  });

export const getUserInfo = (token: AccessToken): Promise<any> =>
  fetch('https://lichess.org/api/account', {
    headers: { 'Authorization': `Bearer ${token.token.access_token}` }
  }).then(res => res.json());
