#!/bin/sh
# This script belongs on rubik:/home/puzzler-crom-data/puzzler-dump/load-puzzles.sh
# And is called by deploy-db.sh

mongorestore mongodb://localhost:27017 --db puzzler --collection puzzle2_puzzle puzzler/puzzle2_puzzle.bson --writeConcern '{w:0}'
mongorestore mongodb://localhost:27017 --db puzzler --collection puzzle2_round puzzler/puzzle2_round.bson --writeConcern '{w:0}'
mongorestore mongodb://localhost:27017 --db puzzler --collection puzzle2_blocklist puzzler/puzzle2_blocklist.bson --writeConcern '{w:0}'
mongo puzzler --eval 'db.puzzle2_blocklist.find().forEach(p => db.puzzle2_puzzle.deleteOne(p))'
