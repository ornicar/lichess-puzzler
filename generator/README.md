Generate puzzles from a game database.

So. What makes a good chess puzzle?

- forced moves. Each move, by the player or the opponent, should be the only reasonable move.
  - that means, for the player, that any other move loses brutally.
  - for the opponent, it means that any other moves loses way more brutally 
  than the puzzle solution already does.
    - e.g. getting checkmated instead of just losing material
    - allowing a faster checkmate?
- the player either checkmates or ends up with massive material advantage
- at the beginning of the puzzle, the win is not as obvious as it is at the end

these "obvious" mentions don't mean anything to stockfish. Only to humans.
That is where we need manual validation

- puzzles should also show diversity of motives and win condition.
- puzzles should happen in the opening, midgame and endgame.
- the opponent should play human-like moves, not obscure stockfish lines

- a puzzle should always start after a mistake/blunder of the opponent?

```
python3 -m venv venv
. venv/bin/activate
python3 generator.py -f file.pgn -t 6 -v -u http://localhost:8000/puzzle
```
