#!/bin/sh

TARGET=root@study.lichess.ovh
DIR=puzzler-dump

rm -rf $DIR
mongodump --db puzzler --collection puzzle2_puzzle --out $DIR
mongodump --db puzzler --collection puzzle2_round --out $DIR
mongodump --db puzzler --collection puzzle2 --out $DIR

rsync -av $DIR $TARGET:/home/puzzler-crom-data
