# UI to manually review new puzzle candidates

## Dev

```
cd front
yarn install
yarn dev
cd ../back
export OAUTH_APP_SECRET='lichessOauthAppSecret'
export COOKIE_SECRET='sessionCookieSecret'
yarn dev
```

## Prod

```
cd back
yarn build
export OAUTH_APP_SECRET='lichessOauthAppSecret'
export COOKIE_SECRET='sessionCookieSecret'
yarn start
```
