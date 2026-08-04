#!/bin/sh
set -e

cd ~/lichess-puzzler/tagger
. venv/bin/activate
echo "Themes"
python tagger.py
echo "Zug"
python tagger.py --zug

echo "Themes denormalize"
mongosh puzzler ~/lila/cron/mongodb-puzzle-denormalize-themes.js

# echo "Paths"
# mongo puzzler ~/lichess-sysadmin/cron/mongodb-puzzle-regen-paths.js
