#!/bin/sh

TARGET=root@rubik.lichess.ovh
DIR=puzzler-dump

echo "Dumping collections to $DIR"
rm -rf $DIR
mongodump --db puzzler --collection puzzle2_puzzle --out $DIR
mongodump --db puzzler --collection puzzle2_round --out $DIR
mongodump --db puzzler --collection puzzle2 --out $DIR

echo "Sending $DIR to $TARGET"
rsync -av $DIR $TARGET:/home/puzzler-crom-data

ssh $TARGET 'cd /home/puzzler-crom-data/puzzler-dump && ./load-puzzles.sh'
