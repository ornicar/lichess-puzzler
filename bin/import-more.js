#!/bin/sh

~/.scripts/fetch-mongodb-collection root@godot.lichess.ovh puzzler puzzle2

cd ~/lichess-puzzler/tagger
. venv/bin/activate
python tagger.py

cd ~/lichess-puzzler/phaser
sbt run

cd ~/lichess-puzzler
mongo puzzler bin/copy-to-play.js
