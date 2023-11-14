const fs = require('fs');

const buildColl = db.puzzle2;
const playColl = db.puzzle2_puzzle;
const blockColl = db.puzzle2_blocklist;

const blocklist = makeBlocklist('bad-puzzles.txt');

buildColl.deleteMany({ _id: { $in: blocklist } });
playColl.deleteMany({ _id: { $in: blocklist } });
blockColl.drop();
blocklist.forEach(_id => blockColl.updateOne({ _id }, { $set: { _id } }, { upsert: true }));

buffer = [];

function processBuffer(buf) {
  const existingIds = new Set(playColl.distinct('_id', { _id: { $in: buf.map(p => p._id) } }));
  const missing = buf
    .filter(p => !existingIds.has(p._id))
    .map(p => ({
      _id: p._id,
      gameId: p.gameId,
      fen: p.fen,
      themes: [],
      glicko: {
        r: 1500,
        d: 500,
        v: 0.09,
      },
      plays: NumberInt(0),
      vote: 1,
      vu: NumberInt(10),
      vd: NumberInt(0),
      line: p.moves.join(' '),
      cp: p.cp,
      tagMe: true,
    }));
  if (missing.length) playColl.insertMany(missing, { ordered: false });
}

buildColl
  .find({ _id: { $nin: blocklist }, createdAt: { $gt: new Date(Date.now() - 1000 * 3600 * 24 * 7) } })
  .forEach(p => {
    if (p.moves.length < 2) return;
    buffer.push(p);
    if (buffer.length >= 1000) {
      processBuffer(buffer);
      buffer = [];
    }
  });

processBuffer(buffer);

function makeBlocklist(file) {
  return fs
    .readFileSync(file)
    .toString('UTF8')
    .split('\n')
    .map(l => l.trim())
    .filter(l => l);
}
