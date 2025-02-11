#!/bin/sh
# This script belongs on rubik:/home/puzzler-crom-data/puzzler-dump/load-puzzles.sh
# And is called by deploy-db.sh

options="--db puzzler --writeConcern '{w:0}' --noIndexRestore"

mongorestore mongodb://localhost:27017 --collection puzzle2_puzzle puzzler/puzzle2_puzzle.bson $options
mongorestore mongodb://localhost:27017 --collection puzzle2_round puzzler/puzzle2_round.bson $options
mongorestore mongodb://localhost:27017 --collection puzzle2_blocklist puzzler/puzzle2_blocklist.bson $options
mongosh puzzler --eval 'db.puzzle2_blocklist.find().forEach(p => db.puzzle2_puzzle.deleteOne(p))'
