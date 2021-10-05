#!/bin/sh

cd ~/lichess-puzzler/tagger
. venv/bin/activate
echo "Themes"
python tagger.py --threads=10
echo "Zug"
python tagger.py --zug --threads=10

echo "Themes denormalize"
mongo puzzler ~/lichess-sysadmin/cron/mongodb-puzzle-denormalize-themes.js

echo "Paths"
# mongo puzzler ~/lichess-sysadmin/cron/mongodb-puzzle-regen-paths.js
