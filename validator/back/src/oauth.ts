import { AuthorizationCode, AccessToken } from 'simple-oauth2';
import { config } from './config';
import fetch from 'node-fetch';

const client = new AuthorizationCode({
  client: {
    id: config.oauth.client.id,
    secret: config.oauth.client.secret
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

const state = Math.random().toString(36).substring(2);

/* const authorizationUri = `${config.oauth.server.tokenHost}${config.oauth.server.authorizePath}?response_type=code&client_id=${config.oauth.client.id}&redirect_uri=${config.oauth.client.redirectUri}&scope=${config.oauth.client.scopes.join('%20')}&state=${state}`; */
export const authorizationUri = client.authorizeURL({
  redirect_uri: config.oauth.client.redirectUri,
  scope: config.oauth.client.scopes,
  state: state
});

export const getToken = (code: string): Promise<AccessToken> => 
  client.getToken({
    code,
    redirect_uri: config.oauth.client.redirectUri
  });

export const getUserInfo = (token: AccessToken): Promise<any> =>
  fetch(config.oauth.server.url.userInfo, {
    headers: { 'Authorization': `Bearer ${token.token.access_token}` }
  }).then(res => res.json());
