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

echo "Masters"
cd ~/lichess-puzzler
./bin/master-theme.sh

cd ~/lichess-puzzler
