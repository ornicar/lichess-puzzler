#!/bin/sh

DIR=puzzler-dump

mongodump --db puzzler --collection puzzle2_puzzle --out $DIR
mongodump --db puzzler --collection puzzle2_round --out $DIR

mongorestore --db lichess --collection puzzle2_puzzle $DIR/puzzler/puzzle2_puzzle.bson 2> >(grep -v duplicate)
mongorestore --db lichess --collection puzzle2_round $DIR/puzzler/puzzle2_round.bson 2> >(grep -v duplicate)

mongo lichess bin/update-puzzle2_master.js

mongo puzzler bin/set-master-themes.js
