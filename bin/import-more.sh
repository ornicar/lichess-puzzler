#!/bin/sh

echo "Download"
~/.scripts/fetch-mongodb-collection root@godot.lichess.ovh puzzler puzzle2

cd ~/lichess-puzzler
echo "Copy"
mongo puzzler bin/copy-to-play.js

echo "Tag"
cd ~/lichess-puzzler/tagger
. venv/bin/activate
python tagger.py

echo "Phase"
cd ~/lichess-puzzler/phaser
sbt run

echo "Ratings"
cd ~/lichess-puzzler
mongo puzzler bin/random-ratings.js

echo "Votes"
cd ~/lichess-puzzler
mongo puzzler bin/random-votes.js

echo "Paths"
cd ~/lichess-puzzler
mongo puzzler bin/make-paths.js

echo "Games"
cd ~/lichess-mongo-import
yarn run puzzle-game-all

cd ~/lichess-puzzler
