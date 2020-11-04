db.puzzle2.ensureIndex({gameId:1},{unique:true});
db.puzzle2.ensureIndex({fen:1,'moves.0':1},{unique:true});

const chars = '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ';
function randomId() {
  let result = '';
  for (let i = 5; i > 0; --i) result += chars[Math.floor(Math.random() * chars.length)];
  return result;
}

db.puzzle.find().forEach(p => {
  p._id = randomId()
  db.puzzle2.insert(p);
});
