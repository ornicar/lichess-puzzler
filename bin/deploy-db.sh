#!/bin/sh

port=27517

for collection in puzzle2_puzzle puzzle2_round puzzle2_blocklist; do
  echo "Deploying $collection"
  mongodump -d puzzler -c $collection --archive |
    mongorestore --port=$port --archive # --dryRun -v # | rg -vF 'E11000'
done

echo "Removing blocked puzzles"
mongosh --port=$port --eval 'db.puzzle2_puzzle.deleteMany({_id:{$in:db.puzzle2_blocklist.distinct("_id")}})'
