#!/bin/sh
# This script belongs on rubik:/home/puzzler/puzzler-dump/load-puzzles.sh
# And is called by deploy-db.sh

mongorestore mongodb://localhost:27017 --db puzzler --collection puzzle2_puzzle puzzler/puzzle2_puzzle.bson --writeConcern '{w:0}' --noIndexRestore
mongorestore mongodb://localhost:27017 --db puzzler --collection puzzle2_round puzzler/puzzle2_round.bson --writeConcern '{w:0}' --noIndexRestore
mongorestore mongodb://localhost:27017 --db puzzler --collection puzzle2_blocklist puzzler/puzzle2_blocklist.bson --writeConcern '{w:0}' --noIndexRestore
mongosh puzzler --eval 'db.puzzle2_blocklist.find().forEach(p => db.puzzle2_puzzle.deleteOne(p))'
