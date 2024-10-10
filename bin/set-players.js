conn = Mongo();
lichess = conn.getDB('lichess');
puzzler = conn.getDB('puzzler');
load('bin/super-gms-list.js');

const titledUsers = new Set(lichess.user4.distinct('_id', { title: { $exists: 1, $ne: 'BOT' } }));

gms = 0;
titled = 0;
puzzler.puzzle2_puzzle.find({ users: { $exists: false } }, { gameId: 1, users: 1 }).forEach(p => {
  if (!p.users) {
    const game = lichess.game5.findOne({ _id: p.gameId });
    if (!game) throw `Missing game ${p.gameId} for puzzle ${p._id}`;
    p.users = game && game.us;
    if (p.users.length != 2) throw `Invalid users for puzzle ${p._id}: ${game}`;
    puzzler.puzzle2_puzzle.updateOne({ _id: p._id }, { $set: { users: p.users } });
  }

  const masters = p.users.filter(u => titledUsers.has(u)).length;
  const t = [];
  if (masters > 0) t.push('master');
  if (masters > 1) t.push('masterVsMaster');
  if (p.users.find(u => supergms.has(u))) {
    gms++;
    t.push('superGM');
  }
  if (t.length) {
    titled++;
    puzzler.puzzle2_puzzle.updateOne({ _id: p._id }, { $addToSet: { themes: { $each: t } } });
    puzzler.puzzle2_round.updateOne({ _id: 'lichess:' + p._id }, { $addToSet: { t: { $each: t.map(t => '+' + t) } } });
  }
});

print('titled: ', titled);
print('gms: ', gms);
