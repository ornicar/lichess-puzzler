#!/bin/sh
set -e

source=192.168.1.200

echo "Tag new puzzles"
mongosh $source:27017/puzzler --eval 'db.puzzle2.updateMany({recent:true},{$unset:{recent:true}});db.puzzle2.updateMany({createdAt:{$gt:new Date(Date.now() - 1000 * 3600 * 24 * 14)}},{$set:{recent:true}})'

echo "Download"
mongodump --db=puzzler --collection=puzzle2 --host=$source --gzip --archive --query '{"recent":true}' | mongorestore --gzip --archive --drop

echo "Games"
cd ~/lichess-mongo-import
yarn run puzzle-game-all

echo "Users"
cd ~/lichess-mongo-import
yarn run puzzle-game-user

cd ~/lichess-puzzler
echo "Copy"
mongosh puzzler bin/copy-to-play.js

echo "Themes"
cd ~/lichess-puzzler
./bin/retag.sh

echo "Players"
cd ~/lichess-puzzler
mongosh ./bin/set-players.js

cd ~/lichess-puzzler
./bin/deploy-db.sh

ssh "root@rubik.lichess.ovh" 'cd /home/puzzler-crom-data/puzzler-dump && ./load-puzzles.sh'
