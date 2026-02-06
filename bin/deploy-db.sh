#!/bin/sh

TARGET=thonk-nokey
DIR=puzzler-dump

echo "Dumping collections to $DIR"
rm -rf $DIR
mongodump --db puzzler --collection puzzle2_puzzle --out $DIR
mongodump --db puzzler --collection puzzle2_round --out $DIR
mongodump --db puzzler --collection puzzle2 --out $DIR
mongodump --db puzzler --collection puzzle2_blocklist --out $DIR

echo "Sending $DIR to $TARGET"
rsync -av $DIR $TARGET:/home/puzzler

ssh $TARGET 'cd /home/puzzler/puzzler-dump && ./load-puzzles.sh'
