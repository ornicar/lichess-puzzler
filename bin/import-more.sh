#!/bin/sh
set -e

source=192.168.1.200

echo "Tag new puzzles"
mongo $source:27017/puzzler --eval 'db.puzzle2.update({recent:true},{$unset:{recent:true}});db.puzzle2.updateMany({createdAt:{$gt:new Date(Date.now() - 1000 * 3600 * 24 * 7)}},{$set:{recent:true}})'

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
mongo puzzler bin/copy-to-play.js

echo "Phase"
cd ~/lichess-puzzler/phaser
sbt run

echo "Themes"
cd ~/lichess-puzzler
./bin/retag.sh

echo "Players"
cd ~/lichess-puzzler
mongo ./bin/set-players.js

cd ~/lichess-puzzler
./bin/deploy-db.sh

ssh "root@rubik.lichess.ovh" 'cd /home/puzzler-crom-data/puzzler-dump && ./load-puzzles.sh'
