#!/bin/sh

echo "Download"
~/.scripts/fetch-mongodb-collection root@godot.lichess.ovh puzzler puzzle2

cd ~/lichess-puzzler
echo "Copy"
mongo puzzler bin/copy-to-play.js

echo "Phase"
cd ~/lichess-puzzler/phaser
sbt run

echo "Ratings"
cd ~/lichess-puzzler
mongo puzzler bin/random-ratings.js

echo "Votes"
cd ~/lichess-puzzler
mongo puzzler bin/random-votes.js

echo "Themes"
cd ~/lichess-puzzler
./bin/retag.sh

echo "Games"
cd ~/lichess-mongo-import
yarn run puzzle-game-all

cd ~/lichess-puzzler
