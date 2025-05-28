#!/bin/sh
set -e

cd ~/lichess-puzzler/tagger
. venv/bin/activate
echo "Themes"
python tagger.py --threads=1
echo "Zug"
python tagger.py --zug --threads=2

echo "Themes denormalize"
mongosh puzzler ~/lila/cron/mongodb-puzzle-denormalize-themes.js

# echo "Paths"
# mongo puzzler ~/lichess-sysadmin/cron/mongodb-puzzle-regen-paths.js
