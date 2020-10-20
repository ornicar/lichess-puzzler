#!/usr/bin/env python

import chess
import chess.pgn

import argparse

parser = argparse.ArgumentParser(description='Generate chess puzzles out of a PGN file')
parser.add_argument('file', nargs=1, help='the PGN file')

args = parser.parse_args()
print(args.file)

pgn = open(args.file[0], "r", encoding="utf-8")
game = chess.pgn.read_game(pgn)

print(game)
