#!/bin/sh

TARGET=mongodb://localhost:27517/puzzler

for collection in puzzle2_puzzle puzzle2_round puzzle2_blocklist; do
  echo "Deploying $collection"
  mongodump -d puzzler -c $collection --archive | mongorestore -d puzzler -c $collection --archive $target
done

echo "Removing blocked puzzles"
mongosh $TARGET --eval 'db.puzzle2_blocklist.find().forEach(p => db.puzzle2_puzzle.deleteOne(p))'
