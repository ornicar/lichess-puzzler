// mongosh ~/.mongoshrc.js bin/fix-prod-players.js

mainSec = sec();
local = connect('localhost:27017/lichess');
puzzler = prod(ports.rubik, 'puzzler');
load('bin/super-gms-list.js');

const titledUsers = new Set(mainSec.user4.distinct('_id', { title: { $exists: 1, $ne: 'BOT' } }));

const count = puzzler.puzzle2_puzzle.estimatedDocumentCount();
const it = 0;

const batchUpdate = [];

const flushBatchUpdate = async () => {
  if (!batchUpdate.length) return;
  console.log(`Flushing ${batchUpdate.length} updates`);
  const writes = batchUpdate.map(update => ({ updateOne: update }))
  await puzzler.puzzle2_puzzle.bulkWrite(writes);
  batchUpdate.length = 0;
}

const scheduleUpdate = async (id, update) => {
  batchUpdate.push({ filter: { _id: id }, update });
  if (batchUpdate.length >= 200) await flushBatchUpdate();
}

// puzzler.puzzle2_puzzle.find({ users: { $exists: false } }, { gameId: 1 }).forEach(p => {
puzzler.puzzle2_puzzle.find({}, { gameId: 1, users: 1 }).forEach(async p => {
  game = local.game5.findOne({ _id: p.gameId }, { us: 1 });
  if (!game) {
    console.log(`Fetching game ${p.gameId} for puzzle ${p._id}`);
    game = mainSec.game5.findOne({ _id: p.gameId }, { us: 1 });
  }
  if (!game) throw `Missing game ${p.gameId} for puzzle ${p._id}`;
  const users = game.us;
  if (!users || users.length !== 2) {
    console.error(`Invalid users for puzzle ${p._id} and game ${JSON.stringify(game)}: ${users}`);
    return;
  }

  const masters = users.filter(u => titledUsers.has(u)).length;
  const t = [];
  if (masters > 0) t.push('master');
  if (masters > 1) t.push('masterVsMaster');
  if (users.find(u => supergms.has(u))) t.push('superGM');

  const update = {
    $set: { users },
    ...(t.length ? { $addToSet: { themes: { $each: t } } } : {})
  }

  if (t.length || users.join('') !== (p.users || []).join('')) {
    await scheduleUpdate(p._id, update);
  }

  if (t.length) {
    await puzzler.puzzle2_round.updateOne({ _id: 'lichess:' + p._id }, { $addToSet: { t: { $each: t.map(t => '+' + t) } } });
  }

  it++;
  if (it % 1000 == 0) console.log(`${it}/${count} ${p._id} -> ${users} | ${t.join('+')}`);
});

flushBatchUpdate();
