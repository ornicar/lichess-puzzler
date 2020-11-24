#!/bin/sh

echo "Download"
~/.scripts/fetch-mongodb-collection root@godot.lichess.ovh puzzler puzzle2

echo "Tag"
cd ~/lichess-puzzler/tagger
. venv/bin/activate
python tagger.py

echo "Phase"
cd ~/lichess-puzzler/phaser
sbt run

cd ~/lichess-puzzler
echo "Copy"
mongo puzzler bin/copy-to-play.js
echo "Votes"
mongo puzzler bin/random-votes.js
echo "Paths"
mongo puzzler bin/make-paths.js

echo "Games"
cd ~/lichess-mongo-import
yarn run puzzle-game-all

cd ~/lichess-puzzler
