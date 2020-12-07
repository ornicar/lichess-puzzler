#!/bin/sh

echo "Themes"
cd ~/lichess-puzzler/tagger
. venv/bin/activate
python tagger.py

echo "Themes denormalize"
mongo puzzler ~/lichess-sysadmin/cron/mongodb-puzzle-denormalize-themes.js

echo "Paths"
mongo puzzler ~/lichess-sysadmin/cron/mongodb-puzzle-regen-paths.js
