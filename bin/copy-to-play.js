const buildColl = db.puzzle2;
const playColl = db.puzzle2_puzzle;

buildColl.find().forEach(p => {
  try {
    p.glicko = {
      r: 1500,
      d: 500,
      v: 0.09
    };
    p.plays = 0;
    p.vote = 1;
    p.line = p.moves.join(' ');
    delete p.generator;
    delete p.ip;
    delete p.kind;
    delete p.moves;
    delete p.moves;
    playColl.insert(p);
  } catch {}
});
