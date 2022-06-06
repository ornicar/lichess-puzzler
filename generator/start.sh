#!/bin/sh

cd ~/lichess-puzzler/generator/ && . venv/bin/activate && python generator.py -f ../data/lichess_db_standard_rated_2021-11.pgn.bz2 --url=http://192.168.1.200:9371 -e stockfish --token=t $@
