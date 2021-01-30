#!/bin/sh

echo "Download"
~/.scripts/fetch-mongodb-collection root@godot.lichess.ovh puzzler puzzle2

echo "Games"
cd ~/lichess-mongo-import
yarn run puzzle-game-all

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
