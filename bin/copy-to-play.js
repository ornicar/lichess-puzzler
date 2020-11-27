const buildColl = db.puzzle2;
const playColl = db.puzzle2_puzzle;

buildColl.find({'review.approved':{$ne:false}}).forEach(p => {
  try {
    playColl.insert({
      _id: p._id,
      gameId: p.gameId,
      fen: p.fen,
      themes: p.tags,
      glicko: {
        r: 1500,
        d: 500,
        v: 0.09
      },
      plays: NumberInt(0),
      vote: NumberInt(1),
      line: p.moves.join(' ')
    });
  } catch {}
});
