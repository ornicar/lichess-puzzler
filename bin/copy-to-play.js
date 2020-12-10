const buildColl = db.puzzle2;
const playColl = db.puzzle2_puzzle;

buffer = [];

function process(buf) {
  const existingIds = new Set(playColl.distinct('_id', {_id:{$in:buf.map(p => p._id)}}));
  const missing = buf.filter(p => !existingIds.has(p._id)).map(p => ({
    _id: p._id,
    gameId: p.gameId,
    fen: p.fen,
    themes: [],
    glicko: {
      r: 1500,
      d: 500,
      v: 0.09
    },
    plays: NumberInt(0),
    vote: NumberInt(1),
    line: p.moves.join(' '),
    cp: p.cp
  }));
  if (missing.length) playColl.insertMany(missing, {ordered:false});
}

buildColl.find({'review.approved':{$ne:false}}).forEach(p => {
  if (p.moves.length < 2) return;
  buffer.push(p);
  if (buffer.length >= 1000) {
    process(buffer);
    buffer = [];
  }
});

process(buffer);
