// mongosh ~/.mongoshrc.js bin/fix-prod-players.js
mainSec = sec();
local = connect('localhost:27017/lichess');
puzzler = prod(ports.rubik, 'puzzler');

const count = puzzler.puzzle2_puzzle.count({ users: { $exists: false } });
const it = 0;
puzzler.puzzle2_puzzle.find({ users: { $exists: false } }, { gameId: 1 }).forEach(p => {
  const game = local.game5.findOne({ _id: p.gameId }, { us: 1 }) || mainSec.game5.findOne({ _id: p.gameId }, { us: 1 });
  if (!game) throw `Missing game ${p.gameId} for puzzle ${p._id}`;
  const users = game.us;
  if (users.length !== 2) throw `Invalid users for puzzle ${p._id}: ${users}`;
  puzzler.puzzle2_puzzle.update({ _id: p._id }, { $set: { users } });
  it++;
  console.log(`${it}/${count} ${p._id} -> ${users}`);
});
