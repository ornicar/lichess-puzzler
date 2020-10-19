lichess puzzler
---------------

Let's renew the puzzle collection.
We'll produce a collection of new puzzles out of the lichess game database.

We need a program that generates puzzles,
and one that allows manual validation and categorization of each and every puzzle.

## Generator
Use stockfish and database.lichess.org to produce puzzle candidates.
Python is probably the language of choice because of
https://github.com/niklasf/python-chess

The generator posts candidates to the validator.

## Validator
Stores puzzle candidates and lets people review them with a web UI.

Let's go with python and flask.

mongodb puzzle:
```
{
  _id: 1, // incremental
  createdAt: date,
  gameId: string,
  fen: string,
  ply: number,
  moves: [uci],
  review: { // after a review was done
    at: date,
    score: 0-5, // quality
    rating: 1200 // estimated rating
    topics: [string],
  }
}
```
